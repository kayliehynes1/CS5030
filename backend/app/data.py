from datetime import datetime, timedelta
from typing import List

from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    name: str
    email: str
    password: str
    role: str


class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    role: str


class Room(BaseModel):
    id: int
    name: str
    capacity: int
    facilities: List[str] = Field(default_factory=list)


class Booking(BaseModel):
    id: int
    room_id: int
    organiser_id: int
    attendee_ids: List[int]
    start_time: datetime
    end_time: datetime


USERS: List[User] = [
    User(id=1, name="Alice Johnson", email="alice@example.com", password="password123", role="organiser"),
    User(id=2, name="Ben Lee", email="ben@example.com", password="password123", role="attendee"),
    User(id=3, name="Chloe Smith", email="chloe@example.com", password="password123", role="attendee"),
]

ROOMS: List[Room] = [
    Room(id=1, name="Seminar Room A", capacity=12, facilities=["projector", "whiteboard"]),
    Room(id=2, name="Collaboration Hub", capacity=8, facilities=["display", "video conferencing"]),
]

_base_time = datetime(2024, 10, 1, 9, 0, 0)
BOOKINGS: List[Booking] = [
    Booking(
        id=1,
        room_id=1,
        organiser_id=1,
        attendee_ids=[2, 3],
        start_time=_base_time,
        end_time=_base_time + timedelta(hours=1),
    ),
    Booking(
        id=2,
        room_id=2,
        organiser_id=1,
        attendee_ids=[2],
        start_time=_base_time + timedelta(hours=2),
        end_time=_base_time + timedelta(hours=3),
    ),
]
