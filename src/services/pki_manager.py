import datetime
import uuid
from typing import Optional, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.v2x_models import PKICertificate

class PKIManager:
    """
    V2X PKI管理クラス
    証明書の発行、ローテーション、失効、検証を行う。
    """

    def __init__(self):
        # 簡易的なRoot CA秘密鍵の生成 (本来はHSM等で管理)
        self.ca_private_key = ec.generate_private_key(ec.SECP256R1())
        self.ca_public_key = self.ca_private_key.public_key()

        # 簡易的なRoot CA証明書の生成
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"JP"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Tokyo"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"V2X Root CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"v2x-root-ca.example.com"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)

        self.ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.ca_public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now
        ).not_valid_after(
            now + datetime.timedelta(days=3650)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).sign(self.ca_private_key, hashes.SHA256())

    async def issue_certificate(
        self,
        session: AsyncSession,
        vehicle_id: str,
        cert_type: str = "enrollment"
    ) -> PKICertificate:
        """
        証明書を発行する (x509, EC P-256)

        Args:
            session (AsyncSession): DBセッション
            vehicle_id (str): 車両ID
            cert_type (str): 証明書タイプ

        Returns:
            PKICertificate: 発行された証明書モデル
        """
        # 鍵ペアの生成 (車両用) - 本来は車両側で生成してCSRを送るが、ここではシミュレーション
        vehicle_private_key = ec.generate_private_key(ec.SECP256R1())
        vehicle_public_key = vehicle_private_key.public_key()

        # サブジェクト設定
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"JP"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"V2X Vehicle"),
            x509.NameAttribute(NameOID.COMMON_NAME, vehicle_id),
        ])

        # 有効期限
        valid_from = datetime.datetime.now(datetime.timezone.utc)
        valid_until = valid_from + datetime.timedelta(days=365 if cert_type == "enrollment" else 1) # 短期証明書対応

        # 証明書作成
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_cert.subject
        ).public_key(
            vehicle_public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            valid_from
        ).not_valid_after(
            valid_until
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True,
        ).sign(self.ca_private_key, hashes.SHA256())

        # PEM形式への変換 (保存用)
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        serial_str = str(cert.serial_number)

        # DBへ保存
        pki_cert = PKICertificate(
            vehicle_id=vehicle_id,
            cert_type=cert_type,
            serial_number=serial_str,
            valid_from=valid_from,
            valid_until=valid_until,
            revoked=False
        )
        session.add(pki_cert)
        await session.commit()
        await session.refresh(pki_cert)

        return pki_cert

    async def rotate_pseudonym(self, session: AsyncSession, vehicle_id: str) -> PKICertificate:
        """
        擬似名証明書(Pseudonym Certificate)をローテーションする。
        プライバシー保護のため、定期的に変更されるID用の証明書を発行。

        Args:
            session (AsyncSession): DBセッション
            vehicle_id (str): 車両ID

        Returns:
            PKICertificate: 新しい証明書
        """
        # 新しい擬似IDを生成するか、vehicle_idに紐づく新しい短期証明書を発行
        # ここではvehicle_idは固定で、cert_type="pseudonym"として発行
        return await self.issue_certificate(session, vehicle_id, cert_type="pseudonym")

    async def revoke_certificate(self, session: AsyncSession, serial_number: str) -> bool:
        """
        証明書を失効させ、CRLを更新する(CRL更新は簡易的)。

        Args:
            session (AsyncSession): DBセッション
            serial_number (str): シリアル番号

        Returns:
            bool: 成功したかどうか
        """
        stmt = select(PKICertificate).where(PKICertificate.serial_number == serial_number)
        result = await session.execute(stmt)
        cert = result.scalar_one_or_none()

        if cert:
            cert.revoked = True
            await session.commit()
            return True
        return False

    def verify_certificate(self, cert_pem: bytes, signature: bytes, data: bytes) -> bool:
        """
        証明書を使用して署名を検証する。

        Args:
            cert_pem (bytes): PEM形式の証明書データ
            signature (bytes): 署名データ
            data (bytes): 署名対象データ

        Returns:
            bool: 検証成功ならTrue
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_pem)
            public_key = cert.public_key()

            # EC P-256 (SECP256R1) の署名検証
            public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as e:
            # print(f"Verification failed: {e}")
            return False
