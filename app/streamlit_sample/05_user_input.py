import streamlit as st

list_selected_area: list[str] = st.multiselect("エリアを選択", ["1", "3"])
display_period = st.slider("表示期間（日）", min_value=1, max_value=100, value=30)

st.write(f"選択したエリア: {list_selected_area}、表示期間: {display_period}日")
