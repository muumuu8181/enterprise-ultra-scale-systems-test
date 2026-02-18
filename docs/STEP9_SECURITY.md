# Step 9: セキュリティ・ガバナンス仕様

## 1. 概要
AI/MLシステムの透明性（Transparency）、公平性（Fairness）、安全性（Safety）を確保し、規制要件および企業ポリシーに準拠する。モデルの振る舞いを説明可能にし、データの出所を追跡可能な状態にする。

## 2. クラス設計

### 2.1 モデルカード生成
**File**: `src/governance/model_card.py`

#### Class: `ModelCardGenerator`
GoogleのModel Card Toolkitの概念に基づき、モデルの概要・性能・制限事項をまとめたドキュメントを自動生成する。

*   **Methods**:
    *   `generate(model_version_id: str) -> ModelCard`
        *   **説明**: 指定されたモデルバージョンのメタデータ、開発者、学習データ概要、評価指標を集約し、MarkdownまたはHTML形式のレポートを出力する。
        *   **項目**: Intended Use（用途）、Limitations（制限）、Ethical Considerations（倫理的考慮）。
    *   `validate_fairness(model: Model, test_data: pd.DataFrame, sensitive_attrs: List[str]) -> FairnessReport`
        *   **説明**: 指定されたセンシティブ属性（性別、年齢など）に基づいて、モデルの予測が公平であるかを評価する。
        *   **指標**: Equal Opportunity Difference, Disparate Impact Ratio。

### 2.2 データ来歴管理
**File**: `src/governance/data_lineage.py`

#### Class: `DataLineageTracker`
データセットの生成過程（Lineage）を記録し、データの派生関係を可視化する。

*   **Methods**:
    *   `record_lineage(dataset_id: str, transformation: str, output_id: str) -> None`
        *   **説明**: 入力データセット、適用された変換処理（SQL/Spark Job）、出力データセットの関係をグラフDB（Neo4j等）またはメタデータDBに記録する。
    *   `get_upstream_lineage(dataset_id: str) -> List[LineageNode]`
        *   **説明**: 指定されたデータセットがどの元データから派生したかを再帰的に遡って取得する。データの汚染調査等に使用。

## 3. セキュリティ仕様

### 3.1 認証・認可 (RBAC)
KeycloakまたはActive Directoryと連携し、以下のロールに基づくアクセス制御を行う。

*   **Data Scientist**: 実験実行、モデル登録、Notebook作成が可能。Productionへのデプロイ権限はなし。
*   **ML Engineer**: パイプライン構築、モデルデプロイ、推論API管理が可能。
*   **MLOps Engineer**: クラスタ管理、監視設定、システム構成変更が可能。
*   **Admin**: 全権限、監査ログ閲覧が可能。

### 3.2 データ保護
*   **保存データの暗号化 (At Rest)**:
    *   S3バケット: Server-Side Encryption (SSE-S3 / SSE-KMS) を強制。
    *   データベース: EBSボリュームの暗号化。
    *   モデルアーティファクト: AES-256による暗号化。
*   **通信の暗号化 (In Transit)**:
    *   全API通信: TLS 1.3 (HTTPS) を強制。
    *   内部通信: Istio mTLS (Mutual TLS) によりマイクロサービス間の通信を暗号化・相互認証。

### 3.3 監査 (Audit)
*   **操作ログ**: 誰がいつどのモデルをデプロイしたか、データセットを削除したか等の操作を記録。
*   **推論ログ**: 機密情報（PII）が含まれる可能性があるため、保存前に自動マスキング処理を行う。
*   **コンプライアンス**: GDPR/CCPA対応として、特定ユーザーのデータ削除要求（Right to be Forgotten）に対応するAPIを用意。
