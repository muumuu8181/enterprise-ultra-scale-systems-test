# データベース設計書 (DATABASE.md)

## 1. 概要
本システムでは、用途に応じて以下のデータベース技術を組み合わせて使用する。

*   **PostgreSQL 15+**: 車両マスタ、ユーザー情報、証明書管理などのリレーショナルデータ。
*   **TimescaleDB**: 車両位置情報、V2Xメッセージログなどの時系列データ（ハイパーテーブル機能）。
*   **Redis Cluster 7.x**: リアルタイムセッション管理、Pub/Subメッセージング、キャッシュ。

## 2. スキーマ定義 (PostgreSQL / TimescaleDB)

### 2.1 車両・フリート管理

車両の基本情報およびスペック、現在の状態を管理する。

```sql
-- 車両フリート管理テーブル
CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY,
    vin VARCHAR(17) UNIQUE NOT NULL,
    make VARCHAR(50),
    model VARCHAR(50),
    year INT,
    autonomy_level INT CHECK (autonomy_level BETWEEN 0 AND 5),
    v2x_capabilities JSONB,  -- DSRC/C-V2X/5G 対応状況
    certificate_id UUID REFERENCES v2x_certificates(id),
    hardware_version VARCHAR(50),
    software_version VARCHAR(100),
    last_ota_update TIMESTAMPTZ,
    odometer_km NUMERIC(10,2),
    status VARCHAR(20) DEFAULT 'active', -- active, maintenance, decommissioned
    fleet_id UUID REFERENCES fleets(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- インデックス: VINでの検索、フリート単位での検索を高速化
CREATE INDEX idx_vehicles_vin ON vehicles(vin);
CREATE INDEX idx_vehicles_fleet_id ON vehicles(fleet_id);
```

### 2.2 位置情報履歴 (時系列データ)

TimescaleDBのハイパーテーブル機能を使用し、大量のプローブデータを効率的に格納・圧縮する。

```sql
-- 車両位置履歴 (TimescaleDB hypertable)
CREATE TABLE vehicle_positions (
    time TIMESTAMPTZ NOT NULL,
    vehicle_id UUID NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    altitude FLOAT,
    heading FLOAT,  -- 0.1 degree resolution
    speed FLOAT,    -- m/s
    accuracy_m FLOAT,
    positioning_source VARCHAR(20),  -- RTK/GNSS/V2X/DR
    confidence FLOAT
);

-- ハイパーテーブル化 (1時間ごとのチャンク分割)
SELECT create_hypertable('vehicle_positions', 'time', chunk_time_interval => INTERVAL '1 hour');

-- 複合インデックス: 特定車両の時間範囲検索用
CREATE INDEX idx_vehicle_positions_veh_time ON vehicle_positions (vehicle_id, time DESC);
```

### 2.3 V2Xメッセージログ

法的証拠および解析用に、送受信されたV2Xメッセージを記録する。

```sql
-- V2Xメッセージログ
CREATE TABLE v2x_messages (
    time TIMESTAMPTZ NOT NULL,
    message_id UUID DEFAULT gen_random_uuid(),
    message_type VARCHAR(20) NOT NULL,  -- CAM/DENM/SPAT/MAP/CPM/MCM
    sender_id UUID,
    station_type VARCHAR(20),  -- vehicle/rsu/traffic_light
    payload BYTEA NOT NULL,    -- ASN.1 DER encoded binary
    rssi_dbm SMALLINT,
    channel_busy_ratio FLOAT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    verified BOOLEAN DEFAULT FALSE,
    certificate_id UUID
);

SELECT create_hypertable('v2x_messages', 'time', chunk_time_interval => INTERVAL '1 hour');

-- 地域別検索のための空間インデックス (PostGIS連携想定)
-- CREATE INDEX idx_v2x_messages_geom ON v2x_messages USING GIST (ST_MakePoint(longitude, latitude));
```

### 2.4 HD Map バージョン管理

地図データのバージョンと配信状況を管理する。

