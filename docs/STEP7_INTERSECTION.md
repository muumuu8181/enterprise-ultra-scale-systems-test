### IntersectionManager クラス詳細仕様

**request_intersection_slot(ego: EgoState, eta: float) -> SlotAllocation**
- AIM（Autonomous Intersection Management）プロトコル:
  1. 交差点に到達300m前にスロットリクエスト送信（V2X MCM）
  2. RSU/路側サーバーが衝突チェック（全車両の軌道交差判定）
  3. スロット割り当て（通過時刻 ± 1秒ウィンドウ）
  4. 割り当てられたスロットに合わせて速度調整
  5. 通過後に完了通知

### テストケース一覧
| テストID | シナリオ | 期待結果 |
|---|---|---|
| TC-V2X-001 | 2台が同時に交差点進入 | 先着優先でスロット割り当て、衝突なし |
| TC-V2X-002 | SPAT受信 → GLOSA計算 | 推奨速度40km/h → 信号青で通過 |
| TC-V2X-003 | 緊急車両CAM受信 | 周囲車両が路肩退避マヌーバ実行 |
| TC-V2X-004 | NLOS歩行者検知（V2X） | RSUのCPMで歩行者情報受信 → 減速 |
| TC-V2X-005 | 疑似ID ローテーション | 5分後に新IDでCAM送信、追跡不可 |
| TC-V2X-006 | OTA更新（差分パッチ） | 10MB差分→正常適用→バージョン確認 |
