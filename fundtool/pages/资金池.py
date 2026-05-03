from datetime import date

import streamlit as st

from core.database import get_all_holdings, get_cash_pool, get_cash_pool_log, update_cash_pool

st.title("资金池")
cash = get_cash_pool()
st.markdown(f"## 当前可投资金池余额：¥{cash:,.2f}")

principal = sum([h['buy_amount'] for h in get_all_holdings()])
ratio = principal / (principal + cash) if principal + cash > 0 else 0
st.write("资金利用率")
st.progress(min(max(ratio, 0), 1))

st.subheader("历史流水")
logs = get_cash_pool_log()
running = cash
show = []
for item in logs:
    show.append({"日期": item['date'], "变动金额": item['change_amount'], "原因": item['reason'], "变动后余额": running})
    running -= item['change_amount']
st.dataframe(show)

st.subheader("手动调整")
amount = st.number_input("调整金额(充值为正，支出为负)", value=0.0)
reason = st.text_input("原因", value="手动调整")
if st.button("提交调整"):
    update_cash_pool(amount, reason, str(date.today()))
    st.success("调整完成")
