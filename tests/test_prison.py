import pytest
from datetime import date
from src.models.prison_models import Inmate, Cell, SecurityLevel, InmateStatus, CellStatus

async def create_test_data(db_session):
    cell = Cell(block_id="A", cell_number="101", capacity=2, security_level=SecurityLevel.MINIMUM)
    db_session.add(cell)

    inmate = Inmate(
        inmate_number="12345", name="John Doe", dob=date(1980, 1, 1),
        sentence_start=date(2020, 1, 1), offense_category="Theft",
        security_level=SecurityLevel.MINIMUM, status=InmateStatus.INCARCERATED
    )
    db_session.add(inmate)
    await db_session.commit()
    await db_session.refresh(cell)
    await db_session.refresh(inmate)
    return cell, inmate

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_create_and_get_inmate(client, db_session):
    await create_test_data(db_session)

    # Test GET /inmates
    response = await client.get("/api/v1/inmates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["inmate_number"] == "12345"

@pytest.mark.asyncio
async def test_incident_report(client, db_session):
    await create_test_data(db_session)

    # Get inmate id
    inmates = (await client.get("/api/v1/inmates")).json()
    inmate_id = inmates[0]["id"]

    incident_data = {
        "inmate_id": inmate_id,
        "incident_type": "assault",
        "severity": "high",
        "location": "Cafeteria",
        "investigating_officer": "Officer Smith",
        "status": "reported"
    }

    response = await client.post("/api/v1/incidents/report", json=incident_data)
    assert response.status_code == 200
    data = response.json()
    assert data["incident_type"] == "assault"
    assert data["inmate_id"] == inmate_id

@pytest.mark.asyncio
async def test_visitation_endpoints(client):
    # No need for DB data for mocked endpoints
    response = await client.get("/api/v1/visitation/schedule?inmate_id=1")
    assert response.status_code == 200

    booking_data = {
        "inmate_id": 1,
        "visitor_name": "Jane Doe",
        "date": "2023-10-27",
        "time_slot": "10:00-11:00"
    }
    response = await client.post("/api/v1/visitation/book", json=booking_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Visitation booked"

@pytest.mark.asyncio
async def test_assign_inmate(client, db_session):
    cell, inmate = await create_test_data(db_session)

    # Verify initial state
    assert inmate.cell_id is None
    assert cell.current_occupancy == 0

    assign_data = {"inmate_id": inmate.id}
    response = await client.post(f"/api/v1/cells/{cell.id}/assign-inmate", json=assign_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Inmate assigned to cell"

    # Verify assignment via API
    inmate_profile = (await client.get(f"/api/v1/inmates/{inmate.id}/profile")).json()
    assert inmate_profile["cell_id"] == cell.id

    # Verify cell occupancy increased
    cells = (await client.get("/api/v1/cells/occupancy")).json()
    target_cell = next(c for c in cells if c["id"] == cell.id)
    assert target_cell["current_occupancy"] == 1

@pytest.mark.asyncio
async def test_assign_inmate_transfer(client, db_session):
    # Test transferring inmate from one cell to another
    cell1 = Cell(block_id="A", cell_number="101", capacity=2, security_level=SecurityLevel.MINIMUM)
    cell2 = Cell(block_id="A", cell_number="102", capacity=2, security_level=SecurityLevel.MINIMUM)
    inmate = Inmate(
        inmate_number="67890", name="Jane Doe", dob=date(1985, 1, 1),
        sentence_start=date(2021, 1, 1), offense_category="Fraud",
        security_level=SecurityLevel.MINIMUM, status=InmateStatus.INCARCERATED
    )
    db_session.add_all([cell1, cell2, inmate])
    await db_session.commit()
    await db_session.refresh(cell1)
    await db_session.refresh(cell2)
    await db_session.refresh(inmate)

    # Assign to cell 1
    await client.post(f"/api/v1/cells/{cell1.id}/assign-inmate", json={"inmate_id": inmate.id})

    # Verify cell 1 occupancy
    cell1_data = (await client.get("/api/v1/cells/occupancy")).json()
    c1 = next(c for c in cell1_data if c["id"] == cell1.id)
    assert c1["current_occupancy"] == 1

    # Assign to cell 2 (Transfer)
    await client.post(f"/api/v1/cells/{cell2.id}/assign-inmate", json={"inmate_id": inmate.id})

    # Verify cell 1 occupancy decremented
    cell_data = (await client.get("/api/v1/cells/occupancy")).json()
    c1 = next(c for c in cell_data if c["id"] == cell1.id)
    c2 = next(c for c in cell_data if c["id"] == cell2.id)

    assert c1["current_occupancy"] == 0
    assert c2["current_occupancy"] == 1

    # Verify inmate cell_id
    inmate_profile = (await client.get(f"/api/v1/inmates/{inmate.id}/profile")).json()
    assert inmate_profile["cell_id"] == cell2.id
