import pandas as pd
import streamlit as st

from core.database import get_all_holdings, get_cash_pool, get_today_advice, get_today_card

st.title("今日总览")

holdings = get_all_holdings()
total_value = sum([h.get('buy_amount', 0) for h in holdings])
cash = get_cash_pool()
advice_list = get_today_advice()

c1, c2, c3 = st.columns(3)
c1.metric("总持仓市值", f"¥{total_value:,.2f}")
c2.metric("可投资金池余额", f"¥{cash:,.2f}")
c3.metric("今日建议基金数量", len(advice_list))

st.subheader("建议列表")
if not advice_list:
    st.info("今日建议尚未生成，请点击侧边栏刷新")
else:
    for a in advice_list:
        with st.container(border=True):
            st.write(f"**{a['fund_code']}** | `{a['branch']}` | {a['action']}")
            st.progress(max(min(float(a.get('confidence', 0)), 1), 0))
            st.write(a.get("reason", ""))
            if a.get("risk_warning"):
                st.error(a["risk_warning"])

card = get_today_card()
if card:
    st.subheader("今日知识卡片")
    st.markdown(f"## {card['term']}")
    st.write(card["explanation"])
    st.write(f"例子：{card['example']}")
