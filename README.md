# Semiconductor Manufacturing Platform

This platform manages wafer lots, equipment, process steps, and yield analysis.

## Features
- Wafer Lot Tracking
- Equipment Management & Maintenance
- Process Step Logging
- Yield Analysis & Wafer Maps
- Capacity Forecasting

## Tech Stack
- Python (FastAPI, SQLAlchemy)
- PostgreSQL
- Redis
- InfluxDB
- Celery

## API Documentation
The API documentation is available at `/docs` when running the service.

## Getting Started
1. Run `docker-compose up -d` to start the services.
2. The API will be available at `http://localhost:8000`.
