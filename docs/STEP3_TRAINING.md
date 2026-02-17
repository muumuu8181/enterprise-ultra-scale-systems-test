# Step 3: 分散学習基盤仕様

## 1. 概要
学習基盤は、RayおよびKubeRayを中心に構成され、PyTorch DDP、DeepSpeed ZeROを活用した大規模分散学習をサポートする。ジョブスケジューラによりリソースの効率的な利用と優先度制御を実現する。

## 2. クラス設計

### 2.1 分散学習マネージャ (Ray)
**File**: `src/training/distributed/ray_trainer.py`

#### Class: `RayDistributedTrainer`
Rayクラスタ上での学習ジョブのライフサイクルを管理する。

*   **Methods**:
    *   `submit_job(config: TrainingConfig) -> str`
        *   **説明**: 学習設定を受け取り、KubeRayクラスタへジョブを投入する。
        *   **引数**: `config` (モデル定義、データパス、GPU数など)
        *   **戻り値**: `job_id` (UUID文字列)
    *   `get_job_status(job_id: str) -> JobStatus`
        *   **説明**: ジョブの現在のステータス（PENDING, RUNNING, COMPLETED, FAILED）を取得する。
    *   `scale_workers(job_id: str, num_workers: int) -> None`
        *   **説明**:実行中のジョブに対してワーカー数を動的に変更する（Elastic Training対応）。
    *   `collect_metrics(job_id: str) -> List[MetricRecord]`
        *   **説明**: 各ワーカーから学習メトリクス（Loss, Accuracy, GPU使用率）を収集する。

### 2.2 DDPランチャー
**File**: `src/training/distributed/ddp_launcher.py`

#### Class: `DDPLauncher`
PyTorch Distributed Data Parallel (DDP) の起動を抽象化する。

*   **Methods**:
    *   `launch(num_nodes: int, num_gpus_per_node: int, training_fn: Callable, config: dict) -> None`
        *   **説明**: 指定されたノード数・GPU数で分散学習プロセスを立ち上げる。内部で `torch.distributed.launch` 相当の処理を行う。
    *   `_setup_nccl(master_addr: str, master_port: int) -> None`
        *   **説明**: NCCLバックエンドの初期化と通信グループの確立を行う。

### 2.3 DeepSpeedラッパー
**File**: `src/training/distributed/deepspeed_wrapper.py`

#### Class: `DeepSpeedWrapper`
Microsoft DeepSpeedを使用したメモリ最適化学習（ZeROステージ1-3）を容易にするラッパー。

*   **Methods**:
    *   `wrap_model(model: nn.Module, config: DeepSpeedConfig) -> DeepSpeedEngine`
        *   **説明**: PyTorchモデルをDeepSpeedエンジンでラップし、最適化機能を有効化する。
    *   `_build_zero_config(stage: Literal[1,2,3]) -> dict`
        *   **説明**: ZeROステージに応じた設定辞書（Optimizer Offload, Param Offload等）を生成する。
    *   `checkpoint(engine: DeepSpeedEngine, path: str) -> None`
        *   **説明**: 分散チェックポイントの保存を行う。
    *   `load_checkpoint(engine: DeepSpeedEngine, path: str) -> None`
        *   **説明**: 分散チェックポイントからの復元を行う。

### 2.4 ジョブスケジューラ
**File**: `src/training/scheduler/job_scheduler.py`

#### Class: `MLJobScheduler`
複数の学習ジョブの優先順位付けとリソース割り当てを行う。

*   **Methods**:
    *   `queue_job(job: TrainingJob) -> str`
        *   **説明**: ジョブを待ち行列に追加する。優先度（Priority）に基づきソートされる。
    *   `allocate_resources(job: TrainingJob) -> ResourceAllocation`
        *   **説明**: 利用可能なGPUリソースを確認し、ジョブに割り当てる。不足している場合はKubeRayにオートスケールを要求する。
    *   `preempt_job(job_id: str, reason: str) -> None`
        *   **説明**: 高優先度ジョブのために、実行中の低優先度ジョブを中断（Checkpoint保存後に停止）させる。
    *   `get_queue_status() -> QueueStatus`
        *   **説明**: 現在のキューの長さ、待機中のジョブ一覧を返す。

### 2.5 ハイパーパラメータ最適化
**File**: `src/training/hyperopt/optuna_study.py`

#### Class: `HyperOptManager`
Optunaを用いた分散ハイパーパラメータ探索を管理する。

*   **Methods**:
    *   `create_study(config: StudyConfig) -> Study`
        *   **説明**: 新しい最適化スタディを作成し、DB（`hyperopt_studies`）に登録する。
    *   `optimize(study_id: str, n_trials: int, timeout: int) -> BestTrial`
        *   **説明**: 指定された回数または時間内で最適化を実行する。
    *   `parallel_optimize(study_id: str, n_trials: int, n_jobs: int) -> BestTrial`
        *   **説明**: Rayタスクを用いて複数のトライアルを並列実行し、探索を高速化する。

## 3. インフラ構成 (KubeRay)

*   **Head Node**: スケジューラ、GCS (Global Control Store)、Dashboardを実行。
*   **Worker Node (GPU)**: 学習タスクを実行。NVIDIA GPU Operatorによりドライバを管理。
*   **Autoscaling**: 保留中のタスク数に応じてWorker Podを自動増減。
