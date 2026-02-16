from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.models import Base
import pytest
from datetime import datetime, timedelta

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_election_flow():
    # 1. Create Election
    start = datetime.now()
    end = start + timedelta(hours=1)
    response = client.post("/elections", json={
        "name": "General Election 2024",
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    })
    assert response.status_code == 200, response.text
    election_data = response.json()
    election_id = election_data["id"]

    # 2. Register Candidates
    c1 = client.post("/candidates", json={"name": "Alice", "election_id": election_id})
    assert c1.status_code == 200, c1.text
    c1_id = c1.json()["id"]

    c2 = client.post("/candidates", json={"name": "Bob", "election_id": election_id})
    assert c2.status_code == 200, c2.text
    c2_id = c2.json()["id"]

    # 3. Register Voter
    voter = client.post("/voters", json={"real_id": "MY_ID_12345"})
    assert voter.status_code == 200, voter.text

    # 4. Cast Vote
    vote_payload = {
        "voter_real_id": "MY_ID_12345",
        "election_id": election_id,
        "candidate_id": c1_id
    }
    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 200, vote.text

    # 5. Check Results
    results = client.get(f"/elections/{election_id}/results")
    assert results.status_code == 200, results.text
    data = results.json()
    assert data["Alice"] == 1
    assert "Bob" not in data or data["Bob"] == 0

    # 6. Double Voting Prevention
    vote_payload_2 = {
        "voter_real_id": "MY_ID_12345",
        "election_id": election_id,
        "candidate_id": c2_id
    }
    vote2 = client.post("/votes", json=vote_payload_2)
    assert vote2.status_code == 403, "Double voting should be forbidden"

    # 7. Multi-Election Voting (Should be allowed)
    # Create Election 2
    response = client.post("/elections", json={
        "name": "Local Election 2024",
        "start_time": start.isoformat(),
        "end_time": end.isoformat()
    })
    assert response.status_code == 200, response.text
    election2_id = response.json()["id"]

    # Register Candidate for Election 2
    c3 = client.post("/candidates", json={"name": "Charlie", "election_id": election2_id})
    c3_id = c3.json()["id"]

    # Vote in Election 2 (Same Voter)
    vote3 = client.post("/votes", json={
        "voter_real_id": "MY_ID_12345",
        "election_id": election2_id,
        "candidate_id": c3_id
    })
    assert vote3.status_code == 200, "Voter should be able to vote in a different election"
