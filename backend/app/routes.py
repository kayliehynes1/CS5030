from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta

from .storage import save_users, save_bookings, save_notifications

from .data import (
    BOOKINGS,
    ROOMS,
    USERS,
    NOTIFICATIONS,
    Booking,
    Room,
    PublicUser,
    CreateBookingRequest,
    CancelBookingRequest,
    DeclineInvitationRequest,
    User,
    BookingResponse,
    Notification,
    NotificationResponse,
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


def create_notification(user_id: int, notif_type: str, title: str, message: str, booking_id: int = None):
    """Helper function to create and save a notification"""
    new_id = max((n.id for n in NOTIFICATIONS), default=0) + 1
    notification = Notification(
        id=new_id,
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        booking_id=booking_id,
        created_at=datetime.utcnow(),
        is_read=False
    )
    NOTIFICATIONS.append(notification)
    save_notifications(NOTIFICATIONS)
    return notification


def process_booking_reminders():
    """
    Check for bookings starting in 1 hour and create reminder notifications.
    """
    now = datetime.utcnow()
    target_time = now + timedelta(hours=1)
    
    for booking in BOOKINGS:
        # Skip if already sent or not exactly one hour away
        if booking.reminder_sent or booking.start_time != target_time:
            continue
        
        # Get room name and calculate time
        room = next((r for r in ROOMS if r.id == booking.room_id), None)
        room_name = room.name if room else "Unknown Room"
        time_until = booking.start_time - now
        minutes = int(time_until.total_seconds() / 60)
        time_str = booking.start_time.strftime('%H:%M')
        
        # Create reminders for all recipients (organizer + attendees)
        recipients = [booking.organiser_id] + booking.attendee_ids
        
        for user_id in recipients:
            is_organizer = user_id == booking.organiser_id
            message_prefix = "Your meeting" if is_organizer else "Meeting"
            
            create_notification(
                user_id=user_id,
                notif_type="booking_reminder",
                title="Upcoming Meeting Reminder",
                message=f"{message_prefix} '{booking.title}' in {room_name} starts at {time_str} (in 1 hour).",
                booking_id=booking.id
            )
        
        # Mark reminder as sent
        booking.reminder_sent = True
    
    save_bookings(BOOKINGS)


def booking_to_response(booking: Booking, current_user: User) -> BookingResponse:
    """
    Transform a Booking object to BookingResponse format for frontend.
    """
    # Find the room to get name and capacity
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    room_name = room.name if room else "Unknown Room"
    capacity = room.capacity if room else 0
    
    # Calculate current attendees (accepted attendees + organizer, NOT pending)
    current_attendees = len(booking.attendee_ids) + 1
    
    # Check if current user is the organizer
    is_organizer = booking.organiser_id == current_user.id
    
    # Determine invitation status for current user
    invitation_status = None
    if not is_organizer:
        if current_user.id in booking.pending_attendee_ids:
            invitation_status = "pending"
        elif current_user.id in booking.attendee_ids:
            invitation_status = "accepted"
    
    # Get attendee emails (accepted only)
    attendee_emails = [
        user.email for attendee_id in booking.attendee_ids
        if (user := next((u for u in USERS if u.id == attendee_id), None))
    ]
    
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
        notes=booking.notes,
        attendee_emails=attendee_emails,
        invitation_status=invitation_status
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
        role=data.role.lower() if data.role else "student",
        failed_attempts=0,
        locked_until=None
    )
    USERS.append(new_user)
    save_users(USERS)
    
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
    """Authenticate user and return JWT token"""
    # Find user by email
    user = next((u for u in USERS if u.email == credentials.email), None)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=423, 
            detail=f"Account locked until {user.locked_until.strftime('%H:%M:%S')}"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        # Increment failed attempts
        user.failed_attempts += 1
        
        # Lock account after 3 failed attempts
        if user.failed_attempts >= 3:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            save_users(USERS)
            raise HTTPException(
                status_code=423, 
                detail="Account locked for 15 minutes due to too many failed attempts"
            )
        
        save_users(USERS)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Reset failed attempts on successful login
    user.failed_attempts = 0
    user.locked_until = None
    save_users(USERS)
    
    # Create JWT token
    token = create_access_token(user.id, user.email)
    
    return LoginResponse(
        token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
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


@router.get("/rooms/available", response_model=List[Room])
def get_available_rooms(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    start_time: str = Query(..., description="Start time in HH:MM format"),
    end_time: str = Query(..., description="End time in HH:MM format"),
    current_user: User = Depends(get_current_user)
) -> List[Room]:
    """
    Return rooms available for the specified date and time range.
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
    """Return upcoming bookings for the current user (as organiser, accepted attendee, or pending invitee)."""
    now = datetime.utcnow()
    user_bookings = [
        b for b in BOOKINGS
        if (b.organiser_id == current_user.id 
            or current_user.id in b.attendee_ids 
            or current_user.id in b.pending_attendee_ids)
        and b.start_time > now
    ]
    sorted_bookings = sorted(user_bookings, key=lambda b: b.start_time)
    
    return [booking_to_response(b, current_user) for b in sorted_bookings]


@router.get("/bookings/organized", response_model=List[BookingResponse])
def get_organized_bookings(current_user: User = Depends(get_current_user)) -> List[BookingResponse]:
    """Return bookings organized by the current user."""
    organized = [b for b in BOOKINGS if b.organiser_id == current_user.id]
    sorted_bookings = sorted(organized, key=lambda b: b.start_time)
    
    return [booking_to_response(b, current_user) for b in sorted_bookings]


@router.get("/bookings/past", response_model=List[BookingResponse])
def get_past_bookings(current_user: User = Depends(get_current_user)) -> List[BookingResponse]:
    """Return past bookings for the current user (as organizer or accepted attendee)."""
    now = datetime.utcnow()
    user_bookings = [
        b for b in BOOKINGS
        if (b.organiser_id == current_user.id 
            or current_user.id in b.attendee_ids)
        and b.end_time <= now
    ]
    
    # Sort by start time (most recent first)
    user_bookings.sort(key=lambda b: b.start_time, reverse=True)
    
    return [booking_to_response(b, current_user) for b in user_bookings]


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


def _parse_request_times(date_str: str, start_str: str, end_str: str) -> tuple[datetime, datetime]:
    """
    Parse date/time strings into datetimes with basic validation shared by create/update.
    """
    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_date = datetime.strptime(start_str, "%H:%M").time()
        end_date = datetime.strptime(end_str, "%H:%M").time()
        start = datetime.combine(booking_date, start_date)
        end = datetime.combine(booking_date, end_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time.",
        )

    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    if start < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cannot book in the past.")

    return start, end


def _resolve_attendees(attendee_emails: list[str]) -> list[int]:
    """Convert attendee emails to user IDs or raise if any are invalid."""
    attendee_ids: list[int] = []
    invalid_emails: list[str] = []
    for email in attendee_emails:
        user = next((u for u in USERS if u.email == email), None)
        if user:
            attendee_ids.append(user.id)
        else:
            invalid_emails.append(email)

    if invalid_emails:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attendee emails: {', '.join(invalid_emails)}",
        )

    return attendee_ids


def _get_room_or_404(room_id: int) -> Room:
    room = next((r for r in ROOMS if r.id == room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found.")
    return room


def _validate_capacity(room: Room, accepted_count: int, pending_count: int) -> None:
    """Ensure total attendees (accepted + pending + organizer) do not exceed capacity."""
    total_people = accepted_count + pending_count + 1  # +1 organizer
    if total_people > room.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Room capacity is {room.capacity}, but {total_people} people specified.",
        )


def _ensure_room_available(room_id: int, start: datetime, end: datetime, *, exclude_booking_id: int | None = None) -> None:
    """Check availability, optionally excluding a specific booking (for updates)."""
    for booking in BOOKINGS:
        if exclude_booking_id and booking.id == exclude_booking_id:
            continue
        if booking.room_id == room_id and overlaps(start, end, booking.start_time, booking.end_time):
            raise HTTPException(
                status_code=409,
                detail=f"Room already booked from {booking.start_time.strftime('%H:%M')} to {booking.end_time.strftime('%H:%M')}.",
            )


@router.post("/bookings", response_model=BookingResponse, status_code=201)
def create_booking(
    req: CreateBookingRequest,
    current_user: User = Depends(get_current_user)
) -> BookingResponse:
    """
    Create a new booking with validation
    """

    start, end = _parse_request_times(req.date, req.start_time, req.end_time)
    room = _get_room_or_404(req.room_id)
    attendee_ids = _resolve_attendees(req.attendee_emails)
    _validate_capacity(room, accepted_count=0, pending_count=len(attendee_ids))
    _ensure_room_available(req.room_id, start, end)

    # Create new booking ID
    new_id = max((b.id for b in BOOKINGS), default=0) + 1

    # Create final Booking object
    new_booking = Booking(
        id=new_id,
        room_id=req.room_id,
        organiser_id=current_user.id,
        attendee_ids=[], 
        pending_attendee_ids=attendee_ids, 
        title=req.title,
        notes=req.notes,
        start_time=start,
        end_time=end,
        visibility=req.visibility,
        status="confirmed",
        reminder_sent=False
    )

    BOOKINGS.append(new_booking)
    save_bookings(BOOKINGS)
    
    return booking_to_response(new_booking, current_user)


@router.put("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    req: CreateBookingRequest,
    current_user: User = Depends(get_current_user)
) -> BookingResponse:
    """
    Update a booking (organiser-only).
    """

    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]


    start, end = _parse_request_times(req.date, req.start_time, req.end_time)
    new_attendee_ids = _resolve_attendees(req.attendee_emails)
    
    # Separate existing accepted attendees from new invitations
    current_accepted = set(booking.attendee_ids)
    all_requested = set(new_attendee_ids)
    
    # Keep existing accepted attendees
    accepted_attendees = list(current_accepted & all_requested)
    
    # New attendees go to pending (those not currently accepted)
    new_pending = list(all_requested - current_accepted)
    
    # Combine with existing pending (remove duplicates)
    current_pending = set(booking.pending_attendee_ids)
    all_pending = list((current_pending | set(new_pending)) - current_accepted)

    room = _get_room_or_404(req.room_id)
    _validate_capacity(room, accepted_count=len(accepted_attendees), pending_count=len(all_pending))
    _ensure_room_available(req.room_id, start, end, exclude_booking_id=booking.id)

    # Update booking
    updated_booking = booking.copy(update={
        "room_id": req.room_id,
        "attendee_ids": accepted_attendees, 
        "pending_attendee_ids": all_pending,
        "title": req.title,
        "notes": req.notes,
        "start_time": start,
        "end_time": end,
        "visibility": req.visibility,
    })

    BOOKINGS[idx] = updated_booking
    save_bookings(BOOKINGS)
    
    return booking_to_response(updated_booking, current_user)


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    body: CancelBookingRequest = None 
) -> None:
    """
    Delete a booking (organisers only). 
    Optionally accepts a cancellation reason that will be included in notifications.
    """
    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]

    # Get room name for notification
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    room_name = room.name if room else "Unknown Room"
    
    # Get cancellation reason
    reason = body.reason if body and body.reason else None
    reason_text = f"\n\nReason: {reason}" if reason else ""
    
    # Notify all accepted attendees about cancellation
    for attendee_id in booking.attendee_ids:
        create_notification(
            user_id=attendee_id,
            notif_type="booking_cancelled",
            title="Meeting Cancelled",
            message=f"The meeting '{booking.title}' scheduled for {booking.start_time.strftime('%Y-%m-%d at %H:%M')} in {room_name} has been cancelled by the organizer.{reason_text}",
            booking_id=booking.id
        )
    
    # Also notify pending attendees
    for attendee_id in booking.pending_attendee_ids:
        create_notification(
            user_id=attendee_id,
            notif_type="booking_cancelled",
            title="Meeting Invitation Cancelled",
            message=f"Your invitation to '{booking.title}' scheduled for {booking.start_time.strftime('%Y-%m-%d at %H:%M')} in {room_name} has been cancelled.{reason_text}",
            booking_id=booking.id
        )

    del BOOKINGS[idx]
    save_bookings(BOOKINGS)


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
    
    return booking_to_response(booking, current_user)


@router.post("/bookings/{booking_id}/accept", status_code=200)
def accept_invitation(
    booking_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Accept an invitation to a booking.
    """
    idx = _booking_index(booking_id)
    booking = BOOKINGS[idx]
    
    # Validation: Must be in pending invitations
    if current_user.id not in booking.pending_attendee_ids:
        if current_user.id in booking.attendee_ids:
            raise HTTPException(
                status_code=400, 
                detail="You have already accepted this invitation"
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="You don't have a pending invitation to this booking"
            )
    
    
    # Validation: Check room capacity
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    if room:
        # Count: current accepted attendees + organiser + new person
        total_people = len(booking.attendee_ids) + 1 + 1
        if total_people > room.capacity:
            raise HTTPException(
                status_code=400, 
                detail=f"Booking is at full capacity ({room.capacity} people)"
            )
    
    # Validation: Can't join meetings that already started
    if booking.start_time < datetime.utcnow():
        raise HTTPException(
            status_code=400, 
            detail="This booking has already started"
        )
    
    # All validations passed - move from pending to accepted
    booking.pending_attendee_ids.remove(current_user.id)
    booking.attendee_ids.append(current_user.id)
    save_bookings(BOOKINGS)
    
    return {
        "message": "Successfully accepted invitation",
        "booking_id": booking_id,
        "booking_title": booking.title,
        "start_time": booking.start_time.isoformat()
    }


@router.post("/bookings/{booking_id}/decline", status_code=200)
def decline_invitation(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    body: DeclineInvitationRequest = None
) -> dict:
    """
    Decline an invitation or cancel attendance.
    """
    booking = BOOKINGS[_booking_index(booking_id)]
    
    # Determine user's current status
    is_pending = current_user.id in booking.pending_attendee_ids
    is_accepted = current_user.id in booking.attendee_ids
    
    # Validation
    if current_user.id == booking.organiser_id:
        raise HTTPException(400, "Organisers cannot decline. Use DELETE /bookings/{id} to cancel.")
    if is_accepted and booking.start_time < datetime.utcnow():
        raise HTTPException(400, "Cannot cancel after meeting started")
    
    # Prepare notification
    action = "declined the invitation to" if is_pending else "cancelled their attendance for"
    reason_text = f"\n\nReason: {body.reason}" if body and body.reason else ""
    room = next((r for r in ROOMS if r.id == booking.room_id), None)
    room_name = room.name if room else "Unknown Room"
    
    create_notification(
        user_id=booking.organiser_id,
        notif_type="invitation_declined",
        title="Attendee Response",
        message=f"{current_user.name} has {action} your meeting '{booking.title}' "
                f"scheduled for {booking.start_time.strftime('%Y-%m-%d at %H:%M')} "
                f"in {room_name}.{reason_text}",
        booking_id=booking.id
    )
    
    # Remove user from appropriate list
    target_list = booking.pending_attendee_ids if is_pending else booking.attendee_ids
    target_list.remove(current_user.id)
    save_bookings(BOOKINGS)
    
    return {
        "message": "Declined invitation" if is_pending else "Cancelled attendance",
        "booking_id": booking_id,
        "booking_title": booking.title
    }


@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(current_user: User = Depends(get_current_user)) -> List[NotificationResponse]:
    """
    Get all notifications for the current user.
    Also processes any pending booking reminders.
    """
    # Process reminders before returning notifications
    process_booking_reminders()
    
    # Get user's notifications (sorted by most recent first)
    user_notifications = [
        n for n in NOTIFICATIONS 
        if n.user_id == current_user.id
    ]
    user_notifications.sort(key=lambda n: n.created_at, reverse=True)
    
    # Transform to response format
    return [
        NotificationResponse(
            id=n.id,
            type=n.type,
            title=n.title,
            message=n.message,
            booking_id=n.booking_id,
            created_at=n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            is_read=n.is_read
        )
        for n in user_notifications
    ]


@router.get("/notifications/unread/count")
def get_unread_count(current_user: User = Depends(get_current_user)) -> dict:
    """Get count of unread notifications for the current user."""
    # Process reminders first
    process_booking_reminders()
    
    unread_count = sum(
        1 for n in NOTIFICATIONS 
        if n.user_id == current_user.id and not n.is_read
    )
    return {"count": unread_count}


@router.put("/notifications/{notification_id}/read", status_code=200)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Mark a notification as read."""
    # Find notification
    notification = next((n for n in NOTIFICATIONS if n.id == notification_id), None)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Check ownership
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only mark your own notifications as read")
    
    # Mark as read
    notification.is_read = True
    save_notifications(NOTIFICATIONS)
    
    return {"message": "Notification marked as read"}


@router.delete("/notifications/{notification_id}", status_code=204)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete a notification."""
    # Find notification
    for idx, notification in enumerate(NOTIFICATIONS):
        if notification.id == notification_id:
            
            del NOTIFICATIONS[idx]
            save_notifications(NOTIFICATIONS)
            return
    
    raise HTTPException(status_code=404, detail="Notification not found")