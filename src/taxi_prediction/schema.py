import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import Index, Series

from .consts import MAX_PREDICT_DAYS


class TaxiDatasetSchema(pa.DataFrameModel):
    date: Series[np.datetime64]
    area: Series[pd.CategoricalDtype]
    num_trip: Series[int] = pa.Field(ge=0)


class InferInputSchema(pa.DataFrameModel):
    date: Index[np.datetime64]
    target_date: Index[np.datetime64]
    area: Series[pd.CategoricalDtype]
    num_trip: Series[int] = pa.Field(ge=0)
    weekday: Series[int] = pa.Field(in_range={"min_value": 0, "max_value": 6})
    target_lead: Series[int] = pa.Field(
        in_range={"min_value": 1, "max_value": MAX_PREDICT_DAYS}
    )

    @pa.dataframe_check
    def target_date_is_consistent(cls, df: pd.DataFrame) -> Series[bool]:
        """date + target_lead = target_date の関係式が
        成り立っていることをチェックする
        """
        return df.index.get_level_values("date") + pd.to_timedelta(  # type: ignore
            df["target_lead"], unit="D"
        ) == df.index.get_level_values("target_date")

    class Config:
        strict = True
        coerce = True


class TrainInputSchema(InferInputSchema):
    target: Series[int] = pa.Field(ge=0)


class InferOutputSchema(pa.DataFrameModel):
    date: Index[np.datetime64]
    target_date: Index[np.datetime64]
    area: Series[pd.CategoricalDtype]
    pred: Series[float]
