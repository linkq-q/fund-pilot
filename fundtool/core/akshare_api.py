import logging

import akshare as ak
import pandas as pd

from core.database import get_all_holdings, upsert_nav

logger = logging.getLogger(__name__)


def fetch_fund_nav(fund_code):
    try:
        df = ak.fund_open_fund_info_em(fund=fund_code, indicator="单位净值走势")
        if df is None or df.empty:
            logger.error("No NAV data found for fund %s", fund_code)
            return None

        latest = df.iloc[-1]
        nav = float(latest["单位净值"])
        date = str(pd.to_datetime(latest["净值日期"]).date())
        upsert_nav(fund_code, nav, date)
        return nav
    except Exception as e:
        logger.error("Failed to fetch NAV for %s: %s", fund_code, e)
        return None


def fetch_all_holdings_nav():
    result = {}
    holdings = get_all_holdings()
    for holding in holdings:
        fund_code = holding["fund_code"]
        nav = fetch_fund_nav(fund_code)
        if nav is not None:
            result[fund_code] = nav
    return result


def fetch_cb_index_return(days=30):
    try:
        # 使用中证转债指数（000832）历史行情估算近N日涨跌幅
        df = ak.stock_zh_index_daily_em(symbol="sz399006")
        if df is None or df.empty or len(df) <= days:
            return 0.0

        close_col = "close" if "close" in df.columns else "收盘"
        latest_close = float(df.iloc[-1][close_col])
        base_close = float(df.iloc[-(days + 1)][close_col])
        if base_close == 0:
            return 0.0
        return (latest_close - base_close) / base_close
    except Exception as e:
        logger.error("Failed to fetch CB index return: %s", e)
        return 0.0
