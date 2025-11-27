# University Room Booking System

Room booking system for CS5030 coursework. Built with Python, FastAPI, and Tkinter.

## Requirements

- Python 3.11+
- pip

## Quick Start

### 1. Install dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd "../front end"
pip install -r requirements.txt
```

### 2. Run the application

Terminal 1 (backend):
```bash
cd backend
python3.11 run.py
```

Terminal 2 (frontend):
```bash
cd "front end"
python3.11 main.py
```

## Test Accounts

| Role    | Email                           | Password      |
|---------|--------------------------------|---------------|
| Student | alicejohnson@st-andrews.ac.uk  | password123   |
| Staff   | chloesmith@st-andrews.ac.uk    | password2025  |

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## API Documentation

With the backend running, visit `http://localhost:8000/docs`

## Project Structure

```
CS5030/
├── backend/
│   ├── app/
│   │   ├── auth.py           # JWT authentication
│   │   ├── data.py           # Data models
│   │   ├── routes.py         # API endpoints
│   │   ├── storage.py        # JSON persistence
│   │   ├── validation.py     # Input validation
│   │   └── services/         # Business logic
│   ├── tests/                # Unit and integration tests
│   ├── run.py
│   └── requirements.txt
├── front end/
│   ├── main.py               # GUI entry point
│   ├── auth_manager.py       # Login/registration
│   ├── dashboard.py          # Main interface
│   ├── api_client.py         # Backend API client
│   └── requirements.txt
└── README.md
```

## Troubleshooting

**Port 8000 in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Tkinter issues on macOS:**
Use Python 3.11 from Homebrew: `brew install python@3.11`
