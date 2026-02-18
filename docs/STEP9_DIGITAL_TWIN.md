# STEP 9: デジタルツイン・シミュレーション (STEP9_DIGITAL_TWIN.md)

## 1. 概要
実世界での開発・テストの限界 (高コスト、危険性、再現性欠如) を克服するため、デジタルツイン技術を活用し、仮想空間での検証を行う。NVIDIA OmniverseおよびUnreal Engine 5 (UE5) をコアエンジンとし、フォトリアリスティックな環境でセンサーデータを生成する。

## 2. シミュレーションプラットフォーム構成

### 2.1 コアエンジン
*   **NVIDIA Omniverse Replicator**: 合成データ生成 (Synthetic Data Generation) のための基盤。物理ベースレンダリング (Path Tracing) により現実の光学的特性を再現。
*   **Unreal Engine 5 + AirSim**: 車両力学モデル (PhysX/Chaos) とビジュアルレンダリングを担当。
*   **CARLA Simulator**: 都市環境シミュレーション、歩行者モデル、交通流生成。

### 2.2 OpenSCENARIO 2.0 (OSC 2.0)
シナリオ記述言語としてASAM OpenSCENARIO 2.0を採用。抽象度の高い記述から具体的なテストケースを自動生成する。

```python
scenario my_cut_in:
    ego_vehicle: vehicle
    target_vehicle: vehicle

    do parallel:
        ego_vehicle.drive()
        target_vehicle.drive() with:
            speed(30kph)
            lane_change(left, 5s)
```

## 3. テストフェーズ

### 3.1 MIL (Model-in-the-Loop)
*   **対象**: 制御アルゴリズム (Matlab/Simulink)、経路計画ロジック。
*   **環境**: PC上での純粋な数値シミュレーション。

### 3.2 SIL (Software-in-the-Loop)
*   **対象**: 実際のC++コード (AUTOSAR AP上で動作するもの)。
*   **環境**: Dockerコンテナ内の仮想ECU。
*   **連携**: ROS 2 Bridge経由でCARLAと接続。

### 3.3 HIL (Hardware-in-the-Loop)
*   **対象**: 実機ECU (NVIDIA DRIVE Orin)。
*   **環境**: dSPACEまたはNI (National Instruments) のHILリグ。センサー信号を物理的または電気的に注入 (Sensor Injection)。

### 4. 合成データ生成パイプライン (SDG)

AIモデルの学習データ不足を解消するため、仮想空間で自動生成した教師データを利用する。

*   **Domain Randomization**: 天候 (晴れ、雨、雪、霧)、照明 (昼、夕方、夜)、テクスチャ、オブジェクト配置をランダムに変化させ、汎化性能を高める。
*   **Edge Case Generation**: 事故寸前、逆走車、動物の飛び出しなど、実データ収集が困難なレアケースを重点的に生成。
*   **Automatic Annotation**: バウンディングボックス、セマンティックセグメンテーション、深度マップ等の正解ラベルを自動出力。

## 5. リアルタイム・ミラーリング

現実の車両および交通流を、低遅延でデジタルツインへ反映する。

*   **Vehicle Shadow**: 実車両の状態 (位置、速度、センサー値) をクラウド上の仮想車両 (Shadow) に同期。
*   **Traffic Mirroring**: RSU等からの情報を元に、周囲の他車両や歩行者を仮想空間にスポーンさせる。
*   **Prediction Simulation**: 現在の状況から数秒先を並列シミュレーションし、リスク予測を行う (Faster-than-real-time simulation)。
