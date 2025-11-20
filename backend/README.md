# Backend

This repository currently contains the backend for the CS5030 Coursework 2 room booking system. It exposes a minimal FastAPI service with in-memory data.

## What's Included

- `backend/app/data.py` — Pydantic models (`User`, `Room`, `Booking`) and example seed data stored in lists.
- `backend/app/routes.py` — Endpoints for service health, users, rooms, and bookings.
- `backend/app/__init__.py` — FastAPI application factory that wires the router.
- `backend/run.py` — Development entry point that runs Uvicorn with auto-reload.
- `README.md` — Overview and usage instructions.

## Setting up a Virtual Environment

macOS / Linux:

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. Install dependencies inside the environment.

Windows (PowerShell):

1. `python -m venv .venv`
2. `.venv\Scripts\Activate.ps1`
3. Install dependencies inside the environment.

## Running the Server

1. Activate the virtual environment (see above).
2. Install FastAPI and Uvicorn `pip install fastapi uvicorn`.
3. From the project root, run `python backend/run.py`.
4. Visit `http://127.0.0.1:8000/health` to verify the service is running.
