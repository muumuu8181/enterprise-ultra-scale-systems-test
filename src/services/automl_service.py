import pandas as pd
import numpy as np
import optuna
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, mean_squared_error, r2_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import shap
import onnx
import onnxmltools
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import json
import os
from typing import Dict, Any, Tuple, Optional, List

class AutoMLService:
    """
    AutoMLサービス: ハイパーパラメータ探索、アルゴリズム選択、レポート生成、ONNXエクスポートを行う
    """

    def __init__(self, dataset_path: Optional[str] = None, target_column: Optional[str] = None, task_type: str = "classification"):
        self.dataset_path = dataset_path
        self.target_column = target_column
        self.task_type = task_type  # classification or regression
        self.df = None
        self.X = None
        self.y = None
        self.best_model = None
        self.best_params = {}
        self.best_algorithm_name = ""
        self.label_encoders = {}

    def load_data(self):
        """
        データセットをロードし、前処理を行う
        """
        if self.dataset_path and os.path.exists(self.dataset_path):
            self.df = pd.read_csv(self.dataset_path)
        elif self.dataset_path == "mock": # For testing
             # Generate dummy data
            from sklearn.datasets import make_classification
            X, y = make_classification(n_samples=100, n_features=5, random_state=42)
            self.df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(5)])
            self.df["target"] = y
            self.target_column = "target"
        else:
            raise FileNotFoundError(f"Dataset not found at {self.dataset_path}")

        # 欠損値処理 (簡易版: 平均値埋め/最頻値埋め)
        self.df = self.df.fillna(self.df.mean(numeric_only=True))
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].fillna(self.df[col].mode()[0])

        # 特徴量とターゲットの分離
        if self.target_column not in self.df.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in dataset")

        self.y = self.df[self.target_column]
        self.X = self.df.drop(columns=[self.target_column])

        # カテゴリカル変数のエンコーディング
        for col in self.X.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            self.X[col] = le.fit_transform(self.X[col])
            self.label_encoders[col] = le

        # ターゲット変数のエンコーディング（分類問題の場合）
        if self.task_type == "classification" and self.y.dtype == 'object':
             le_target = LabelEncoder()
             self.y = le_target.fit_transform(self.y)
             self.label_encoders[self.target_column] = le_target

    def search_hyperparams(self, algorithm: str, n_trials: int = 100) -> Dict[str, Any]:
        """
        Optunaを使用してハイパーパラメータ探索を行う
        """
        if self.X is None or self.y is None:
            self.load_data()

        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)

        def objective(trial):
            if algorithm == "xgboost":
                params = {
                    "verbosity": 0,
                    "objective": "binary:logistic" if self.task_type == "classification" else "reg:squarederror",
                    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                    "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                }
                model = xgb.XGBClassifier(**params) if self.task_type == "classification" else xgb.XGBRegressor(**params)
            elif algorithm == "lightgbm":
                params = {
                    "objective": "binary" if self.task_type == "classification" else "regression",
                    "metric": "binary_logloss" if self.task_type == "classification" else "rmse",
                    "verbosity": -1,
                    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 20, 300),
                }
                model = lgb.LGBMClassifier(**params) if self.task_type == "classification" else lgb.LGBMRegressor(**params)
            elif algorithm == "randomforest":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 500),
                    "max_depth": trial.suggest_int("max_depth", 3, 20),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
                    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                }
                model = RandomForestClassifier(**params) if self.task_type == "classification" else RandomForestRegressor(**params)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            if self.task_type == "classification":
                return accuracy_score(y_test, preds)
            else:
                return -mean_squared_error(y_test, preds) # Optuna maximizes, so negative MSE

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials)
        return study.best_params

    def select_best_algorithm(self) -> Tuple[str, Dict[str, Any], float]:
        """
        XGBoost/LightGBM/RandomForestを比較し、最良のアルゴリズムを選択する
        """
        algorithms = ["xgboost", "lightgbm", "randomforest"]
        best_score = -float("inf")
        best_algo = ""
        best_params = {}

        # 評価用データ
        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)

        for algo in algorithms:
            print(f"Optimizing {algo}...")
            params = self.search_hyperparams(algo, n_trials=100)

            # 最適パラメータで再学習して評価
            if algo == "xgboost":
                model = xgb.XGBClassifier(**params) if self.task_type == "classification" else xgb.XGBRegressor(**params)
            elif algo == "lightgbm":
                model = lgb.LGBMClassifier(**params) if self.task_type == "classification" else lgb.LGBMRegressor(**params)
            elif algo == "randomforest":
                model = RandomForestClassifier(**params) if self.task_type == "classification" else RandomForestRegressor(**params)

            model.fit(X_train, y_train)
            preds = model.predict(X_test)

            if self.task_type == "classification":
                score = accuracy_score(y_test, preds) # Metric can be customized
            else:
                score = r2_score(y_test, preds)

            if score > best_score:
                best_score = score
                best_algo = algo
                best_params = params
                self.best_model = model # Keep the best model instance

        self.best_algorithm_name = best_algo
        self.best_params = best_params
        return best_algo, best_params, best_score

    def generate_model_report(self) -> Dict[str, Any]:
        """
        特徴量重要度, SHAP値, 混同行列などを含むレポートを生成する
        """
        if self.best_model is None:
            raise ValueError("No model trained yet.")

        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)
        preds = self.best_model.predict(X_test)

        report = {
            "algorithm": self.best_algorithm_name,
            "params": self.best_params,
        }

        # Metrics
        if self.task_type == "classification":
            report["metrics"] = {
                "accuracy": float(accuracy_score(y_test, preds)),
                "f1": float(f1_score(y_test, preds, average='weighted')),
                # AUC handles probabilities, skipping for simplicity or needs predict_proba
            }
            try:
                if hasattr(self.best_model, "predict_proba"):
                    probs = self.best_model.predict_proba(X_test)
                    if len(np.unique(y_test)) == 2:
                        report["metrics"]["auc"] = float(roc_auc_score(y_test, probs[:, 1]))
                    else:
                        report["metrics"]["auc"] = float(roc_auc_score(y_test, probs, multi_class='ovr'))
            except Exception as e:
                report["metrics"]["auc_error"] = str(e)

            # Confusion Matrix
            try:
                cm = confusion_matrix(y_test, preds)
                report["confusion_matrix"] = cm.tolist()
            except Exception as e:
                report["confusion_matrix_error"] = str(e)

        else:
            report["metrics"] = {
                "mse": float(mean_squared_error(y_test, preds)),
                "r2": float(r2_score(y_test, preds))
            }

        # Feature Importance
        if hasattr(self.best_model, "feature_importances_"):
            report["feature_importance"] = dict(zip(self.X.columns, self.best_model.feature_importances_.astype(float)))

        # SHAP Values (Sample)
        try:
            explainer = shap.Explainer(self.best_model, X_train)
            # Calculate SHAP values for a subset to save time
            shap_values = explainer(X_test[:100])
            # Summarize SHAP values (mean absolute value)
            shap_summary = np.abs(shap_values.values).mean(axis=0)
            report["shap_importance"] = dict(zip(self.X.columns, shap_summary.tolist()))
        except Exception as e:
            report["shap_error"] = str(e)

        return report

    def export_to_onnx(self, output_path: str):
        """
        学習済みモデルをONNXフォーマットでエクスポートする
        """
        if self.best_model is None:
            raise ValueError("No model trained yet.")

        initial_type = [('float_input', FloatTensorType([None, self.X.shape[1]]))]

        if self.best_algorithm_name == "xgboost":
            # XGBoost specific export
            # onnxmltools or convert_sklearn wrapping
            # XGBoost has its own export_text/json, but to ONNX we use onnxmltools
            onnx_model = onnxmltools.convert_xgboost(self.best_model, initial_types=initial_type)
        elif self.best_algorithm_name == "lightgbm":
            onnx_model = onnxmltools.convert_lightgbm(self.best_model, initial_types=initial_type)
        elif self.best_algorithm_name == "randomforest":
            onnx_model = convert_sklearn(self.best_model, initial_types=initial_type)
        else:
            raise ValueError(f"ONNX export not supported for {self.best_algorithm_name}")

        with open(output_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
