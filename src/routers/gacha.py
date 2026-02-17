from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/gacha", tags=["gacha"])

class PullRequest(BaseModel):
    count: int

@router.post("/pull")
async def pull_gacha(request: PullRequest):
    return {"message": "Gacha pulled successfully", "count": request.count}
