from fastapi import FastAPI
from src.api.v1.workspace import router as workspace_router

app = FastAPI(title="Chat Messaging Platform")

app.include_router(workspace_router)

@app.get("/")
async def root():
    return {"message": "Chat Messaging Platform"}
