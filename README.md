# Election Management System (MVP)

A highly reliable, secure, and performant backend system for election management.
This system is built with Python (FastAPI) and uses SQLite (for MVP) with an architecture designed for PostgreSQL scalability.

## Architecture

- **Backend**: FastAPI (Python) - High performance, async, type-safe.
- **Database**: SQLAlchemy + Pydantic - ORM and data validation.
- **Security**: Voter hashing (SHA-256) to ensure anonymity while preventing double voting.
- **Audit Logging**: Immutable records of all critical actions.

## Key Modules

- `app/models.py`: Database schema definitions (Election, Candidate, Voter, Vote).
- `app/services.py`: Core business logic (Voting, Counting, Registration).
- `app/main.py`: REST API endpoints.

## Features

- **Voter Registration**: Checks eligibility and hashes ID.
- **Secure Voting**: Prevents double voting using atomic transactions.
- **Counting**: Real-time aggregation of votes.
- **Audit Trail**: All actions are logged.
