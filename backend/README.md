# Backend

FastAPI server for the room booking system.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python run.py
```

Server starts at `http://localhost:8000`

## API Docs

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
pytest tests/ -v
```
