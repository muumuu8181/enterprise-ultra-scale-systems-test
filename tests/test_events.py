import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_create_event(client: AsyncClient):
    payload = {
        "title": "Tech Conference 2024",
        "organizer_id": 1,
        "event_type": "conference",
        "start_date": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=12)).isoformat(),
        "capacity": 500,
        "ticket_types": {"standard": 100, "vip": 200},
        "status": "published"
    }
    response = await client.post("/api/v1/events/create", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_register_attendee(client: AsyncClient):
    # First create event
    event_payload = {
        "title": "Concert",
        "organizer_id": 1,
        "event_type": "concert",
        "start_date": datetime.now(timezone.utc).isoformat(),
        "end_date": datetime.now(timezone.utc).isoformat(),
        "capacity": 100,
        "ticket_types": {"ga": 50},
        "status": "published"
    }
    event_res = await client.post("/api/v1/events/create", json=event_payload)
    event_id = event_res.json()["id"]

    # Register
    reg_payload = {
        "event_id": event_id,
        "attendee_id": 101,
        "ticket_type": "ga",
        "amount_paid": 50.0
    }
    response = await client.post("/api/v1/registrations/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == event_id
    assert data["attendee_id"] == 101

@pytest.mark.asyncio
async def test_dashboard(client: AsyncClient):
    # Create event
    event_res = await client.post("/api/v1/events/create", json={
        "title": "Workshop",
        "organizer_id": 1,
        "event_type": "workshop",
        "start_date": datetime.now(timezone.utc).isoformat(),
        "end_date": datetime.now(timezone.utc).isoformat(),
        "capacity": 10,
        "ticket_types": {},
        "status": "published"
    })
    event_id = event_res.json()["id"]

    # Register 2 people
    await client.post("/api/v1/registrations/register", json={"event_id": event_id, "attendee_id": 1, "ticket_type": "free", "amount_paid": 0})
    reg_res = await client.post("/api/v1/registrations/register", json={"event_id": event_id, "attendee_id": 2, "ticket_type": "free", "amount_paid": 0})
    reg_id = reg_res.json()["id"]

    # Check-in one
    await client.post(f"/api/v1/check-in/{reg_id}")

    # Dashboard
    dash_res = await client.get(f"/api/v1/events/{event_id}/dashboard")
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["total_registrations"] == 2
    assert dash["total_checkins"] == 1
    assert dash["occupancy_rate"] == 0.2

@pytest.mark.asyncio
async def test_venue_booking(client: AsyncClient):
    # Create venue
    venue_res = await client.post("/api/v1/venues/create", json={
        "name": "Grand Hall",
        "address": "123 Main St",
        "capacity": 1000,
        "facilities": {},
        "hourly_rate": 500.0,
        "availability_calendar": {},
        "contact_email": "contact@venue.com"
    })
    assert venue_res.status_code == 201
    venue_id = venue_res.json()["id"]

    # Create event
    event_start = datetime.now(timezone.utc) + timedelta(days=20)
    event_res = await client.post("/api/v1/events/create", json={
        "title": "Gala",
        "organizer_id": 1,
        "event_type": "conference",
        "start_date": event_start.isoformat(),
        "end_date": (event_start + timedelta(hours=4)).isoformat(),
        "capacity": 500,
        "ticket_types": {},
        "status": "published"
    })
    assert event_res.status_code == 201
    event_id = event_res.json()["id"]

    # Book venue
    book_res = await client.post("/api/v1/venues/book", json={"venue_id": venue_id, "event_id": event_id})
    assert book_res.status_code == 200

    # Search venues on that date - should be empty or filtered out
    search_res = await client.get("/api/v1/venues/search", params={"date": event_start.isoformat()})
    assert search_res.status_code == 200, f"Search failed: {search_res.text}"
    venues = search_res.json()
    # Logic: Filter out booked. So if we booked it, it should NOT be in the list.
    venue_ids = [v["id"] for v in venues]
    assert venue_id not in venue_ids
