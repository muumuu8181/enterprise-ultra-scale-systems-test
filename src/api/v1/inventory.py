from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.db.session import get_db
from src.models.inventory_mes import RawMaterial, BillOfMaterials, ProductionOrder
from src.schemas.inventory import (
    RawMaterialCreate, RawMaterialResponse,
    MaterialStatus, MaterialIssueRequest
)

router = APIRouter()

@router.post("/raw-materials", response_model=RawMaterialResponse)
async def create_raw_material(material: RawMaterialCreate, db: AsyncSession = Depends(get_db)):
    db_material = RawMaterial(**material.model_dump())
    db.add(db_material)
    await db.commit()
    await db.refresh(db_material)
    return db_material

@router.get("/raw-materials/low-stock", response_model=List[RawMaterialResponse])
async def get_low_stock_materials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RawMaterial).where(RawMaterial.stock_qty < RawMaterial.reorder_point))
    return result.scalars().all()

@router.post("/bom/{product_id}/validate-materials")
async def validate_bom_materials(product_id: int, quantity: float = Body(embed=True), db: AsyncSession = Depends(get_db)):
    # Check if we have enough materials to produce 'quantity' of 'product_id'
    result = await db.execute(select(BillOfMaterials).where(BillOfMaterials.product_id == product_id))
    bom_items = result.scalars().all()

    if not bom_items:
        raise HTTPException(status_code=404, detail="BOM not found for product")

    status = {"is_sufficient": True, "missing_items": []}

    for item in bom_items:
        required = item.qty_required * quantity * (1 + item.waste_factor)
        material = await db.get(RawMaterial, item.material_id)

        if not material:
             status["is_sufficient"] = False
             status["missing_items"].append({"material_id": item.material_id, "error": "Material not found"})
             continue

        if material.stock_qty < required:
            status["is_sufficient"] = False
            status["missing_items"].append({
                "material_id": material.id,
                "required": required,
                "available": material.stock_qty
            })

    return status

@router.get("/production-orders/{id}/material-status", response_model=MaterialStatus)
async def check_order_material_status(id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(ProductionOrder, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Assume BOM lookup by product_id
    items_result = await db.execute(select(BillOfMaterials).where(BillOfMaterials.product_id == order.product_id))
    bom_items = items_result.scalars().all()

    status = {"is_sufficient": True, "missing_items": []}
    for item in bom_items:
        required = item.qty_required * order.planned_qty * (1 + item.waste_factor)
        material = await db.get(RawMaterial, item.material_id)
        if not material or material.stock_qty < required:
            status["is_sufficient"] = False
            status["missing_items"].append({
                "material_id": item.material_id,
                "required": required,
                "available": material.stock_qty if material else 0
            })

    return status

@router.post("/production-orders/{id}/issue-materials")
async def issue_materials(id: int, db: AsyncSession = Depends(get_db)):
    # We must ensure atomicity. Check and deduct in one transaction with locks.
    order = await db.get(ProductionOrder, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "ISSUED":
        raise HTTPException(status_code=400, detail="Materials already issued")

    items_result = await db.execute(select(BillOfMaterials).where(BillOfMaterials.product_id == order.product_id))
    bom_items = items_result.scalars().all()

    reservations = {}

    # Iterate and lock materials to prevent race conditions
    for item in bom_items:
        required = item.qty_required * order.planned_qty * (1 + item.waste_factor)

        # Select for update to lock the row
        stmt = select(RawMaterial).where(RawMaterial.id == item.material_id).with_for_update()
        res = await db.execute(stmt)
        material = res.scalar_one_or_none()

        if not material:
             raise HTTPException(status_code=400, detail=f"Material ID {item.material_id} not found")

        if material.stock_qty < required:
             raise HTTPException(status_code=400, detail=f"Insufficient stock for material {material.name} (ID: {item.material_id}). Required: {required}, Available: {material.stock_qty}")

        material.stock_qty -= required
        reservations[str(item.material_id)] = required

    order.material_reservations = reservations
    order.status = "ISSUED"

    # Commit changes
    await db.commit()
    await db.refresh(order)
    return {"status": "success", "order_id": order.id}
