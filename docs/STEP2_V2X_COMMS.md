# STEP 2: V2X通信スタック設計 (STEP2_V2X_COMMS.md)

## 1. 概要
V2X通信スタックは、車両 (V2V)、インフラ (V2I)、歩行者 (V2P)、ネットワーク (V2N) との安全かつ低遅延な情報交換を実現する中核モジュールである。本システムでは、ETSI ITS-G5 (DSRC)、C-V2X (3GPP Rel-16 PC5/Uu)、および5G NR-V2Xのハイブリッド運用を前提とする。

## 2. 通信プロトコルスタック

### 2.1 Access Layer (L1/L2)
*   **DSRC (IEEE 802.11p)**: 5.9GHz帯、CSMA/CA方式。見通し通信に強い。
*   **C-V2X (PC5 Mode 4)**: 3GPP Rel-14/15/16。GNSS同期、SPS (Semi-Persistent Scheduling) による自律リソース選択。
*   **5G NR Uu**: 大容量データのクラウドアップロード、地図配信。

### 2.2 Network & Transport Layer (L3/L4)
*   **GeoNetworking (ETSI EN 302 636)**: 地理的ルーティング (GeoUnicast, GeoBroadcast, Topologically-Scoped Broadcast)。
*   **BTP (Basic Transport Protocol)**: ポート番号による上位プロトコル識別。
*   **IPv6**: インターネット接続用。

### 2.3 Facilities Layer (L5/L6/L7)
*   **CAM (Cooperative Awareness Message)**: 定期的な状態通知 (1-10Hz)。
*   **DENM (Decentralized Environmental Notification Message)**: イベント駆動型の危険通知。
*   **SPAT (Signal Phase and Timing)**: 信号現示情報。
*   **MAP (Map Data)**: 交差点幾何構造。
*   **CPM (Collective Perception Message)**: 自車が検知したオブジェクト情報の共有。

## 3. メッセージ定義 (C++17 Implementation)

### 3.1 CAM (Cooperative Awareness Message)
ETSI EN 302 637-2準拠。

```cpp
#include <cstdint>
#include <vector>

// 基本データ型定義 (分解能を考慮)
using HeadingValue = uint16_t;       // 0.1 degree (0..3600)
using SpeedValue = uint16_t;         // 0.01 m/s (0..16382)
using DriveDirection = uint8_t;      // 0: Forward, 1: Backward
using VehicleLengthValue = uint16_t; // 0.1 m
using VehicleWidthValue = uint16_t;  // 0.1 m
using LongAccelValue = int16_t;      // 0.1 m/s^2
using CurvatureValue = int16_t;      // 1/30000 1/m
using YawRateValue = int16_t;        // 0.01 degree/s

struct CAMMessage {
    uint32_t stationID;            // 一意のステーションID (Pseudonym)
    uint64_t generationDeltaTime;  // 65536ms wrap-around

    struct BasicVehicleContainerHighFrequency {
        HeadingValue heading;
        SpeedValue speed;
        DriveDirection driveDirection;
        VehicleLengthValue vehicleLength;
        VehicleWidthValue vehicleWidth;
        LongAccelValue longitudinalAcceleration;
        CurvatureValue curvature;
        YawRateValue yawRate;
    } highFrequencyContainer;

    struct BasicVehicleContainerLowFrequency {
        enum class VehicleRole : uint8_t {
            DEFAULT = 0,
            PUBLIC_TRANSPORT = 1,
            SPECIAL_TRANSPORT = 2,
            DANGEROUS_GOODS = 3,
            ROAD_WORK = 4,
            RESCUE = 5,
            EMERGENCY = 6,
            SAFETY_CAR = 7
        } vehicleRole;

        uint16_t exteriorLights; // Bitmask

        struct PathPoint {
            int32_t deltaLatitude;
            int32_t deltaLongitude;
            int16_t deltaAltitude;
        };
        std::vector<PathPoint> pathHistory;  // 最大23点
    } lowFrequencyContainer;
};
```

### 3.2 DENM (Decentralized Environmental Notification Message)
ETSI EN 302 637-3準拠。

```cpp
enum class DENMEventType : uint16_t {
    TRAFFIC_JAM = 1,
    ACCIDENT = 2,
    ROAD_WORKS = 3,
    ADVERSE_WEATHER = 4,
    HUMAN_PRESENCE_ON_ROAD = 11,
    WRONG_WAY_DRIVING = 14,
    EMERGENCY_VEHICLE_APPROACHING = 95
};

struct DENMMessage {
    struct ManagementContainer {
        uint32_t actionID;      // イベント識別子
        uint64_t detectionTime;
        uint64_t referenceTime;
        uint32_t termination;   // イベント終了条件
        struct GeoPosition {
            int32_t latitude;
            int32_t longitude;
            int32_t altitude;
        } eventPosition;
        uint16_t relevanceDistance; // イベント有効範囲
        uint16_t relevanceTrafficDirection;
    } management;

    struct SituationContainer {
        uint8_t informationQuality; // 1-7
        DENMEventType eventType;
        uint8_t causeCode;
        uint8_t subCauseCode;
    } situation;

    struct LocationContainer {
        std::vector<ManagementContainer::GeoPosition> eventSpeed;
        std::vector<ManagementContainer::GeoPosition> eventHeading;
    } location;

    struct AlacarteContainer {
        uint16_t lanePosition;
        int16_t temperature; // 道路状況用
    } alacarte;
};
```

