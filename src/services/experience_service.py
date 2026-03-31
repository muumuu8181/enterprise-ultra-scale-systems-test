from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.models.employee_models import Employee, SurveyResponse, WellbeingMetric, SurveyType, MetricType
import datetime
import json

class ExperienceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_employee_experience_score(self, employee_id: int):
        # Mock calculation: average of engagement score and recent survey sentiment
        result = await self.db.execute(select(Employee).filter(Employee.id == employee_id))
        employee = result.scalar_one_or_none()
        if not employee:
            return None

        # Get recent surveys
        result = await self.db.execute(select(SurveyResponse).filter(SurveyResponse.employee_id == employee_id))
        surveys = result.scalars().all()

        avg_sentiment = 0.0
        if surveys:
            # Assuming sentiment_score is 0-10 or similar
            avg_sentiment = sum([s.sentiment_score for s in surveys if s.sentiment_score is not None]) / len(surveys)

        # Combining engagement score and sentiment. Assuming similar scales.
        return {
            "employee_id": employee_id,
            "experience_score": (employee.engagement_score + avg_sentiment) / 2 if employee.engagement_score is not None else avg_sentiment
        }

    async def get_employee_journey(self, employee_id: int):
        # Mock journey: hire date + survey submissions
        result = await self.db.execute(select(Employee).filter(Employee.id == employee_id))
        employee = result.scalar_one_or_none()
        if not employee:
            return []

        timeline = [{"date": employee.hire_date, "event": "Hired", "type": "milestone"}]

        result = await self.db.execute(select(SurveyResponse).filter(SurveyResponse.employee_id == employee_id))
        surveys = result.scalars().all()
        for s in surveys:
            timeline.append({
                "date": s.submitted_at,
                "event": f"Submitted {s.survey_type.value} survey",
                "sentiment": s.sentiment_score,
                "type": "survey"
            })

        # Sort by date. Handle None dates if any (shouldn't be for hire_date/submitted_at based on model)
        return sorted(timeline, key=lambda x: x['date'] if x['date'] else datetime.datetime.min)

    async def submit_survey(self, survey_data: dict):
        # Expecting survey_data to match SurveyResponse model fields
        new_survey = SurveyResponse(**survey_data)
        self.db.add(new_survey)
        await self.db.commit()
        await self.db.refresh(new_survey)
        return new_survey

    async def get_survey_results(self, survey_type: str = None, period: str = None):
        # Simple aggregation
        query = select(SurveyResponse)
        if survey_type:
            query = query.filter(SurveyResponse.survey_type == survey_type)
        # Period filtering is mock for now

        result = await self.db.execute(query)
        surveys = result.scalars().all()
        return surveys

    async def get_team_wellbeing_summary(self, department: str):
        # Get employees in department
        result = await self.db.execute(select(Employee.id).filter(Employee.department == department))
        employee_ids = result.scalars().all()

        if not employee_ids:
            return {}

        # Get metrics
        result = await self.db.execute(select(WellbeingMetric).filter(WellbeingMetric.employee_id.in_(employee_ids)))
        metrics = result.scalars().all()

        summary = {}
        for m in metrics:
            # m.metric_type is an Enum
            m_type = m.metric_type.value if hasattr(m.metric_type, 'value') else m.metric_type
            if m_type not in summary:
                summary[m_type] = []
            if m.score is not None:
                summary[m_type].append(m.score)

        return {k: sum(v)/len(v) for k, v in summary.items() if v}

    async def get_wellbeing_trends(self):
        # Mock trend analysis
        return {"trend": "improving", "details": "Satisfaction up 5%"}

    async def get_engagement_drivers(self):
        return ["Career Growth", "Manager Support", "Work-Life Balance"]

    async def get_attrition_risk(self):
        # Identify employees with low engagement
        result = await self.db.execute(select(Employee).filter(Employee.engagement_score < 3.0)) # Assuming 1-5 scale
        at_risk = result.scalars().all()
        return [{"employee_id": e.id, "risk_level": "High", "name": e.name} for e in at_risk]

    async def submit_kudos(self, kudos_data: dict):
        # Mock storage for kudos
        return {"status": "success", "kudos": kudos_data}
