from fastapi import FastAPI
from src.core.config import get_settings
from src.api.v1 import tickets, contact_center

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(tickets.router, prefix=settings.API_V1_STR)
app.include_router(contact_center.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Customer Support Platform"}
