import contextlib
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine
from src.routers import accounts, transactions, reports
from src.api.v1 import foreign_exchange
from src.api.v1 import connections

# Structlog configuration
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # DB接続 (Startup)
    logger.info("Starting up application...")

    # Check DB connection
    try:
        async with engine.begin() as conn:
             logger.info("Database connection established.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    yield

    # DB切断 (Shutdown)
    logger.info("Shutting down application...")
    await engine.dispose()

app = FastAPI(
    title="Banking System API",
    lifespan=lifespan,
    debug=settings.debug
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(foreign_exchange.router)
app.include_router(connections.router)
app.include_router(connections.accounts_router)

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}
