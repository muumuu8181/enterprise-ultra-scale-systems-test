from fastapi import APIRouter

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/")
async def get_transactions():
    """取引一覧を取得する"""
    return []
