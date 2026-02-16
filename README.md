# Convenience Store POS & Management System (MVP)

This project implements the core architecture for a large-scale POS system, featuring Edge Computing (Store System) and Cloud (HQ System) with real-time synchronization and AI forecasting.

## Architecture

*   **`hq_system/`**: Central Head Office system.
    *   Manages Master Data (Products).
    *   Aggregates Sales from all stores.
    *   AI Demand Forecasting.
*   **`store_system/`**: Edge Store system.
    *   POS (Point of Sale) functionality.
    *   Offline-first architecture (local SQLite).
    *   Background Sync Worker to push data to HQ.
*   **`shared/`**: Common data models and utilities.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the System

You need to run three components:

1.  **HQ System** (Port 8000):
    ```bash
    uvicorn hq_system.main:app --host 0.0.0.0 --port 8000
    ```

2.  **Store System** (Port 8001):
    ```bash
    uvicorn store_system.main:app --host 0.0.0.0 --port 8001
    ```

3.  **Sync Worker**:
    ```bash
    python -m store_system.sync_worker
    ```
    *Note: Ensure HQ is running on port 8000.*

## Usage Example

1.  **Create Product (HQ):**
    `POST http://localhost:8000/products`
    ```json
    {"jan_code": "123", "name": "Onigiri", "price": 150}
    ```

2.  **Sync Product to Store:**
    (For MVP, manually create in Store or assume sync)
    `POST http://localhost:8001/products`
    ```json
    {"jan_code": "123", "name": "Onigiri", "price": 150}
    ```

3.  **POS Checkout (Store):**
    `POST http://localhost:8001/pos/checkout`
    ```json
    {
      "store_id": "store_001",
      "payment_method": "cash",
      "items": [{"product_id": 1, "quantity": 2}]
    }
    ```

4.  **Sync:**
    The Sync Worker will automatically push the sale to HQ within 10 seconds.

5.  **Check Forecast (HQ):**
    `GET http://localhost:8000/forecast/Onigiri`

## Testing

Run the integration suite:
```bash
python -m pytest tests/test_integration.py
```
