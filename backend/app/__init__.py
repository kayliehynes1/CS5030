from contextlib import asynccontextmanager
from fastapi import FastAPI

from .routes import router
from .storage import initialize_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - load data on startup"""
    initialize_storage()
    yield


app = FastAPI(title="Room Booking API", version="1.0.0", lifespan=lifespan)
app.include_router(router)

__all__ = ["app"]
