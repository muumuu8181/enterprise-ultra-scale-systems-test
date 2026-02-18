```sql
CREATE TABLE models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    framework VARCHAR(50) NOT NULL CHECK (framework IN ('pytorch','tensorflow','jax','sklearn','xgboost','onnx')),
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('classification','regression','detection','nlp','embedding','generative')),
    owner VARCHAR(100),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE model_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(model_id),
    version VARCHAR(50) NOT NULL,
    stage VARCHAR(20) NOT NULL DEFAULT 'None'
        CHECK (stage IN ('None','Staging','Production','Archived')),
    artifact_uri TEXT NOT NULL,
    artifact_size_bytes BIGINT,
    run_id UUID REFERENCES runs(run_id),
    framework_version VARCHAR(50),
    python_version VARCHAR(20),
    input_schema JSONB,
    output_schema JSONB,
    metrics_snapshot JSONB,
    promoted_at TIMESTAMPTZ,
    promoted_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_id, version)
);
CREATE INDEX idx_model_versions_model_stage ON model_versions(model_id, stage);

CREATE TABLE experiments (
    experiment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) UNIQUE NOT NULL,
    artifact_location TEXT,
    lifecycle_stage VARCHAR(20) DEFAULT 'active' CHECK (lifecycle_stage IN ('active','deleted')),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(experiment_id),
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING'
        CHECK (status IN ('RUNNING','SCHEDULED','FINISHED','FAILED','KILLED')),
    start_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    artifact_uri TEXT,
    source_type VARCHAR(20),
    source_name TEXT,
    entry_point_name TEXT,
    user_id VARCHAR(100),
    tags JSONB DEFAULT '{}'
);
CREATE INDEX idx_runs_experiment_id ON runs(experiment_id, start_time DESC);
CREATE INDEX idx_runs_status ON runs(status) WHERE status = 'RUNNING';

CREATE TABLE metrics (
    id BIGSERIAL,
    run_id UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    key VARCHAR(250) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    step BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

CREATE TABLE params (
    run_id UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    key VARCHAR(250) NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (run_id, key)
);

CREATE TABLE training_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES runs(run_id),
    job_name VARCHAR(200) NOT NULL,
    cluster VARCHAR(50) NOT NULL,
    framework VARCHAR(50),
    gpu_type VARCHAR(50),
    gpu_count INT NOT NULL DEFAULT 1,
    cpu_count INT NOT NULL DEFAULT 4,
    memory_gb INT,
    image_uri TEXT,
    entry_script TEXT,
    config JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    cost_usd NUMERIC(10,4)
);

CREATE TABLE serving_endpoints (
    endpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) UNIQUE NOT NULL,
    model_version_id UUID REFERENCES model_versions(version_id),
    replicas INT NOT NULL DEFAULT 1,
    min_replicas INT NOT NULL DEFAULT 1,
    max_replicas INT NOT NULL DEFAULT 10,
    target_concurrency INT DEFAULT 100,
    traffic_percentage INT NOT NULL DEFAULT 100 CHECK (traffic_percentage BETWEEN 0 AND 100),
    accelerator_type VARCHAR(50),
    accelerator_count INT DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'CREATING',
    endpoint_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```
