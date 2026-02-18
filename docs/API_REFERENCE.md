### モデル管理API

#### POST /api/v1/models
モデル登録

```json
Request:
{
  "model_name": "fraud-detector-v2",
  "model_type": "classification",
  "framework": "pytorch",
  "owner_team": "risk-ml"
}
Response 201:
{
  "model_id": "uuid",
  "created_at": "..."
}
```

#### POST /api/v1/models/{model_id}/versions
バージョン登録

```json
Request:
{
  "version_tag": "v1.2.0",
  "artifact_uri": "s3://mlplatform/models/fraud/v1.2.0/",
  "metrics": {
    "auc": 0.947,
    "f1": 0.891,
    "precision": 0.912
  },
  "parameters": {
    "learning_rate": 0.001,
    "epochs": 50,
    "batch_size": 256
  }
}
Response 201:
{
  "version_id": "uuid"
}
```

#### POST /api/v1/models/{model_id}/versions/{version_id}/promote
本番昇格

```json
Request:
{
  "justification": "Improved AUC by 0.02 vs v1.1.0"
}
Response 200:
{
  "status": "production",
  "promoted_at": "..."
}
```
**バリデーション**: 必須メトリクス閾値 (AUC>0.90) を超えていなければ HTTP 422

#### GET /api/v1/models/{model_id}/versions
バージョン一覧（ステータスでフィルタ可能）

### 実験・トラッキングAPI

#### POST /api/v1/experiments/{exp_id}/runs
Run開始

```json
Request:
{
  "parameters": {
    "lr": 0.001,
    "batch_size": 128
  },
  "tags": {
    "env": "gpu-cluster-a"
  }
}
Response 201:
{
  "run_id": "uuid",
  "status": "running"
}
```

#### POST /api/v1/runs/{run_id}/metrics
メトリクス記録（バッチ対応）

```json
Request:
{
  "metrics": [
    {"key": "train_loss", "value": 0.245, "step": 100},
    {"key": "val_accuracy", "value": 0.887, "step": 100}
  ]
}
```

#### POST /api/v1/runs/{run_id}/finish
Run完了

```json
Request:
{
  "status": "completed",
  "final_metrics": {
    "test_auc": 0.947
  }
}
```

### 推論API

#### POST /api/v1/endpoints/{endpoint_name}/predict
リアルタイム推論

```json
Request:
{
  "instances": [
    {
      "feature_1": 0.5,
      "feature_2": "tokyo",
      "feature_3": 1250.0
    }
  ],
  "parameters": {
    "return_proba": true
  }
}
Response 200:
{
  "predictions": [{"label": "fraud", "probability": 0.93}],
  "model_version": "v1.2.0",
  "latency_ms": 12
}
```

**SLA**: P99レイテンシ < 50ms

#### POST /api/v1/batch-jobs
バッチ推論ジョブ送信

```json
Request:
{
  "endpoint_id": "uuid",
  "input_uri": "s3://data/batch/2026-02-17/",
  "output_uri": "s3://results/batch/2026-02-17/",
  "max_workers": 16
}
Response 202:
{
  "job_id": "uuid",
  "status": "queued"
}
```

### トレーニングジョブAPI

#### POST /api/v1/training-jobs
ジョブ送信

```json
Request:
{
  "job_name": "fraud-v2-training",
  "job_type": "distributed",
  "num_workers": 8,
  "gpus_per_worker": 4,
  "queue_name": "gpu-high",
  "resource_config": {
    "instance_type": "p3.8xlarge"
  }
}
Response 202:
{
  "job_id": "uuid",
  "position_in_queue": 3
}
```
