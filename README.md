# Construction Project Management System

This is a large-scale Project Management and Cost Control System for construction companies.
The system is built with a scalable architecture using **Django** (Backend) and **React** (Frontend).

## Architecture

- **Backend:** Django 4.2 + Django REST Framework (DRF)
  - Modular Apps: `core`, `projects`, `costs`, `safety`, `quality`
  - Database: SQLite (dev) -> PostgreSQL (prod)
- **Frontend:** React + TypeScript + Vite
  - UI Library: Material UI
  - State Management: React Hooks

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+

### Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the server:
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://localhost:8000/api/`.

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The application will run at `http://localhost:5173`.

## Modules & Roadmap

- **Project Management:**
  - [x] Project List & Details (Implemented)
  - [ ] Gantt Chart & Critical Path
  - [ ] Progress Tracking

- **Cost Control:**
  - [ ] Budgeting
  - [ ] Expense Tracking
  - [ ] Payment Management

- **Safety & Quality:**
  - [ ] Safety Patrol Reports
  - [ ] Quality Inspection Records

- **Technical:**
  - [ ] BIM Integration
  - [ ] IoT Sensor Data
  - [ ] Drone Imagery Analysis

## API Documentation

- `GET /api/projects/`: List all projects.
- `POST /api/projects/`: Create a new project.
- `GET /api/projects/{id}/`: Retrieve project details.
