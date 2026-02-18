```sql
-- IoTデバイスマスタ
CREATE TABLE devices (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_eui VARCHAR(16) UNIQUE NOT NULL,
    device_type VARCHAR(50) NOT NULL CHECK (device_type IN (
        'temperature','humidity','co2','pm25','traffic_camera',
        'parking_sensor','water_level','power_meter','ev_charger','weather_station'
    )),
    protocol VARCHAR(20) NOT NULL CHECK (protocol IN ('mqtt','lorawan','http','modbus','bacnet')),
    location GEOMETRY(Point, 4326),
    zone_id UUID REFERENCES zones(zone_id),
    firmware_version VARCHAR(50),
    battery_level SMALLINT CHECK (battery_level BETWEEN 0 AND 100),
    last_seen TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','maintenance','decommissioned')),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_devices_location ON devices USING GIST(location);
CREATE INDEX idx_devices_type_status ON devices(device_type, status);

-- センサーデータ時系列（TimescaleDB hypertable）
CREATE TABLE sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    device_id UUID NOT NULL REFERENCES devices(device_id),
    metric_name VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    quality SMALLINT DEFAULT 100 CHECK (quality BETWEEN 0 AND 100),
    location GEOMETRY(Point, 4326)
);
SELECT create_hypertable('sensor_readings', 'time', chunk_time_interval => INTERVAL '1 hour');
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
CREATE INDEX idx_sensor_readings_device ON sensor_readings(device_id, time DESC);
CREATE INDEX idx_sensor_readings_metric ON sensor_readings(metric_name, time DESC);

-- 交通流量時系列
CREATE TABLE traffic_flows (
    time TIMESTAMPTZ NOT NULL,
    intersection_id UUID NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('N','S','E','W','NE','NW','SE','SW')),
    vehicle_count INT NOT NULL DEFAULT 0,
    avg_speed_kmh FLOAT,
    occupancy_pct FLOAT,
    incident_detected BOOLEAN DEFAULT FALSE
);
SELECT create_hypertable('traffic_flows', 'time', chunk_time_interval => INTERVAL '1 hour');
CREATE INDEX idx_traffic_flows_intersection ON traffic_flows(intersection_id, time DESC);

-- 空間テーブル（PostGIS）
CREATE TABLE zones (
    zone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_name VARCHAR(200) NOT NULL,
    zone_type VARCHAR(50) CHECK (zone_type IN ('residential','commercial','industrial','green','transport','emergency')),
    boundary GEOMETRY(MultiPolygon, 4326) NOT NULL,
    population INT,
    area_sqm FLOAT GENERATED ALWAYS AS (ST_Area(boundary::geography)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_zones_boundary ON zones USING GIST(boundary);

CREATE TABLE roads (
    road_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_name VARCHAR(200),
    road_type VARCHAR(30) CHECK (road_type IN ('highway','arterial','collector','local','pedestrian')),
    geom GEOMETRY(LineString, 4326) NOT NULL,
    speed_limit_kmh INT,
    lanes INT,
    one_way BOOLEAN DEFAULT FALSE,
    surface VARCHAR(30)
);
CREATE INDEX idx_roads_geom ON roads USING GIST(geom);

-- デジタルツインスナップショット
CREATE TABLE digital_twin_snapshots (
    time TIMESTAMPTZ NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    state JSONB NOT NULL,
    version BIGINT NOT NULL DEFAULT 1,
    source VARCHAR(50)
);
SELECT create_hypertable('digital_twin_snapshots', 'time', chunk_time_interval => INTERVAL '1 day');

-- 緊急インシデント（PostGIS）
CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type VARCHAR(50) NOT NULL CHECK (incident_type IN ('fire','accident','medical','crime','flood','hazmat','other')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical','high','medium','low')),
    location GEOMETRY(Point, 4326) NOT NULL,
    address TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'reported' CHECK (status IN ('reported','dispatched','on_scene','resolved','closed')),
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    assigned_vehicles JSONB DEFAULT '[]',
    caller_id VARCHAR(100),
    description TEXT
);
CREATE INDEX idx_incidents_location ON incidents USING GIST(location);
CREATE INDEX idx_incidents_status ON incidents(status) WHERE status NOT IN ('resolved','closed');

-- スマートパーキング
CREATE TABLE parking_lots (
    lot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_name VARCHAR(200) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    total_spaces INT NOT NULL,
    available_spaces INT NOT NULL,
    ev_spaces INT DEFAULT 0,
    disabled_spaces INT DEFAULT 0,
    hourly_rate NUMERIC(8,2),
    currency VARCHAR(3) DEFAULT 'JPY',
    status VARCHAR(20) DEFAULT 'open',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_parking_lots_location ON parking_lots USING GIST(location);

-- EVチャージャー
CREATE TABLE ev_chargers (
    charger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id UUID REFERENCES parking_lots(lot_id),
    location GEOMETRY(Point, 4326) NOT NULL,
    charger_type VARCHAR(20) CHECK (charger_type IN ('AC_Level1','AC_Level2','DC_Fast','CHAdeMO','CCS')),
    max_power_kw FLOAT,
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available','occupied','faulted','offline')),
    current_session_id UUID,
    total_energy_kwh FLOAT DEFAULT 0
);
```
