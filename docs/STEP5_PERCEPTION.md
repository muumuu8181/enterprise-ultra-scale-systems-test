# STEP 5: 環境認識・物体検出 (STEP5_PERCEPTION.md)

## 1. 概要
環境認識システムは、センサーフュージョン結果に基づき、周囲の動的・静的オブジェクトの意味論的理解 (Semantic Understanding) を行う。Deep Learningモデルを活用し、歩行者、車両、信号、標識等を高精度に検出し、さらにそれらの将来的な挙動 (Intent Prediction) を予測する。

## 2. 知覚パイプライン構成

### 2.1 物体検出 (Object Detection)
*   **2D Detection**: YOLOv9 (TensorRT最適化済み) を使用し、カメラ画像からBounding Boxを検出。
*   **3D Detection**: PointPillars または CenterPoint を使用し、LiDAR点群から3D Bounding Boxを検出。
*   **BEVFusion**: カメラとLiDARの特徴量をBird's Eye View (俯瞰図) 空間で統合し、悪天候時のロバスト性を向上。

### 2.2 セマンティックセグメンテーション
*   **モデル**: SegFormer または DeepLabV3+。
*   **用途**: 走行可能領域 (Drivable Area) の抽出、車線境界線 (Lane Markings) の検出。

### 2.3 物体追跡 (Object Tracking)
*   **2D Tracking**: ByteTrack (低信頼度検出の活用)。
*   **3D Tracking**: AB3DMOT (3D Multi-Object Tracking)。カルマンフィルタとハンガリアン法によるアソシエーション。

### 2.4 行動予測 (Behavior Prediction)
*   **モデル**: Trajectron++ または VectorNet。
*   **機能**: 他車両や歩行者の過去の軌跡から、数秒先の位置分布を確率的に予測。

## 3. クラス設計 (Python Implementation)

### 3.1 PerceptionPipeline
認識処理のメインフローを制御するクラス。

```python
import numpy as np
from typing import List, Tuple
from .models import YOLOv9, PointPillars, BEVFusion
from .tracking import ByteTrack, AB3DMOT
from .prediction import Trajectron

class PerceptionPipeline:
    def __init__(self, config: dict):
        self.detector_2d = YOLOv9(weights=config['yolo_weights'], engine='tensorrt')
        self.detector_3d = PointPillars(weights=config['pp_weights'])
        self.segmenter = BEVFusion(weights=config['bev_weights'])
        self.tracker = AB3DMOT(max_age=5, min_hits=3)
        self.predictor = Trajectron(horizon=5.0)

    def detect_objects_2d(self, frame: np.ndarray) -> List['Detection2D']:
        """カメラ画像からの2D物体検出"""
        # Preprocessing -> Inference -> NMS
        detections = self.detector_2d.infer(frame)
        return [d for d in detections if d.confidence > 0.5]

    def detect_objects_3d(self, pointcloud: np.ndarray) -> List['Detection3D']:
        """LiDAR点群からの3D物体検出"""
        # Voxelization -> Backbone -> Head
        return self.detector_3d.infer(pointcloud)

    def segment_scene(self, frame: np.ndarray, pointcloud: np.ndarray) -> 'SemanticMap':
        """走行可能領域と車線のセグメンテーション"""
        return self.segmenter.infer(frame, pointcloud)

    def track_objects(self, detections: List['Detection3D'], dt: float) -> List['TrackedObject']:
        """時系列トラッキングによるID割り当て"""
        # Update Kalman Filters -> Association -> Track Management
        tracks = self.tracker.update(detections, dt)
        return tracks

    def predict_trajectories(self, tracked_objects: List['TrackedObject'], horizon_s: float) -> List['Trajectory']:
        """将来軌道の予測 (マルチモーダル)"""
        trajectories = []
        for obj in tracked_objects:
            # Generate potential futures
            futures = self.predictor.predict(obj.history, horizon_s)
            trajectories.append(futures)
        return trajectories

    def classify_agent_intent(self, agent: 'TrackedObject') -> 'AgentIntent':
        """歩行者の横断意図や車両の車線変更意図を分類"""
        # LSTM or Transformer based classification
        intent_prob = self.intent_classifier.infer(agent.history)
        return AgentIntent(intent_prob)

    def detect_lane_markings(self, frame: np.ndarray) -> 'LaneMarkingList':
        """車線境界線の多項式近似"""
        mask = self.segmenter.get_lane_mask(frame)
        return self.lane_fitter.fit(mask)

    def estimate_free_space(self, perception_data: 'PerceptionData') -> 'FreeSpaceGrid':
        """占有格子地図を用いた空きスペース推定"""
        return self.occupancy_grid_mapper.update(perception_data)
```

### 3.2 V2X Object Fusion
自律センサーの認識結果とV2X (CPM/CAM) 情報を統合するクラス。

```python
class V2XObjectFusion:
    def __init__(self):
        self.fusion_kf = KalmanFilter()

    def fuse_v2x_detections(self, local_objects: List['TrackedObject'], v2x_messages: List['CAMMessage']) -> List['TrackedObject']:
        """ローカル認識とV2X情報の統合"""
        fused_list = local_objects.copy()

        for msg in v2x_messages:
            # 座標変換 (WGS84 -> Local Cartesian)
            v2x_obj = self.convert_cam_to_object(msg)

            # マッチング (IoU or Distance)
            match = self.find_match(local_objects, v2x_obj)

            if match:
                # 既存オブジェクトの補正 (位置精度向上)
                match.update_with_v2x(v2x_obj)
            else:
                # 新規オブジェクトとして追加 (見通し外の車両など)
                # NLOS (Non-Line-of-Sight) Object
                v2x_obj.is_remote = True
                fused_list.append(v2x_obj)

        return fused_list

    def resolve_identity_conflicts(self, candidates: List['TrackedObject']) -> 'TrackedObject':
        """ID競合の解決ロジック"""
        # 信頼度の高い方を優先、または平均化
        return max(candidates, key=lambda x: x.confidence)

    def extend_perception_range(self, v2x_objects: List['CAMMessage']) -> List['ObjectList']:
        """センサー範囲外のオブジェクト情報を構築"""
        # 半径300m以上の遠方車両情報の管理
        return [self.convert_cam_to_object(msg) for msg in v2x_objects]
```

## 4. モデル最適化と推論

### 4.1 TensorRT最適化
NVIDIA GPUでの高速推論のため、学習済みモデル (PyTorch/ONNX) をTensorRT Engineへ変換する。

*   **量子化**: FP32 -> INT8 (キャリブレーションデータセットを使用)。
*   **レイヤー融合**: Conv + BN + ReLUなどを単一カーネルに融合。

### 4.2 レイテンシ要件
*   **Detection**: < 30ms
*   **Tracking**: < 5ms
*   **Fusion**: < 2ms
*   **Prediction**: < 10ms

合計 50ms 以内にPerceptionループを完了させる必要がある。
