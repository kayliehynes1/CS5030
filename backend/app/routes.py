from typing import List
from fastapi import APIRouter, HTTPException
from .data import BOOKINGS, ROOMS, USERS, Booking, Room, User

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple heartbeat endpoint for uptime monitoring."""
    return {"status": "ok"}


@router.get("/users", response_model=List[User])
def list_users() -> List[User]:
    """Return the list of users in the system."""
    return USERS


@router.get("/rooms", response_model=List[Room])
def list_rooms() -> List[Room]:
    """Return all rooms and their facilities."""
    return ROOMS


@router.get("/bookings", response_model=List[Booking])
def list_bookings() -> List[Booking]:
    """Return the current in-memory bookings."""
    return BOOKINGS


def _booking_index(booking_id: int) -> int:
    for idx, booking in enumerate(BOOKINGS):
        if booking.id == booking_id:
            return idx
    raise HTTPException(status_code=404, detail="Booking not found")


@router.post("/bookings", response_model=Booking, status_code=201)
def create_booking(booking: Booking) -> Booking:
    if any(existing.id == booking.id for existing in BOOKINGS):
        raise HTTPException(status_code=409, detail="Booking with that ID already exists")
    BOOKINGS.append(booking)
    return booking


@router.put("/bookings/{booking_id}", response_model=Booking)
def update_booking(booking_id: int, booking: Booking) -> Booking:
    idx = _booking_index(booking_id)
    updated_booking = booking.copy(update={"id": booking_id})
    BOOKINGS[idx] = updated_booking
    return updated_booking


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: int) -> None:
    idx = _booking_index(booking_id)
    del BOOKINGS[idx]

