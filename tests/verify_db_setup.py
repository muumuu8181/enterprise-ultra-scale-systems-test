import asyncio
import sys
import os

# Add src to python path so imports work
sys.path.append(os.getcwd())

from src.db.session import engine
from src.db.base import Base
from src.models.insurance_models import Policy, Claim, Underwriting

async def verify():
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

    print("Verification complete.")

if __name__ == "__main__":
    asyncio.run(verify())
