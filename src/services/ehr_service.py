from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from src.models.ehr_models import PatientRecord, LabOrder, ReferralLetter
from src.schemas.ehr_schemas import PatientSummary, Interaction

class EHRService:
    async def compile_patient_summary(self, patient_id: str, db: AsyncSession) -> Optional[PatientSummary]:
        stmt = select(PatientRecord).where(PatientRecord.patient_id == patient_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return PatientSummary.model_validate(record)

    async def check_drug_interactions(self, medications: list[str]) -> List[Interaction]:
        interactions = []
        # Mock logic
        meds_lower = [m.lower() for m in medications]
        if "aspirin" in meds_lower and "warfarin" in meds_lower:
            interactions.append(Interaction(
                severity="high",
                description="Increased risk of bleeding."
            ))
        return interactions

    async def generate_discharge_summary(self, consultation_id: str, db: AsyncSession) -> str:
        # In a real system, this would fetch consultation notes, diagnosis, etc.
        # Here we will just return a template.
        return f"Discharge Summary for Consultation {consultation_id}: Patient is stable and discharged."

ehr_service = EHRService()
