from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .data import BOOKINGS, ROOMS, USERS, Booking, Room, User, UserPublic

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "attendee"


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple heartbeat endpoint for uptime monitoring."""
    return {"status": "ok"}


@router.get("/users", response_model=List[UserPublic])
def list_users() -> List[UserPublic]:
    """Return the list of users in the system."""
    return [UserPublic(**user.dict(exclude={"password"})) for user in USERS]


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


@router.post("/auth/login", response_model=AuthResponse)
def login(auth: AuthRequest) -> AuthResponse:
    """Authenticate by email and password."""
    for user in USERS:
        if user.email == auth.email and user.password == auth.password:
            token = f"token-{user.id}"
            return AuthResponse(token=token, user=UserPublic(**user.dict(exclude={"password"})))
    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(data: RegisterRequest) -> AuthResponse:
    """Create a new user account."""
    if any(u.email == data.email for u in USERS):
        raise HTTPException(status_code=409, detail="Email already registered")

    next_id = max([user.id for user in USERS] + [0]) + 1
    new_user = User(
        id=next_id,
        name=data.name,
        email=data.email,
        password=data.password,
        role=data.role or "attendee",
    )
    USERS.append(new_user)
    token = f"token-{new_user.id}"
    return AuthResponse(token=token, user=UserPublic(**new_user.dict(exclude={"password"})))
