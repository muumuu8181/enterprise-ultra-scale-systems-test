# Smart City Urban OS / Data Integration Platform

This project is a scaffold for a scalable Smart City Data Integration Platform. It is designed to handle high-volume sensor data, integrate diverse urban services, and provide APIs for citizen applications.

## Architecture

The system follows a **Microservices Architecture** with an Event-Driven backbone (MQTT/Kafka).

### Core Components

1.  **IoT Edge / Data Collection**: Simulated sensors (Traffic Cameras, Signals, Environmental monitors) pushing data to the edge.
2.  **Message Broker**: MQTT (Mosquitto) for lightweight IoT messaging.
3.  **Data Ingestion Service**: Subscribes to raw sensor streams, validates data against schemas, and persists to the Data Lake.
4.  **Data Lake**: Centralized storage for raw and processed data (simulated with local file storage for this PoC).
5.  **Urban API Gateway**: REST API (FastAPI) providing unified access to data for dashboards and external apps.

## Directory Structure

- `services/`: Microservices for different domains.
    - `traffic-collector/`: Simulates traffic sensors.
    - `data-ingestion/`: Handles data intake and storage.
    - `urban-api/`: Exposes data via HTTP.
- `shared/`: Shared libraries and schemas.
- `data/`: Local storage for the Data Lake.

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.9+

### Running the System

```bash
docker-compose up --build
```
