from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.ml_models import Base, utc_now

class AnnotationTask(Base):
    """
    アノテーションタスク定義 (Annotation Task Definition)

    属性:
        id: タスクID
        dataset_id: データセットID
        task_type: タスクタイプ (classification/detection/segmentation)
        status: ステータス (pending, in_progress, completed)
        total_items: 総アイテム数
        completed_items: 完了アイテム数
        created_at: 作成日時
    """
    __tablename__ = "annotation_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(Integer, index=True)
    task_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    items: Mapped[List["AnnotationItem"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    annotations: Mapped[List["Annotation"]] = relationship(back_populates="task", cascade="all, delete-orphan")

class AnnotationItem(Base):
    """
    アノテーション対象アイテム (Annotation Item)

    属性:
        id: アイテムID
        task_id: タスクID
        content: コンテンツ (URL/パス/テキスト)
        status: ステータス (pending, annotated)
    """
    __tablename__ = "annotation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("annotation_tasks.id"))
    content: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")

    task: Mapped["AnnotationTask"] = relationship(back_populates="items")
    annotations: Mapped[List["Annotation"]] = relationship(back_populates="item", cascade="all, delete-orphan")

class Annotation(Base):
    """
    アノテーション結果 (Annotation Result)

    属性:
        id: アノテーションID
        task_id: タスクID
        item_id: アイテムID
        label: ラベル (JSON)
        confidence: 信頼度
        annotator_id: アノテータID
        created_at: 作成日時
    """
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("annotation_tasks.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("annotation_items.id"))
    label: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    annotator_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    task: Mapped["AnnotationTask"] = relationship(back_populates="annotations")
    item: Mapped["AnnotationItem"] = relationship(back_populates="annotations")
