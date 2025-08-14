from logging import getLogger

import hydra
import mlflow
from omegaconf import DictConfig

from taxi_prediction.model import LGBModel
from taxi_prediction.process import load_dataset, preprocess_for_train, split_dataset

logger = getLogger(__name__)


@hydra.main(config_path="conf", config_name="config")
def main(config: DictConfig) -> None:
    mlflow.set_tracking_uri("file:///app/mlruns")
    mlflow.set_experiment("taxi_prediction")

    with mlflow.start_run():
        mlflow.log_param("train_ratio", config.train_ratio)
        mlflow.log_params(config.model)
        mlflow.log_params(config.train)
        mlflow.set_tag("model_type", "lightgbm")

        # データの読み込み
        dataset = load_dataset(config.data_path)

        # 前処理
        dataset_train, dataset_valid = split_dataset(dataset, config.train_ratio)
        df_train = preprocess_for_train(dataset_train)
        df_valid = preprocess_for_train(dataset_valid)
        logger.info(f"train_size: {len(df_train)}")
        logger.info(f"valid_size: {len(df_valid)}")
        mlflow.log_table(df_train, "df_train.json")
        mlflow.log_table(df_valid, "df_valid.json")

        # 学習
        model = LGBModel(dict(config.model))
        model.fit(df_train, df_valid, **config.train)

        # 予測・評価
        scores = model.evaluate(df_valid)
        logger.info(f"scores: {scores}")
        mlflow.log_metrics(scores)

        # モデルの保存
        model.save("model.pickle")
        mlflow.log_artifact("model.pickle")


if __name__ == "__main__":
    main()
