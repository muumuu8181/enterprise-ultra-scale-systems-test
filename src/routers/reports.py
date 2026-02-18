from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/")
async def get_reports():
    """レポートを取得する"""
    return {}
