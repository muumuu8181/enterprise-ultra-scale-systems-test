from fastapi import FastAPI
from src.api.v1.streaming import router as streaming_router
from src.api.v1.monetization import router as monetization_router

app = FastAPI(title="Video Streaming Platform")

app.include_router(streaming_router)
app.include_router(monetization_router)

@app.get("/")
async def root():
    return {"message": "Video Streaming Platform API"}
