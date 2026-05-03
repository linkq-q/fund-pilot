from datetime import date

import sqlite3
import streamlit as st

from core.akshare_api import fetch_fund_nav
from core.database import (
    DB_PATH,
    add_holding,
    add_transaction,
    get_all_holdings,
    get_latest_nav,
    update_cash_pool,
)

st.title("交易记录")

with st.form("buy_form"):
    st.subheader("买入录入")
    fund_code = st.text_input("基金代码")
    fund_name = st.text_input("基金名称")
    fund_role = st.selectbox("基金角色", ["底仓", "收益型"])
    buy_amount = st.number_input("买入金额", min_value=0.0, value=0.0)
    buy_date = st.date_input("买入日期", value=date.today())
    if st.form_submit_button("提交买入"):
        nav = fetch_fund_nav(fund_code) or (get_latest_nav(fund_code) or {}).get("nav", 1)
        shares = buy_amount / nav if nav else 0
        add_holding(fund_code, fund_name, fund_role, buy_amount, str(buy_date), shares)
        add_transaction(fund_code, "买入", buy_amount, str(buy_date), "手动买入")
        update_cash_pool(-buy_amount, f"买入{fund_code}", str(buy_date))
        st.success("买入已记录")

holdings = get_all_holdings()
if holdings:
    with st.form("sell_form"):
        st.subheader("减仓录入")
        fund_map = {f"{h['fund_name']}({h['fund_code']})": h for h in holdings}
        sel = st.selectbox("选择基金", list(fund_map.keys()))
        amount = st.number_input("减仓金额", min_value=0.0, value=0.0)
        sell_date = st.date_input("操作日期", value=date.today(), key="sell_date")
        if st.form_submit_button("提交减仓"):
            h = fund_map[sel]
            ratio = amount / h['buy_amount'] if h['buy_amount'] else 0
            new_shares = max(h['shares'] * (1 - ratio), 0)
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE holdings SET shares=? WHERE fund_code=?", (new_shares, h['fund_code']))
            conn.commit(); conn.close()
            add_transaction(h['fund_code'], "减仓", amount, str(sell_date), "手动减仓")
            update_cash_pool(amount, f"减仓{h['fund_code']}", str(sell_date))
            st.success("减仓已记录")

st.subheader("历史流水")
conn = sqlite3.connect(DB_PATH)
rows = conn.execute("SELECT * FROM transactions ORDER BY date DESC,id DESC").fetchall()
conn.close()
st.dataframe(rows)
