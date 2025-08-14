import pandas as pd
import streamlit as st

uploaded_file = st.file_uploader("予測用ファイルをアップロードしてください", type="csv")
if uploaded_file is not None:
    df_upload = pd.read_csv(uploaded_file, parse_dates=["date"])
    df_upload["area"] = df_upload["area"].astype("category")
    st.dataframe(df_upload)
