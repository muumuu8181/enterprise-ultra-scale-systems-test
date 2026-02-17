-- MLモデルマスタ
CREATE TABLE models (
  model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name VARCHAR(200) NOT NULL,
  model_type VARCHAR(50) NOT NULL CHECK (model_type IN (
    'classification','regression','object_detection','nlp','recommendation',
    'time_series','generative','reinforcement','anomaly_detection'
  )),
  framework VARCHAR(30) NOT NULL CHECK (framework IN ('pytorch','tensorflow','jax','sklearn','xgboost','onnx')),
  owner_team VARCHAR(100) NOT NULL,
  description TEXT,
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_models_type ON models(model_type);

-- モデルバージョン
CREATE TABLE model_versions (
  version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id UUID NOT NULL REFERENCES models(model_id),
  version_tag VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'staging' CHECK (status IN ('staging','production','archived','failed')),
  artifact_uri VARCHAR(500) NOT NULL,  -- S3/GCS path
  framework_version VARCHAR(30),
  python_version VARCHAR(20),
  input_schema JSONB NOT NULL DEFAULT '{}',
  output_schema JSONB NOT NULL DEFAULT '{}',
  metrics JSONB NOT NULL DEFAULT '{}',
  parameters JSONB NOT NULL DEFAULT '{}',
  promoted_at TIMESTAMPTZ,
  promoted_by VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (model_id, version_tag)
);
CREATE INDEX idx_model_versions_model ON model_versions(model_id, status);
CREATE INDEX idx_model_versions_status ON model_versions(status);

-- 実験
CREATE TABLE experiments (
  experiment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_name VARCHAR(200) NOT NULL UNIQUE,
  model_id UUID NOT NULL REFERENCES models(model_id),
  owner VARCHAR(100) NOT NULL,
  description TEXT,
  tags JSONB DEFAULT '[]',
  artifact_location VARCHAR(500),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- トレーニングRun
CREATE TABLE runs (
  run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id UUID NOT NULL REFERENCES experiments(experiment_id),
  status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed','killed','scheduled')),
  start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  end_time TIMESTAMPTZ,
  source_type VARCHAR(30) CHECK (source_type IN ('notebook','job','api','autotrigger')),
  git_commit VARCHAR(40),
  parameters JSONB NOT NULL DEFAULT '{}',
  tags JSONB DEFAULT '{}',
  artifact_uri VARCHAR(500),
  error_message TEXT
);
CREATE INDEX idx_runs_experiment ON runs(experiment_id, start_time DESC);
CREATE INDEX idx_runs_status ON runs(status) WHERE status = 'running';

-- メトリクス時系列
CREATE TABLE metrics (
  metric_id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL REFERENCES runs(run_id),
  metric_name VARCHAR(200) NOT NULL,
  value DOUBLE PRECISION NOT NULL,
  step BIGINT NOT NULL DEFAULT 0,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_metrics_run ON metrics(run_id, metric_name, step);

-- トレーニングジョブ
CREATE TABLE training_jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES runs(run_id),
  job_name VARCHAR(200) NOT NULL,
  job_type VARCHAR(30) NOT NULL CHECK (job_type IN ('single','distributed','hyperopt','nas')),
  cluster VARCHAR(50) NOT NULL,
  num_workers INT NOT NULL DEFAULT 1,
  gpus_per_worker INT NOT NULL DEFAULT 0,
  cpu_per_worker INT NOT NULL DEFAULT 4,
  memory_gb_per_worker INT NOT NULL DEFAULT 16,
  priority INT NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
  queue_name VARCHAR(100) NOT NULL DEFAULT 'default',
  status VARCHAR(20) NOT NULL DEFAULT 'queued',
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  cost_usd NUMERIC(10,4),
  resource_config JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_training_jobs_status ON training_jobs(status, submitted_at);
CREATE INDEX idx_training_jobs_queue ON training_jobs(queue_name, priority DESC, submitted_at);

-- 推論エンドポイント
CREATE TABLE serving_endpoints (
  endpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint_name VARCHAR(200) NOT NULL UNIQUE,
  model_version_id UUID NOT NULL REFERENCES model_versions(version_id),
  deployment_type VARCHAR(30) NOT NULL CHECK (deployment_type IN ('realtime','batch','streaming','edge')),
  status VARCHAR(20) NOT NULL DEFAULT 'deploying' CHECK (status IN ('deploying','active','scaling','updating','stopped','failed')),
  replicas INT NOT NULL DEFAULT 1,
  min_replicas INT NOT NULL DEFAULT 1,
  max_replicas INT NOT NULL DEFAULT 10,
  target_cpu_utilization INT NOT NULL DEFAULT 70,
  endpoint_url VARCHAR(500),
  sla_latency_p99_ms INT,
  sla_availability_pct NUMERIC(5,3) DEFAULT 99.9,
  deployed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- A/Bテスト設定
CREATE TABLE ab_tests (
  test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_name VARCHAR(200) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('draft','running','paused','completed')),
  traffic_split JSONB NOT NULL,  -- {"endpoint_a": 0.9, "endpoint_b": 0.1}
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ,
  success_metric VARCHAR(100) NOT NULL,
  minimum_sample_size INT NOT NULL DEFAULT 1000,
  significance_level NUMERIC(4,3) NOT NULL DEFAULT 0.05,
  created_by VARCHAR(100),
  conclusion TEXT
);

-- 推論リクエストログ（パーティション）
CREATE TABLE inference_logs (
  log_id BIGSERIAL,
  endpoint_id UUID NOT NULL,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  latency_ms INT NOT NULL,
  status_code INT NOT NULL,
  input_size_bytes INT,
  output_size_bytes INT,
  model_version_id UUID NOT NULL,
  ab_test_id UUID,
  region VARCHAR(30),
  error_type VARCHAR(100)
) PARTITION BY RANGE (requested_at);
CREATE TABLE inference_logs_2026_q1 PARTITION OF inference_logs FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE inference_logs_2026_q2 PARTITION OF inference_logs FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE INDEX idx_inference_logs_endpoint ON inference_logs(endpoint_id, requested_at DESC);
CREATE INDEX idx_inference_logs_latency ON inference_logs(endpoint_id, latency_ms) WHERE status_code = 200;
