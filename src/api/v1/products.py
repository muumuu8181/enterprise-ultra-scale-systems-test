from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.models.marketplace_models import AuthType, PricingModel

router = APIRouter()

# Pydantic models for request/response
class ProductCreate(BaseModel):
    provider_id: int
    name: str
    category: str
    description: str
    base_url: str
    auth_type: AuthType
    pricing_model: PricingModel

class ProductResponse(ProductCreate):
    id: int

class SubscriptionCreate(BaseModel):
    consumer_id: int
    product_id: int
    plan_id: str

class SubscriptionResponse(SubscriptionCreate):
    id: int
    api_key: str
    quota_per_month: int
    usage_this_month: int

class VersionResponse(BaseModel):
    id: int
    version: str
    changelog: str
    deprecated: bool
    sunset_date: Optional[datetime]

# Endpoints

@router.post("/products/publish", response_model=ProductResponse)
async def publish_product(product: ProductCreate):
    # Mock implementation
    # Using dict() for Pydantic v1/v2 compatibility
    return {
        "id": 1,
        **product.dict()
    }

@router.get("/products/search", response_model=List[ProductResponse])
async def search_products(
    category: Optional[str] = None,
    free: bool = Query(False)
):
    # Mock implementation
    return []

@router.get("/products/{id}/docs")
async def get_product_docs(id: int):
    # Mock implementation
    return {"docs_url": f"https://api.example.com/products/{id}/docs"}

@router.get("/products/{id}/versions", response_model=List[VersionResponse])
async def get_product_versions(id: int):
    # Mock implementation
    return [
        {
            "id": 101,
            "version": "1.0.0",
            "changelog": "Initial release",
            "deprecated": False,
            "sunset_date": None
        }
    ]

@router.post("/subscriptions/subscribe", response_model=SubscriptionResponse)
async def subscribe_product(subscription: SubscriptionCreate):
    # Mock implementation
    return {
        "id": 501,
        "consumer_id": subscription.consumer_id,
        "product_id": subscription.product_id,
        "plan_id": subscription.plan_id,
        "api_key": "api_key_12345",
        "quota_per_month": 1000,
        "usage_this_month": 0
    }

@router.get("/subscriptions/{id}/usage")
async def get_subscription_usage(id: int):
    # Mock implementation
    return {
        "subscription_id": id,
        "usage_this_month": 45,
        "quota_per_month": 1000
    }
