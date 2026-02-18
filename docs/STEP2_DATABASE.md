# Step 2: DB詳細設計・DDL一覧

## 1. DDL (Data Definition Language)

### 1.1 モデル管理

#### 1. models
モデルの基本情報を管理するテーブル。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `model_id` | UUID | PK | 一意な識別子 |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL | モデル名 |
| `framework` | ENUM | NOT NULL | 'pytorch', 'tensorflow', 'sklearn', 'xgboost' |
| `task_type` | ENUM | NOT NULL | 'classification', 'regression', 'nlp', 'cv', 'rl' |
| `created_by` | VARCHAR(255) | NOT NULL | 作成者ID |
| `description` | TEXT | | 詳細説明 |
| `tags` | JSONB | | メタデータタグ |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 作成日時 |

#### 2. model_versions
モデルのバージョン管理テーブル。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `version_id` | UUID | PK | バージョンID |
| `model_id` | UUID | FK(models.model_id) | 親モデルID |
| `version_str` | VARCHAR(50) | NOT NULL | バージョン番号 (v1.0.0など) |
| `status` | ENUM | DEFAULT 'staging' | 'staging', 'production', 'archived' |
| `metrics` | JSONB | | 評価指標 |
| `parameters` | JSONB | | 学習時パラメータ |
| `artifact_uri` | VARCHAR(1024) | NOT NULL | モデルアーティファクトURI (S3) |
| `git_commit` | VARCHAR(40) | | コミットハッシュ |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 作成日時 |

### 1.2 実験管理

#### 3. experiments
MLflow Experimentに相当する実験管理テーブル。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `experiment_id` | UUID | PK | 実験ID |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL | 実験名 |
| `description` | TEXT | | 説明 |
| `owner` | VARCHAR(255) | NOT NULL | 所有者 |
| `tags` | JSONB | | 実験タグ |
| `artifact_location` | VARCHAR(1024) | | アーティファクト保存先ルートURI |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 作成日時 |

#### 4. runs
各実験の実行履歴。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `run_id` | UUID | PK | 実行ID |
| `experiment_id` | UUID | FK(experiments.experiment_id) | 実験ID |
| `status` | ENUM | NOT NULL | 'running', 'completed', 'failed', 'killed' |
| `start_time` | TIMESTAMP | NOT NULL | 開始時間 |
| `end_time` | TIMESTAMP | | 終了時間 |
| `metrics` | JSONB | | 最終メトリクス値 |
| `params` | JSONB | | 実行時パラメータ |
| `tags` | JSONB | | 実行タグ |
| `artifact_uri` | VARCHAR(1024) | | このRunのアーティファクトURI |

#### 5. metrics
時系列メトリクスデータ。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `metric_id` | UUID | PK | メトリクスID |
| `run_id` | UUID | FK(runs.run_id) | 実行ID |
| `key` | VARCHAR(255) | NOT NULL | メトリクス名 (accuracy, lossなど) |
| `value` | FLOAT | NOT NULL | 値 |
| `step` | INT | NOT NULL | ステップ数/エポック数 |
| `timestamp` | TIMESTAMP | NOT NULL | 記録日時 |

#### 6. artifacts
生成物メタデータ。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `artifact_id` | UUID | PK | アーティファクトID |
| `run_id` | UUID | FK(runs.run_id) | 実行ID |
| `path` | VARCHAR(1024) | NOT NULL | 相対パス |
| `artifact_type` | ENUM | NOT NULL | 'model', 'dataset', 'plot', 'code' |
| `size_bytes` | BIGINT | | ファイルサイズ |
| `checksum` | VARCHAR(64) | | チェックサム (SHA256) |
| `storage_uri` | VARCHAR(1024) | NOT NULL | 完全なS3 URI |

### 1.3 学習実行

#### 7. training_jobs
KubeRay/Job Scheduler等で実行される学習ジョブ。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `job_id` | UUID | PK | ジョブID |
| `name` | VARCHAR(255) | NOT NULL | ジョブ名 |
| `status` | ENUM | DEFAULT 'pending' | 'pending', 'running', 'completed', 'failed' |
| `num_gpus` | INT | NOT NULL | 必要GPU数 |
| `num_nodes` | INT | NOT NULL | 必要ノード数 |
| `framework` | VARCHAR(50) | NOT NULL | 使用フレームワーク |
| `config_json` | JSONB | | ジョブ設定詳細 |
| `started_at` | TIMESTAMP | | 開始日時 |
| `completed_at` | TIMESTAMP | | 完了日時 |
| `resource_usage` | JSONB | | リソース消費統計 |

