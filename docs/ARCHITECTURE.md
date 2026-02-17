# システムアーキテクチャ設計書 (ARCHITECTURE.md)

## 1. システム全体構成

### 1.1 階層構造
本システムは、以下の3層アーキテクチャで構成される。
1.  **Vehicle Layer (OBU)**: 車載ユニット。リアルタイム制御、センサー処理、V2X通信を担当。
2.  **Edge Layer (RSU/MEC)**: 路側ユニットおよびモバイルエッジコンピューティング。交差点制御、ローカルマップ配信、低遅延処理を担当。
3.  **Cloud Layer**: 中央クラウド。ビッグデータ分析、フリート管理、地図生成、デジタルツイン、SCMSを担当。

```mermaid
graph TD
    subgraph Cloud Layer
        TrafficCenter[Traffic Management Center]
        MapServer[HD Map Server]
        SCMS[Security Credential Management System]
        OTA[OTA Update Server]
        DigitalTwin[Digital Twin Simulation]
    end

    subgraph Edge Layer
        RSU1[Road Side Unit 1]
        RSU2[Road Side Unit 2]
        MEC[Mobile Edge Computing Node]
    end

    subgraph Vehicle Layer
        OBU1[Vehicle 1 (OBU)]
        OBU2[Vehicle 2 (OBU)]
        OBU3[Vehicle 3 (OBU)]
    end

    Cloud Layer <--> |Fiber/5G Backhaul| Edge Layer
    Edge Layer <--> |DSRC/C-V2X PC5| Vehicle Layer
    Vehicle Layer <--> |5G NR Uu| Cloud Layer
    Vehicle Layer <--> |DSRC/C-V2X PC5| Vehicle Layer
```

### 1.2 通信プロトコル
*   **V2V (Vehicle-to-Vehicle)**: DSRC (IEEE 802.11p), C-V2X PC5 (Mode 4). BSM/CAMの交換。
*   **V2I (Vehicle-to-Infrastructure)**: DSRC (WAVE), C-V2X PC5. SPAT/MAP/RSAの受信。
*   **V2N (Vehicle-to-Network)**: 5G NR Uu interface. 交通情報、地図更新、OTA。

## 2. マイクロサービスアーキテクチャ

### 2.1 車載システム (OBU)
AUTOSAR Adaptive Platform上に構築される。

*   **Perception Service**: センサーデータ（LiDAR, Camera, Radar）を入力とし、物体検出・追跡結果を出力。
*   **Localization Service**: GNSS/IMU/SLAM/HD Mapマッチングにより、高精度な自己位置を推定。
*   **Planning Service**: 周辺環境と目的地に基づき、最適な経路と軌道を生成。
*   **Control Service**: 軌道追従のためのステアリング、アクセル、ブレーキ制御。
*   **V2X Communication Service**: 各種V2Xメッセージのエンコード/デコード、署名検証、送受信管理。

### 2.2 クラウドシステム
Kubernetes上にデプロイされるマイクロサービス群。

*   **Fleet Management Service**: 車両の状態監視、配車管理。
*   **Map Update Service**: 車両からのプローブデータ収集、差分地図生成、配信。
*   **V2X Message Broker**: MQTT/Kafkaを用いたメッセージの大規模配信。
*   **SCMS Service**: 証明書ライフサイクル管理 (Enrollment, Authorization, CRL)。

## 3. データフロー

### 3.1 センサーフュージョンと制御ループ
1.  **Sensing**: LiDAR/Camera/Radarから生データを取得。
2.  **Perception**: 物体検出、セグメンテーション、トラッキングを実施。
3.  **Fusion**: センサーデータとV2Xメッセージ (BSM/CAM) を統合。
4.  **Planning**: リスクマップを作成し、行動決定と軌道生成。
5.  **Control**: 車両アクチュエータへの指令値生成 (CAN Bus)。

### 3.2 地図更新フロー
1.  **Data Collection**: 車両が走行中に地図との差異（工事、規制、地物変化）を検出。
2.  **Upload**: 差異情報をクラウドへアップロード (5G)。
3.  **Validation**: クラウド側で複数車両からのデータを照合・検証。
4.  **Generation**: 差分パッチ (Lanelet2/OpenDRIVE) を生成。
5.  **Distribution**: 該当エリアの車両へ配信 (Multicast/Geo-fencing)。

## 4. 技術スタック詳細

### 4.1 ハードウェア
*   **Vehicle**: NVIDIA DRIVE AGX Orin (SoC), Velodyne LiDAR, Continental Radar.
*   **Edge**: NVIDIA Jetson AGX Orin / IGX Orin.
*   **Cloud**: AWS/Azure/GCP (Kubernetes Cluster), GPU Instances for Training/Simulation.

### 4.2 ソフトウェア
*   **OS**: QNX / Linux (Real-time Kernel), ROS 2 Humble based middleware.
*   **Language**: C++17/20 (Core Logic), Python (AI/Tools), Rust (Safety Critical), Go (Cloud Microservices).
*   **Middleware**: DDS (Data Distribution Service), SOME/IP, MQTT-SN.
*   **Database**: PostgreSQL (Metadata), TimescaleDB (TimeSeries), Redis (Cache/State).
*   **AI/ML**: PyTorch, TensorRT, ONNX Runtime.

## 5. レイテンシバジェット

| 通信経路 | 目標レイテンシ | 備考 |
| :--- | :--- | :--- |
| Sensor -> Perception | < 30ms | Compute bound (GPU) |
| Perception -> Planning | < 10ms | CPU bound |
| Planning -> Control | < 5ms | Real-time constraint |
| V2V (DSRC/PC5) | < 10ms | Air interface |
| V2I (Edge) | < 20ms | Local processing |
| V2N (Cloud) | < 100ms | 5G Network |

## 6. セキュリティアーキテクチャ

*   **PKI (Public Key Infrastructure)**: IEEE 1609.2準拠の証明書管理。
*   **HSM (Hardware Security Module)**: 秘密鍵のハードウェア保護。
*   **Secure Boot**: 改ざん検知と信頼の連鎖 (Chain of Trust)。
*   **Firewall/IDS**: 車載ネットワークへの不正侵入検知・防止。
