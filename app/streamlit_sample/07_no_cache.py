import time

import streamlit as st


def heavy_process() -> str:
    time.sleep(3)
    return "heavy process"


display_period = st.slider("表示期間（日）", min_value=1, max_value=100, value=30)
heavy_process()
st.write(f"表示期間: {display_period}日")
