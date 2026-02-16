# Global Airline Reservation & Operations System

This project is a prototype implementation of a large-scale global airline reservation and operations management system.

## Modules

### Reservation & Ticketing
- Flight Inventory Management
- Booking & PNR Creation
- Fare Calculation (TBD)
- Seat Management (TBD)

### Operations Management
- Flight Scheduling (Basic)

## Tech Stack
- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite (for prototype)
- Pydantic

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn src.app.main:app --reload
   ```
