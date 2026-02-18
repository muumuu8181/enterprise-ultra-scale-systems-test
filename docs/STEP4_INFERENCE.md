# Step 4: 推論サービング基盤仕様

## 1. 概要
推論基盤は、Triton Inference ServerとKServeを活用し、低レイテンシ（p99 < 50ms）かつ高スループットな推論を提供する。また、オンライン推論、バッチ推論、ストリーミング推論（LLM向け）の3つのモードをサポートする。

## 2. クラス設計

### 2.1 モデルサーバー
**File**: `src/inference/serving/model_server.py`

#### Class: `ModelServer`
FastAPIベースの推論サーバーコア。

*   **Methods**:
    *   `load_model(version_id: str, device: str) -> None`
        *   **説明**: 指定されたモデルバージョンをストレージからダウンロードし、GPU/CPUメモリにロードする。
    *   `predict(inputs: List[Any]) -> List[Any]`
        *   **説明**: 単一またはバッチ入力に対して推論を実行し、結果を返す。
    *   `predict_stream(inputs: Any) -> AsyncGenerator`
        *   **説明**: LLM向け。トークン生成ごとに結果をストリーミング（Server-Sent Events）で返す。
    *   `unload_model(version_id: str) -> None`
        *   **説明**: 不要になったモデルをメモリから解放する。
    *   `get_model_info() -> ModelInfo`
        *   **説明**: 現在ロードされているモデルのメタデータ（バージョン、入力形状など）を返す。

### 2.2 Tritonバックエンド
**File**: `src/inference/serving/triton_backend.py`

#### Class: `TritonInferenceBackend`
NVIDIA Triton Inference Serverへのインターフェース。

*   **Methods**:
    *   `deploy_model(model_config: TritonConfig) -> None`
        *   **説明**: Triton形式のモデル構成ファイル（config.pbtxt）を生成し、サーバーにデプロイする。
    *   `infer(model_name: str, inputs: np.ndarray, outputs: List[str]) -> Dict[str, np.ndarray]`
        *   **説明**: gRPC経由でTritonサーバーに推論リクエストを送信する。
    *   `dynamic_batching(requests: List[Request]) -> BatchResult`
        *   **説明**: 複数の同時リクエストを動的にまとめてバッチ処理し、スループットを向上させる。
    *   `get_metrics() -> ServerMetrics`
        *   **説明**: Tritonが公開するPrometheusメトリクス（GPU使用率、キュー滞留時間など）を取得する。

### 2.3 KServeアダプター
**File**: `src/inference/serving/kserve_adapter.py`

#### Class: `KServeAdapter`
Kubernetes上のKServeリソース（InferenceService）を操作する。

*   **Methods**:
    *   `create_inference_service(name: str, model_uri: str, resources: ResourceConfig) -> InferenceService`
        *   **説明**: 新しい推論サービスのマニフェストを作成し、K8sクラスタに適用する。
    *   `scale(name: str, min_replicas: int, max_replicas: int) -> None`
        *   **説明**: HPA (Horizontal Pod Autoscaler) の設定を更新し、負荷に応じたオートスケール範囲を変更する。
    *   `blue_green_deploy(name: str, new_version: str) -> None`
        *   **説明**: 新バージョンのサービスを立ち上げ、ヘルスチェック通過後にトラフィックを切り替える（Blue/Greenデプロイ）。

### 2.4 バッチ推論プロセッサ
**File**: `src/inference/batching/batch_processor.py`

#### Class: `BatchInferenceProcessor`
大量データに対する非同期推論処理を管理する。

*   **Methods**:
    *   `submit_batch_job(dataset_uri: str, model_version_id: str, output_uri: str) -> str`
        *   **説明**: バッチ推論ジョブをキューに登録する。
        *   **戻り値**: job_id
    *   `process_batch(job_id: str) -> BatchResult`
        *   **説明**: RayまたはSparkを用いてデータを分割し、並列推論を実行して結果を保存する。

### 2.5 A/Bテストルーター
**File**: `src/inference/ab_testing/ab_router.py`

#### Class: `ABTestRouter`
リクエストのルーティングと実験結果の分析を行う。

*   **Methods**:
    *   `route_request(test_id: str, request: Request) -> (endpoint_id: str, response: Response)`
        *   **説明**: 設定されたトラフィック分割比率（Traffic Split）に基づき、リクエストをBaseまたはCandidateのエンドポイントに振り分ける。
    *   `analyze_results(test_id: str) -> ABTestAnalysis`
        *   **説明**: 実験期間中のログを集計し、CVRやCTRなどの指標について統計的検定（t検定、カイ二乗検定など）を行う。
    *   `promote_winner(test_id: str) -> None`
        *   **説明**: 勝者となったモデルを正式なProductionモデルとして昇格させ、トラフィックを100%割り当てる。

## 3. インフラ構成 (KServe)

*   **InferenceService**: KServeのカスタムリソース定義(CRD)。サーバーレス推論を実現。
*   **Istio / Knative**: トラフィック管理とオートスケーリング（ゼロスケール含む）を担当。
*   **Model Mesh**: 多数のモデルを少数のPodで効率的にサービングする（マルチモデルサービング）。
