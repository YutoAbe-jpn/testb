import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def _plot_prediction(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df, x="date", y="num_trip", color="area", markers=True, line_dash="label"
    )
    fig.update_layout(
        title="乗車数の推移",
        xaxis_title="日付",
        yaxis_title="乗車数",
        legend_title="エリア, ラベル",
    )
    return fig


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

fig = _plot_prediction(df)
st.plotly_chart(fig)
