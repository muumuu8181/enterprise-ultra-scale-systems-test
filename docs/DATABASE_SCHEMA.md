```sql
CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin VARCHAR(17) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL CHECK (vehicle_type IN ('passenger','truck','bus','autonomous','ev','emergency')),
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    v2x_capability VARCHAR(20) CHECK (v2x_capability IN ('DSRC','C-V2X_PC5','C-V2X_Uu','hybrid')),
    pseudonym_cert_id VARCHAR(128),
    status VARCHAR(20) NOT NULL DEFAULT 'registered',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicle_positions (
    time TIMESTAMPTZ NOT NULL,
    vehicle_id UUID NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    heading_deg FLOAT,
    speed_kmh FLOAT,
    acceleration_ms2 FLOAT,
    location GEOMETRY(Point, 4326)
);
SELECT create_hypertable('vehicle_positions', 'time', chunk_time_interval => INTERVAL '10 minutes');
SELECT add_retention_policy('vehicle_positions', INTERVAL '7 days');

CREATE TABLE v2x_messages (
    msg_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    msg_type VARCHAR(10) NOT NULL CHECK (msg_type IN ('CAM','DENM','SPAT','MAP','IVI','MCM')),
    sender_id UUID,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sender_lat DOUBLE PRECISION,
    sender_lng DOUBLE PRECISION,
    rssi_dbm SMALLINT,
    message_data JSONB NOT NULL,
    station_type VARCHAR(20)
);

CREATE TABLE v2x_certificates (
    cert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(vehicle_id),
    cert_type VARCHAR(20) NOT NULL CHECK (cert_type IN ('enrollment','authorization','pseudonym')),
    cert_pem TEXT NOT NULL,
    public_key_hash VARCHAR(64) UNIQUE NOT NULL,
    issuer_id VARCHAR(100) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ
);

CREATE TABLE map_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id VARCHAR(50) NOT NULL,
    version_string VARCHAR(20) NOT NULL,
    format VARCHAR(20) CHECK (format IN ('lanelet2','opendrive','nds')),
    download_uri VARCHAR(500) NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    delta_from_version VARCHAR(20)
);

CREATE TABLE rsus (
    rsu_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rsu_name VARCHAR(100) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    communication_range_m INT NOT NULL DEFAULT 300,
    supported_protocols JSONB NOT NULL DEFAULT '[]',
    managed_intersection_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_heartbeat_at TIMESTAMPTZ
);
CREATE INDEX idx_rsus_location ON rsus USING GIST(location);
```
