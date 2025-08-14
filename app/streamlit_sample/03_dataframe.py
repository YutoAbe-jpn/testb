import datetime

import pandas as pd
import streamlit as st

df = pd.DataFrame(
    {
        "area": [1, 1, 1, 3, 3, 3],
        "date": [
            datetime.date(2019, 12, 1),
            datetime.date(2019, 12, 2),
            datetime.date(2019, 12, 3),
            datetime.date(2019, 12, 1),
            datetime.date(2019, 12, 2),
            datetime.date(2019, 12, 3),
        ],
        "num_trip": [100, 200, 300, 200, 400, 600],
        "label": ["実績", "実績", "予測", "実績", "実績", "予測"],
    }
)

st.dataframe(df)
