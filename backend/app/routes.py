from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta

from .data import (
    BOOKINGS,
    ROOMS,
    USERS,
    Booking,
    Room,
    PublicUser,
    CreateBookingRequest,
    User,
    BookingResponse, 
)
from .auth import (
    get_current_user, 
    LoginRequest, 
    LoginResponse, 
    RegisterRequest,
    create_access_token, 
    verify_password,
    hash_password
)

router = APIRouter(prefix="/api") 


# Helper function to transform Booking to BookingResponse
def booking_to_response(booking: Booking, current_user: User) -> BookingResponse:
    """
    Transform a Booking object to BookingResponse format for frontend.
    Includes computed fields like room_name, current_attendees, is_organizer.
    """
    # Find the room to get name and capacity
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    room_name = room.name if room else "Unknown Room"
    capacity = room.capacity if room else 0
    
    # Calculate current attendees (attendees + organizer)
    current_attendees = len(booking.attendee_ids) + 1
    
    # Check if current user is the organizer
    is_organizer = booking.organiser_id == current_user.id
    
    return BookingResponse(
        id=booking.id,
        title=booking.title,
        room_name=room_name,
        date=booking.start_time.strftime("%Y-%m-%d"),
        start_time=booking.start_time.strftime("%H:%M"),
        end_time=booking.end_time.strftime("%H:%M"),
        current_attendees=current_attendees,
        capacity=capacity,
        is_organizer=is_organizer,
        status=booking.status,
        notes=booking.notes
    )


@router.get("/health")
def health_check() -> dict[str, str]:
    """Simple heartbeat endpoint for uptime monitoring."""
    return {"status": "ok"}

@router.post("/auth/register", response_model=LoginResponse, status_code=201)
def register(data: RegisterRequest) -> LoginResponse:
    """Create a new user account."""
    
    # Check if email already exists
    if any(u.email == data.email for u in USERS):
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Create new user with hashed password
    next_id = max([user.id for user in USERS] + [0]) + 1
    new_user = User(
        id=next_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role or "Student",
        failed_attempts=0,
        locked_until=None
    )
    USERS.append(new_user)
    
    # Create JWT token
    token = create_access_token(new_user.id, new_user.email)
    
    return LoginResponse(
        token=token,
        user={
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }
    )