## 4. 通信制御ロジック

### 4.1 V2X Communication Manager
アプリケーション層と通信層の仲介を行う主要クラス。

```cpp
class V2XCommunicationStack {
public:
    // CAM送信 (定期実行)
    void sendCAM(const VehicleState& state, uint8_t priority) {
        CAMMessage cam;
        cam.stationID = getCurrentStationID();
        cam.highFrequencyContainer.heading = state.heading * 10;
        cam.highFrequencyContainer.speed = state.speed * 100;
        // ... パッキング処理 ...

        asn1::Encoder encoder;
        std::vector<uint8_t> payload = encoder.encode(cam);
        scheduleTransmission(TxPriority::HIGH, 100); // 100ms interval
    }

    // DENM送信 (イベント駆動)
    void sendDENM(const HazardInfo& hazard, DENMEventType type) {
        DENMMessage denm;
        denm.management.actionID = generateActionID();
        denm.situation.eventType = type;
        // ... パッキング処理 ...

        asn1::Encoder encoder;
        std::vector<uint8_t> payload = encoder.encode(denm);
        scheduleTransmission(TxPriority::CRITICAL, 0); // Immediate
    }

    // SPAT受信処理
    void receiveSPAT(SPATMessage& spat, IntersectionID id) {
        TrafficLightState tls = parseSPAT(spat);
        IntersectionManager::updateSignalState(id, tls);
    }

    // 輻輳制御 (DCC: Decentralized Congestion Control)
    void performCongestionControl(float channelBusyRatio) {
        // ETSI TS 102 687
        if (channelBusyRatio > 0.6) {
            // 送信頻度を下げる、または送信パワーを下げる
            current_cam_interval_ms_ = 500; // 2Hz
            current_tx_power_dbm_ -= 3;
        } else {
            current_cam_interval_ms_ = 100; // 10Hz
            current_tx_power_dbm_ = 23;     // Max power
        }
    }

private:
    uint16_t current_cam_interval_ms_;
    int8_t current_tx_power_dbm_;
};
```

### 4.2 C-V2X PC5 Stack (Sidelink)
3GPP Rel-16 Mode 4 (自律リソース選択) の実装。

```cpp
class C_V2X_PC5Stack {
public:
    void initializeSidelinkScheduler(SidelinkConfig& config);

    // リソースプールの選択 (Zone IDに基づく)
    void selectResourcePool(ResourcePoolConfig& pool) {
        // 現在位置からZone IDを計算
        uint32_t zoneId = computeZoneId(current_gps_position_);
        current_pool_ = pool.getPoolForZone(zoneId);
    }

    // SCI (Sidelink Control Information) 送信
    void transmitSCI(SCIFormat1A& sci, uint8_t subchannelIndex);

    // 受信処理
    void receiveSidelinkData(SidelinkPDU& pdu) {
        if (!verifySignature(pdu)) {
            logError("Signature verification failed");
            return;
        }
        processPDU(pdu);
    }

    // CBR (Channel Busy Ratio) 測定
    float measureCBR() {
        // 直近100msのRSSIを測定し、閾値を超えるサブチャネルの割合を計算
        return phy_layer_->measureRSSI() / total_subchannels_;
    }

    // 送信電力制御
    void adaptTransmissionPower(float cbr_target) {
        float current_cbr = measureCBR();
        if (current_cbr > cbr_target) {
            phy_layer_->reduceTxPower();
        }
    }

private:
    PhyLayer* phy_layer_;
    ResourcePool current_pool_;
};
```

## 5. RSU連携

RSUは、交差点周辺の動的情報を集約し、車両へ配信する。

*   **I2V (Infrastructure-to-Vehicle)**: RSU -> Vehicle
    *   SPAT: 信号の現在の色と残り時間 (赤信号残り15秒など)。
    *   MAP: 交差点のレーン接続情報 (Lane Topology)。
    *   CPM: RSUのセンサーで見えている死角の車両・歩行者情報。

*   **V2I (Vehicle-to-Infrastructure)**: Vehicle -> RSU
    *   SRM (Signal Request Message): 公共車両や緊急車両からの優先信号要求。
