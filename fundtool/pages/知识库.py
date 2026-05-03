import streamlit as st

from core.database import get_all_cards

st.title("知识库")
keyword = st.text_input("按术语名称搜索", "")
cards = get_all_cards()
if keyword:
    cards = [c for c in cards if keyword.lower() in c['term'].lower()]

for c in cards:
    with st.container(border=True):
        st.caption(c['date'])
        st.markdown(f"### {c['term']}")
        st.write(c['explanation'])
        st.write(f"例子：{c['example']}")
