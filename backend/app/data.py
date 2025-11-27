from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
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
    status: str = "confirmed" 
    reminder_sent: bool = False  # Track if 1-hour reminder was sent

class Notification(BaseModel):
    """Notification model for user notifications"""
    id: int
    user_id: int 
    type: str 
    title: str
    message: str
    booking_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False

class CreateBookingRequest(BaseModel):
    room_id: int
    title: str
    date: str
    start_time: str
    end_time: str
    notes: Optional[str] = None
    attendee_emails: List[str] = []

    @field_validator('title')
    def validate_title(cls, v):
        if len(v) > 200:
            raise ValueError("Title must be less than 200 characters")
        return v.strip()
    
    @field_validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 1000:
            raise ValueError("Notes must be less than 1000 characters")
        return v
    
    @field_validator('attendee_emails')
    def validate_attendee_count(cls, v):
        if len(v) > 50:
            raise ValueError("Maximum 50 attendees allowed")
        return v

class CancelBookingRequest(BaseModel):
    """Request model for cancelling a booking with optional reason"""
    reason: Optional[str] = None

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if v and len(v) > 500:
            raise ValueError("Reason must be less than 500 characters")
        return v

class DeclineInvitationRequest(BaseModel):
    """Request model for declining an invitation with optional reason"""
    reason: Optional[str] = None

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v):
        if v and len(v) > 500:
            raise ValueError("Reason must be less than 500 characters")
        return v

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
    attendee_emails: List[str] = Field(default_factory=list)  
    invitation_status: Optional[str] = None  

class NotificationResponse(BaseModel):
    """Notification response for frontend"""
    id: int
    type: str
    title: str
    message: str
    booking_id: Optional[int]
    created_at: str
    is_read: bool

USERS: List[User] = [
    User(id=1, name="Alice Johnson", email="alicejohnson@st-andrews.ac.uk", password_hash=hash_password("password123"), role="student"),
    User(id=2, name="Ben Lee", email="benlee@st-andrews.ac.uk", password_hash=hash_password("password012!"), role="student"),
    User(id=3, name="Chloe Smith", email="chloesmith@st-andrews.ac.uk", password_hash=hash_password("password2025"), role="staff"),
]

ROOMS: List[Room] = [
    Room(id=1, name="Seminar Room A", capacity=12, facilities=["projector", "whiteboard"], building="Main Building"),
    Room(id=2, name="Collaboration Hub", capacity=8, facilities=["display", "video conferencing"], accessibility=["hearing loop"], building="Computer Science Building"),
    Room(id=3, name="Study Room B", capacity=6, facilities=["whiteboard"], accessibility=["wheelchair accessible"],restricted_to=[], building="Library"),
    Room(id=4, name="Faculty Meeting Room", capacity=15, facilities=["projector", "video conferencing", "whiteboard"], accessibility=[],restricted_to=["staff"], building="Admin Building"),
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

# Store notifications
NOTIFICATIONS: List[Notification] = []