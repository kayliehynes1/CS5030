from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field
from .auth import hash_password


class User(BaseModel):
    id: int
    name: str
    email: str
    role: str
    password_hash: str
    failed_attempts: int = 0 
    locked_until: Optional[datetime] = None

class Room(BaseModel):
    id: int
    name: str
    capacity: int
    facilities: List[str] = Field(default_factory=list)
    accessibility: list[str] = Field(default_factory=list)
    restricted_to: list[str] = Field(default_factory=list)
    building: str


class Booking(BaseModel):
    id: int
    room_id: int
    organiser_id: int
    attendee_ids: List[int] = Field(default_factory=list)  # Accepted attendees
    pending_attendee_ids: List[int] = Field(default_factory=list)  # Pending invitations
    title: str
    notes: Optional[str] = None
    start_time: datetime
    end_time: datetime
    visibility: str = "private" 
    status: str = "confirmed" 

class CreateBookingRequest(BaseModel):
    room_id: int
    title: str
    date: str
    start_time: str
    end_time: str
    notes: Optional[str] = None
    visibility: str = "private"
    attendee_emails: List[str] = []

class PublicUser(BaseModel):
    id: int
    name: str
    email: str

class BookingResponse(BaseModel):
    """Booking response formatted for frontend"""
    id: int
    title: str
    room_name: str
    date: str  
    start_time: str 
    end_time: str  
    current_attendees: int
    capacity: int
    is_organizer: bool
    status: str
    notes: Optional[str] = None
    attendee_emails: List[str] = Field(default_factory=list)  # Added for showing attendees
    invitation_status: Optional[str] = None  # "pending", "accepted", or None (if organizer)

USERS: List[User] = [
    User(id=1, name="Alice Johnson", email="alicejohnson@st-andrews.ac.uk", password_hash=hash_password("password123"), role="student"),
    User(id=2, name="Ben Lee", email="benlee@st-andrews.ac.uk", password_hash=hash_password("password012!"), role="student"),
    User(id=3, name="Chloe Smith", email="chloesmith@st-andrews.ac.uk", password_hash=hash_password("password2025"), role="staff"),
]

ROOMS: List[Room] = [
    Room(id=1, name="Seminar Room A", capacity=12, facilities=["projector", "whiteboard"], building="Main Building"),
    Room(id=2, name="Collaboration Hub", capacity=8, facilities=["display", "video conferencing"], building="Jack Cole Building"),
]

_base_time = datetime(2025, 1, 15, 9, 0, 0)
BOOKINGS: List[Booking] = [
    Booking(
        id=1,
        room_id=1,
        organiser_id=1,
        attendee_ids=[2, 3],
        title="Team Sync",
        start_time=_base_time,
        end_time=_base_time + timedelta(hours=1),
    ),
    Booking(
        id=2,
        room_id=2,
        organiser_id=1,
        attendee_ids=[2],
        title="Planning Session",
        start_time=_base_time + timedelta(hours=2),
        end_time=_base_time + timedelta(hours=3),
    ),
]