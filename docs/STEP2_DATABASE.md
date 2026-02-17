# Step 2: DB詳細設計 (STEP2_DATABASE.md)

本ドキュメントでは、TimescaleDBおよびPostGISを用いた詳細なテーブル定義とDDL要件を記述する。

## 1. 共通要件
- **主キー**: 基本的にUUID v4を使用。
- **時系列データ**: `time`カラムをパーティションキーとするHypertable。
- **空間データ**: SRID 4326 (WGS84) を使用し、GISTインデックスを作成。
- **タイムゾーン**: 全て `TIMESTAMPTZ` (UTC) で保存。

## 2. テーブル定義 (DDL仕様)

### 2.1 IoTデバイス管理
**Table: `devices`**
- `device_id`: UUID (PK)
- `name`: TEXT
- `device_type`: ENUM ('camera', 'traffic_light', 'weather', 'power_meter', 'water_meter', 'parking', 'ev_charger')
- `location`: GEOMETRY(Point, 4326)
- `status`: TEXT
- `firmware_version`: TEXT
- `last_seen`: TIMESTAMPTZ

### 2.2 センサーデータ (Hypertable)
**Table: `sensor_readings`**
- `time`: TIMESTAMPTZ (Not Null, Partition Key)
- `device_id`: UUID
- `metric_name`: TEXT
- `value`: DOUBLE PRECISION
- `unit`: TEXT
- `quality_flag`: INT
- **備考**: TimescaleDB Hypertable化。圧縮ポリシー適用。

### 2.3 交通管理
**Table: `traffic_flows` (Hypertable)**
- `time`: TIMESTAMPTZ
- `intersection_id`: UUID
- `direction`: TEXT
- `vehicle_count`: INT
- `avg_speed`: FLOAT
- `congestion_level`: INT

**Table: `roads`**
- `road_id`: UUID (PK)
- `name`: TEXT
- `road_class`: TEXT
- `geometry`: GEOMETRY(LineString, 4326)
- `speed_limit`: INT
- `lanes`: INT

**Table: `intersections`**
- `intersection_id`: UUID (PK)
- `location`: GEOMETRY(Point, 4326)
- `signal_controller_id`: UUID
- `cycle_time`: INT
- `adaptive_control`: BOOLEAN

**Table: `traffic_signals`**
- `signal_id`: UUID (PK)
- `intersection_id`: UUID (FK)
- `phase_plan`: JSONB
- `current_phase`: INT
- `green_time`: INT

**Table: `parking_lots`**
- `lot_id`: UUID (PK)
- `name`: TEXT
- `location`: GEOMETRY(Point, 4326)
- `total_spaces`: INT
- `available_spaces`: INT
- `ev_spaces`: INT
- `updated_at`: TIMESTAMPTZ

### 2.4 公共交通
**Table: `public_transit`**
- `route_id`: UUID (PK)
- `name`: TEXT
- `route_type`: ENUM ('bus', 'tram', 'subway')
- `polyline`: GEOMETRY(LineString, 4326)

**Table: `transit_vehicles`**
- `vehicle_id`: UUID (PK)
- `route_id`: UUID (FK)
- `location`: GEOMETRY(Point, 4326)
- `speed`: FLOAT
- `occupancy_pct`: FLOAT
- `next_stop_id`: UUID
- `delay_minutes`: INT
- `updated_at`: TIMESTAMPTZ

### 2.5 エネルギー・環境
**Table: `energy_consumption` (Hypertable)**
- `time`: TIMESTAMPTZ
- `zone_id`: UUID
- `consumption_kwh`: DOUBLE PRECISION
- `peak_demand`: FLOAT
- `solar_generation`: FLOAT
- `grid_import`: FLOAT

**Table: `water_usage` (Hypertable)**
- `time`: TIMESTAMPTZ
- `district_id`: UUID
- `flow_rate`: FLOAT
- `pressure`: FLOAT
- `quality_ph`: FLOAT
- `turbidity`: FLOAT

**Table: `air_quality` (Hypertable)**
- `time`: TIMESTAMPTZ
- `station_id`: UUID
- `pm25`: FLOAT
- `pm10`: FLOAT
- `no2`: FLOAT
- `co2`: FLOAT
- `temperature`: FLOAT
- `humidity`: FLOAT

**Table: `power_grid_nodes`**
- `node_id`: UUID (PK)
- `name`: TEXT
- `node_type`: ENUM ('substation', 'transformer', 'ev_charger')
- `location`: GEOMETRY(Point, 4326)
- `capacity_kw`: FLOAT

**Table: `renewable_sources`**
- `source_id`: UUID (PK)
- `source_type`: ENUM ('solar', 'wind', 'hydro')
- `location`: GEOMETRY(Point, 4326)
- `installed_capacity_kw`: FLOAT

### 2.6 防災・緊急サービス
**Table: `incidents`**
- `incident_id`: UUID (PK)
- `incident_type`: ENUM ('accident', 'fire', 'flood', 'crime', 'medical')
- `location`: GEOMETRY(Point, 4326)
- `severity`: INT
- `status`: TEXT
- `reported_at`: TIMESTAMPTZ
- `resolved_at`: TIMESTAMPTZ

**Table: `citizen_reports`**
- `report_id`: UUID (PK)
- `category`: ENUM ('pothole', 'graffiti', 'illegal_parking', 'noise', 'stray_animal')
- `location`: GEOMETRY(Point, 4326)
- `description`: TEXT
- `photo_uri`: TEXT
- `status`: TEXT
- `reported_at`: TIMESTAMPTZ

**Table: `alerts`**
- `alert_id`: UUID (PK)
- `alert_type`: TEXT
- `severity`: ENUM ('info', 'warning', 'critical', 'emergency')
- `message`: TEXT
- `affected_zone_id`: UUID (FK)
- `created_at`: TIMESTAMPTZ
- `acknowledged_at`: TIMESTAMPTZ

### 2.7 その他
**Table: `zones`**
- `zone_id`: UUID (PK)
- `name`: TEXT
- `zone_type`: ENUM ('residential', 'commercial', 'industrial', 'park', 'emergency')
- `boundary`: GEOMETRY(Polygon, 4326)
- `population`: INT
- `area_sqm`: FLOAT

**Table: `city_services`**
- `service_id`: UUID (PK)
- `name`: TEXT
- `service_type`: TEXT
- `api_endpoint`: TEXT
- `status`: TEXT
- `last_health_check`: TIMESTAMPTZ

**Table: `digital_twin_snapshots`**
- `snapshot_id`: UUID (PK)
- `snapshot_time`: TIMESTAMPTZ
- `entity_type`: TEXT
- `entity_id`: UUID
- `state_json`: JSONB
- `version`: INT

## 3. 運用ポリシー
- **インデックス**: 全ての幾何カラム (`location`, `boundary`, `geometry`, `polyline`) にGISTインデックスを作成。
- **連続集計 (Continuous Aggregates)**: センサーデータ等は5分、1時間、1日単位で自動集計ビューを作成。
- **データ保持 (Retention)**:
  - raw data: 30日
  - aggregate: 2年
  - incident: 10年
