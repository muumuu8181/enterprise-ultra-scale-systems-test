from fastapi.testclient import TestClient

def create_flight(client, flight_number, origin, destination):
    flight_data = {
        "flight_number": flight_number,
        "origin": origin,
        "destination": destination,
        "departure_time": "2023-12-25T10:00:00",
        "capacity": 200,
        "seats": [
            {"seat_number": "1A", "class_type": "Business", "is_booked": False},
            {"seat_number": "1B", "class_type": "Business", "is_booked": False}
        ]
    }
    response = client.post("/api/v1/flights/", json=flight_data)
    assert response.status_code == 200
    return response.json()

def test_create_flight(client):
    data = create_flight(client, "UA123", "SFO", "JFK")
    assert data["flight_number"] == "UA123"
    assert len(data["seats"]) == 2

def test_search_flights(client):
    # Ensure flight exists
    create_flight(client, "UA124", "SFO", "JFK")
    response = client.get("/api/v1/flights/?origin=SFO&destination=JFK")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Check if at least one flight matches
    assert any(f["flight_number"] == "UA124" for f in data)

def test_create_booking(client):
    flight = create_flight(client, "UA125", "SFO", "JFK")
    flight_id = flight["id"]
    seat_id = flight["seats"][0]["id"]

    booking_data = {
        "flight_id": flight_id,
        "seat_id": seat_id,
        "passenger_name": "John Doe",
        "passenger_email": "john.doe@example.com",
        "status": "PENDING"
    }
    response = client.post("/api/v1/bookings/", json=booking_data)
    assert response.status_code == 200
    data = response.json()
    assert data["passenger_name"] == "John Doe"
    # Status should be confirmed if seat is provided
    assert data["status"] == "CONFIRMED"

def test_get_booking(client):
    flight = create_flight(client, "AA456", "LAX", "LHR")
    flight_id = flight["id"]
    seat_id = flight["seats"][0]["id"]

    booking_data = {
        "flight_id": flight_id,
        "seat_id": seat_id,
        "passenger_name": "Jane Doe",
        "passenger_email": "jane.doe@example.com",
        "status": "PENDING"
    }
    booking_response = client.post("/api/v1/bookings/", json=booking_data)
    pnr = booking_response.json()["pnr"]

    response = client.get(f"/api/v1/bookings/{pnr}")
    assert response.status_code == 200
    assert response.json()["pnr"] == pnr
    assert response.json()["passenger_name"] == "Jane Doe"
