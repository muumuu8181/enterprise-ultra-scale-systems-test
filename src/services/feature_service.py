from typing import List, Dict, Any
from pydantic import BaseModel
import random
import asyncio
import datetime

class DriftReport(BaseModel):
    feature_id: int
    drift_detected: bool
    drift_score: float
    report_generated_at: str

async def compute_feature(feature_id: int, entity_ids: List[str]) -> Dict[str, Any]:
    """
    Computes features for a list of entity IDs.
    In a real system, this would trigger a spark job or query a data warehouse.
    """
    # Simulate processing delay
    await asyncio.sleep(0.1)

    results = {}
    for entity_id in entity_ids:
        # Generate a random value based on entity_id hash
        value = hash(entity_id + str(feature_id)) % 100
        results[entity_id] = value

    return results

async def serve_online(entity_id: str, feature_names: List[str]) -> Dict[str, Any]:
    """
    Serves features from an online store (e.g., Redis).
    """
    # Simulate low latency lookup
    await asyncio.sleep(0.01)

    results = {}
    for feature_name in feature_names:
        # Simulate value
        results[feature_name] = random.random()

    return {entity_id: results}

async def detect_feature_drift(feature_id: int) -> DriftReport:
    """
    Detects data drift for a given feature.
    """
    await asyncio.sleep(0.5)

    drift_score = random.random()
    detected = drift_score > 0.8

    return DriftReport(
        feature_id=feature_id,
        drift_detected=detected,
        drift_score=drift_score,
        report_generated_at=datetime.datetime.now().isoformat()
    )
