# Step 6: 実験管理・MLflow仕様

## 1. 概要
MLflowを中心とした実験管理基盤を構築し、実験の再現性（Reproducibility）とトレーサビリティを確保する。モデルの学習パラメータ、メトリクス、アーティファクト、コードバージョンを一元的にトラッキングする。

## 2. クラス設計

### 2.1 実験トラッカー
**File**: `src/experiment_tracking/mlflow_client.py`

#### Class: `MLflowExperimentTracker`
MLflow Tracking Serverへの記録インターフェース。

*   **Methods**:
    *   `start_run(experiment_name: str, run_name: str, tags: Dict[str, str]) -> Run`
        *   **説明**: 新しい実験実行（Run）を開始する。既存の実験がなければ作成する。
    *   `log_params(params: Dict[str, Any]) -> None`
        *   **説明**: 学習パラメータ（learning_rate, batch_sizeなど）を記録する。
    *   `log_metrics(metrics: Dict[str, float], step: int) -> None`
        *   **説明**: 評価指標（accuracy, lossなど）をステップごとに記録する。
    *   `log_artifact(local_path: str, artifact_path: str) -> None`
        *   **説明**: 生成物（画像、ログファイル、設定ファイル）をS3上のアーティファクトストアにアップロードする。
    *   `log_model(model: Any, artifact_path: str, registered_name: str) -> ModelInfo`
        *   **説明**: 学習済みモデルをMLflow Modelフォーマットで保存し、Model Registryに登録する。
    *   `end_run(status: str) -> None`
        *   **説明**: Runを終了し、ステータス（FINISHED/FAILED）を更新する。

### 2.2 モデルレジストリ
**File**: `src/model_registry/registry.py`

#### Class: `ModelRegistry`
学習済みモデルのバージョン管理とライフサイクル制御を行う。

*   **Methods**:
    *   `register(run_id: str, model_name: str, description: str) -> ModelVersion`
        *   **説明**: 指定されたRunで生成されたモデルをレジストリに新規バージョンとして登録する。
    *   `transition_stage(name: str, version: str, stage: str) -> None`
        *   **説明**: モデルバージョンのステージを変更する（None -> Staging -> Production -> Archived）。
    *   `get_latest_version(name: str, stages: List[str]) -> ModelVersion`
        *   **説明**: 指定されたステージ（例: Production）にある最新のモデルバージョン情報を取得する。
    *   `compare_versions(version_a: str, version_b: str, metric_name: str) -> Comparison`
        *   **説明**: 2つのモデルバージョンのメトリクスを比較し、改善度を算出する。
    *   `archive_old_versions(name: str, keep_n: int = 5) -> List[str]`
        *   **説明**: Productionから外れた古いバージョンをArchivedステータスに変更し、整理する。

## 3. データフローと連携

### 3.1 MLflow Tracking Server
*   **バックエンドDB**: PostgreSQL（実験メタデータ、パラメータ、メトリクス）。
*   **アーティファクトストア**: S3互換ストレージ（モデルバイナリ、プロット画像）。
*   **UI**: MLflow UIを提供し、ブラウザから実験結果の可視化・比較が可能。

### 3.2 連携フロー
1.  **学習ジョブ**: `MLflowExperimentTracker` を使用して学習プロセスを記録。
2.  **自動登録**: 検証スコアが閾値を超えた場合、`log_model` でモデルをレジストリに登録。
3.  **デプロイ**: 推論サービス（KServe）はModel Registryを参照し、指定されたステージ（Staging/Production）のモデルをロードする。
