# Step 3: IoTゲートウェイ・センサー管理仕様 (STEP3_IOT.md)

## 1. 概要
IoTデバイス（カメラ、センサー、スマートメーター等）からのデータ収集、デバイス認証、プロビジョニング、状態監視を行うモジュールの仕様。

## 2. コンポーネント設計

### 2.1 MQTT Gateway (`src/iot/gateway/mqtt_broker.py`)
標準的なMQTTブローカーとして機能し、デバイスからのパブリッシュを受け付ける。
- **機能**:
    - `connect(broker_url, port=8883) -> None`: ブローカーへの接続。TLS暗号化必須。
    - `subscribe(topics: List[str]) -> None`: 必要なトピックの購読。
    - `publish_command(device_id, command: DeviceCommand) -> None`: デバイスへの制御コマンド送信。
    - `_on_message(topic, payload) -> None`: 受信メッセージの処理とKafkaへの投入。

### 2.2 LoRaWAN Gateway (`src/iot/gateway/lorawan_gateway.py`)
LoRaWANネットワークサーバーからのアップリンクを処理する。
- **機能**:
    - `handle_uplink(packet: LoRaPacket) -> SensorReading`: パケットの受信と解析。
    - `decode_payload(device_type, payload_hex) -> dict`: デバイスタイプごとのバイナリペイロードのデコード処理。

### 2.3 デバイス管理レジストリ (`src/iot/device_mgmt/registry.py`)
デバイスのライフサイクル管理を行う。
- **機能**:
    - `register(device: Device) -> str`: 新規デバイスの登録と認証キーの発行（プロビジョニング）。
    - `update_firmware(device_id, version) -> None`: OTA (Over-The-Air) ファームウェアアップデートのスケジュールと配信。
    - `detect_anomaly(device_id, readings) -> AnomalyResult`: センサー値に基づく故障予知（単純な閾値または統計モデル）。
    - `get_nearby_devices(location, radius_m, device_type) -> List[Device]`: 位置情報を基にしたデバイス検索。

## 3. 対応プロトコル
- **MQTT 3.1.1 / 5.0**: 主力プロトコル。QoS 1を基本とする。
- **CoAP**: 制約デバイス向け。
- **HTTP/2**: リッチなデバイスやバッチアップロード向け。
- **LoRaWAN**: 長距離・低電力センサー向け。
- **Zigbee / BLE**: エッジゲートウェイ配下の近距離通信。

## 4. セキュリティ要件
- **認証**: デバイス証明書 (X.509) または トークンベース認証。
- **暗号化**: TLS 1.2/1.3 による通信経路の暗号化。
- **アイソレーション**: デバイス侵害時に影響を最小化するための論理的な分離。
