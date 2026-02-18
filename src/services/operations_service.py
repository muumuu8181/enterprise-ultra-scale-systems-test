from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from src.models.airport_models import Flight, Gate, GateAssignment, FlightStatus, GateStatus

async def assign_gate(flight_id: int, session: AsyncSession) -> Optional[Gate]:
    """
    Assigns an available gate to a flight.
    """
    # 1. Get the flight
    result = await session.execute(select(Flight).where(Flight.id == flight_id))
    flight = result.scalar_one_or_none()
    if not flight:
        return None

    # 2. Find an available gate
    # Simplified logic: just pick the first available gate
    result = await session.execute(select(Gate).where(Gate.status == GateStatus.AVAILABLE))
    available_gate = result.scalars().first()

    if available_gate:
        # 3. Assign
        flight.gate_id = available_gate.id
        available_gate.status = GateStatus.OCCUPIED
        available_gate.assigned_flight_id = flight.id
        await session.commit()
        await session.refresh(flight)
        return available_gate

    return None

async def optimize_gate_allocation(day: date, session: AsyncSession) -> List[GateAssignment]:
    """
    Optimizes gate allocation for a given day.
    This is a placeholder for a complex optimization algorithm.
    """
    # Get all flights for the day
    start_of_day = datetime.combine(day, datetime.min.time())
    end_of_day = datetime.combine(day, datetime.max.time())

    result = await session.execute(
        select(Flight).where(Flight.scheduled_dep >= start_of_day, Flight.scheduled_dep <= end_of_day)
    )
    flights = result.scalars().all()

    # Get all gates
    result = await session.execute(select(Gate))
    gates = result.scalars().all()

    assignments = []

    # Dummy allocation logic
    gate_iterator = iter(gates)
    for flight in flights:
        try:
            gate = next(gate_iterator)
            assignments.append(GateAssignment(
                gate_id=gate.id,
                flight_id=flight.id,
                assigned_time=flight.scheduled_dep
            ))
        except StopIteration:
            # Reset iterator or handle unassigned
            gate_iterator = iter(gates)
            if gates:
                gate = next(gate_iterator)
                assignments.append(GateAssignment(
                    gate_id=gate.id,
                    flight_id=flight.id,
                    assigned_time=flight.scheduled_dep
                ))

    return assignments

async def calculate_on_time_performance(airline: str, period: str, session: AsyncSession) -> float:
    """
    Calculates on-time performance for an airline over a period.
    Period format: 'YYYY-MM' or 'YYYY-MM-DD' (simplified)
    """
    # Parse period (simplified)
    # Assume period is a month for now

    query = select(func.count(Flight.id)).where(Flight.airline == airline)

    total_result = await session.execute(query)
    total_flights = total_result.scalar() or 0

    if total_flights == 0:
        return 0.0

    on_time_query = query.where(Flight.status == FlightStatus.ON_TIME)
    on_time_result = await session.execute(on_time_query)
    on_time_flights = on_time_result.scalar() or 0

    return (on_time_flights / total_flights) * 100.0
