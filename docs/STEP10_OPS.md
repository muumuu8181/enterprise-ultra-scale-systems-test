# Step 10: 運用・パフォーマンス仕様

## 1. 概要
本番環境での安定稼働（Reliability）を保証し、大規模ワークロードに耐えうるインフラ構成とテスト戦略を定義する。

## 2. 運用・テスト

### 2.1 テストコード構成
**File Structure**: `tests/`

*   **Unit Tests (`tests/unit/`)**:
    *   `test_distributed_trainer.py`: Rayジョブ投入、ステータス遷移の検証。
    *   `test_hyperopt.py`: Optunaスタディ作成、トライアル最適化ロジックの検証。
    *   `test_drift_detector.py`: PSI、KS統計量の計算精度（正解データとの比較）。
    *   `test_feature_store.py`: Online Store/Offline Store間の特徴量整合性（パリティ）検証。
    *   `test_model_registry.py`: モデルバージョン登録、ステージ遷移、承認フローの検証。

*   **Integration Tests (`tests/integration/`)**:
    *   `test_training_pipeline.py`: 生データ投入 -> 前処理 -> 学習 -> 評価 -> 登録までの一連のフローを確認。
    *   `test_serving_flow.py`: モデルデプロイ -> 推論リクエスト -> レスポンス確認 -> メトリクス記録を確認。
    *   `test_pipeline_e2e.py`: データパイプライン（Airflow DAG）の実行確認。

*   **Performance Tests (`tests/performance/`)**:
    *   `locustfile.py`: 負荷生成ツール（Locust）を用いて、推論エンドポイントに対して同時多数のリクエストを送信し、レイテンシとスループットを計測する。

### 2.2 性能目標
*   **推論レイテンシ**:
    *   p99 < 50ms (画像分類、テーブルデータ予測)
    *   LLM生成: < 100ms (Time To First Token)
*   **推論スループット**:
    *   100,000 requests/sec (全クラスター合計)
*   **学習スループット**:
    *   1,000,000 samples/sec (分散データ並列時)
*   **デプロイ速度**:
    *   < 60秒 (モデルアーティファクト取得からPod起動完了まで)

## 3. インフラストラクチャ詳細

### 3.1 計算リソース (Compute)
*   **GPU Nodes**:
    *   **Spec**: NVIDIA H100 (80GB) × 8 GPUs / Node
    *   **Count**: 64 Nodes (Total 512 GPUs)
    *   **Memory**: 2TB RAM / Node
    *   **Network**: InfiniBand 400Gbps (NCCL通信用)
*   **CPU Nodes**:
    *   **Spec**: AMD EPYC (64 Cores)
    *   **Count**: 256 Nodes (Total 16,384 Cores)
    *   **Memory**: 512GB RAM / Node
    *   **Use Case**: データ前処理 (Spark), 推論CPUフォールバック, 管理コンポーネント

### 3.2 ストレージ (Storage)
*   **Tier 1: High Performance (GPFS / Lustre)**
    *   **Capacity**: 10 PB
    *   **Throughput**: 1 TB/sec
    *   **Use Case**: 学習データセット（画像、動画、音声）、チェックポイント一時保存
*   **Tier 2: Object Storage (S3 Compatible)**
    *   **Capacity**: 100 PB
    *   **Durability**: 99.999999999%
    *   **Use Case**: モデルアーカイブ、ログ、バックアップ、Coldデータ
*   **Tier 3: Database Storage (NVMe SSD)**
    *   **Capacity**: 500 TB
    *   **IOPS**: 1,000,000
    *   **Use Case**: PostgreSQL, Redis, Elasticsearch

### 3.3 ネットワーク (Network)
*   **Core Switch**: 100GbE Spine-Leaf Architecture
*   **Load Balancer**: Hardware LB (F5) -> Ingress Controller (Nginx/Istio)
*   **Latency**: < 100µs (Node-to-Node)

## 4. 障害対応 (Incident Response)

### 4.1 自動復旧
*   **Pod Failure**: Kubernetes Liveness Probeにより自動再起動。
*   **Node Failure**: Cluster Autoscalerにより代替ノードを起動し、Podを再スケジューリング。
*   **Region Failure**: マルチリージョン構成（DRサイト）へのフェイルオーバー（RTO < 1時間）。

### 4.2 バックアップ
*   **Metadata DB**: 1時間ごとの増分バックアップ + 日次フルバックアップ。
*   **Feature Store**: 定期スナップショット。
*   **Model Artifacts**: S3 Versioning有効化 + Cross-Region Replication。
