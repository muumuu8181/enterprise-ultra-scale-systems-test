from fastapi import FastAPI
from src.api.v1 import discovery, podcasts

app = FastAPI(title="Audio Music Platform", version="1.0.0")

app.include_router(discovery.router)
app.include_router(podcasts.router)
app.include_router(podcasts.episode_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Audio Music Platform"}
