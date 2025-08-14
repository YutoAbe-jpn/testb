import datetime
from pathlib import Path

import pandas as pd
import pandera as pa
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pandera.typing import DataFrame

from taxi_prediction.model import LGBModel
from taxi_prediction.process import postprocess, preprocess_for_infer
from taxi_prediction.schema import TaxiDatasetSchema


@st.cache_resource
def load_model(model_path: str | Path) -> LGBModel:
    """学習済みモデルを読み込む"""
    return LGBModel.load(model_path)


@st.cache_data
@pa.check_types
def inference_usecase(
    df: DataFrame[TaxiDatasetSchema],
    model_path: str | Path,
    predict_start_date: datetime.date,
) -> DataFrame[TaxiDatasetSchema]:
    """推論のワークフロー。前処理から予測までの一連の処理を行う"""
    df_processed = preprocess_for_infer(df)
    model = load_model(model_path)
    df_pred = model.predict(df_processed)
    return postprocess(df_pred, predict_date=predict_start_date)


def _filter_by_area(df: pd.DataFrame, list_selected_area: list[str]) -> pd.DataFrame:
    """ユーザーが入力したエリアでデータをフィルタリングする

    Note: list_selected_areaが空の場合はすべてのエリアを選択する
    """
    if len(list_selected_area) == 0:
        return df
    return df[df["area"].isin(list_selected_area)]


def _filter_by_display_period(df: pd.DataFrame, display_period: int) -> pd.DataFrame:
    """最新の日付から指定された表示期間（日数）分のデータを抽出する"""
    return df[df["date"] > df["date"].max() - pd.Timedelta(days=display_period)]


def _plot_prediction(df: pd.DataFrame) -> go.Figure:
    """予測結果をグラフ化する"""
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


def main() -> None:
    model_path = "model/model.pickle"

    st.title("タクシーの乗車数予測")
    st.write("タクシーの乗車数を予測するプロトタイプです。")
    st.header("予測用ファイルのアップロード")

    uploaded_file = st.file_uploader(
        "予測用ファイルをアップロードしてください", type="csv"
    )

    if uploaded_file is not None:
        df_upload = pd.read_csv(uploaded_file, parse_dates=["date"])
        df_upload["area"] = df_upload["area"].astype("category")

        st.header("予測結果の表示")
        list_selected_area: list[str] = st.multiselect(
            "エリアを選択", df_upload["area"].unique()
        )
        display_period = st.slider(
            "実績データの表示期間（日）", min_value=1, max_value=100, value=30
        )

        df_upload = _filter_by_area(df_upload, list_selected_area)
        df_upload = _filter_by_display_period(df_upload, display_period)

        df_pred = inference_usecase(
            df_upload, model_path=model_path, predict_start_date=df_upload["date"].max()
        )

        df_upload["label"] = "実績"
        df_pred["label"] = "予測"

        df_concat = pd.concat([df_upload, df_pred], ignore_index=True)

        fig = _plot_prediction(df_concat)
        st.plotly_chart(fig)


if __name__ == "__main__":
    main()
