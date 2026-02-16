# Semiconductor Manufacturing System (Wafer Fab)

A proof-of-concept for a Semiconductor Manufacturing Execution System (MES), Statistical Process Control (SPC), and Equipment Engineering (EE) system.

## Modules

- **MES (backend/main.py):** Lot tracking (Move In/Out), Recipe Management, Equipment Status.
- **SPC (backend/spc.py):** Process capability (Cp/Cpk), Control charts (Xbar-R).
- **Equipment Engineering (backend/simulator.py):** Simulated SECS/GEM data streams, Fault Detection (FDC).
- **Frontend (frontend/):** React + Vite dashboard for real-time visualization.

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