#### 8. hyperopt_studies
Optuna Study情報。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `study_id` | UUID | PK | Study ID |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL | Study名 |
| `direction` | ENUM | NOT NULL | 'minimize', 'maximize' |
| `algorithm` | ENUM | DEFAULT 'tpe' | 'tpe', 'cma', 'grid', 'random' |
| `n_trials` | INT | NOT NULL | 試行回数上限 |
| `best_trial_id` | UUID | | 最良トライアルへの参照 |
| `status` | VARCHAR(20) | | Studyステータス |

#### 9. hyperopt_trials
Optuna Trial情報。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `trial_id` | UUID | PK | Trial ID |
| `study_id` | UUID | FK(hyperopt_studies.study_id) | Study ID |
| `number` | INT | NOT NULL | 試行番号 |
| `status` | VARCHAR(20) | NOT NULL | 'COMPLETE', 'PRUNED', 'FAIL', 'WAITING' |
| `params` | JSONB | NOT NULL | 試行パラメータ |
| `value` | FLOAT | | 目的関数値 |
| `duration_seconds` | FLOAT | | 実行時間 |

### 1.4 Feature Store

#### 10. feature_definitions
特徴量のメタデータ定義。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `feature_id` | UUID | PK | 特徴量ID |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL | 特徴量名 |
| `entity_type` | VARCHAR(50) | NOT NULL | エンティティ種別 (user, item) |
| `value_type` | ENUM | NOT NULL | 'int', 'float', 'string', 'bool', 'list' |
| `description` | TEXT | | 説明 |
| `owner` | VARCHAR(255) | | 管理者 |
| `tags` | JSONB | | 分類タグ |

#### 11. feature_views
Feature View定義。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `view_id` | UUID | PK | View ID |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL | View名 |
| `entities` | JSONB | NOT NULL | 関連エンティティリスト |
| `features` | JSONB | NOT NULL | 特徴量リスト |
| `ttl_seconds` | INT | | 有効期限 (TTL) |
| `online_enabled` | BOOLEAN | DEFAULT FALSE | Online Store同期有効化 |
| `offline_enabled` | BOOLEAN | DEFAULT TRUE | Offline Store同期有効化 |

#### 12. feature_materializations
Feature Storeへの同期（Materialization）ジョブ履歴。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `mat_id` | UUID | PK | マテリアライズID |
| `view_id` | UUID | FK(feature_views.view_id) | 対象View ID |
| `start_time` | TIMESTAMP | NOT NULL | データ範囲開始 |
| `end_time` | TIMESTAMP | NOT NULL | データ範囲終了 |
| `status` | VARCHAR(20) | | 実行ステータス |
| `rows_processed` | BIGINT | | 処理行数 |
| `completed_at` | TIMESTAMP | | 完了日時 |

### 1.5 推論サービング

#### 13. serving_endpoints
推論エンドポイントの構成。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `endpoint_id` | UUID | PK | エンドポイントID |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL | エンドポイント名 |
| `model_version_id` | UUID | FK(model_versions.version_id) | デプロイモデルバージョン |
| `framework` | VARCHAR(50) | NOT NULL | 推論ランタイム |
| `replicas` | INT | DEFAULT 1 | 起動レプリカ数 |
| `cpu_request` | VARCHAR(20) | | CPUリクエスト (例: "500m") |
| `memory_request` | VARCHAR(20) | | メモリリクエスト (例: "2Gi") |
| `gpu_request` | VARCHAR(20) | | GPUリクエスト (例: "1") |
| `status` | ENUM | | 'pending', 'running', 'failed' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 作成日時 |

