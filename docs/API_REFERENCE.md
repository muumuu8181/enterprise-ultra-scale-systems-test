### IoTデータAPI

#### POST /api/v1/devices デバイス登録
```json
Request:
{
  "device_eui": "A1B2C3D4E5F6A1B2",
  "device_type": "pm25",
  "protocol": "mqtt",
  "location": {"lat": 35.681, "lng": 139.767},
  "zone_id": "uuid"
}
Response 201:
{
  "device_id": "uuid",
  "config": {
    "report_interval_sec": 60
  }
}
```

#### GET /api/v1/sensors/latest 直近センサーデータ（空間クエリ対応）
| パラメータ | 型 | 説明 |
|---|---|---|
| lat, lng | float | 中心座標 |
| radius_m | int | 半径(メートル) |
| metric | string | センサー種別フィルタ |
| limit | int | 最大件数 (default: 100) |

#### GET /api/v1/sensors/{device_id}/history 時系列データ取得
| パラメータ | 型 | 説明 |
|---|---|---|
| start | datetime | 開始時刻 (ISO 8601) |
| end | datetime | 終了時刻 |
| step | string | 集計粒度 (1m/5m/1h/1d) |
| aggregation | string | avg/max/min/sum |

### 交通管理API

#### GET /api/v1/traffic/intersections/{id}/flow 交差点の現在交通流量

#### POST /api/v1/traffic/signals/{id}/preempt 信号プリエンプション（緊急車両用）
```json
Request:
{
  "incident_id": "uuid",
  "route": ["sig-001", "sig-002", "sig-003"],
  "duration_sec": 120
}
```

#### GET /api/v1/routing/optimal 最適ルート計算
| パラメータ | 型 | 説明 |
|---|---|---|
| origin_lat, origin_lng | float | 出発地 |
| dest_lat, dest_lng | float | 目的地 |
| mode | string | car/emergency/bicycle/pedestrian |
| avoid_zones | string[] | 回避ゾーンID |

### 緊急通報API

#### POST /api/v1/emergency/report 緊急通報
```json
Request:
{
  "incident_type": "fire",
  "severity": "critical",
  "location": {"lat": 35.681, "lng": 139.767},
  "description": "3階建てビル火災"
}
Response 201:
{
  "incident_id": "uuid",
  "dispatched_vehicles": [...],
  "eta_sec": 240
}
```

#### GET /api/v1/emergency/incidents/active 進行中インシデント一覧（空間フィルタ対応）

### パーキングAPI

#### GET /api/v1/parking/nearby 近隣駐車場検索
| パラメータ | 説明 |
|---|---|
| lat, lng | 現在地 |
| radius_m | 検索半径 |
| ev_only | EVチャージャー有りのみ |

#### POST /api/v1/parking/{lot_id}/reserve 駐車場予約
```json
Request:
{
  "user_id": "uuid",
  "duration_hours": 2,
  "vehicle_type": "ev",
  "charger_required": true
}
Response 201:
{
  "reservation_id": "uuid",
  "space_number": "B-42",
  "charger_id": "uuid"
}
```