@router.post("/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest) -> LoginResponse:
    """
    Authenticate user and return JWT token
    
    Returns token and user info on success, 401 on failure
    """
    # Find user by email
    user = next((u for u in USERS if u.email == credentials.email), None)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if account is locked (NFR-3.3)
    if user.locked_until and user.locked_until > datetime.now():
        raise HTTPException(
            status_code=423, 
            detail=f"Account locked until {user.locked_until.strftime('%H:%M:%S')}"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        # Increment failed attempts
        user.failed_attempts += 1
        
        # Lock account after 3 failed attempts (NFR-3.3)
        if user.failed_attempts >= 3:
            user.locked_until = datetime.now() + timedelta(minutes=15)
            raise HTTPException(
                status_code=423, 
                detail="Account locked for 15 minutes after 3 failed attempts"
            )
        
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Reset failed attempts on successful login
    user.failed_attempts = 0
    user.locked_until = None
    
    # Create JWT token
    token = create_access_token(user.id, user.email)
    
    # Return response
    return LoginResponse(
        token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role, 
        }
    )


@router.get("/users", response_model=List[PublicUser])
def list_users(current_user: User = Depends(get_current_user)) -> List[PublicUser]:
    """Return the list of users (safe public version)."""
    return [PublicUser(id=u.id, name=u.name, email=u.email) for u in USERS]


@router.get("/rooms", response_model=List[Room])
def list_rooms(current_user: User = Depends(get_current_user)) -> List[Room]:
    """Return all rooms and their facilities."""
    return ROOMS


# NEW: Get available rooms endpoint
@router.get("/rooms/available", response_model=List[Room])
def get_available_rooms(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    start_time: str = Query(..., description="Start time in HH:MM format"),
    end_time: str = Query(..., description="End time in HH:MM format"),
    current_user: User = Depends(get_current_user)
) -> List[Room]:
    """
    Return rooms available for the specified date and time range.
    Checks for conflicts with existing bookings.
    """
    # Parse the date and time
    try:
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        start_dt = datetime.strptime(start_time, "%H:%M").time()
        end_dt = datetime.strptime(end_time, "%H:%M").time()
        start = datetime.combine(booking_date, start_dt)
        end = datetime.combine(booking_date, end_dt)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")
    
    # Find rooms that don't have conflicting bookings
    available_rooms = []
    for room in ROOMS:
        is_available = True
        for booking in BOOKINGS:
            if booking.room_id == room.id:
                # Check for overlap
                if start < booking.end_time and end > booking.start_time:
                    is_available = False
                    break
        
        if is_available:
            available_rooms.append(room)
    
    return available_rooms


@router.get("/bookings/upcoming", response_model=List[BookingResponse])
def get_upcoming_bookings(current_user: User = Depends(get_current_user)) -> List[BookingResponse]:
    """Return upcoming bookings for the current user (as organiser or attendee)."""
    now = datetime.now()
    user_bookings = [
        b for b in BOOKINGS
        if (b.organiser_id == current_user.id or current_user.id in b.attendee_ids)
        and b.start_time > now
    ]
    sorted_bookings = sorted(user_bookings, key=lambda b: b.start_time)
    
    # Transform to BookingResponse format
    return [booking_to_response(b, current_user) for b in sorted_bookings]


# NEW: Get organized bookings endpoint
@router.get("/bookings/organized", response_model=List[BookingResponse])
def get_organized_bookings(current_user: User = Depends(get_current_user)) -> List[BookingResponse]:
    """Return bookings organized by the current user."""
    organized = [b for b in BOOKINGS if b.organiser_id == current_user.id]
    sorted_bookings = sorted(organized, key=lambda b: b.start_time)
    
    # Transform to BookingResponse format
    return [booking_to_response(b, current_user) for b in sorted_bookings]


# NEW: Get user profile endpoint
@router.get("/user/profile")
def get_user_profile(current_user: User = Depends(get_current_user)) -> dict:
    """Return the current user's profile information."""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


def _booking_index(booking_id: int) -> int:
    """Return index of booking or raise 404."""
    for idx, booking in enumerate(BOOKINGS):
        if booking.id == booking_id:
            return idx
    raise HTTPException(status_code=404, detail="Booking not found")


def overlaps(a_start, a_end, b_start, b_end) -> bool:
    """Check if two time ranges overlap."""
    return a_start < b_end and b_start < a_end


@router.post("/bookings", response_model=BookingResponse, status_code=201)
def create_booking(
    req: CreateBookingRequest,
    current_user: User = Depends(get_current_user)
) -> BookingResponse:
    """
    Create a new booking with validation:
    - Date/time parsing and validation
    - Room existence check
    - Capacity validation (FR-2.8)
    - Availability check (FR-2.11)
    - Permission checks
    """

    # --- 1. Parse date + time into proper datetime objects ---
    try:
        booking_date = datetime.strptime(req.date, "%Y-%m-%d").date()
        start_dt = datetime.strptime(req.start_time, "%H:%M").time()
        end_dt = datetime.strptime(req.end_time, "%H:%M").time()
        start = datetime.combine(booking_date, start_dt)
        end = datetime.combine(booking_date, end_dt)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time.")

    # Validate time range
    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    # Validate not in the past
    if start < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book in the past.")

    # --- 2. Check the room exists ---
    room = next((r for r in ROOMS if r.id == req.room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found.")

    # --- 3. Convert attendee emails -> user IDs ---
    attendee_ids = []
    invalid_emails = []
    for email in req.attendee_emails:
        user = next((u for u in USERS if u.email == email), None)
        if user:
            attendee_ids.append(user.id)
        else:
            invalid_emails.append(email)
    
    if invalid_emails:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid attendee emails: {', '.join(invalid_emails)}"
        )

    # Capacity check (including organiser) - FR-2.8
    total_people = len(attendee_ids) + 1  # +1 for organiser
    if total_people > room.capacity:
        raise HTTPException(
            status_code=400, 
            detail=f"Room capacity is {room.capacity}, but {total_people} people specified."
        )

    # --- 4. Availability check - FR-2.11 ---
    for b in BOOKINGS:
        if b.room_id == req.room_id and overlaps(start, end, b.start_time, b.end_time):
            raise HTTPException(
                status_code=409, 
                detail=f"Room already booked from {b.start_time.strftime('%H:%M')} to {b.end_time.strftime('%H:%M')}."
            )

    # --- 5. Create new booking ID ---
    new_id = max((b.id for b in BOOKINGS), default=0) + 1

    # --- 6. Create final Booking object ---
    new_booking = Booking(
        id=new_id,
        room_id=req.room_id,
        organiser_id=current_user.id,
        attendee_ids=attendee_ids,
        title=req.title,
        notes=req.notes,
        start_time=start,
        end_time=end,
        visibility=req.visibility,
        status="confirmed",
    )

    BOOKINGS.append(new_booking)
    
    # Return transformed response
    return booking_to_response(new_booking, current_user)


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    req: CreateBookingRequest,
    current_user: User = Depends(get_current_user)
) -> BookingResponse:
    """
    Update a booking (organiser-only).
    Revalidates all constraints.
    """

    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]

    # Permission check - FR-2.15
    if booking.organiser_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the organiser can modify this booking.")

    # Parse and validate date/time
    try:
        booking_date = datetime.strptime(req.date, "%Y-%m-%d").date()
        start_dt = datetime.strptime(req.start_time, "%H:%M").time()
        end_dt = datetime.strptime(req.end_time, "%H:%M").time()
        start = datetime.combine(booking_date, start_dt)
        end = datetime.combine(booking_date, end_dt)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format.")

    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    # Convert attendee emails to IDs
    attendee_ids = []
    invalid_emails = []
    for email in req.attendee_emails:
        user = next((u for u in USERS if u.email == email), None)
        if user:
            attendee_ids.append(user.id)
        else:
            invalid_emails.append(email)
    
    if invalid_emails:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid attendee emails: {', '.join(invalid_emails)}"
        )

    # Check room exists
    room = next((r for r in ROOMS if r.id == req.room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found.")

    # Capacity check
    total_people = len(attendee_ids) + 1
    if total_people > room.capacity:
        raise HTTPException(
            status_code=400, 
            detail=f"Room capacity is {room.capacity}, but {total_people} people specified."
        )

    # Availability check (exclude current booking)
    for b in BOOKINGS:
        if b.id != booking.id and b.room_id == req.room_id and overlaps(start, end, b.start_time, b.end_time):
            raise HTTPException(
                status_code=409, 
                detail=f"Room already booked from {b.start_time.strftime('%H:%M')} to {b.end_time.strftime('%H:%M')}."
            )

    # Update booking
    updated_booking = booking.copy(update={
        "room_id": req.room_id,
        "attendee_ids": attendee_ids,
        "title": req.title,
        "notes": req.notes,
        "start_time": start,
        "end_time": end,
        "visibility": req.visibility,
    })

    BOOKINGS[idx] = updated_booking
    
    # Return transformed response
    return booking_to_response(updated_booking, current_user)


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete a booking – organisers only (FR-2.16)."""
    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]

    # Permission check
    if booking.organiser_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the organiser can delete this booking.")

    del BOOKINGS[idx]

# ============================================================================
# INVITATION ENDPOINTS
# ============================================================================

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking_details(
    booking_id: int,
    current_user: User = Depends(get_current_user)
) -> BookingResponse:
    """
    Get details of a specific booking.
    
    Allows users to view booking information before accepting/declining.
    Privacy: Only organiser, attendees, or public bookings viewable.
    """
    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]
    
    # Privacy check for private bookings
    if booking.visibility == "private":
        # Only organiser and current attendees can view
        is_organiser = current_user.id == booking.organiser_id
        is_attendee = current_user.id in booking.attendee_ids
        
        if not (is_organiser or is_attendee):
            raise HTTPException(
                status_code=403, 
                detail="You do not have access to this private booking"
            )
    
    # Return transformed response
    return booking_to_response(booking, current_user)


@router.post("/bookings/{booking_id}/accept", status_code=200)
def accept_invitation(
    booking_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Accept an invitation to a booking (FR-3.1, FR-3.2).
    
    Adds the current user to the booking's attendee list.
    Validates capacity and timing before accepting.
    """
    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]
    
    # Validation 1: Check if already attending
    if current_user.id in booking.attendee_ids:
        raise HTTPException(
            status_code=400, 
            detail="You are already registered for this booking"
        )
    
    # Validation 2: Organisers can't join as attendees
    if current_user.id == booking.organiser_id:
        raise HTTPException(
            status_code=400, 
            detail="You are the organiser of this booking"
        )
    
    # Validation 3: Check room capacity (FR-2.8)
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    if room:
        # Count: current attendees + organiser + new person
        total_people = len(booking.attendee_ids) + 1 + 1
        if total_people > room.capacity:
            raise HTTPException(
                status_code=400, 
                detail=f"Booking is at full capacity ({room.capacity} people)"
            )
    
    # Validation 4: Can't join meetings that already started
    if booking.start_time < datetime.now():
        raise HTTPException(
            status_code=400, 
            detail="This booking has already started"
        )
    
    # All validations passed - add user to attendees
    booking.attendee_ids.append(current_user.id)
    
    return {
        "message": "Successfully registered for booking",
        "booking_id": booking_id,
        "booking_title": booking.title,
        "start_time": booking.start_time.isoformat()
    }


@router.post("/bookings/{booking_id}/decline", status_code=200)
def decline_invitation(
    booking_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Decline an invitation or cancel attendance (FR-3.6).
    
    Removes the current user from the booking's attendee list.
    Organisers should use DELETE to cancel the entire booking.
    """
    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]
    
    # Validation 1: Must be attending to decline
    if current_user.id not in booking.attendee_ids:
        raise HTTPException(
            status_code=400, 
            detail="You are not registered for this booking"
        )
    
    # Validation 2: Organisers should delete, not decline
    if current_user.id == booking.organiser_id:
        raise HTTPException(
            status_code=400, 
            detail="Organisers cannot decline their own bookings. Use DELETE /bookings/{id} to cancel."
        )
    
    # Validation 3: Can't cancel after meeting started
    if booking.start_time < datetime.now():
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel attendance after meeting has started"
        )
    
    # All validations passed - remove user from attendees
    booking.attendee_ids.remove(current_user.id)
    
    return {
        "message": "Successfully cancelled your registration",
        "booking_id": booking_id,
        "booking_title": booking.title,
        "removed_at": datetime.now().isoformat()
    }