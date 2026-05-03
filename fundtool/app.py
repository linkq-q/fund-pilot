from datetime import datetime

import pandas as pd
import streamlit as st

from core.database import get_cash_pool, init_db
from core.scheduler import trigger_manually

init_db()

st.set_page_config(page_title="基金助手", layout="wide")
st.title("基金助手")

cash = get_cash_pool()
st.sidebar.markdown("### 可投资金池")
st.sidebar.markdown(f"## ¥{cash:,.2f}")
st.sidebar.caption(f"今日最后更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if st.sidebar.button("立即刷新数据"):
    summary = trigger_manually()
    st.sidebar.success("刷新完成")
    st.sidebar.json(summary)

st.write("请从左侧页面导航查看详情。")
