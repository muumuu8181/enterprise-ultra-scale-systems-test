from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from datetime import datetime

from src.services.model_registry import get_db
from src.models.annotation_models import AnnotationTask, AnnotationItem, Annotation

router = APIRouter(prefix="/annotations", tags=["annotations"])

# --- Schemas ---

class TaskType(str, Enum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ExportFormat(str, Enum):
    COCO = "coco"
    YOLO = "yolo"
    PASCAL_VOC = "pascal_voc"

class TaskCreate(BaseModel):
    dataset_id: int = Field(..., description="データセットID")
    task_type: TaskType = Field(..., description="タスクタイプ")

class TaskResponse(BaseModel):
    id: int
    dataset_id: int
    task_type: str
    status: str
    total_items: int
    completed_items: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ItemResponse(BaseModel):
    id: int
    task_id: int
    content: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class AnnotationCreate(BaseModel):
    label: Dict[str, Any] = Field(..., description="アノテーションラベル (JSON)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度")
    annotator_id: str = Field(..., description="アノテータID")

class AnnotationResponse(BaseModel):
    id: int
    task_id: int
    item_id: int
    label: Dict[str, Any]
    confidence: float
    annotator_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProgressResponse(BaseModel):
    total_items: int
    completed_items: int
    progress_percentage: float

# --- Endpoints ---

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    """
    新規アノテーションタスクを作成します。
    テスト用にダミーアイテム(10個)を自動生成します。
    """
    # Create Task
    task = AnnotationTask(
        dataset_id=task_in.dataset_id,
        task_type=task_in.task_type.value,
        status="pending",
        total_items=10,
        completed_items=0
    )
    db.add(task)
    await db.flush() # get ID

    # Create Mock Items
    items = []
    for i in range(10):
        items.append(AnnotationItem(
            task_id=task.id,
            content=f"dataset_{task_in.dataset_id}_item_{i}.jpg",
            status="pending"
        ))
    db.add_all(items)
    await db.commit()
    await db.refresh(task)
    return task

@router.get("/tasks/{task_id}/items", response_model=List[ItemResponse])
async def get_task_items(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    タスク内の未アノテーションアイテムを取得します。
    """
    result = await db.execute(
        select(AnnotationItem)
        .where(AnnotationItem.task_id == task_id)
        .where(AnnotationItem.status == "pending")
    )
    return result.scalars().all()

@router.post("/items/{item_id}/annotate", response_model=AnnotationResponse)
async def annotate_item(item_id: int, ann_in: AnnotationCreate, db: AsyncSession = Depends(get_db)):
    """
    アイテムにアノテーションを付与します。
    """
    # Check item
    result = await db.execute(select(AnnotationItem).where(AnnotationItem.id == item_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status == "annotated":
        raise HTTPException(status_code=400, detail="Item already annotated")

    # Create Annotation
    annotation = Annotation(
        task_id=item.task_id,
        item_id=item_id,
        label=ann_in.label,
        confidence=ann_in.confidence,
        annotator_id=ann_in.annotator_id
    )
    db.add(annotation)

    # Update Item Status
    item.status = "annotated"
    db.add(item)

    # Update Task Progress
    task_result = await db.execute(select(AnnotationTask).where(AnnotationTask.id == item.task_id))
    task = task_result.scalars().first()
    if task:
        task.completed_items += 1
        if task.completed_items >= task.total_items:
            task.status = "completed"
        else:
            task.status = "in_progress"
        db.add(task)

    await db.commit()
    await db.refresh(annotation)
    return annotation

@router.get("/tasks/{task_id}/progress", response_model=ProgressResponse)
async def get_task_progress(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    タスクの進捗状況を取得します。
    """
    result = await db.execute(select(AnnotationTask).where(AnnotationTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    percentage = (task.completed_items / task.total_items * 100) if task.total_items > 0 else 0.0
    return ProgressResponse(
        total_items=task.total_items,
        completed_items=task.completed_items,
        progress_percentage=percentage
    )

@router.post("/tasks/{task_id}/export")
async def export_annotations(
    task_id: int,
    format: ExportFormat = Query(..., description="Export format: coco, yolo, pascal_voc"),
    db: AsyncSession = Depends(get_db)
):
    """
    アノテーションデータを指定されたフォーマットでエクスポートします。
    """
    # Check task
    task_res = await db.execute(select(AnnotationTask).where(AnnotationTask.id == task_id))
    task = task_res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get all annotations
    anns_res = await db.execute(select(Annotation).where(Annotation.task_id == task_id))
    annotations = anns_res.scalars().all()

    # Format Logic (Mocked structure)
    if format == ExportFormat.COCO:
        return {
            "info": {"description": f"Task {task_id} Export"},
            "images": [{"id": a.item_id, "file_name": "unknown"} for a in annotations],
            "annotations": [
                {
                    "id": a.id,
                    "image_id": a.item_id,
                    "category_id": 1,
                    "bbox": a.label.get("bbox", []),
                    "score": a.confidence
                }
                for a in annotations
            ]
        }
    elif format == ExportFormat.YOLO:
        return {
            "files": {
                f"{a.item_id}.txt": f"0 {a.label.get('cx', 0)} {a.label.get('cy', 0)} {a.label.get('w', 0)} {a.label.get('h', 0)}"
                for a in annotations
            }
        }
    elif format == ExportFormat.PASCAL_VOC:
        return {
            "files": {
                f"{a.item_id}.xml": f"<annotation><object><name>obj</name><bndbox>...</bndbox></object></annotation>"
                for a in annotations
            }
        }

    return {}
