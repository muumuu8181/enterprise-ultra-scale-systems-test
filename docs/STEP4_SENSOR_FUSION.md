# STEP 4: センサーフュージョン設計 (STEP4_SENSOR_FUSION.md)

## 1. 概要
センサーフュージョンは、LiDAR (距離計測)、Camera (視覚情報)、Radar (速度・距離計測)、GNSS/IMU (位置・姿勢) から得られる異種データを統合し、車両周辺の正確な環境モデル (World Model) を構築する。本システムでは、Unscented Kalman Filter (UKF) および Deep Learning Fusion (BEV) を組み合わせたハイブリッドアプローチを採用する。

## 2. センサー構成と前処理

### 2.1 LiDAR (Velodyne VLP-32C / Ouster OS1-128)
*   **点群処理**: 生点群から地面除去、ノイズフィルタリングを行う。
*   **クラスタリング**: ユークリッド距離に基づくクラスタリング (Euclidean Clustering) で物体候補を抽出。
*   **バウンディングボックス推定**: PCA (主成分分析) または L-Shape Fitting で3Dボックスを生成。

### 2.2 Camera (8眼 Surround-View)
*   **入力**: 4K/60fps, HDR, Global Shutter。
*   **前処理**: 歪み補正 (Undistortion)、露光調整。
*   **物体検出**: YOLOv9等による2Dバウンディングボックス検出。

### 2.3 Radar (Continental ARS548, 77GHz FMCW)
*   **特徴**: 全天候型、ドップラー効果による直接的な速度計測。
*   **処理**: RCS (Radar Cross Section) フィルタリング、静止画除去 (Clutter Removal)。

## 3. フュージョンアルゴリズム

### 3.1 処理パイプライン
1.  **Time Synchronization**: 各センサーデータのタイムスタンプ同期 (PTP: Precision Time Protocol)。
2.  **Coordinate Transformation**: 各センサー座標系から車両中心座標系 (Base Link) への変換。
3.  **Data Association**: 既知のトラック (追跡対象) と新規観測データの紐付け (GNN: Global Nearest Neighbor / Hungarian Algorithm)。
4.  **State Estimation**: UKFによる位置・速度・加速度の更新。
5.  **Track Management**: 新規トラック生成、ロストトラック削除、ID管理。

## 4. クラス設計 (C++ Implementation)

### 4.1 SensorFusionEngine
センサーフュージョンのメインループを管理するクラス。

```cpp
#include <vector>
#include <eigen3/Eigen/Dense>
#include "sensor_types.hpp"

class SensorFusionEngine {
public:
    SensorFusionEngine();

    // 各センサーからのデータ入力
    void processLiDARFrame(const PointCloud2& cloud, Timestamp ts) {
        PointCloud2 filtered = preprocessor_.voxelDownsample(cloud, 0.1f);
        ClusterList clusters = preprocessor_.euclideanClustering(filtered, 0.5f, 10);
        BoundingBox3DList boxes = preprocessor_.fitBoundingBoxes(clusters);

        Measurement measurement;
        measurement.type = SensorType::LIDAR;
        measurement.objects = boxes;
        measurement.timestamp = ts;

        updateTracks(measurement);
    }

    void processCameraFrame(const Image& img, CameraID cam_id, Timestamp ts) {
        // AI検出器による推論 (非同期処理推奨)
        DetectionList detections = detector_.detect(img);

        Measurement measurement;
        measurement.type = SensorType::CAMERA;
        measurement.objects = projectTo3D(detections, cam_id); // 2D->3D Projection
        measurement.timestamp = ts;

        updateTracks(measurement);
    }

    void processRadarFrame(const RadarScan& scan, Timestamp ts) {
        Measurement measurement;
        measurement.type = SensorType::RADAR;
        measurement.objects = converter_.fromRadarScan(scan); // Range-Rate info included
        measurement.timestamp = ts;

        updateTracks(measurement);
    }

    void processIMUData(const IMUData& imu, Timestamp ts) {
        // 予測ステップ (Prediction Step) の更新に使用
        ukf_.predict(imu.dt);
    }

    void processGNSSFix(const GNSSFix& fix, Timestamp ts) {
        // 絶対位置の補正 (Localization)
        pose_estimator_.updateGNSS(fix);
    }

    // 統合されたオブジェクトリストの取得
    ObjectList getFusedObjectList() const {
        return track_manager_.getConfirmedTracks();
    }

    // 自車運動推定 (Ego Motion)
    EgoMotion getEgoMotionEstimate() const {
        return pose_estimator_.getCurrentState();
    }

    // 占有格子地図 (Occupancy Grid Map) の生成
    OccupancyGrid getOccupancyGrid(float resolution_m) {
        return occupancy_mapper_.generateGrid(resolution_m);
    }

    // センサー間キャリブレーション
    void calibrateSensorExtrinsics(CalibrationTarget& target) {
        // Target detection logic
        calibration_manager_.startCalibration(target);
    }

private:
    PointCloudProcessor preprocessor_;
    ObjectDetector detector_;
    UnscentedKalmanFilter ukf_;
    TrackManager track_manager_;
    PoseEstimator pose_estimator_;
    OccupancyMapper occupancy_mapper_;
    CalibrationManager calibration_manager_;

    void updateTracks(const Measurement& meas) {
        // 1. Gating
        // 2. Data Association (Mahalanobis Distance)
        // 3. Update Step (UKF)
    }
};
```

### 4.2 PointCloudProcessor
点群処理特化クラス。PCL (Point Cloud Library) または CUDA実装を利用。

```cpp
class PointCloudProcessor {
public:
    // 地面除去 (RANSAC or Ray Ground Filter)
    PointCloud2 removeGround(const PointCloud2& cloud) {
        // Plane segmentation
        return cloud_without_ground;
    }

    // ダウンサンプリング (Voxel Grid Filter)
    PointCloud2 voxelDownsample(const PointCloud2& cloud, float voxel_size) {
        // Reduce point density for performance
        return downsampled_cloud;
    }

    // クラスタリング (Euclidean Cluster Extraction)
    ClusterList euclideanClustering(const PointCloud2& cloud, float eps, int min_pts) {
        // KdTree search
        return clusters;
    }

    // バウンディングボックス適合
    BoundingBox3DList fitBoundingBoxes(const ClusterList& clusters) {
        BoundingBox3DList boxes;
        for (const auto& cluster : clusters) {
            // PCA for orientation estimation
            boxes.push_back(computeOrientedBox(cluster));
        }
        return boxes;
    }

    // 法線推定
    PointCloud2 normalEstimation(const PointCloud2& cloud, int knn) {
        // For surface features
        return cloud_with_normals;
    }
};
```

## 5. 状態ベクトルとカルマンフィルタ

追跡対象の状態ベクトル $x$ は以下のように定義する。

$$
x = [p_x, p_y, p_z, v, \psi, \dot{\psi}, a]
$$

ここで:
*   $p_x, p_y, p_z$: 位置
*   $v$: 速度
*   $\psi$: ヨー角 (Heading)
*   $\dot{\psi}$: ヨーレート
*   $a$: 加速度

CTR (Constant Turn Rate and Velocity) モデルまたは CTRA (Constant Turn Rate and Acceleration) モデルを遷移モデルとして使用する。

### 5.1 共分散行列 $P$
初期状態の不確実性を定義し、観測ごとに更新することで、推定値の信頼度を評価する。

$$
P_{k|k} = (I - K_k H_k) P_{k|k-1}
$$
