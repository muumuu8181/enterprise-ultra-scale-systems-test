### ABTestRouter クラス詳細仕様

**route(request: InferenceRequest) -> BackendSelection**
- トラフィック分割アルゴリズム:
  - endpoint_id をキーにしたRedisからtraffic_split設定を取得
  - random.random() < traffic_pct/100 で確率的に振り分け
  - 振り分け結果をRedisに記録（統計集計用）

### テストケース一覧
| テストID | シナリオ | 期待結果 |
|---|---|---|
| TC-INF-001 | 正常推論（画像分類） | 200 OK, predictions配列返却 |
| TC-INF-002 | モデル未ロード | 503 Service Unavailable |
| TC-INF-003 | 入力形状不一致 | 400 Bad Request |
| TC-INF-004 | A/Bテスト トラフィック50/50 | 1000リクエスト中、各モデルへ450-550件 |
| TC-INF-005 | Tritonタイムアウト（5秒） | 504 Gateway Timeout |
| TC-INF-006 | 特徴量ストア接続断 | フォールバック: 特徴量なしで推論継続 |
