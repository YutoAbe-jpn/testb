import io

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from pandera.typing import DataFrame

from taxi_prediction.process import preprocess_for_infer, preprocess_for_train
from taxi_prediction.schema import TaxiDatasetSchema


@pytest.fixture
def df_sample() -> DataFrame[TaxiDatasetSchema]:
    csv_data = """
date,area,num_trip
2024-01-01,1,5
2024-01-02,1,8
2024-01-01,2,20
2024-01-02,2,18
"""
    df = pd.read_csv(io.StringIO(csv_data), parse_dates=["date"])
    df["area"] = df["area"].astype("category")
    return df  # type: ignore


def test_preprocess_for_infer(df_sample: DataFrame[TaxiDatasetSchema]) -> None:
    actual = preprocess_for_infer(df_sample, max_predict_days=3)

    expected_csv = """
date,target_date,area,num_trip,weekday,target_lead
2024-01-01,2024-01-02,1,5,0,1
2024-01-01,2024-01-03,1,5,0,2
2024-01-01,2024-01-04,1,5,0,3
2024-01-02,2024-01-03,1,8,1,1
2024-01-02,2024-01-04,1,8,1,2
2024-01-02,2024-01-05,1,8,1,3
2024-01-01,2024-01-02,2,20,0,1
2024-01-01,2024-01-03,2,20,0,2
2024-01-01,2024-01-04,2,20,0,3
2024-01-02,2024-01-03,2,18,1,1
2024-01-02,2024-01-04,2,18,1,2
2024-01-02,2024-01-05,2,18,1,3
"""
    expected = pd.read_csv(
        io.StringIO(expected_csv), parse_dates=["date", "target_date"]
    ).set_index(["date", "target_date"])
    expected["area"] = expected["area"].astype("category")

    assert_frame_equal(actual, expected)


def test_preprocess_for_train(df_sample: DataFrame[TaxiDatasetSchema]) -> None:
    actual = preprocess_for_train(df_sample, max_predict_days=3)

    expected_csv = """
date,target_date,area,num_trip,weekday,target_lead,target
2024-01-01,2024-01-02,1,5,0,1,8
2024-01-01,2024-01-02,2,20,0,1,18
"""
    expected = pd.read_csv(
        io.StringIO(expected_csv), parse_dates=["date", "target_date"]
    ).set_index(["date", "target_date"])
    expected["area"] = expected["area"].astype("category")

    assert_frame_equal(actual, expected, check_dtype=False)
