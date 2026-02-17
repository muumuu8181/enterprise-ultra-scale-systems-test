# Step 1: プロジェクト構造・用語集

## 1. プロジェクトディレクトリ構造

本プラットフォームのソースコードおよび設定ファイルは以下の構造で管理される。

```text
mlops-platform/
├── docs/                       # 設計書・仕様書
├── src/                        # ソースコード
│   ├── training/               # 学習基盤
│   │   ├── distributed/        # 分散学習管理 (Ray/DDP)
│   │   ├── scheduler/          # ジョブスケジューラ (Go)
│   │   └── hyperopt/           # ハイパーパラメータ最適化
│   ├── inference/              # 推論基盤
│   │   ├── serving/            # モデルサービング (KServe/Triton)
│   │   ├── batching/           # バッチ推論
│   │   └── ab_testing/         # A/Bテストルーター
│   ├── feature_store/          # フィーチャーストア (Feast)
│   ├── model_registry/         # モデルレジストリ
│   ├── pipeline/               # MLパイプライン (Airflow/Kubeflow)
│   ├── monitoring/             # モデル監視・ドリフト検知
│   └── api/                    # API Gateway (FastAPI)
├── k8s/                        # Kubernetes マニフェスト
│   ├── training/               # KubeRay クラスタ設定
│   └── serving/                # KServe 設定
└── tests/                      # テストコード
```

## 2. 用語集 (Glossary)

本プロジェクトで使用される主要な用語の定義。

| 用語 | 英語表記 | 定義・説明 |
| :--- | :--- | :--- |
| **MLOps** | Machine Learning Operations | 機械学習モデルの開発・運用を自動化・効率化する手法や基盤。 |
| **DDP** | Distributed Data Parallel | PyTorchなどが提供する分散データ並列学習手法。各GPUにモデルのコピーを持ち、勾配のみを同期する。 |
| **ZeRO** | Zero Redundancy Optimizer | DeepSpeedが提供するメモリ最適化分散学習技術。モデルの状態（パラメータ、勾配、オプティマイザ状態）をGPU間で分割保持することで大規模モデルの学習を可能にする。 |
| **KV-Cache** | Key-Value Cache | TransformerベースのLLM推論において、Attention計算の再計算を避けるためにKeyとValueのペアをキャッシュし高速化する技術。 |
| **ONNX** | Open Neural Network Exchange | 異なるフレームワーク間でモデルを交換・利用するための共通フォーマット。 |
| **TensorRT** | TensorRT | NVIDIAが提供するGPU向け推論最適化ライブラリ・ランタイム。量子化やレイヤー統合により推論を高速化する。 |
| **Feature Drift** | Feature Drift | 学習時の入力データの分布と、推論時の入力データの分布が乖離する現象。精度の低下要因となる。 |
| **Concept Drift** | Concept Drift | 入力データとターゲット変数の関係性が時間とともに変化する現象（例：ユーザーの嗜好変化）。 |
| **Shadow Mode** | Shadow Mode | 新しいモデルを本番環境にデプロイする際、実際のリクエストを並行して流し（シャドーイング）、既存モデルの応答には影響を与えずに新モデルの挙動やエラーを確認する手法。 |
| **Canary Release** | Canary Release | 新しいモデルへのトラフィックを段階的に増やし（例: 1% -> 10% -> 100%）、問題が発生した場合に即座にロールバックするデプロイ戦略。 |
| **Data Version Control** | Data Version Control (DVC) | コードのバージョン管理と同様に、大規模なデータセットやモデルファイルのバージョンを管理する手法・ツール。 |
| **RLHF** | Reinforcement Learning from Human Feedback | 人間のフィードバックに基づく強化学習。LLMの出力を人間の好みに合わせるために用いられる。 |
| **LoRA** | Low-Rank Adaptation | LLMなどの巨大な事前学習済みモデルを効率的にファインチューニングする手法。全パラメータではなく、少数の追加パラメータのみを更新する。 |
