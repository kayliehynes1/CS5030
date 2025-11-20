from fastapi import FastAPI

from .routes import router

app = FastAPI(title="Room Booking API", version="0.1.0")
app.include_router(router)

__all__ = ["app"]
