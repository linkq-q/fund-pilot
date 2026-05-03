from datetime import datetime

from config import ANNUAL_TARGET
from core.database import (
    get_holding,
    get_latest_nav,
    get_nav_history,
    get_transactions,
)


def calc_profit_rate(buy_amount, current_value):
    if buy_amount == 0:
        return 0
    return (current_value - buy_amount) / buy_amount


def calc_hold_days(buy_date_str):
    buy_date = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
    return (datetime.now().date() - buy_date).days


def calc_annualized_return(profit_rate, hold_days):
    if hold_days == 0:
        return 0
    return (profit_rate / hold_days) * 365


def calc_annualized_multiple(annualized_return, target=ANNUAL_TARGET):
    if target == 0:
        return 0
    return annualized_return / target


def calc_current_value(shares, latest_nav):
    return shares * latest_nav


def calc_position_ratio(current_value, total_portfolio_value, cash_pool):
    denominator = total_portfolio_value + cash_pool
    if denominator == 0:
        return 0
    return current_value / denominator


def calc_drawdown(fund_code, days=90):
    history = get_nav_history(fund_code, days)
    if len(history) < 2:
        return 0
    navs = [item["nav"] for item in history]
    peak = max(navs)
    current = navs[0]
    if peak == 0:
        return 0
    drawdown = (peak - current) / peak
    return max(drawdown, 0)


def calc_days_since_last_action(fund_code):
    txs = get_transactions(fund_code)
    if not txs:
        return 999
    last_date = datetime.strptime(txs[0]["date"], "%Y-%m-%d").date()
    return (datetime.now().date() - last_date).days


def build_fund_snapshot(fund_code, cash_pool, total_portfolio_value):
    holding = get_holding(fund_code)
    if holding is None:
        raise ValueError(f"Holding not found for fund_code={fund_code}")

    latest_nav_row = get_latest_nav(fund_code)
    latest_nav = latest_nav_row["nav"] if latest_nav_row else 0

    current_value = calc_current_value(holding["shares"], latest_nav)
    profit_rate = calc_profit_rate(holding["buy_amount"], current_value)
    hold_days = calc_hold_days(holding["buy_date"])
    annualized_return = calc_annualized_return(profit_rate, hold_days)
    annualized_multiple = calc_annualized_multiple(annualized_return)
    position_ratio = calc_position_ratio(current_value, total_portfolio_value, cash_pool)
    drawdown = calc_drawdown(fund_code)
    days_since_last_action = calc_days_since_last_action(fund_code)

    return {
        "fund_code": holding["fund_code"],
        "fund_name": holding["fund_name"],
        "fund_role": holding["fund_role"],
        "buy_amount": holding["buy_amount"],
        "current_value": current_value,
        "profit_rate": profit_rate,
        "hold_days": hold_days,
        "annualized_return": annualized_return,
        "annualized_multiple": annualized_multiple,
        "position_ratio": position_ratio,
        "drawdown": drawdown,
        "days_since_last_action": days_since_last_action,
        "cash_pool_available": cash_pool,
    }
