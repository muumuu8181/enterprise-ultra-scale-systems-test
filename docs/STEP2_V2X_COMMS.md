### V2XCommunicationStack クラス詳細仕様

**sendCAM(state: VehicleState, priority: uint8) -> None**
- 送信周期: 100ms（10Hz）固定
- CAM生成: 現在のGNSS位置・速度・heading・加速度から BasicContainer 構築
- 疑似ID (pseudonym): 5分ごとに自動ローテーション（プライバシー保護）
- 署名: ECDSA P-256（IEEE 1609.2 implicit certificate）
- チャネル混雑制御: CBR > 60% のとき送信電力を3dB削減（ETSI TS 102 687）

**receiveSPAT + calculateGLOSA(distance_m: float) -> float**
- SPAT受信: RSUから信号現示タイミング受信（各フェーズのminEndTime/maxEndTime/likelyTime）
- GLOSA速度計算:
  - 青信号到達速度: v = distance / timeToGreen（最大速度制限以下）
  - 赤信号回避速度: v = distance / (timeToGreen + cycleLengh)
  - 省エネ最適化: 勾配考慮（道路傾斜角から回生・加速エネルギー最小化）
- 出力: 推奨速度 [km/h]（HMIへ表示）
