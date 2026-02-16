# Music Streaming Platform (Core)

This repository contains the foundational code for a large-scale music streaming platform. This initial commit focuses on the **Music Management** service, providing core data models and API endpoints.

## Features

- **Music Management**:
  - Artists
  - Albums
  - Tracks (with metadata like ISRC and Duration)
- **API**: RESTful endpoints powered by FastAPI.
- **Database**: Initial SQLite setup for development (SQLAlchemy).

## Architecture & Scalability

- **Currently Implemented**:
  - Synchronous I/O (SQLAlchemy ORM + SQLite).
  - Basic CRUD operations.
- **Planned Roadmap**:
  - **Async I/O**: Migration to `asyncpg` + `aiosqlite` for high concurrency.
  - **Service Separation**: Splitting into microservices (Metadata, Streaming, Auth, Recommendations).
  - **Streaming Core**: Implementing HLS/DASH streaming logic.
  - **DRM Integration**: Integrating FairPlay/Widevine.
  - **Caching**: Redis layer for metadata.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Run tests:
   ```bash
   pytest
   ```
