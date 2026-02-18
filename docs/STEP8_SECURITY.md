# STEP 8: セキュリティ・PKI基盤 (STEP8_SECURITY.md)

## 1. 概要
V2X通信の信頼性を担保するため、IEEE 1609.2およびETSI TS 103 097に準拠した公開鍵基盤 (PKI) であるSCMS (Security Credential Management System) を構築する。プライバシー保護のための仮名証明書 (Pseudonym Certificate) の利用、車両の不正検知 (Misbehavior Detection)、および将来の量子コンピュータ脅威に備えた耐量子暗号 (Post-Quantum Cryptography) を実装する。

## 2. SCMSアーキテクチャ

SCMSは、V2Xシステムの信頼の起点 (Root of Trust) となる。

### 2.1 コンポーネント構成
*   **Root CA (RCA)**: 最上位認証局。ポリシー生成者。
*   **Enrollment CA (ECA)**: 車両の登録証明書 (Enrollment Cert) を発行。
*   **Pseudonym CA (PCA)**: 短期間有効な仮名証明書 (Pseudonym Cert) を発行。
*   **Registration Authority (RA)**: 車両の正当性確認 (Shuffle Request)。
*   **Linkage Authority (LA)**: プライバシー保護のためのリンク値生成 (LA1, LA2)。
*   **Misbehavior Authority (MA)**: 不正車両の特定とCRL (Certificate Revocation List) の発行。

### 2.2 証明書タイプ
1.  **Enrollment Certificate**: 長期間有効 (数年)。車両固有のIDと公開鍵を含む。
2.  **Pseudonym Certificate**: 短期間有効 (1週間程度、使用期間は5分)。車両追跡を防ぐため、多数発行しローテーションして使用する。
3.  **Application Certificate**: インフラ (RSU) 用。特定のアプリケーション (SPAT/MAP) の署名に使用。

## 3. 車載セキュリティ実装 (HSM/TPM)

秘密鍵の漏洩を防ぐため、耐タンパー性を持つHSM (Hardware Security Module) を利用する。

### 3.1 鍵管理
*   **TPM 2.0 / SHE (Secure Hardware Extension)**: 秘密鍵の生成、保存、署名演算をハードウェア内部で完結させる。
*   **Secure Boot**: ファームウェア改ざん検知。Root of Trustからの署名チェーン検証。

### 3.2 署名・検証フロー
1.  **Message Generation**: アプリケーションがメッセージ (CAM) を作成。
2.  **Signing**: HSMへメッセージハッシュを送信し、ECDSA (NIST P-256) 署名を取得。
3.  **Transmission**: 署名付きメッセージを放送。
4.  **Verification**: 受信側で署名を検証 (Butterfly Key Expansion技術を利用)。

## 4. 量子耐性暗号 (PQC)

将来的な「Harvest Now, Decrypt Later」攻撃への対策として、NIST選定の次世代暗号アルゴリズムを導入する。

### 4.1 アルゴリズム選定
*   **鍵交換**: CRYSTALS-Kyber (Lattice-based)。
*   **デジタル署名**: CRYSTALS-Dilithium (Lattice-based)。

### 4.2 ハイブリッド方式
現行の楕円曲線暗号 (ECC) とPQCを併用するハイブリッド証明書を採用し、互換性と安全性を両立する。

## 5. 不正検知システム (Misbehavior Detection)

悪意ある車両や故障した車両を排除する仕組み。

### 5.1 ローカル検知 (On-Board)
*   **Plausibility Check**: 受信メッセージの物理的整合性チェック。
    *   例: 速度500km/hの車両、位置が急激に飛ぶ車両。
*   **Consistency Check**: 複数センサーとの整合性チェック。
    *   例: レーダーで検知できないのにV2Xで位置を主張する車両 (Ghost Vehicle)。

### 5.2 グローバル検知 (Cloud/MA)
*   **Report Aggregation**: 複数の車両から特定の車両に対する異常報告を集約。
*   **Revocation**: しきい値を超えた場合、その車両の証明書をCRLに追加し、全車両へ配信。

## 6. セキュア通信プロトコル

### 6.1 V2N (Vehicle-to-Network)
*   **TLS 1.3**: 相互認証 (mTLS) を必須とし、PFS (Perfect Forward Secrecy) を確保。
*   **OAuth 2.0 / OIDC**: サービス認可フロー。

### 6.2 ソフトウェアアップデート (OTA)
*   **Uptane**: 自動車向けOTAセキュリティフレームワーク。
*   **Director / Image Repository**: メタデータとイメージの分離署名。
*   **Secondary ECU Update**: Gateway ECU経由での配下ECU更新時の正当性検証。
