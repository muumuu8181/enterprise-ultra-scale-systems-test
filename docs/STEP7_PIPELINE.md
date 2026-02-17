# Step 7: MLパイプライン仕様 (Airflow / Kubeflow)

## 1. 概要
データ処理から学習、評価、デプロイまでの一連のワークフローを自動化し、継続的学習（Continuous Training: CT）を実現する。ワークフローエンジンとして Apache Airflow と Kubeflow Pipelines (KFP) の2つをサポートし、ユースケースに応じて選択可能とする。

## 2. クラス設計

### 2.1 Airflow DAGビルダー
**File**: `src/pipeline/airflow_dag_builder.py`

#### Class: `AirflowDAGBuilder`
設定ファイルからAirflow DAG（Directed Acyclic Graph）を動的に生成する。

*   **Methods**:
    *   `build_training_dag(config: PipelineConfig) -> DAG`
        *   **説明**: 定期学習パイプラインを構築する。
        *   **構成タスク**: [Data Check] -> [Preprocess (Spark)] -> [Train (Ray)] -> [Evaluate] -> [Register Model] -> [Deploy (Canary)]
    *   `build_batch_inference_dag(config: BatchConfig) -> DAG`
        *   **説明**: 夜間バッチ推論パイプラインを構築する。
        *   **構成タスク**: [Load Data] -> [Inference (Ray)] -> [Save Result (S3)] -> [Notify]
    *   `build_feature_refresh_dag(config: FeatureConfig) -> DAG`
        *   **説明**: Feature Storeへのデータ同期パイプラインを構築する。

### 2.2 Kubeflow Pipelinesランナー
**File**: `src/pipeline/kubeflow_pipeline.py`

#### Class: `KubeflowPipelineRunner`
Kubernetesネイティブなパイプライン実行を管理する。

*   **Methods**:
    *   `build_pipeline(steps: List[PipelineStep]) -> Pipeline`
        *   **説明**: コンポーネント定義からKFP DSLを用いてパイプラインオブジェクトを作成する。
    *   `submit(pipeline: Pipeline, arguments: Dict[str, Any]) -> PipelineRun`
        *   **説明**: KFP APIサーバーにパイプラインをサブミットし、実行を開始する。
    *   `get_run_status(run_id: str) -> RunStatus`
        *   **説明**: 実行中のパイプラインの進行状況を取得する。

## 3. パイプラインステップ詳細

各ステップは独立したDockerコンテナとして実行され、入力・出力を通じて連携する。

### 3.1 Data Validation
*   **ツール**: Great Expectations
*   **機能**: 入力データのスキーマ検証、欠損値チェック、値の範囲チェック。異常がある場合はパイプラインを停止しアラートを発報。

### 3.2 Preprocessing
*   **ツール**: Apache Spark on K8s
*   **機能**: 大規模データセットの分散処理、特徴量エンジニアリング、正規化、エンコーディング。

### 3.3 Training
*   **ツール**: Ray Cluster (KubeRay)
*   **機能**: `src/training/distributed` モジュールを呼び出し、分散学習を実行。

### 3.4 Evaluation
*   **ツール**: Custom Python Script + MLflow
*   **機能**: テストデータセットを用いた精度評価。ビジネスKPI（売上予測誤差など）の検証。Productionモデルとの性能比較。

### 3.5 Canary Deploy
*   **ツール**: KServe / Istio
*   **機能**: 新モデルをトラフィックの10%に適用し、エラー率とレイテンシを監視。問題なければ50% -> 100%へ段階的に拡大。

## 4. トリガー
*   **スケジュール実行**: CRON形式（Airflow）。
*   **イベント駆動**: データ到着時（S3 Event Notification -> Lambda -> Airflow Trigger）。
*   **手動実行**: 管理画面からのオンデマンド実行。
