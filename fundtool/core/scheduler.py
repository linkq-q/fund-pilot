import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from core.akshare_api import fetch_all_holdings_nav
from core.calculator import build_fund_snapshot, calc_current_value
from core.database import (
    get_all_holdings,
    get_cash_pool,
    get_latest_nav,
    get_today_advice,
    get_today_card,
    save_daily_advice,
    save_daily_card,
    update_cash_pool,
)
from core.deepseek_api import generate_advice, generate_daily_card
from core.router import run_router

logger = logging.getLogger(__name__)


def _branch_priority(branch):
    order = ["Branch_6", "Branch_5", "Branch_4", "Branch_1", "Branch_7", "Branch_2", "Branch_0", "Branch_3"]
    for i, b in enumerate(order):
        if branch.startswith(b):
            return i
    return 999


def run_daily_pipeline():
    errors = []
    nav_updated = 0
    advice_generated = 0
    card_generated = False
    run_date = datetime.now().strftime("%Y-%m-%d")

    # step1
    nav_map = {}
    try:
        nav_map = fetch_all_holdings_nav()
        nav_updated = len(nav_map)
    except Exception as e:
        errors.append(f"步骤1失败: {e}")
        logger.exception("step1 failed")

    holdings = []
    total_portfolio_value = 0
    try:
        holdings = get_all_holdings()
        for h in holdings:
            latest = get_latest_nav(h["fund_code"])
            nav = latest["nav"] if latest else 0
            total_portfolio_value += calc_current_value(h["shares"], nav)
    except Exception as e:
        errors.append(f"步骤2失败: {e}")
        logger.exception("step2 failed")

    cash_pool = 0
    try:
        cash_pool = get_cash_pool()
    except Exception as e:
        errors.append(f"步骤3失败: {e}")
        logger.exception("step3 failed")

    for h in holdings:
        try:
            snapshot = build_fund_snapshot(h["fund_code"], cash_pool, total_portfolio_value)
            router_result = run_router(snapshot)

            if router_result.get("skip"):
                result = {
                    "action": "跳过",
                    "confidence": 0.0,
                    "reason": router_result.get("skip_reason", "本次跳过"),
                    "risk_warning": None,
                    "cash_pool_change": 0,
                }
            else:
                result = generate_advice(snapshot, router_result)

            save_daily_advice(
                run_date,
                h["fund_code"],
                router_result.get("branch", "Unknown"),
                result.get("action"),
                result.get("confidence"),
                result.get("reason"),
                result.get("risk_warning"),
                result.get("cash_pool_change", 0),
            )
            advice_generated += 1

            if result.get("cash_pool_change", 0) != 0:
                update_cash_pool(result["cash_pool_change"], f"AI建议:{h['fund_code']}", run_date)
                cash_pool = get_cash_pool()
        except Exception as e:
            errors.append(f"步骤4基金{h['fund_code']}失败: {e}")
            logger.exception("step4 failed for %s", h["fund_code"])

    try:
        if get_today_card() is None:
            advices = get_today_advice()
            if advices:
                top = sorted(advices, key=lambda x: _branch_priority(x.get("branch", "")))[0]
                card = generate_daily_card(top.get("branch", ""), top.get("fund_code", ""))
                if card:
                    save_daily_card(run_date, card["term"], card["explanation"], card["example"])
                    card_generated = True
    except Exception as e:
        errors.append(f"步骤5失败: {e}")
        logger.exception("step5 failed")

    return {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nav_updated": nav_updated,
        "advice_generated": advice_generated,
        "card_generated": card_generated,
        "errors": errors,
    }


def trigger_manually():
    summary = run_daily_pipeline()
    print(summary)
    return summary


def setup_scheduler():
    scheduler = BackgroundScheduler()
    # scheduler.add_job(run_daily_pipeline, "cron", day_of_week="0-4", hour=13, minute=50)
    # scheduler.start()
    return scheduler
