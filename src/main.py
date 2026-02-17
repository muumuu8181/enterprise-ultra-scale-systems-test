import contextlib
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.routers import accounts, transactions, reports

# Structlog configuration
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Database setup (minimal for lifespan)
# Note: In a real app, this might be in a separate database module
engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

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

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}
