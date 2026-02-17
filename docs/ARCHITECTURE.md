### V2X通信スタック構成図（Mermaid）
```mermaid graph TB
  subgraph OnBoard[車載システム DRIVE AGX Orin]
    AppLayer[Application Layer CAM/DENM/SPAT/CPM]
    FacLayer[Facilities Layer ITS-S]
    NetLayer[Network Layer GeoNetworking]
    AccessDSRC[DSRC IEEE 802.11p]
    AccessCV2X[C-V2X PC5 Mode4]
    Access5G[5G NR-V2X Uu]
    AppLayer --> FacLayer --> NetLayer
    NetLayer --> AccessDSRC
    NetLayer --> AccessCV2X
    NetLayer --> Access5G
  end
  subgraph RSU[路側機]
    RSU_App[RSU SPAT/MAP/RSA Broadcast]
    RSU_Net[GeoNetworking]
    RSU_PHY[DSRC / C-V2X]
    RSU_App --> RSU_Net --> RSU_PHY
  end
  subgraph Cloud[クラウド基盤]
    HDMapServer[HD Map Server]
    SCMS[SCMS PKI]
    FleetMgmt[Fleet Management]
    OTAServer[OTA Server hawkBit]
  end
  AccessDSRC <-->|300m| RSU_PHY
  Access5G <-->|Uu Interface| Cloud
```

### 自動運転処理パイプライン（シーケンス図）
```mermaid sequenceDiagram
  loop 100ms周期
    LiDAR->>SensorFusion: PointCloud2 (10Hz)
    Camera->>SensorFusion: Image x8 (30Hz)
    Radar->>SensorFusion: RadarScan (20Hz)
    IMU->>SensorFusion: IMUData (200Hz)
    SensorFusion->>Perception: FusedObjectList
    V2XStack->>Perception: CAMMessages (neighbors)
    Perception->>V2XObjectFusion: LocalObjects + V2XObjects
    V2XObjectFusion->>Planning: ExtendedObjectList (NLOS含む)
    Planning->>Planning: decideBehavior(FSM)
    Planning->>Planning: planLocalTrajectory(MPC)
    Planning->>Control: ControlCommand{steer, throttle, brake}
  end
```
