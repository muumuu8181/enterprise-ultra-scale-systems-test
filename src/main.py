from fastapi import FastAPI
from src.api.v1 import telematics, damage_claims
from src.core.database import engine, Base
import src.models.rental_models # Import to register models

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(telematics.router, prefix="/telematics", tags=["telematics"])
app.include_router(damage_claims.router, prefix="/damage-claims", tags=["damage-claims"])

@app.get("/")
def read_root():
    return {"message": "Rental Car Service API"}
