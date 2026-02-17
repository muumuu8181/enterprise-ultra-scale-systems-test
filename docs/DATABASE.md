# DB設計書・テーブル一覧 (DATABASE.md)

## 1. データベース戦略
本システムでは、データの特性に応じて複数のデータベース技術を使い分ける「Polyglot Persistence」を採用する。

### 1.1 使用データベース
- **TimescaleDB (PostgreSQL拡張)**:
    - 用途: IoTセンサーデータ、交通流、エネルギー消費などの時系列データ。
    - 特徴: Hypertableによる自動パーティショニング、高圧縮、SQL互換。
- **PostGIS (PostgreSQL拡張)**:
    - 用途: 地理空間情報 (道路、建物、デバイス位置、境界)。
    - 特徴: 高速な空間インデックス (GiST)、空間クエリ。
- **ClickHouse**:
    - 用途: 過去データの長期保存、大規模集計分析。
    - 特徴: カラムナストアによる超高速集計。
- **Redis**:
    - 用途: リアルタイムキャッシュ、セッション管理、一時的な状態保持。

## 2. データ保持ポリシー
- **Raw Data (生データ)**: 30日間保持 (TimescaleDB)
- **Aggregated Data (集計データ)**: 2年間保持 (TimescaleDB / ClickHouse)
    - 連続集計 (Continuous Aggregates): 5分、1時間、1日単位で自動集計。
- **Incident Data (インシデント記録)**: 10年間保持 (監査・分析用)

## 3. テーブル一覧 (TimescaleDB + PostGIS)

| No. | テーブル名 | 説明 | 備考 |
|-----|------------|------|------|
| 1 | `devices` | IoTデバイス管理 | PostGIS (Point) |
| 2 | `sensor_readings` | センサー計測値 | Hypertable |
| 3 | `traffic_flows` | 交通流データ | Hypertable |
| 4 | `energy_consumption` | エネルギー消費データ | Hypertable |
| 5 | `water_usage` | 水道使用量・水質 | Hypertable |
| 6 | `air_quality` | 大気質データ | Hypertable |
| 7 | `incidents` | インシデント・事故情報 | PostGIS (Point) |
| 8 | `zones` | 都市ゾーン定義 | PostGIS (Polygon) |
| 9 | `roads` | 道路ネットワーク | PostGIS (LineString) |
| 10 | `intersections` | 交差点情報 | PostGIS (Point) |
| 11 | `traffic_signals` | 信号機制御情報 | |
| 12 | `parking_lots` | 駐車場情報 | PostGIS (Point) |
| 13 | `public_transit` | 公共交通ルート | PostGIS (LineString) |
| 14 | `transit_vehicles` | 公共交通車両位置 | PostGIS (Point) |
| 15 | `power_grid_nodes` | 電力網ノード | PostGIS (Point) |
| 16 | `renewable_sources` | 再生可能エネルギー源 | PostGIS (Point) |
| 17 | `citizen_reports` | 市民通報 | PostGIS (Point) |
| 18 | `city_services` | 市行政サービスAPI | |
| 19 | `alerts` | アラート・警報 | |
| 20 | `digital_twin_snapshots` | デジタルツイン状態保存 | JSONB |

詳細は `docs/STEP2_DATABASE.md` を参照。
