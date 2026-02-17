from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.dataset_models import Dataset, DatasetSplit
from typing import List, Optional
import random

class DatasetManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_dataset(self, name: str, storage_path: str, schema: dict, size_bytes: int, version: str = "v1", tags: dict = None, row_count: int = 0) -> Dataset:
        dataset = Dataset(
            name=name,
            version=version,
            storage_path=storage_path,
            schema=schema,
            row_count=row_count,
            size_bytes=size_bytes,
            tags=tags or {}
        )
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)
        return dataset

    async def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        result = await self.db.execute(select(Dataset).where(Dataset.id == dataset_id))
        return result.scalars().first()

    async def list_datasets(self, search: str = None, tag_filter: str = None) -> List[Dataset]:
        query = select(Dataset)
        if search:
            query = query.where(Dataset.name.ilike(f"%{search}%"))

        result = await self.db.execute(query)
        datasets = list(result.scalars().all())

        if tag_filter:
            filtered = []
            for ds in datasets:
                if ds.tags and tag_filter in ds.tags:
                     filtered.append(ds)
            return filtered

        return datasets

    async def validate_schema(self, dataset_id: int) -> bool:
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return False
        # TODO: Implement actual schema validation logic (e.g., check if data file matches schema JSON)
        # This is a placeholder that assumes valid if dataset exists.
        return True

    async def split_dataset(self, dataset_id: int, train_ratio: float, val_ratio: float, test_ratio: float, random_seed: int = 42) -> List[DatasetSplit]:
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")

        total_rows = dataset.row_count
        train_rows = int(total_rows * train_ratio)
        val_rows = int(total_rows * val_ratio)
        test_rows = total_rows - train_rows - val_rows

        if test_rows < 0:
             test_rows = 0

        created_splits = []
        for split_type, count in [("train", train_rows), ("val", val_rows), ("test", test_rows)]:
            if count > 0:
                split = DatasetSplit(
                    dataset_id=dataset.id,
                    split_type=split_type,
                    storage_path=f"{dataset.storage_path}/{split_type}",
                    row_count=count
                )
                self.db.add(split)
                created_splits.append(split)

        await self.db.commit()
        for s in created_splits:
            await self.db.refresh(s)

        return created_splits

    async def get_statistics(self, dataset_id: int):
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            return None
        return {
            "row_count": dataset.row_count,
            "size_bytes": dataset.size_bytes
        }
