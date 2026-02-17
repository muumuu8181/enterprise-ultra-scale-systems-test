from fastapi import APIRouter

router = APIRouter(prefix="/rankings", tags=["rankings"])

@router.get("/top100")
async def get_top100():
    return [{"rank": i, "user": f"User {i}", "score": 1000-i} for i in range(1, 101)]
