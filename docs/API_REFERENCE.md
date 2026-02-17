# API Reference

## V2XメッセージングAPI
### POST /api/v1/v2x/cam
- **説明**: CAM受信（ETSI EN 302 637-2準拠、10Hz、basic_container + high_frequency_container）

### POST /api/v1/v2x/denm
- **説明**: DENM送信（management_container + situation_container）

### GET /api/v1/v2x/spat/{intersection_id}
- **説明**: 信号フェーズ取得

### POST /api/v1/v2x/glosa
- **説明**: GLOSA最適速度計算（distance, time_to_green, vehicle_classから `advice_speed_kmh = distance / (time_to_green + duration/2) × 3.6` で算出）

## 車両管理API
### POST /api/v1/vehicles
- **説明**: 車両登録

### POST /api/v1/vehicles/{id}/position
- **説明**: 位置情報更新（10Hz）

### GET /api/v1/vehicles/{id}/nearby
- **説明**: 周辺車両検索（ST_DWithin 200m）

### POST /api/v1/vehicles/{id}/ota/subscribe
- **説明**: OTA購読（current_software_versions, preferred_window）

## HDマップAPI
### GET /api/v1/maps/regions/{id}/latest
- **説明**: 最新バージョン確認

### GET /api/v1/maps/tiles
- **説明**: タイル差分取得（tile_ids, from_version, format）

### POST /api/v1/maps/regions/{id}/publish
- **説明**: 新バージョン公開（admin）

## PKI証明書API
### POST /api/v1/certs/pseudonym/rotate
- **説明**: 仮名証明書ローテーション（5km毎/15分毎、旧証明書をCRLへ）

### GET /api/v1/certs/{cert_id}/status
- **説明**: 証明書有効性確認

### GET /api/v1/certs/crl/latest
- **説明**: 証明書失効リスト取得
