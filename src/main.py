from fastapi import FastAPI
from src.db.base import Base
from src.db.session import engine
from src.api.v1.threats import router as threats_router

app = FastAPI(title="Cybersecurity Platform")

app.include_router(threats_router, prefix="/threats", tags=["threats"])

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cybersecurity Platform"}
