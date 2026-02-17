from fastapi import FastAPI
from .api.v1 import accounts, transactions
from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="銀行コアバンキングシステム API"
)

# Accounts Router: /api/v1/accounts
app.include_router(accounts.router, prefix=f"{settings.API_V1_STR}/accounts", tags=["accounts"])

# Transactions Router: /api/v1 (contains /accounts/.../deposit, /transfers)
app.include_router(transactions.router, prefix=f"{settings.API_V1_STR}", tags=["transactions"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
