from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from models import Lot, Equipment, LotStatus, EquipmentStatus
from spc import generate_control_chart_data

app = FastAPI(title="Semiconductor MES API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
lots: Dict[str, Lot] = {
    "LOT001": Lot(lot_id="LOT001", product_id="PROD-A", quantity=25, status=LotStatus.WAITING),
    "LOT002": Lot(lot_id="LOT002", product_id="PROD-B", quantity=24, status=LotStatus.WAITING)
}

equipment_list: Dict[str, Equipment] = {
    "EQP01": Equipment(equipment_id="EQP01", type="LITHO", status=EquipmentStatus.IDLE),
    "EQP02": Equipment(equipment_id="EQP02", type="ETCH", status=EquipmentStatus.IDLE),
    "EQP03": Equipment(equipment_id="EQP03", type="CVD", status=EquipmentStatus.MAINTENANCE)
}

@app.get("/")
def read_root():
    return {"message": "Welcome to Semi-MES API"}

# --- MES Endpoints ---

@app.get("/api/v1/mes/lots", response_model=List[Lot])
def get_lots():
    return list(lots.values())

@app.post("/api/v1/mes/move-in/{lot_id}/{equipment_id}")
def move_in(lot_id: str, equipment_id: str):
    if lot_id not in lots:
        raise HTTPException(status_code=404, detail="Lot not found")
    if equipment_id not in equipment_list:
        raise HTTPException(status_code=404, detail="Equipment not found")

    lot = lots[lot_id]
    eqp = equipment_list[equipment_id]

    if lot.status != LotStatus.WAITING:
        raise HTTPException(status_code=400, detail=f"Lot status is {lot.status}, expected WAITING")

    if eqp.status != EquipmentStatus.IDLE:
        raise HTTPException(status_code=400, detail=f"Equipment status is {eqp.status}, expected IDLE")

    # Update State
    lot.status = LotStatus.PROCESSING
    lot.current_step = eqp.type
    lot.history.append(f"Move-In at {equipment_id} on {datetime.now()}")

    eqp.status = EquipmentStatus.RUNNING
    eqp.current_lot_id = lot_id

    return {"message": "Move-In Successful", "lot": lot, "equipment": eqp}

@app.post("/api/v1/mes/move-out/{lot_id}/{equipment_id}")
def move_out(lot_id: str, equipment_id: str):
    if lot_id not in lots:
        raise HTTPException(status_code=404, detail="Lot not found")
    if equipment_id not in equipment_list:
        raise HTTPException(status_code=404, detail="Equipment not found")

    lot = lots[lot_id]
    eqp = equipment_list[equipment_id]

    if lot.status != LotStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Lot is not processing")

    if eqp.current_lot_id != lot_id:
        raise HTTPException(status_code=400, detail="Lot mismatch on equipment")

    # Update State
    lot.status = LotStatus.WAITING # Or COMPLETED if last step
    lot.history.append(f"Move-Out at {equipment_id} on {datetime.now()}")

    eqp.status = EquipmentStatus.IDLE
    eqp.current_lot_id = None

    return {"message": "Move-Out Successful", "lot": lot, "equipment": eqp}

# --- Equipment Endpoints ---

@app.get("/api/v1/equipment", response_model=List[Equipment])
def get_equipment():
    return list(equipment_list.values())

@app.get("/api/v1/equipment/{equipment_id}", response_model=Equipment)
def get_equipment_detail(equipment_id: str):
    if equipment_id not in equipment_list:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment_list[equipment_id]

@app.put("/api/v1/equipment/{equipment_id}/status")
def update_equipment_status(equipment_id: str, status: EquipmentStatus):
    if equipment_id not in equipment_list:
        raise HTTPException(status_code=404, detail="Equipment not found")

    eqp = equipment_list[equipment_id]
    eqp.status = status
    return eqp

# --- SPC Endpoints ---

@app.get("/api/v1/spc/chart/{parameter_id}")
def get_spc_chart(parameter_id: str):
    data = generate_control_chart_data(parameter_id)
    return data
