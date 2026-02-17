import pytest
from httpx import AsyncClient
from src.core.config import settings

@pytest.mark.asyncio
async def test_create_circuit(client: AsyncClient):
    payload = {
        "name": "Bell State",
        "qubit_count": 2,
        "gate_sequence": {"gates": ["H", "CNOT"]},
        "depth": 2,
        "description": "Creates a Bell state",
        "tags": {"type": "entanglement"}
    }
    response = await client.post(f"{settings.API_V1_STR}/circuits/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Bell State"
    assert "id" in data

@pytest.mark.asyncio
async def test_visualize_circuit(client: AsyncClient):
    # First create a circuit
    payload = {
        "name": "Test Circuit",
        "qubit_count": 1,
        "gate_sequence": {},
        "depth": 1
    }
    create_res = await client.post(f"{settings.API_V1_STR}/circuits/create", json=payload)
    circuit_id = create_res.json()["id"]

    response = await client.get(f"{settings.API_V1_STR}/circuits/{circuit_id}/visualize")
    assert response.status_code == 200
    assert "visualization" in response.json()

@pytest.mark.asyncio
async def test_run_simulation(client: AsyncClient):
    # Create circuit
    create_payload = {
        "name": "Sim Circuit",
        "qubit_count": 1,
        "gate_sequence": {},
        "depth": 1
    }
    create_res = await client.post(f"{settings.API_V1_STR}/circuits/create", json=create_payload)
    circuit_id = create_res.json()["id"]

    # Run simulation
    sim_payload = {
        "circuit_id": circuit_id,
        "backend": "statevector",
        "shots": 100
    }
    response = await client.post(f"{settings.API_V1_STR}/simulations/run", json=sim_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed" # Mock logic sets it to completed immediately
    assert data["backend"] == "statevector"

@pytest.mark.asyncio
async def test_algorithm_lifecycle(client: AsyncClient):
    # Create algorithm
    algo_payload = {
        "name": "Grover's Algorithm",
        "algorithm_type": "grover",
        "description": "Search algorithm",
        "complexity_class": "BQP"
    }
    create_res = await client.post(f"{settings.API_V1_STR}/algorithms", json=algo_payload)
    assert create_res.status_code == 200
    algo_id = create_res.json()["id"]

    # List algorithms
    list_res = await client.get(f"{settings.API_V1_STR}/algorithms?type=grover")
    assert list_res.status_code == 200
    data = list_res.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Grover's Algorithm"

    # Instantiate algorithm
    inst_res = await client.post(f"{settings.API_V1_STR}/algorithms/{algo_id}/instantiate", json={"params": {"n": 3}})
    assert inst_res.status_code == 200
    circuit_data = inst_res.json()
    assert "Instance" in circuit_data["name"]
