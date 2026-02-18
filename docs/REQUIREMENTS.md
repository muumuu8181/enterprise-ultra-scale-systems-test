### 機能要件一覧
| ID | 機能名 | 説明 |
|---|---|---|
| FR-001 | CAM送受信 | ETSI EN 302 637-2準拠 10Hzで自車状態をブロードキャスト |
| FR-002 | DENM送信 | 危険情報・工事情報・緊急車両接近をDENMで配信 |
| FR-003 | SPAT受信・GLOSA | 信号フェーズ受信から最適速度アドバイス計算 |
| FR-004 | HD Map管理 | Lanelet2形式地図の差分更新（<1秒配信） |
| FR-005 | センサー融合 | LiDAR+Camera+Radar+IMUの統合物体リスト生成 |
| FR-006 | 物体検出・追跡 | YOLOv9-V2X + ByteTrack による3D追跡 |
| FR-007 | 経路計画 | Lanelet2 RoutingGraph + MPC による軌跡生成 |
| FR-008 | 交差点協調管理 | slot-based AIM による無信号交差点通過調整 |
| FR-009 | プラトーニング（隊列走行） | CACC制御・先頭車両追従・隊列形成/解散 |
| FR-010 | V2X PKI証明書管理 | SCMS連携・疑似ID 5分ローテーション・失効確認 |
| FR-011 | OTA更新 | Eclipse hawkBit経由での差分ファームウェア配信 |
| FR-012 | eCall自動通報 | 衝突検知→ERA-GLONASS/eCall自動発信 |
