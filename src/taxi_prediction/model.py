import pickle
from pathlib import Path
from typing import Any, Self

import lightgbm as lgb
import pandera as pa
from pandera.typing import DataFrame
from sklearn.metrics import mean_absolute_error

from .schema import InferInputSchema, InferOutputSchema, TrainInputSchema


class LGBModel:
    """
    LightGBMのラッパークラス
    """

    def __init__(self, params: dict[str, Any]) -> None:
        self._params = params.copy()
        self._model: lgb.Booster | None = None

    @pa.check_types
    def fit(
        self,
        df_train: DataFrame[TrainInputSchema],
        df_valid: DataFrame[TrainInputSchema],
        num_boost_round: int = 1000,
        early_stopping_rounds: int = 10,
    ) -> Self:
        """
        モデルを学習する
        """
        data_train = lgb.Dataset(
            data=df_train.drop(columns=["target"]), label=df_train["target"]
        )
        data_valid = lgb.Dataset(
            data=df_valid.drop(columns=["target"]), label=df_valid["target"]
        )

        self._model = lgb.train(
            params=self._params,
            train_set=data_train,
            valid_sets=[data_train, data_valid],
            valid_names=["train", "valid"],
            num_boost_round=num_boost_round,
            callbacks=[
                lgb.early_stopping(stopping_rounds=early_stopping_rounds),
                lgb.log_evaluation(period=100),
            ],
        )

        return self

    @pa.check_types
    def predict(self, df: DataFrame[InferInputSchema]) -> DataFrame[InferOutputSchema]:
        """
        予測を実行する
        """
        if self._model is None:
            raise ValueError("Model has not been trained.")

        pred = self._model.predict(df, num_iteration=self._model.best_iteration)

        columns = list(InferOutputSchema.to_schema().columns.keys())
        return df.assign(pred=pred)[columns]  # type: ignore

    @pa.check_types
    def evaluate(self, df: DataFrame[TrainInputSchema]) -> dict[str, float]:
        """
        モデルの予測精度を評価する
        評価指標を格納した辞書を返す
        """
        target = df["target"]
        pred = self.predict(df.drop(columns=["target"]))["pred"]

        scores = {}
        scores["mae"] = mean_absolute_error(target, pred)

        return scores

    def save(self, filepath: str | Path) -> None:
        """
        モデルをpickleで保存する
        """
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str | Path) -> Self:
        """
        pickleからモデルのインスタンスを読み込む
        """
        with open(filepath, "rb") as file:
            model = pickle.load(file)

        if not isinstance(model, cls):
            raise TypeError(
                f"Loaded object type does not match expected type. "
                f"Expected: {cls.__name__}, Actual: {type(model).__name__}"
            )

        return model
