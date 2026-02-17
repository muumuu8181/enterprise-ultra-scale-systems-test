from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging

app = FastAPI(
    title="Core Banking Data Processing Service",
    description="Python backend for analytics, risk calculation, and reporting.",
    version="0.1.0"
)

# CORS setup
origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
def read_root():
    return {"message": "Core Banking Data Processing Service is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
