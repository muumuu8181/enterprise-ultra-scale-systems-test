from fastapi import FastAPI
from src.app.api import endpoints
from src.app.database import engine, Base
from src.app.models import flight, booking

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Global Airline System")

app.include_router(endpoints.router, prefix="/api/v1")
