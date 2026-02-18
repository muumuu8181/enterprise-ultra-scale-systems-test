import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.openbanking_models import Consent, ConsentAuditLog, ConsentStatus

class OpenBankingService:
    async def create_consent(
        self,
        db: AsyncSession,
        client_id: str,
        customer_id: str,
        scopes: Dict[str, Any],
        expires_at: Optional[datetime] = None,
        ip_address: Optional[str] = "0.0.0.0"
    ) -> Consent:
        consent = Consent(
            client_id=client_id,
            customer_id=customer_id,
            scopes=scopes,
            status=ConsentStatus.PENDING,
            expires_at=expires_at
        )
        db.add(consent)
        await db.flush()  # To get ID

        log = ConsentAuditLog(
            consent_id=consent.id,
            action="CREATED",
            ip_address=ip_address
        )
        db.add(log)

        await db.commit()
        await db.refresh(consent)
        return consent

    async def validate_consent(
        self,
        db: AsyncSession,
        consent_id: uuid.UUID
    ) -> Optional[Consent]:
        stmt = select(Consent).where(Consent.id == consent_id)
        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        if not consent:
            return None

        # Check expiration
        if consent.expires_at and consent.expires_at < datetime.utcnow():
             if consent.status != ConsentStatus.EXPIRED:
                 consent.status = ConsentStatus.EXPIRED
                 db.add(consent) # Ensure attached to session
                 await db.commit()
             return None

        if consent.status == ConsentStatus.REVOKED:
            return None

        return consent

    async def revoke_consent(
        self,
        db: AsyncSession,
        consent_id: uuid.UUID,
        ip_address: Optional[str] = "0.0.0.0"
    ) -> bool:
        stmt = select(Consent).where(Consent.id == consent_id)
        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        if not consent:
            return False

        if consent.status == ConsentStatus.REVOKED:
            return True

        consent.status = ConsentStatus.REVOKED

        log = ConsentAuditLog(
            consent_id=consent.id,
            action="REVOKED",
            ip_address=ip_address
        )
        db.add(log)

        await db.commit()
        return True

open_banking_service = OpenBankingService()
