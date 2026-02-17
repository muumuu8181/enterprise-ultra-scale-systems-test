import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class DataValidator:
    """
    データ品質検証サービス
    """

    def get_dataset_data(self, dataset_id: str) -> pd.DataFrame:
        """
        データセットIDに基づいてデータを取得する（モック）

        Args:
            dataset_id (str): データセットID

        Returns:
            pd.DataFrame: データフレーム
        """
        # モックデータ
        if dataset_id == "ds_test_1":
            return pd.DataFrame({
                "id": [1, 2, 3, 4, 5, 1],  # 重複あり
                "name": ["Alice", "Bob", None, "Dave", "Eve", "Alice"],
                "age": [25, 30, 35, 150, 25, 25], # 150は外れ値の可能性
                "score": [80.5, 90.0, 85.5, None, 80.5, 80.5]
            })
        elif dataset_id == "ds_empty":
            return pd.DataFrame()
        else:
            # デフォルトのランダムデータ
            return pd.DataFrame(
                np.random.randint(0, 100, size=(10, 4)),
                columns=list('ABCD')
            )

    def check_nulls(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        各カラムのNULL率を計算します。

        Args:
            df (pd.DataFrame): 対象データフレーム

        Returns:
            Dict[str, float]: カラム名とNULL率の辞書
        """
        if df.empty:
            return {}
        return df.isnull().mean().to_dict()

    def check_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> float:
        """
        行の重複率を計算します。

        Args:
            df (pd.DataFrame): 対象データフレーム
            subset (List[str], optional): 重複チェックに用いるカラムリスト

        Returns:
            float: 重複率 (0.0 - 1.0)
        """
        if df.empty:
            return 0.0

        total_rows = len(df)
        unique_rows = len(df.drop_duplicates(subset=subset))
        return 1.0 - (unique_rows / total_rows)

    def check_schema(self, df: pd.DataFrame, expected_schema: Dict[str, str]) -> Dict[str, Any]:
        """
        スキーマの整合性をチェックします。

        Args:
            df (pd.DataFrame): 対象データフレーム
            expected_schema (Dict[str, str]): 期待されるカラム名と型の定義 (簡易版)

        Returns:
            Dict[str, Any]: 整合性チェック結果
        """
        if not expected_schema:
            return {"valid": True, "message": "No schema provided"}

        missing_cols = [col for col in expected_schema if col not in df.columns]

        # 型チェックはpandasのdtypeと文字列のマッピングが複雑なため、ここではカラム存在確認のみとする

        if missing_cols:
            return {
                "valid": False,
                "missing_columns": missing_cols
            }

        return {"valid": True}

    def check_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        数値カラムの統計的分布と外れ値を計算します。

        Args:
            df (pd.DataFrame): 対象データフレーム

        Returns:
            Dict[str, Any]: 各カラムの統計情報
        """
        stats = {}
        # 数値カラムのみ対象
        numeric_df = df.select_dtypes(include=[np.number])

        for col in numeric_df.columns:
            desc = numeric_df[col].describe()

            # IQR法による外れ値検出
            q1 = desc['25%']
            q3 = desc['75%']
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = numeric_df[
                (numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)
            ][col]

            stats[col] = {
                "mean": float(desc['mean']),
                "std": float(desc['std']),
                "min": float(desc['min']),
                "max": float(desc['max']),
                "outlier_count": int(len(outliers)),
                "outlier_ratio": float(len(outliers) / len(df)) if len(df) > 0 else 0.0
            }
        return stats

    def check_referential_integrity(self, df: pd.DataFrame, column: str, reference_values: List[Any]) -> Dict[str, Any]:
        """
        外部キー制約（参照整合性）をチェックします。

        Args:
            df (pd.DataFrame): 対象データフレーム
            column (str): チェック対象のカラム
            reference_values (List[Any]): 参照先の正当な値リスト

        Returns:
            Dict[str, Any]: チェック結果
        """
        if column not in df.columns:
            return {"valid": False, "error": f"Column {column} not found"}

        if not reference_values:
             return {"valid": False, "error": "No reference values provided"}

        # NULLは無視するか、外部キー設定によるが、ここでは無視して計算
        valid_mask = df[column].isin(reference_values) | df[column].isnull()
        invalid_rows = df[~valid_mask]

        integrity_score = valid_mask.mean()

        return {
            "valid": len(invalid_rows) == 0,
            "integrity_score": float(integrity_score),
            "invalid_count": int(len(invalid_rows))
        }

    def generate_quality_score(self, null_report: Dict[str, float], duplicate_rate: float, distribution_report: Dict[str, Any]) -> float:
        """
        総合的な品質スコアを算出します (0-100)。

        Args:
            null_report (Dict): NULL率レポート
            duplicate_rate (float): 重複率
            distribution_report (Dict): 分布レポート

        Returns:
            float: 品質スコア
        """
        score = 100.0

        # 1. NULLによる減点 (重み: 40)
        # 全カラムの平均NULL率に基づく
        if null_report:
            avg_null_rate = sum(null_report.values()) / len(null_report)
            score -= avg_null_rate * 40.0

        # 2. 重複による減点 (重み: 30)
        score -= duplicate_rate * 30.0

        # 3. 外れ値による減点 (重み: 30)
        # 各カラムの外れ値比率の平均
        if distribution_report:
            total_outlier_ratio = sum(item["outlier_ratio"] for item in distribution_report.values())
            avg_outlier_ratio = total_outlier_ratio / len(distribution_report)
            score -= avg_outlier_ratio * 30.0

        return max(0.0, min(100.0, score))
