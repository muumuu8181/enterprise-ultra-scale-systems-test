from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter()

# 簡易的なインメモリ保存
feature_sets_db: Dict[str, Dict[str, Any]] = {}

class FeatureSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    entities: List[str]
    features: List[Dict[str, str]]  # {"name": "age", "type": "int"}
    tags: Optional[Dict[str, str]] = None

class FeatureSetResponse(BaseModel):
    name: str
    description: Optional[str]
    created_at: datetime
    status: str

@router.post("/sets", response_model=FeatureSetResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_set(fs: FeatureSetCreate):
    """
    特徴量セットを定義します。
    """
    if fs.name in feature_sets_db:
        raise HTTPException(status_code=400, detail="Feature set already exists")

    new_fs = fs.model_dump()
    new_fs["created_at"] = datetime.now()
    new_fs["status"] = "created"

    # マテリアライズされたデータを入れる場所 (簡易)
    new_fs["data_store"] = {}

    feature_sets_db[fs.name] = new_fs

    return FeatureSetResponse(
        name=fs.name,
        description=fs.description,
        created_at=new_fs["created_at"],
        status=new_fs["status"]
    )

@router.get("/sets/{name}/values")
async def get_feature_values(name: str, entity_ids: List[str] = Query(...)):
    """
    指定されたエンティティIDに対する特徴量を取得します。
    """
    fs = feature_sets_db.get(name)
    if not fs:
        raise HTTPException(status_code=404, detail="Feature set not found")

    results = []
    # 簡易実装: ランダムあるいは保存された値を返す
    # 本来は Redis や Feature Store (Feastなど) から取得

    for entity_id in entity_ids:
        # マテリアライズされたデータがあればそこから取得
        record = fs["data_store"].get(entity_id)
        if record:
            results.append({"entity_id": entity_id, "values": record, "timestamp": datetime.now()})
        else:
             # データがない場合は空あるいはデフォルト値を返すか、エラーにするか
             # ここでは空の値を返す
             results.append({"entity_id": entity_id, "values": {}, "note": "not_materialized"})

    return {"features": results}

@router.post("/sets/{name}/materialize", status_code=status.HTTP_202_ACCEPTED)
async def materialize_feature_set(name: str):
    """
    特徴量セットをマテリアライズ（計算・永続化）します。
    """
    fs = feature_sets_db.get(name)
    if not fs:
        raise HTTPException(status_code=404, detail="Feature set not found")

    # 非同期処理としてキックするべきだが、ここでは同期的に簡易実行
    fs["status"] = "materializing"

    # ダミーデータを生成して保存
    # 本来はバッチジョブを実行し、結果をRedis/DynamoDB等に書き込む
    import random
    for i in range(10):
        entity_id = f"user_{i}"
        fs["data_store"][entity_id] = {
            f["name"]: random.random() for f in fs["features"]
        }

    fs["status"] = "active"
    fs["last_materialized"] = datetime.now()

    return {"message": "Materialization started", "job_id": "mat_12345"}
