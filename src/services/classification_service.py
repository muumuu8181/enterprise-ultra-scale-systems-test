import asyncio
import random
from typing import Any, Union
from src.models.moderation_models import ClassificationResult, ImageModerationResult

async def classify_text(content: str, language: str) -> ClassificationResult:
    """
    Simulates text classification.
    """
    # Simulate processing delay
    await asyncio.sleep(0.1)

    # Dummy logic
    flagged = "bad" in content.lower()
    confidence = random.uniform(0.7, 0.99) if flagged else random.uniform(0.8, 0.99)
    category = "harassment" if flagged else None

    return ClassificationResult(
        flagged=flagged,
        category=category,
        confidence=confidence
    )

async def classify_image(image_uri: str) -> ImageModerationResult:
    """
    Simulates image classification.
    """
    await asyncio.sleep(0.2)

    # Dummy logic
    flagged = "nsfw" in image_uri.lower()
    confidence = random.uniform(0.8, 0.99)
    labels = ["safe"]
    if flagged:
        labels = ["nsfw", "adult"]

    return ImageModerationResult(
        flagged=flagged,
        labels=labels,
        confidence=confidence
    )

async def detect_spam(content: Union[str, Any]) -> float:
    """
    Detects spam probability. Returns a float between 0.0 and 1.0.
    """
    await asyncio.sleep(0.05)
    # Dummy logic
    if isinstance(content, str) and "buy now" in content.lower():
        return 0.95
    return 0.05
