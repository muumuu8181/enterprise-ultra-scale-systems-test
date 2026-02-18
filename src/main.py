from fastapi import FastAPI
from src.api.v1.work_orders import router as work_orders_router

app = FastAPI(title="Predictive Maintenance Platform")

app.include_router(work_orders_router, prefix="/api/v1", tags=["work-orders"])
