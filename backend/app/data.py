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
    reminder_sent: bool = False  # Track if 1-hour reminder was sent

class Notification(BaseModel):
    """Notification model for user notifications"""
    id: int
    user_id: int  # Recipient of notification
    type: str  # "booking_cancelled", "invitation_declined", "booking_reminder"
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
    visibility: str = "private"
    attendee_emails: List[str] = []

class CancelBookingRequest(BaseModel):
    """Request model for cancelling a booking with optional reason"""
    reason: Optional[str] = None

class DeclineInvitationRequest(BaseModel):
    """Request model for declining an invitation with optional reason"""
    reason: Optional[str] = None

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
    # Small rooms (1-8 people)
    Room(id=1, name="Study Room 101", capacity=4, facilities=["whiteboard"], building="Library"),
    Room(id=2, name="Tutorial Room A", capacity=6, facilities=["whiteboard", "display"], building="Main Building"),
    Room(id=3, name="Meeting Pod 1", capacity=4, facilities=["video conferencing"], building="Jack Cole Building"),
    Room(id=4, name="Group Study 202", capacity=8, facilities=["whiteboard", "projector"], building="Gateway Building"),
    
    # Medium rooms (10-25 people)
    Room(id=5, name="Seminar Room A", capacity=12, facilities=["projector", "whiteboard", "sound system"], building="Main Building"),
    Room(id=6, name="Collaboration Hub", capacity=15, facilities=["display", "video conferencing", "whiteboard"], building="Jack Cole Building"),
    Room(id=7, name="Teaching Room 301", capacity=20, facilities=["projector", "whiteboard", "document camera"], building="Science Building"),
    Room(id=8, name="Workshop Space", capacity=18, facilities=["whiteboard", "display", "movable furniture"], building="Gateway Building"),
    Room(id=9, name="Computer Lab 1", capacity=25, facilities=["computers", "projector", "whiteboard"], building="Jack Cole Building"),
    
    # Large rooms (30-60 people)
    Room(id=10, name="Lecture Theatre A", capacity=50, facilities=["projector", "sound system", "microphone", "recording"], building="Main Building"),
    Room(id=11, name="Auditorium B", capacity=60, facilities=["projector", "sound system", "microphone", "video conferencing", "recording"], building="Gateway Building"),
    Room(id=12, name="Conference Hall", capacity=40, facilities=["projector", "whiteboard", "sound system", "video conferencing"], building="Main Building"),
    
    # Specialized rooms
    Room(id=13, name="Innovation Lab", capacity=30, facilities=["whiteboard", "display", "video conferencing", "coffee machine"], building="Jack Cole Building"),
    Room(id=14, name="Presentation Studio", capacity=20, facilities=["projector", "recording equipment", "green screen", "sound system"], building="Gateway Building"),
    Room(id=15, name="Board Room", capacity=12, facilities=["display", "video conferencing", "whiteboard", "coffee machine"], building="Main Building"),
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