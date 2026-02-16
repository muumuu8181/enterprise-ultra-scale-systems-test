from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Dict

from app.models import SessionLocal, init_db
import app.services as services
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Election Management System", lifespan=lifespan)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ElectionCreate(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime

class CandidateCreate(BaseModel):
    name: str
    election_id: int

class VoterRegister(BaseModel):
    real_id: str

class VoteCast(BaseModel):
    voter_real_id: str
    election_id: int
    candidate_id: int

@app.get("/")
def read_root():
    return {"message": "Election System Online"}

@app.post("/elections")
def create_election(election: ElectionCreate, db: Session = Depends(get_db)):
    try:
        return services.create_election(db, election.name, election.start_time, election.end_time)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/candidates")
def create_candidate(candidate: CandidateCreate, db: Session = Depends(get_db)):
    try:
        return services.register_candidate(db, candidate.name, candidate.election_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/voters")
def register_voter(voter: VoterRegister, db: Session = Depends(get_db)):
    try:
        return services.register_voter(db, voter.real_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/votes")
def cast_vote(vote: VoteCast, db: Session = Depends(get_db)):
    try:
        return services.cast_vote(db, vote.voter_real_id, vote.election_id, vote.candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/elections/{election_id}/results")
def get_results(election_id: int, db: Session = Depends(get_db)):
    return services.tally_votes(db, election_id)
