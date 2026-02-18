# 大規模AI/ML学習・推論統合プラットフォーム基盤 アーキテクチャ設計書

## 1. システム構成図

### 1.1 全体アーキテクチャ概要 (Mermaid)

```mermaid
graph TD
    subgraph Clients
        DataScientist[データサイエンティスト]
        App[業務アプリケーション]
        Admin[運用管理者]
    end

    subgraph "API Gateway (FastAPI)"
        Gateway[API Gateway]
    end

    subgraph "Data Platform"
        FeatureStore[Feature Store (Feast)]
        DataPipeline[Data Pipeline (Airflow/Spark)]
        OfflineStore[(Offline Store S3/HDFS)]
        OnlineStore[(Online Store Redis)]
    end

    subgraph "Training Platform (Ray/KubeRay)"
        Scheduler[Job Scheduler (Go)]
        Trainer[Distributed Trainer (Ray/DDP)]
        HyperOpt[Hyperparameter Optimization]
        Experiment[Experiment Tracking (MLflow)]
    end

    subgraph "Model Management"
        Registry[Model Registry]
        Lineage[Data/Model Lineage]
    end

    subgraph "Inference Platform (KServe/Triton)"
        ModelServer[Model Serving]
        BatchProc[Batch Inference]
        ABTest[A/B Testing Router]
        DriftDetect[Drift Detector]
    end

    subgraph "Infrastructure"
        K8s[Kubernetes Cluster]
        GPU[GPU Cluster (A100/H100)]
        Storage[(High Perf Storage GPFS)]
        MetaDB[(Metadata DB PostgreSQL)]
    end

    %% Data Flow
    DataScientist -->|Experiment/Train| Gateway
    App -->|Inference Request| Gateway
    Admin -->|Monitor/Manage| Gateway

    Gateway -->|Dispatch| Scheduler
    Gateway -->|Route| ABTest

    %% Training Flow
    Scheduler -->|Launch| Trainer
    Trainer -->|Read/Write| FeatureStore
    Trainer -->|Log Metrics| Experiment
    Trainer -->|Save Artifacts| Registry
    Trainer -->|Use| GPU

    %% Feature Store Flow
    DataPipeline -->|Materialize| FeatureStore
    FeatureStore -->|Read| OfflineStore
    FeatureStore -->|Read| OnlineStore

    %% Inference Flow
    ABTest -->|Forward| ModelServer
    ModelServer -->|Get Features| OnlineStore
    ModelServer -->|Load Model| Registry
    ModelServer -->|Log Prediction| DriftDetect

    %% Monitoring
    DriftDetect -->|Alert| Admin
```

## 2. コンポーネント詳細

### 2.1 データ基盤レイヤー (Data Platform)
*   **Feature Store (Feast)**:
    *   **役割**: 特徴量の一元管理、学習時と推論時の特徴量整合性（Training-Serving Skew）の防止。
    *   **Online Store**: Redis Cluster。推論時の低レイテンシアクセス（<5ms）を提供。
    *   **Offline Store**: S3/HDFS (Parquet)。学習時のバッチデータアクセスを提供。
*   **Data Pipeline (Airflow/Spark)**:
    *   **役割**: ETL処理、特徴量生成、データの検証（Great Expectations）。

### 2.2 学習基盤レイヤー (Training Platform)
*   **Distributed Trainer (Ray/PyTorch DDP)**:
    *   **役割**: マルチノード・マルチGPUによる分散学習の実行。
    *   **機能**: データ並列、モデル並列、パイプライン並列。DeepSpeed ZeROによるメモリ最適化。
*   **Job Scheduler (Go)**:
    *   **役割**: 学習ジョブのキューイング、優先度制御、リソース割り当て、プリエンプション。
*   **Hyperparameter Optimization (HyperOpt)**:
    *   **役割**: Optuna/Ray Tuneを用いた分散ハイパーパラメータ探索。

### 2.3 モデル管理レイヤー (Model Management)
*   **Experiment Tracking (MLflow)**:
    *   **役割**: 実験パラメータ、メトリクス、成果物の記録・可視化。
*   **Model Registry**:
    *   **役割**: モデルのバージョン管理、ステージ管理（Staging/Production/Archived）、承認フロー。

### 2.4 推論基盤レイヤー (Inference Platform)
*   **Model Serving (Triton/KServe)**:
    *   **役割**: 高速なモデル推論APIの提供。動的バッチング、モデルの動的ロード/アンロード。
*   **A/B Testing Router**:
    *   **役割**: トラフィックの分割、カナリアリリース、シャドーモードの実行。
*   **Batch Inference**:
    *   **役割**: 大規模データに対する非同期推論処理。

### 2.5 監視・運用レイヤー (Monitoring & Ops)
*   **Drift Detection**:
    *   **役割**: 特徴量分布（Feature Drift）および予測分布（Concept Drift）の監視。PSI/KS検定。
*   **Performance Monitoring**:
    *   **役割**: レイテンシ、スループット、エラー率、リソース使用率の監視（Prometheus/Grafana）。

## 3. データフロー

### 3.1 学習フロー
1.  **データ準備**: AirflowがSparkジョブを起動し、Rawデータを加工してFeature Store (Offline) に保存。
2.  **実験開始**: データサイエンティストが学習ジョブをサブミット。
3.  **スケジューリング**: Job Schedulerがリソース（GPU）を確保し、Rayクラスタ上に学習ワーカーを立ち上げ。
4.  **分散学習**: PyTorch DDP/DeepSpeedにより学習を実行。Feature Storeから学習データを取得。
5.  **記録**: 学習中のメトリクスとモデルアーティファクトをMLflowに記録。
6.  **登録**: 最良のモデルをModel Registryに登録。

### 3.2 推論フロー
1.  **リクエスト受信**: API Gatewayが推論リクエストを受信。
2.  **ルーティング**: A/B Test Routerが対象のモデルバージョンを決定。
3.  **特徴量取得**: Model Serverが必要な特徴量（例：ユーザー行動履歴）をFeature Store (Online/Redis) から取得。
4.  **推論実行**: Triton Inference ServerがGPUを使用して推論を実行。
5.  **レスポンス**: 推論結果をクライアントに返却。
6.  **ログ記録**: 入力データと予測結果を監視システムに非同期送信（ドリフト検知用）。

## 4. インフラストラクチャ設計

*   **Kubernetes (K8s)**: コンテナオーケストレーション基盤。
    *   **KubeRay**: Rayクラスタのオンデマンド構築・オートスケーリング。
    *   **KServe**: 推論サービスの管理（Istio/Knative連携）。
*   **Storage**:
    *   **GPFS/Lustre**: 高速並列ファイルシステム。学習データ読み込みのボトルネック解消。
    *   **S3 Compatible Object Storage**: モデルアーカイブ、ログ、バックアップ。
*   **Database**:
    *   **PostgreSQL**: メタデータ管理（モデル情報、ジョブ情報、ユーザー情報）。パーティショニングとレプリケーションによる負荷分散。
    *   **Redis Cluster**: Feature Store Online Store、キャッシュ、ジョブキュー。
