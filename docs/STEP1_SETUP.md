# STEP 1: 開発環境セットアップ (STEP1_SETUP.md)

## 1. 概要
本プロジェクトでは、車載システム (OBU) 向けにAUTOSAR Adaptive Platformを採用し、クラウド・エッジ側にはKubernetesベースのマイクロサービス環境を構築する。開発はUbuntu 22.04 LTSをベースとし、クロスコンパイル環境 (ARM64) を整備する。

## 2. 開発ワークステーション要件

### 2.1 推奨スペック
*   **OS**: Ubuntu 22.04 LTS (Jammy Jellyfish)
*   **CPU**: AMD Ryzen 9 7950X / Intel Core i9-13900K (16 cores+)
*   **RAM**: 64GB DDR5 (128GB 推奨)
*   **GPU**: NVIDIA RTX 4090 (24GB VRAM) - シミュレーション/AI学習用
*   **Storage**: 2TB NVMe SSD (Gen4/Gen5)

### 2.2 必須ツールチェーン
```bash
# 基本ツール
sudo apt update && sudo apt install -y build-essential cmake ninja-build git git-lfs python3-pip

# AUTOSAR Adaptive (ara::com, ara::exec) 開発用
# ベンダー提供のSDK (Vector Microsar / Elektrobit corbos) を /opt/autosar に配置
export AUTOSAR_ROOT=/opt/autosar/adaptive_R22-11
export PATH=$AUTOSAR_ROOT/bin:$PATH

# NVIDIA DRIVE OS (Cross-compilation for Orin)
# NVIDIA Developer Programへの登録が必要
# SDK Managerを使用してインストール: Drive OS 6.0.8 Linux SDK
export DRIVE_OS_ROOT=/usr/local/driveworks
```

## 3. コンテナ化開発環境 (Docker/Kubernetes)

### 3.1 Docker環境
開発環境の差異を吸収するため、DevContainerを利用する。

```dockerfile
# Dockerfile.dev
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Install ROS 2 Humble
ENV ROS_DISTRO=humble
RUN apt update && apt install -y curl gnupg2 lsb-release \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null \
    && apt update && apt install -y ros-humble-desktop

# Install AUTOSAR build tools
COPY --from=vector/autosar-sdk:r22-11 /opt/autosar /opt/autosar

# Setup functional safety tools (LDRA / Polyspace)
# COPY --from=ldra/testbed:latest /opt/ldra /opt/ldra
```

### 3.2 Kubernetes (k3s/MicroK8s)
ローカルでのマイクロサービス動作確認用。

```bash
# K3s installation
curl -sfL https://get.k3s.io | sh -
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Deploy Kafka & Redis
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install v2x-kafka bitnami/kafka --set persistence.size=10Gi
helm install v2x-redis bitnami/redis-cluster
```

## 4. AUTOSAR Adaptive Platform 設定

### 4.1 マニフェスト定義 (arxml)
サービスインターフェース (`RequiredPort`, `ProvidedPort`) を定義する。

```xml
<!-- V2X Communication Service Interface -->
<SERVICE-INTERFACE>
  <SHORT-NAME>V2XService</SHORT-NAME>
  <IS-SERVICE>true</IS-SERVICE>
  <METHODS>
    <CLIENT-SERVER-OPERATION>
      <SHORT-NAME>SendCAM</SHORT-NAME>
      <ARGUMENTS>
        <ARGUMENT-DATA-PROTOTYPE>
          <SHORT-NAME>camData</SHORT-NAME>
          <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">/Types/CAM</TYPE-TREF>
          <DIRECTION>IN</DIRECTION>
        </ARGUMENT-DATA-PROTOTYPE>
      </ARGUMENTS>
    </CLIENT-SERVER-OPERATION>
  </METHODS>
</SERVICE-INTERFACE>
```

### 4.2 Execution Management (ara::exec)
アプリケーションの起動順序、依存関係、リソース制限を管理する。

*   **Machine State**: `Startup`, `Driving`, `Parking`, `Shutdown`
*   **Function Group**: `SafetyCritical`, `Infotainment`, `V2XStack`

## 5. CI/CD パイプライン

### 5.1 GitLab CI
コミットごとに静的解析、ビルド、単体テストを実行。

```yaml
stages:
  - lint
  - build
  - test
  - safety_check

misra_cpp_check:
  stage: lint
  image: vector/cast:latest
  script:
    - cast_analyze --rules=MISRA_CPP_2023 src/

build_orin:
  stage: build
  image: nvidia/driveos:6.0.8
  script:
    - cmake -B build_orin -DCMAKE_TOOLCHAIN_FILE=Toolchain-aarch64.cmake
    - cmake --build build_orin -j16

safety_test:
  stage: safety_check
  script:
    - ldra_run_testbed --standard=ISO26262_ASIL_D
```

### 5.2 機能安全検証 (ISO 26262)
*   **LDRA Testbed**: コードカバレッジ (MC/DC)、制御フロー解析。
*   **Polyspace**: ランタイムエラー (ゼロ除算、オーバーフロー) の数学的証明。
*   **VectorCAST**: 単体テスト・結合テストの自動化。

### 5.3 Jenkins & Artifactory
複雑な統合テストおよびリリース管理にはJenkinsを使用し、アーティファクト管理にはJFrog Artifactoryを使用する。

*   **Jenkins**: Nightly Build、HILテストの自動実行 (実機接続が必要なため)。
*   **JFrog Artifactory**:
    *   Docker Registry: 開発用・本番用コンテナイメージの保管。
    *   Generic Repo: AUTOSAR ARXML、コンパイル済みバイナリ、ファームウェアのバージョン管理。
    *   Conan: C++パッケージマネージャのリモートリポジトリ。

## 6. シミュレーション環境 (CARLA + ROS 2)

```bash
# CARLA Simulator 0.9.15
docker run -p 2000-2002:2000-2002 --gpus all carlasim/carla:0.9.15 ./CarlaUE4.sh -opengl

# ROS 2 Bridge
source /opt/ros/humble/setup.bash
ros2 launch carla_ros_bridge carla_ros_bridge.launch.py
```
