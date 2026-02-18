## 完全DDL

```sql
-- 車両フリートマスタ
CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin VARCHAR(17) UNIQUE NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INT CHECK (year BETWEEN 2000 AND 2040),
    autonomy_level INT NOT NULL CHECK (autonomy_level BETWEEN 0 AND 5),
    v2x_capabilities JSONB NOT NULL DEFAULT '{"dsrc": false, "c_v2x": false, "5g_v2x": false}',
    certificate_id UUID,
    hardware_version VARCHAR(50),
    software_version VARCHAR(100),
    last_ota_update TIMESTAMPTZ,
    odometer_km NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','maintenance','decommissioned')),
    fleet_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_vehicles_vin ON vehicles(vin);
CREATE INDEX idx_vehicles_fleet ON vehicles(fleet_id, status);

-- 車両位置履歴（TimescaleDB hypertable）
CREATE TABLE vehicle_positions (
    time TIMESTAMPTZ NOT NULL,
    vehicle_id UUID NOT NULL REFERENCES vehicles(vehicle_id),
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    altitude FLOAT,
    heading FLOAT CHECK (heading BETWEEN 0 AND 360),
    speed_ms FLOAT CHECK (speed_ms >= 0),
    accuracy_m FLOAT,
    positioning_source VARCHAR(20) CHECK (positioning_source IN ('RTK','GNSS','V2X','DR','FUSED')),
    confidence FLOAT CHECK (confidence BETWEEN 0 AND 1)
);
SELECT create_hypertable('vehicle_positions', 'time', chunk_time_interval => INTERVAL '1 hour');
SELECT add_retention_policy('vehicle_positions', INTERVAL '30 days');
CREATE INDEX idx_vehicle_positions_vehicle ON vehicle_positions(vehicle_id, time DESC);

-- V2Xメッセージログ（TimescaleDB hypertable）
CREATE TABLE v2x_messages (
    time TIMESTAMPTZ NOT NULL,
    message_id UUID DEFAULT gen_random_uuid(),
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('CAM','DENM','SPAT','MAP','CPM','MCM','IVIM')),
    sender_id UUID,
    station_type VARCHAR(20) CHECK (station_type IN ('vehicle','rsu','traffic_light','pedestrian')),
    payload BYTEA NOT NULL,
    rssi_dbm SMALLINT,
    channel_busy_ratio FLOAT CHECK (channel_busy_ratio BETWEEN 0 AND 1),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    verified BOOLEAN DEFAULT FALSE,
    certificate_id UUID,
    PRIMARY KEY (message_id, time)
);
SELECT create_hypertable('v2x_messages', 'time', chunk_time_interval => INTERVAL '1 hour');
SELECT add_retention_policy('v2x_messages', INTERVAL '7 days');

-- V2X PKI証明書
CREATE TABLE v2x_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_type VARCHAR(20) NOT NULL CHECK (certificate_type IN ('enrollment','pseudonym','authorization')),
    station_id UUID,
    certificate_data BYTEA NOT NULL,
    issuer_id UUID,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revocation_reason VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_v2x_certs_station ON v2x_certificates(station_id, valid_until DESC) WHERE NOT revoked;

-- HD Mapバージョン管理
CREATE TABLE map_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_code VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL CHECK (format IN ('lanelet2','opendrive','nds')),
    file_hash VARCHAR(64) NOT NULL,
    file_size_mb FLOAT,
    bounding_box JSONB,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    download_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (region_code, version)
);

-- 事故・インシデントログ（TimescaleDB hypertable）
CREATE TABLE incidents (
    time TIMESTAMPTZ NOT NULL,
    incident_id UUID DEFAULT gen_random_uuid(),
    incident_type VARCHAR(50) NOT NULL CHECK (incident_type IN ('collision','near_miss','emergency_brake','lane_departure','harsh_acceleration')),
    vehicle_id UUID REFERENCES vehicles(vehicle_id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    severity VARCHAR(20) CHECK (severity IN ('critical','high','medium','low')),
    ego_speed_ms FLOAT,
    ego_heading FLOAT,
    involved_objects JSONB DEFAULT '[]',
    denm_sent BOOLEAN DEFAULT FALSE,
    ecall_triggered BOOLEAN DEFAULT FALSE,
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (incident_id, time)
);
SELECT create_hypertable('incidents', 'time', chunk_time_interval => INTERVAL '1 day');

-- OTAキャンペーン管理
CREATE TABLE ota_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_name VARCHAR(200) NOT NULL,
    component VARCHAR(50) NOT NULL CHECK (component IN ('perception','planning','v2x_stack','hd_map','os','bootloader')),
    target_version VARCHAR(100) NOT NULL,
    rollout_strategy VARCHAR(20) NOT NULL CHECK (rollout_strategy IN ('canary','rolling','immediate')),
    rollout_percentage INT DEFAULT 0 CHECK (rollout_percentage BETWEEN 0 AND 100),
    target_filter JSONB,
    package_url TEXT NOT NULL,
    package_hash VARCHAR(64) NOT NULL,
    package_size_mb FLOAT,
    mandatory BOOLEAN DEFAULT FALSE,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','active','paused','completed','cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RSU（路側機）マスタ
CREATE TABLE rsus (
    rsu_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rsu_name VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    rsu_type VARCHAR(30) CHECK (rsu_type IN ('intersection','highway','urban','tunnel','parking')),
    capabilities JSONB DEFAULT '{"dsrc": true, "c_v2x": false, "5g": false}',
    connected_signal_ids JSONB DEFAULT '[]',
    firmware_version VARCHAR(50),
    last_heartbeat TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active'
);
```
