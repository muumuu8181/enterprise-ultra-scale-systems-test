from fastapi import APIRouter

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/")
async def get_accounts():
    """アカウント一覧を取得する"""
    return []
