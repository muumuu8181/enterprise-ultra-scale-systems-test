# Smart Grid Control & Supply/Demand Management System

## Overview
This project aims to develop a comprehensive Smart Grid Control & Supply/Demand Management System for electric power companies. The system is designed to handle complex operations including demand forecasting, generation planning, distribution automation, renewable energy integration, and smart metering.

## Key Modules

### 1. Supply/Demand Management (`smart_grid/supply_demand`)
- **Demand Forecasting**: Integration with weather data (temperature, humidity, solar radiation) and use of machine learning models (LSTM) for 15-minute interval predictions.
- **Generation Planning**: Optimal operation planning for thermal, hydro, nuclear, and renewable energy plants (Economic Load Dispatch).
- **Balancing**: Real-time balancing of generation and demand, frequency control (50Hz/60Hz).
- **Market**: Imbalance calculation and ancillary services.

### 2. Distribution Automation (`smart_grid/distribution`)
- **SCADA**: Grid monitoring and control, smart meter data collection (30-minute intervals).
- **Outage Management**: Automatic fault location, isolation, and service restoration (FLISR).
- **Voltage Control**: Tap changer control at substations, SVC (Static Var Compensator).

### 3. Renewable Energy Integration (`smart_grid/renewables`)
- **Forecasting**: Solar and wind power generation forecasting based on weather data.
- **VPP (Virtual Power Plant)**: Aggregated control of distributed energy resources (DERs), Demand Response (DR).
- **Battery Control**: Optimization of charge/discharge cycles, peak shifting.

### 4. Smart Metering (`smart_grid/smart_meter`)
- **AMI**: Automated collection of 30-minute meter readings.
- **Billing**: Time-of-use (TOU) pricing, seasonal rates, demand charges.
- **Remote Control**: Remote connection/disconnection of service.

## Technical Architecture

- **Real-time OS**: Capabilities for millisecond-level control response.
- **Database**: Time-series database (InfluxDB) capable of handling 1M writes/second.
- **Edge Computing**: Pre-processing at substation level.
- **Security**: ICS (Industrial Control System) security standards, network segmentation.
- **AI/ML**: Python-based models for forecasting and anomaly detection.

## Getting Started

### Prerequisites
- Python 3.8+
- InfluxDB (for time-series data storage)

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Tests
Run the test suite using `pytest`:
```bash
pytest
```
