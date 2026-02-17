### 全テーブル一覧（表形式）
| テーブル名 | 目的 | 主要カラム |
|---|---|---|
| models | モデルマスタ | model_id, name, framework, task_type |
| model_versions | バージョン管理 | version_id, model_id, version, stage, artifact_uri |
| experiments | 実験グループ | experiment_id, name, artifact_location |
| runs | 実験実行 | run_id, experiment_id, status, start_time, end_time |
| metrics | メトリクス時系列 | run_id, key, value, step, timestamp |
| params | ハイパーパラメータ | run_id, key, value |
| artifacts | アーティファクト | run_id, path, file_size, content_type |
| training_jobs | 学習ジョブ | job_id, run_id, cluster, gpu_count, status |
| hyperopt_studies | Optuna study | study_id, study_name, direction, n_trials |
| feature_views | Feast特徴量定義 | view_id, name, entities, feature_specs |
| serving_endpoints | 推論エンドポイント | endpoint_id, model_version_id, replicas, traffic_pct |
| drift_reports | ドリフト検知結果 | report_id, endpoint_id, psi_score, alert_triggered |