#### 14. inference_requests
推論リクエストのログ（監査・デバッグ用）。全量ではなくサンプリング保存を推奨。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `request_id` | UUID | PK | リクエストID |
| `endpoint_id` | UUID | FK(serving_endpoints.endpoint_id) | エンドポイントID |
| `input_hash` | VARCHAR(64) | | 入力データのハッシュ値 |
| `latency_ms` | INT | | 処理時間 (ms) |
| `status_code` | INT | | HTTPステータスコード |
| `error_message` | TEXT | | エラー詳細 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | リクエスト受信日時 |

#### 15. ab_tests
A/Bテスト設定。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `test_id` | UUID | PK | テストID |
| `name` | VARCHAR(255) | NOT NULL | テスト名 |
| `baseline_endpoint_id` | UUID | FK(serving_endpoints.endpoint_id) | ベースラインモデル |
| `candidate_endpoint_id` | UUID | FK(serving_endpoints.endpoint_id) | チャレンジャーモデル |
| `traffic_split` | FLOAT | NOT NULL | チャレンジャーへのトラフィック割合 (0.0-1.0) |
| `metric_name` | VARCHAR(255) | NOT NULL | 評価指標 |
| `status` | ENUM | DEFAULT 'running' | 'running', 'completed' |
| `start_at` | TIMESTAMP | | 開始日時 |
| `end_at` | TIMESTAMP | | 終了日時 |

### 1.6 パイプライン・監視

#### 16. data_pipelines
データパイプライン定義。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `pipeline_id` | UUID | PK | パイプラインID |
| `name` | VARCHAR(255) | NOT NULL | パイプライン名 |
| `schedule` | VARCHAR(100) | | CRON形式スケジュール |
| `last_run_at` | TIMESTAMP | | 最終実行日時 |
| `next_run_at` | TIMESTAMP | | 次回実行予定日時 |
| `status` | VARCHAR(20) | | 現在のステータス |
| `dag_definition` | JSONB | | DAG定義情報 |

#### 17. pipeline_runs
パイプライン実行履歴。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `run_id` | UUID | PK | 実行ID |
| `pipeline_id` | UUID | FK(data_pipelines.pipeline_id) | パイプラインID |
| `started_at` | TIMESTAMP | NOT NULL | 開始日時 |
| `completed_at` | TIMESTAMP | | 完了日時 |
| `status` | VARCHAR(20) | | 実行結果 |
| `tasks_json` | JSONB | | タスクごとの実行結果詳細 |

#### 18. model_drift_reports
モデルドリフト検知レポート。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `report_id` | UUID | PK | レポートID |
| `endpoint_id` | UUID | FK(serving_endpoints.endpoint_id) | エンドポイントID |
| `check_at` | TIMESTAMP | DEFAULT NOW() | チェック日時 |
| `psi_score` | FLOAT | | PSI (Population Stability Index) |
| `ks_statistic` | FLOAT | | Kolmogorov-Smirnov統計量 |
| `drift_detected` | BOOLEAN | | ドリフト判定結果 |
| `feature_drift_json` | JSONB | | 特徴量ごとのドリフト詳細 |

#### 19. gpu_utilization_logs
GPUクラスタのリソース使用ログ。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `log_id` | UUID | PK | ログID |
| `node_id` | VARCHAR(255) | NOT NULL | ノード名/IP |
| `gpu_index` | INT | NOT NULL | GPUインデックス |
| `utilization_pct` | FLOAT | | GPU使用率(%) |
| `memory_used_gb` | FLOAT | | メモリ使用量(GB) |
| `temperature` | INT | | GPU温度 |
| `recorded_at` | TIMESTAMP | DEFAULT NOW() | 記録日時 |

#### 20. datasets
データセット管理テーブル。

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `dataset_id` | UUID | PK | データセットID |
| `name` | VARCHAR(255) | NOT NULL | データセット名 |
| `version` | VARCHAR(50) | NOT NULL | バージョン |
| `storage_uri` | VARCHAR(1024) | NOT NULL | 保存先URI |
| `format` | ENUM | NOT NULL | 'csv', 'parquet', 'tfrecord', 'jsonl' |
| `size_bytes` | BIGINT | | データサイズ |
| `row_count` | BIGINT | | 行数 |
| `schema_json` | JSONB | | スキーマ情報 |
| `created_at` | TIMESTAMP | DEFAULT NOW() | 作成日時 |
