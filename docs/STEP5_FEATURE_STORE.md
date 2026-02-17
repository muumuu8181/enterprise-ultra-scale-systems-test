# Step 5: フィーチャーストア仕様 (Apache Feast)

## 1. 概要
Feature Storeは、機械学習モデルの学習と推論で使用される特徴量（Feature）を一元管理し、データの再利用性と一貫性（Training-Serving Consistency）を保証する。Apache Feastを採用し、低レイテンシのオンラインサービングと大規模なバッチ取得を実現する。

## 2. クラス設計

### 2.1 Feastクライアント
**File**: `src/feature_store/feast_client.py`

#### Class: `FeastFeatureStoreClient`
Feast SDKをラップし、特徴量の定義・管理を行う。

*   **Methods**:
    *   `apply_feature_view(feature_view: FeatureView) -> None`
        *   **説明**: 特徴量定義（FeatureView）をRegistryに登録・更新する。
    *   `materialize(start_date: datetime, end_date: datetime, feature_views: List[str]) -> None`
        *   **説明**: Offline StoreからOnline Store (Redis) へ指定期間の特徴量データをロードする。定期実行される。
    *   `get_online_features(entity_rows: List[Dict], feature_refs: List[str]) -> pd.DataFrame`
        *   **説明**: 推論時に使用。Redisから最新の特徴量を取得する。
        *   **SLA**: p99 < 5ms
    *   `get_historical_features(entity_df: pd.DataFrame, feature_refs: List[str]) -> pd.DataFrame`
        *   **説明**: 学習時に使用。Point-in-Time Correctness（特定時点の正しいデータ）を考慮して過去データを取得する。

### 2.2 Feature Server (FastAPI)
**File**: `src/feature_store/feature_server.py`

#### Class: `FeatureServer`
HTTP経由で特徴量を提供するAPIサーバー。

*   **Endpoints**:
    *   `POST /features/online`
        *   **Body**: `{"entities": [{"id": "user_1"}], "features": ["user_views:last_30d"]}`
        *   **Response**: `{"user_1": {"user_views:last_30d": 150}}`
        *   **説明**: エンティティIDを受け取り、オンライン特徴量を返す。
    *   `POST /features/batch`
        *   **Body**: `{"entity_query": "SELECT id FROM users", "features": [...]}`
        *   **説明**: バッチ処理向けに大量の特徴量をダンプするジョブを起動する。

## 3. インフラ・データフロー

### 3.1 Online Store (Redis Cluster)
*   **用途**: リアルタイム推論。
*   **データ構造**: Hash型を使用（Key=EntityID, Field=FeatureName, Value=Value）。
*   **更新頻度**: Kafkaストリーム処理（Flink）により準リアルタイム更新、または日次バッチによる更新。

### 3.2 Offline Store (S3 / Parquet)
*   **用途**: モデル学習、バッチ推論、履歴分析。
*   **フォーマット**: Apache Parquet (パーティション分割: 日付/エンティティ)。
*   **データソース**: データウェアハウス (BigQuery/Snowflake) やログ収集基盤からETL処理を経て格納。

### 3.3 Registry
*   **用途**: 特徴量定義、メタデータ、データソース情報の管理。
*   **バックエンド**: PostgreSQL。
