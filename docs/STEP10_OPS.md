# STEP 10: 運用・監視・OTA (STEP10_OPS.md)

## 1. 概要
本システムは、数百万台規模の車両群 (Fleet) と、広域に分散した路側機 (RSU) を一元管理し、継続的な機能改善 (OTA) とリアルタイム監視を行う。システムの信頼性を維持し、法規制 (UN-R155, R156) に準拠するため、包括的な運用プラットフォームを構築する。

## 2. フリート管理ダッシュボード

### 2.1 構成技術
*   **Grafana**: 可視化ダッシュボード。車両位置 (World Map)、稼働率、アラート状況を表示。
*   **Prometheus**: メトリクス収集 (CPU/MEM/GPU usage, Latency)。
*   **Elasticsearch (Elastic Stack)**: ログデータの検索・分析 (Kibana)。

### 2.2 監視項目
*   **車両ステータス**: 位置、速度、バッテリー残量、ハードウェア健全性 (Self-Diagnosis)。
*   **V2X通信品質**: RSSI (受信強度)、パケット損失率 (PLR)、チャネルビジー率 (CBR)。
*   **インシデント**: 急ブレーキ、ニアミス、衝突検知、機能不全 (Disengagement)。

## 3. OTA更新パイプライン (Over-The-Air)

### 3.1 Eclipse hawkBit
オープンソースのIoT更新管理プラットフォームを採用。

*   **Campaign Management**: 更新対象 (特定車種、特定VIN、特定地域) のグルーピングとスケジュール管理。
*   **Rollout Strategy**: カナリアリリース (1% -> 10% -> 100%) により、大規模障害のリスクを低減。
*   **Rollback**: 更新失敗時や不具合発覚時の自動/手動ロールバック機能。

### 3.2 更新パッケージ構成
*   **Full Image**: OSイメージ全体の更新 (A/Bパーティション方式)。
*   **Differential Update**: バイナリ差分のみの更新 (bsdiff)。
*   **Container Update**: Kubernetes/Dockerコンテナ単位のアプリケーション更新。

## 4. ログ収集と異常検知

### 4.1 Fluentd / Logstash
車載機およびRSUからのログを効率的に収集・転送する。

*   **Log format**: JSON形式 (構造化ログ)。
*   **Priority**: Debug, Info, Warn, Error, Critical。
*   **Data thinning**: 重要度に応じた間引き送信 (高負荷時はCriticalのみ)。

### 4.2 PagerDuty統合
重大な異常 (サーバーダウン、大規模な通信障害、サイバー攻撃検知) 発生時、即座に運用担当者へ通知 (電話、SMS、Slack)。

## 5. DR/BCP (Disaster Recovery)

### 5.1 マルチリージョン構成
*   **Active-Active**: 東日本リージョンと西日本リージョンでトラフィックを分散。
*   **Data Replication**: PostgreSQL/TimescaleDBの非同期レプリケーション。Redis ClusterのGeo-Replication。

### 5.2 復旧目標 (RTO/RPO)
*   **RTO (Recovery Time Objective)**: < 5分 (自動フェイルオーバー)。
*   **RPO (Recovery Point Objective)**: < 1秒 (データ消失許容範囲)。

## 6. SOTIF検証とフィールド学習ループ

### 6.1 SOTIF (ISO/PAS 21448) プロセス
*   **Unknown Unsafe**: 未知の危険シナリオを特定し、既知の安全領域へ移行させる。
*   **Triggering Event Analysis**: 誤検知や誤制御を引き起こした要因 (逆光、豪雨、未知の物体) を分析。

### 6.2 データ収集・学習ループ (Data Loop)
1.  **Trigger**: 車両側で特定のイベント (急ブレーキ、介入) を検知。
2.  **Upload**: 前後数十秒のセンサーデータ (Raw Sensor Data) をクラウドへアップロード。
3.  **Annotation**: クラウド側で自動/手動アノテーション。
4.  **Training**: AIモデルの再学習 (Fine-tuning)。
5.  **Evaluation**: シミュレーション環境での回帰テスト。
6.  **Deploy**: OTAによるモデル更新。
