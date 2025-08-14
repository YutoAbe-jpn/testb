import datetime
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from .consts import MAX_PREDICT_DAYS
from .schema import (
    InferInputSchema,
    InferOutputSchema,
    TaxiDatasetSchema,
    TrainInputSchema,
)


@pa.check_types
def load_dataset(filepath: str | Path) -> DataFrame[TaxiDatasetSchema]:
    """
    タクシー乗降数のデータセットを読み込む
    """
    df = pd.read_csv(filepath, parse_dates=["date"])
    df["area"] = df["area"].astype("category")
    return df  # type: ignore


@pa.check_types
def split_dataset(
    df: DataFrame[TaxiDatasetSchema], train_ratio: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    データセットを時系列に沿って2つに分割する
    """
    df = df.sort_values("date").reset_index(drop=True)
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx], df.iloc[split_idx:]


@pa.check_types
def preprocess_for_infer(
    df: DataFrame[TaxiDatasetSchema], max_predict_days: int = MAX_PREDICT_DAYS
) -> DataFrame[InferInputSchema]:
    """
    特徴量を加工し推論用のデータを返す
    """
    # 特徴量を追加
    df = df.assign(weekday=df["date"].dt.weekday.astype(int))

    df_result = pd.DataFrame()
    for lead in range(1, max_predict_days + 1):
        # 予測対象日は何日後か (target_lead) と予測対象日 (target_date) を付加
        df_sub = df.assign(
            target_lead=lead,
            target_date=df["date"] + pd.Timedelta(days=lead),
        )
        df_result = pd.concat([df_result, df_sub])

    df_result = df_result.sort_values(["area", "date", "target_date"]).set_index(
        ["date", "target_date"]
    )

    return df_result  # type: ignore


@pa.check_types
def preprocess_for_train(
    df: DataFrame[TaxiDatasetSchema], max_predict_days: int = MAX_PREDICT_DAYS
) -> DataFrame[TrainInputSchema]:
    """
    推論用データに目的変数を追加した学習用データを返す
    """
    df_result = preprocess_for_infer(
        df, max_predict_days=max_predict_days
    ).reset_index()

    # 目的変数を付加
    df_target = df[["area", "date", "num_trip"]].rename(
        columns={"date": "target_date", "num_trip": "target"}
    )
    df_result = (
        df_result.merge(
            df_target, on=["area", "target_date"], how="left", validate="m:1"
        )
        .dropna(subset=["target"])
        .convert_dtypes()
    )

    df_result = df_result.sort_values(["area", "date", "target_date"]).set_index(
        ["date", "target_date"]
    )

    return df_result  # type: ignore


@pa.check_types
def postprocess(
    df: DataFrame[InferOutputSchema],
    predict_date: datetime.date,
    max_predict_days: int = MAX_PREDICT_DAYS,
) -> DataFrame[TaxiDatasetSchema]:
    """
    モデルの出力を後処理する
    predict_dateからMAX_PREDICT_DAYS日後までの予測を元のデータセットと同様の形式で取得する
    """
    df = df.reset_index()

    # predict_dateからMAX_PREDICT_DAYS日後までの予測に対応する部分を抽出
    predict_datetime = pd.to_datetime(predict_date)
    df_filtered = df[
        (df["date"] == predict_datetime)
        & (df["target_date"] >= predict_datetime + pd.Timedelta(days=1))
        & (df["target_date"] <= predict_datetime + pd.Timedelta(days=max_predict_days))
    ]

    # TaxiDatasetSchemaの形式に変換
    df_result = (
        df_filtered[["target_date", "area", "pred"]]
        .rename(columns={"target_date": "date", "pred": "num_trip"})
        .sort_values(by=["area", "date"])
        .reset_index(drop=True)
    )
    df_result["num_trip"] = df_result["num_trip"].clip(lower=0).astype(int)

    # すべてのエリアに対して予測値が揃っているかチェック
    expected_nrows = df["area"].nunique() * max_predict_days
    if len(df_result) != expected_nrows:
        raise ValueError(
            "Number of extracted rows does not match the expected value. "
            f"Expected: {expected_nrows}, Actual: {len(df_result)}"
        )

    return df_result  # type: ignore
