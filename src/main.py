from fastapi import FastAPI
from src.api.v1 import chatbot, analytics
from src.core.database import engine, Base

app = FastAPI(title="Customer Support Platform")

app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["Chatbot"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