```sql
-- HD Map バージョン管理
CREATE TABLE map_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_code VARCHAR(50) NOT NULL, -- e.g., JP-13 (Tokyo)
    version VARCHAR(50) NOT NULL,
    format VARCHAR(20),  -- lanelet2/opendrive
    file_hash VARCHAR(64) NOT NULL, -- SHA-256
    file_size_mb FLOAT,
    bounding_box JSONB, -- GeoJSON Polygon
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    release_notes TEXT,
    download_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 地図差分パッチ
CREATE TABLE map_patches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_version VARCHAR(50),
    to_version VARCHAR(50),
    region_code VARCHAR(50),
    patch_type VARCHAR(20),  -- incremental/full
    patch_data BYTEA,        -- Binary diff
    patch_size_kb INT,
    checksum VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.5 V2X PKI証明書管理

IEEE 1609.2に基づく証明書ライフサイクル管理。

```sql
-- V2X PKI証明書
CREATE TABLE v2x_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_type VARCHAR(20),  -- enrollment/pseudonym/authorization
    station_id UUID,
    certificate_data BYTEA NOT NULL,  -- IEEE 1609.2 binary format
    issuer_id UUID,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    revocation_reason VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_certs_station_valid ON v2x_certificates(station_id, valid_until);
```

### 2.6 事故・インシデントログ

機能安全および損害保険対応のための重要イベント記録。

```sql
-- 事故・インシデントログ
CREATE TABLE incidents (
    time TIMESTAMPTZ NOT NULL,
    incident_id UUID DEFAULT gen_random_uuid(),
    incident_type VARCHAR(50),  -- collision/near_miss/emergency_brake
    vehicle_id UUID REFERENCES vehicles(vehicle_id),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    severity VARCHAR(20),  -- critical/high/medium/low
    ego_speed_ms FLOAT,
    ego_heading FLOAT,
    involved_objects JSONB, -- ID list of other vehicles/pedestrians
    sensor_data_snapshot_id UUID, -- Link to raw sensor data blob
    denm_sent BOOLEAN DEFAULT FALSE,
    ecall_triggered BOOLEAN DEFAULT FALSE,
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable('incidents', 'time', chunk_time_interval => INTERVAL '1 day');
```

### 2.7 OTA更新管理

ソフトウェアアップデートのキャンペーン管理。

```sql
-- OTA更新管理
CREATE TABLE ota_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_name VARCHAR(200) NOT NULL,
    component VARCHAR(50),  -- perception/planning/v2x_stack/hd_map
    target_version VARCHAR(100),
    rollout_strategy VARCHAR(20),  -- canary/rolling/immediate
    rollout_percentage INT DEFAULT 0,
    target_vehicles JSONB,  -- filter criteria (e.g., {"model": "X", "year": 2024})
    package_url TEXT,
    package_hash VARCHAR(64),
    package_size_mb FLOAT,
    mandatory BOOLEAN DEFAULT FALSE,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.8 路側機 (RSU) 管理

```sql
-- RSU (路側機) 管理
CREATE TABLE rsus (
    rsu_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rsu_name VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    rsu_type VARCHAR(30),  -- intersection/highway/urban
    capabilities JSONB,    -- {"dsrc": true, "cv2x": true, "5g": true}
    connected_signal_ids JSONB, -- Traffic controller IDs
    firmware_version VARCHAR(50),
    last_heartbeat TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active'
);

-- フリート統計 (集計)
CREATE TABLE fleet_statistics (
    time TIMESTAMPTZ NOT NULL,
    fleet_id UUID,
    active_vehicles INT,
    total_km_driven NUMERIC(15,2),
    v2x_message_count BIGINT,
    cam_sent BIGINT,
    denm_received BIGINT,
    avg_channel_busy_ratio FLOAT,
    near_miss_count INT,
    emergency_brake_count INT,
    ota_success_rate FLOAT
);
SELECT create_hypertable('fleet_statistics', 'time', chunk_time_interval => INTERVAL '1 day');
```

## 3. データ保持ポリシー (Retention Policy)

TimescaleDBの機能を利用し、データ鮮度に応じて保持期間を設定する。

*   **Vehicle Positions**: 高頻度データは7日間保持し、その後は1分平均等にダウンサンプリングして1年間保持。
*   **V2X Messages**: 法的要件に従い30日間完全保持。その後、メタデータのみを残してバイナリペイロードは削除またはCold Storage (S3/Glacier) へ移動。
*   **Incidents**: 永久保存（または10年）。

```sql
-- データの自動圧縮ポリシー例
SELECT add_compression_policy('vehicle_positions', INTERVAL '7 days');
```

## 4. Redis Cluster 設計

### 4.1 キー設計
*   `vehicle:pos:{vehicle_id}` -> GeoHash (最新位置)
*   `map:tile:{tile_id}` -> Binary Protobuf (地図キャッシュ)
*   `session:auth:{token}` -> User ID (認証トークン)

### 4.2 Pub/Sub チャンネル
*   `v2x/broadcast/{region_id}`: 広域アラート配信
*   `vehicle/control/{vehicle_id}`: 遠隔操作コマンド (低遅延要求)
