# Step 8: モデル監視・ドリフト検知仕様

## 1. 概要
本番環境でのモデルの健全性（Health）と品質（Quality）を継続的に監視する。Feature Drift（入力分布の変化）やConcept Drift（予測精度の低下）を早期に検知し、アラート通知および自動再学習（Retraining）のトリガーとする。

## 2. クラス設計

### 2.1 ドリフト検知器
**File**: `src/monitoring/drift_detector.py`

#### Class: `ModelDriftDetector`
統計的手法を用いて分布間の距離を測定し、ドリフトを検知する。

*   **Methods**:
    *   `compute_psi(baseline: np.ndarray, current: np.ndarray, bins: int = 10) -> float`
        *   **説明**: Population Stability Index (PSI) を計算する。
        *   **判定基準**: PSI > 0.1 (警告), PSI > 0.25 (ドリフト発生)
    *   `compute_ks_statistic(baseline: np.ndarray, current: np.ndarray) -> KSResult`
        *   **説明**: Kolmogorov-Smirnov検定を実施し、2つの分布が有意に異なるかを判定する。
    *   `detect_concept_drift(y_true_window: List[float], y_pred_window: List[float]) -> DriftResult`
        *   **説明**: 正解ラベル（フィードバック）が得られた場合に、予測誤差の時系列変化を分析する（例: ADWINアルゴリズム）。
    *   `alert_if_drift(endpoint_id: str, threshold: float = 0.25) -> None`
        *   **説明**: 算出された指標が閾値を超えた場合、Slack/PagerDutyへアラートを送信する。

### 2.2 パフォーマンスモニター
**File**: `src/monitoring/performance_monitor.py`

#### Class: `ModelPerformanceMonitor`
推論APIの技術指標（レイテンシ、エラー率）およびビジネス指標を監視する。

*   **Methods**:
    *   `track_prediction_latency(endpoint_id: str, latency_ms: int) -> None`
        *   **説明**: リクエストごとの処理時間を計測し、Prometheusへメトリクスとしてエクスポートする。
    *   `compute_business_metrics(endpoint_id: str, date: date) -> BusinessMetrics`
        *   **説明**: 日次バッチでビジネスKPI（クリック率、コンバージョン率など）を集計する。
    *   `detect_anomaly(metric_series: pd.Series) -> AnomalyResult`
        *   **説明**: z-score（標準化スコア）を用いて、平均から3σ（標準偏差の3倍）以上乖離した異常値を検知する。

## 3. インフラ・可視化

### 3.1 監視ダッシュボード (Grafana)
Grafanaを用いて以下の情報をリアルタイム可視化する。

*   **Overview Panel**: 全モデルの稼働状況、総リクエスト数、平均レイテンシ。
*   **Model Detail Panel**: 特定モデルのバージョン、GPU使用率、推論スループット。
*   **Drift Analysis Panel**: 特徴量ごとの分布ヒストグラム比較（Baseline vs Current）、PSIスコア推移。
*   **Data Quality Panel**: 欠損率、外れ値の発生状況。

### 3.2 アラート通知
*   **Prometheus Alertmanager**:
    *   **High Latency**: p99レイテンシ > 100ms が5分継続した場合。
    *   **High Error Rate**: 5xxエラー率 > 1% が継続した場合。
    *   **Drift Detected**: PSI > 0.25 を検知した場合。
*   **連携先**: Slack, PagerDuty, Email。

### 3.3 データ収集フロー
1.  **推論ログ**: `InferenceRequest` ログを非同期でKafkaへ送信。
2.  **集計**: Kafka Streams / Flink によりウィンドウ集計（1分、1時間）。
3.  **保存**: 集計結果をTimescaleDB (PostgreSQL拡張) または InfluxDB へ格納。
4.  **可視化**: GrafanaがDBを参照してグラフ描画。
