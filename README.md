# 銀行コアバンキングシステム (Core Banking System)

## 概要
銀行の基幹業務（勘定系）を司るシステムです。預金、為替、融資、決済などの主要業務をサポートし、高い可用性とスケーラビリティを実現します。

## 目標
- **コード量**: 250,000行以上 (Step 1-10完遂時)
- **性能**: 10,000 TPS、レスポンスタイム1秒以内
- **可用性**: 99.999% (年間ダウンタイム5分以内)
- **セキュリティ**: Basel III準拠、AML/CFT対応
- **トランザクション**: ACID保証、2相コミット、Sagaパターン

## 技術スタック
- **Backend (Transaction)**: Java 17+ (Spring Boot 3.x)
- **Backend (Data Processing)**: Python 3.11+ (FastAPI, Pandas)
- **Database**: PostgreSQL 15 (Replication), Redis 7.x (Cache)
- **Message Queue**: Apache Kafka 3.x
- **Container**: Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana

## プロジェクト構造
- `backend-java/`: トランザクション処理を担うメインのバックエンド (Spring Boot)
- `backend-python/`: データ分析、バッチ処理、リスク計算などを担うバックエンド (Python)
- `docs/`: 要件定義、アーキテクチャ設計書
- `k8s/`: Kubernetes マニフェスト
- `legacy_trading_system/`: (旧) 証券トレーディングシステム

## セットアップ
### 前提条件
- Docker & Docker Compose
- Java 17+
- Python 3.11+
- Maven 3.8+

### 起動方法
```bash
# インフラストラクチャの起動
docker-compose up -d

# Javaバックエンドのビルドと実行
cd backend-java
mvn clean package
java -jar target/core-banking-0.0.1-SNAPSHOT.jar

# Pythonバックエンドの実行
cd ../backend-python
pip install -r requirements.txt
uvicorn main:app --reload
```
