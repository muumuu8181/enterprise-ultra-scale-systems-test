from typing import Dict, Any

FHIRBundle = Dict[str, Any]

async def export_to_fhir_r4(user_id: int) -> FHIRBundle:
    """
    Exports user data to FHIR R4 Bundle format.
    Mock implementation returning a basic Patient resource.
    """
    # In a real implementation, we would query the database for user details,
    # medications, conditions, etc.
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": str(user_id),
                    "active": True
                }
            }
        ]
    }

async def calculate_medication_adherence(user_id: int) -> float:
    """
    Calculates medication adherence score for a user.
    Mock implementation.
    """
    # Logic: (Taken Doses / Total Prescribed Doses) * 100
    # For now, return a mock value.
    return 85.5

def check_vital_anomaly(vital_type: str, value: float) -> bool:
    """
    Checks for anomalies in vital signs.
    Returns True if an anomaly is detected.
    """
    if vital_type == "spo2":
        if value < 90:
            return True
    elif vital_type == "glucose":
        if value < 70 or value > 140: # Standard non-diabetic range 70-140 approx
            return True
    return False
