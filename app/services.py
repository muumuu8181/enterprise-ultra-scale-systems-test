import hashlib
import os
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Election, Candidate, Voter, Vote, AuditLog, VoterParticipation
from datetime import datetime, timezone

# Use a fixed salt for MVP (in production this would be an env var)
VOTER_ID_SALT = os.getenv("VOTER_ID_SALT", "super_secret_election_salt_2024")

def hash_voter_id(real_id: str) -> str:
    return hashlib.sha256((VOTER_ID_SALT + real_id).encode()).hexdigest()

def create_election(db: Session, name: str, start: datetime, end: datetime):
    election = Election(name=name, start_time=start, end_time=end)
    db.add(election)
    db.commit()
    db.refresh(election)
    return election

def register_candidate(db: Session, name: str, election_id: int):
    candidate = Candidate(name=name, election_id=election_id)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate

def register_voter(db: Session, real_id: str):
    hashed = hash_voter_id(real_id)
    # Check if already exists
    existing = db.query(Voter).filter(Voter.hashed_id == hashed).first()
    if existing:
        return existing

    voter = Voter(hashed_id=hashed)
    db.add(voter)
    db.commit()
    db.refresh(voter)
    return voter

def cast_vote(db: Session, voter_real_id: str, election_id: int, candidate_id: int):
    hashed = hash_voter_id(voter_real_id)

    # Start transaction implicitly via session
    try:
        # 1. Verify Voter exists
        voter = db.query(Voter).filter(Voter.hashed_id == hashed).first()
        if not voter:
            raise ValueError("Voter not registered")

        # 2. Verify Election exists
        election = db.query(Election).filter(Election.id == election_id).first()
        if not election:
             raise ValueError("Election not found")

        # 3. Attempt to record participation (Atomic check via Unique Constraint)
        participation = VoterParticipation(voter_id=voter.id, election_id=election_id)
        db.add(participation)
        # Flush to trigger constraint check immediately
        db.flush()

        # 4. Record Vote
        vote = Vote(election_id=election_id, candidate_id=candidate_id)
        audit = AuditLog(action="VOTE_CAST", details=f"Voter {hashed[:8]}... voted in Election {election_id}")

        db.add(vote)
        db.add(audit)

        # Commit transaction - this ensures atomicity
        db.commit()
        db.refresh(vote)
        return vote

    except IntegrityError:
        db.rollback()
        raise ValueError("Voter has already voted in this election")
    except Exception as e:
        db.rollback()
        raise e

def tally_votes(db: Session, election_id: int):
    results = db.query(Vote.candidate_id, func.count(Vote.id)).filter(Vote.election_id == election_id).group_by(Vote.candidate_id).all()

    # Format result: {candidate_name: count}
    tally = {}
    for cand_id, count in results:
        candidate = db.query(Candidate).filter(Candidate.id == cand_id).first()
        if candidate:
            tally[candidate.name] = count

    return tally
