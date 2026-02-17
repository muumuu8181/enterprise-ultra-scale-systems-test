from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vector_models import VectorCollection, VectorItem


class VectorStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_collection(
        self, name: str, dimension: int, metric: str
    ) -> VectorCollection:
        # Check existence
        stmt = select(VectorCollection).where(VectorCollection.name == name)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Collection {name} already exists")

        if metric not in ["cosine", "euclidean", "dot"]:
            raise ValueError("Metric must be one of: cosine, euclidean, dot")

        collection = VectorCollection(name=name, dimension=dimension, metric=metric)
        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def upsert_vector(
        self,
        collection_name: str,
        external_id: str,
        vector: List[float],
        metadata: Dict[str, Any] = None,
    ) -> VectorItem:
        # Find collection
        stmt = select(VectorCollection).where(VectorCollection.name == collection_name)
        result = await self.db.execute(stmt)
        collection = result.scalar_one_or_none()
        if not collection:
            raise ValueError(f"Collection {collection_name} not found")

        if len(vector) != collection.dimension:
            raise ValueError(
                f"Vector dimension {len(vector)} does not match collection dimension {collection.dimension}"
            )

        # Find item
        stmt = select(VectorItem).where(
            VectorItem.collection_id == collection.id,
            VectorItem.external_id == external_id,
        )
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if item:
            item.embedding = vector
            item.metadata_ = metadata or {}
        else:
            item = VectorItem(
                collection_id=collection.id,
                external_id=external_id,
                embedding=vector,
                metadata_=metadata or {},
            )
            self.db.add(item)
            # Increment count
            collection.item_count += 1

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def search_nearest(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Dict = None,
    ) -> List[VectorItem]:
        # Find collection
        stmt = select(VectorCollection).where(VectorCollection.name == collection_name)
        result = await self.db.execute(stmt)
        collection = result.scalar_one_or_none()
        if not collection:
            raise ValueError(f"Collection {collection_name} not found")

        # Determine operator
        if collection.metric == "cosine":
            op = VectorItem.embedding.cosine_distance(query_vector)
        elif collection.metric == "euclidean":
            op = VectorItem.embedding.l2_distance(query_vector)
        elif collection.metric == "dot":
            op = VectorItem.embedding.max_inner_product(query_vector)
        else:
            op = VectorItem.embedding.cosine_distance(query_vector)

        stmt = select(VectorItem).where(VectorItem.collection_id == collection.id)

        # Apply filters on metadata (assuming JSONB)
        if filters:
            # Simple exact match for top-level keys
            for key, value in filters.items():
                # JSONB containment or equality.
                # For simplicity, let's use the contain operator (@>) for dictionary subset
                # or individual key checks.
                # Here we use individual key check using ->> operator (as text)
                stmt = stmt.where(VectorItem.metadata_[key].astext == str(value))

        stmt = stmt.order_by(op).limit(top_k)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_vector(self, collection_name: str, external_id: str):
        stmt = select(VectorCollection).where(VectorCollection.name == collection_name)
        result = await self.db.execute(stmt)
        collection = result.scalar_one_or_none()
        if not collection:
            raise ValueError(f"Collection {collection_name} not found")

        stmt = select(VectorItem).where(
            VectorItem.collection_id == collection.id,
            VectorItem.external_id == external_id,
        )
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if item:
            await self.db.delete(item)
            collection.item_count -= 1
            await self.db.commit()

    async def build_index(self, collection_name: str):
        # ... logic to build HNSW index ...
        stmt = select(VectorCollection).where(VectorCollection.name == collection_name)
        result = await self.db.execute(stmt)
        collection = result.scalar_one_or_none()
        if not collection:
            raise ValueError(f"Collection {collection_name} not found")

        # Determine ops
        if collection.metric == "cosine":
            ops = "vector_cosine_ops"
        elif collection.metric == "euclidean":
            ops = "vector_l2_ops"
        elif collection.metric == "dot":
            ops = "vector_ip_ops"
        else:
            ops = "vector_cosine_ops"

        # Index name
        index_name = f"idx_hnsw_{collection.id}"

        # We need to cast the column to specific dimension for the index to work on a generic vector column
        # syntax: ((embedding::vector(128)))
        # Note: We must ensure safety against SQL injection if name was used, but here we use ID.

        sql = text(
            f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON vector_items USING hnsw ((embedding::vector({collection.dimension})) {ops})
            WHERE collection_id = :coll_id
        """
        )

        await self.db.execute(sql, {"coll_id": collection.id})
        await self.db.commit()
