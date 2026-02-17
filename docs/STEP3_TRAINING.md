### RayDistributedTrainer クラス詳細仕様

**train(config: TrainingConfig) -> TrainingResult**
- 入力: model_class, dataset_uri, hyperparams, num_workers, gpus_per_worker, max_epochs
- 処理フロー:
  1. Ray Cluster に接続（ray.init）
  2. ScalingConfig を構築（num_workers × gpus_per_worker）
  3. TorchTrainer を初期化（train_loop_per_worker）
  4. MLflow run を開始（自動パラメータ記録）
  5. trainer.fit() を実行
  6. ベストチェックポイントを artifact_uri に保存
  7. MLflow に metrics/artifacts を記録
- 出力: TrainingResult（run_id, best_metric, artifact_uri, duration_sec）
- 例外: InsufficientGPUError, DatasetNotFoundError, OOMError

### DeepSpeedWrapper 設定仕様
- ZeRO Stage 3: パラメータ・勾配・オプティマイザ状態を全ノードに分散
- 設定例（ds_config.json の各フィールド説明）:
  - zero_optimization.stage: 3
  - zero_optimization.offload_optimizer.device: "cpu"（CPU offload）
  - fp16.enabled: true
  - gradient_clipping: 1.0
  - train_micro_batch_size_per_gpu: 4

### ハイパーパラメータ最適化（HyperOptManager）
- search_space の定義方法（Optuna API）
- pruner: MedianPruner（中央値以下の試行を早期打ち切り）
- sampler: TPESampler（Tree-structured Parzen Estimator）
- 並列Trial数: n_jobs = GPU数
- 収束判定: n_trials_without_improvement >= 20 で停止
