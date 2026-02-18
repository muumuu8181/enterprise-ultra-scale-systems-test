from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Use a file-based SQLite database for persistence during development
DATABASE_URL = "sqlite+aiosqlite:///./insurance.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
