from fastapi import FastAPI
from src.api.v1 import pets

app = FastAPI()

app.include_router(pets.router)

@app.get("/")
async def root():
    return {"message": "Pet Care Platform API"}
