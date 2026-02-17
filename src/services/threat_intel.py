from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.security_models import ThreatIndicator, SecurityEvent, Vulnerability, Campaign, SeverityLevel, VulnStatus

async def enrich_ioc(ioc_value: str, ioc_type: str) -> dict:
    # Mock enrichment
    return {
        "ioc_value": ioc_value,
        "ioc_type": ioc_type,
        "threat_score": 85,
        "geo_location": "Unknown",
        "asn": "AS12345"
    }

async def correlate_events(events: list[SecurityEvent]) -> list[Campaign]:
    # Simple correlation logic: group by source_ip
    campaigns = []
    grouped_events = {}

    for event in events:
        if event.source_ip not in grouped_events:
            grouped_events[event.source_ip] = []
        grouped_events[event.source_ip].append(event)

    for source_ip, evts in grouped_events.items():
        if len(evts) > 1: # Only create campaign if multiple events
            campaign = Campaign(
                name=f"Campaign from {source_ip}",
                # associated_events=evts # If we had relationship
            )
            campaigns.append(campaign)

    return campaigns

async def calculate_risk_score(asset_id: str, db: AsyncSession) -> float:
    # Calculate risk based on open vulnerabilities
    stmt = select(Vulnerability).where(
        Vulnerability.affected_system == asset_id,
        Vulnerability.status == VulnStatus.OPEN
    )
    result = await db.execute(stmt)
    vulns = result.scalars().all()

    score = 0.0
    for vuln in vulns:
        score += vuln.cvss_score

    return score
