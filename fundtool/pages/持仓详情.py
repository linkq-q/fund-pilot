import streamlit as st

from core.calculator import build_fund_snapshot
from core.database import get_all_holdings, get_cash_pool, get_latest_advice, get_transactions

st.title("持仓详情")
holdings = get_all_holdings()
if not holdings:
    st.info("暂无持仓")
    st.stop()

name_map = {f"{h['fund_name']}({h['fund_code']})": h for h in holdings}
selected = st.selectbox("选择基金", list(name_map.keys()))
h = name_map[selected]

snapshot = build_fund_snapshot(h['fund_code'], get_cash_pool(), sum([x['buy_amount'] for x in holdings]))
advice = get_latest_advice(h['fund_code'])

left, right = st.columns(2)
with left:
    st.subheader("基础数据")
    st.write(f"买入金额：¥{snapshot['buy_amount']:.2f}")
    st.write(f"当前市值：¥{snapshot['current_value']:.2f}")
    pr = snapshot['profit_rate']
    color = 'green' if pr > 0 else 'red'
    st.markdown(f"持有收益率：:<span style='color:{color}'>{pr:.2%}</span>", unsafe_allow_html=True)
    st.write(f"持有天数：{snapshot['hold_days']}")
    ar = snapshot['annualized_return']
    ar_color = 'green' if ar >= 0.12 else ('red' if ar < 0 else 'orange')
    st.markdown(f"折算年化收益率：<span style='color:{ar_color}'>{ar:.2%}</span>", unsafe_allow_html=True)
    st.write(f"年化倍数：{snapshot['annualized_multiple']:.2f}")

with right:
    st.subheader("AI建议")
    if advice:
        st.write(f"命中分支：{advice['branch']}")
        st.write(f"建议操作：{advice['action']}")
        st.write(f"置信度：{advice['confidence']}")
        st.write(f"理由：{advice['reason']}")
        st.write(f"风险提示：{advice['risk_warning']}")
        st.write(f"建议变动：{advice['cash_pool_change']}")
    else:
        st.info("暂无建议")

st.subheader("历史交易")
st.dataframe(get_transactions(h['fund_code']))
