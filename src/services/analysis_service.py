from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.audit_models import SmartContract, AuditReport, Vulnerability, AuditStatus, RiskLevel, VulnType, Severity

async def static_analysis(source_code: str) -> list[dict]:
    # Mock static analysis
    vulns = []
    if "call.value" in source_code:
        vulns.append({
            "vuln_type": VulnType.REENTRANCY,
            "severity": Severity.CRITICAL,
            "line_number": 10,
            "description": "Potential reentrancy vulnerability detected via call.value.",
            "recommendation": "Use Checks-Effects-Interactions pattern and avoid low-level calls."
        })
    return vulns

async def symbolic_execution(source_code: str) -> list[dict]:
    # Mock symbolic execution
    vulns = []
    if "unchecked" in source_code:
        vulns.append({
            "vuln_type": VulnType.OVERFLOW,
            "severity": Severity.HIGH,
            "line_number": 20,
            "description": "Unchecked arithmetic operation found.",
            "recommendation": "Ensure unchecked block is safe or remove it."
        })
    return vulns

async def generate_audit_report(contract_id: int, db: AsyncSession) -> AuditReport:
    # Fetch contract
    stmt = select(SmartContract).where(SmartContract.id == contract_id)
    result = await db.execute(stmt)
    contract = result.scalar_one_or_none()

    if not contract:
        raise ValueError(f"Contract with id {contract_id} not found")

    # Create Report (Pending -> Scanning)
    report = AuditReport(contract_id=contract_id, status=AuditStatus.SCANNING)
    db.add(report)
    await db.commit()
    await db.refresh(report)

    try:
        # Run Analysis
        vulns_data = []
        vulns_data.extend(await static_analysis(contract.source_code))
        vulns_data.extend(await symbolic_execution(contract.source_code))

        # Save Vulnerabilities
        risk_score = 0
        for v_data in vulns_data:
            vuln = Vulnerability(audit_id=report.id, **v_data)
            db.add(vuln)

            # Simple risk calculation
            if v_data["severity"] == Severity.CRITICAL:
                risk_score += 10
            elif v_data["severity"] == Severity.HIGH:
                risk_score += 5
            elif v_data["severity"] == Severity.MEDIUM:
                risk_score += 2
            else:
                risk_score += 1

        # Update Report
        report.status = AuditStatus.COMPLETED
        report.vulnerabilities_found = len(vulns_data)

        if risk_score >= 10:
            report.risk_level = RiskLevel.CRITICAL
        elif risk_score >= 5:
            report.risk_level = RiskLevel.HIGH
        elif risk_score >= 2:
            report.risk_level = RiskLevel.MEDIUM
        else:
            report.risk_level = RiskLevel.LOW

        await db.commit()
        await db.refresh(report)
        return report

    except Exception as e:
        report.status = AuditStatus.FAILED
        await db.commit()
        raise e
