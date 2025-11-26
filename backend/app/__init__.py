from fastapi import FastAPI

from .routes import router
from .storage import initialize_storage

app = FastAPI(title="Room Booking API", version="0.1.0")

# Initialize storage on startup
@app.on_event("startup")
def startup_event():
    """Load data from storage on startup"""
    initialize_storage()

app.include_router(router)

__all__ = ["app"]