"""
Input validation utilities for the Room Booking System.

Provides centralized validation for:
- Email format
- String lengths
- Password requirements
- Date/time formats
"""
import re
from fastapi import HTTPException

# Validation constants
MAX_NAME_LENGTH = 100
MAX_TITLE_LENGTH = 200
MAX_NOTES_LENGTH = 2000
MAX_EMAIL_LENGTH = 254
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
VALID_ROLES = ["attendee", "organiser"]
ROLE_ALIASES = {
    "student": "attendee",  # backwards compatibility with earlier iteration
}

# Email regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_email(email: str) -> str:
    """
    Validate email format and length.
    
    Args:
        email: Email address to validate
        
    Returns:
        Cleaned email (lowercase, stripped)
        
    Raises:
        HTTPException: If email is invalid
    """
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    email = email.strip().lower()
    
    if len(email) > MAX_EMAIL_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Email must be at most {MAX_EMAIL_LENGTH} characters"
        )
    
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=400, 
            detail="Invalid email format"
        )
    
    return email


def validate_name(name: str, field_name: str = "Name") -> str:
    """
    Validate a name field (user name, room name, etc.).
    
    Args:
        name: Name string to validate
        field_name: Field name for error messages
        
    Returns:
        Cleaned name (stripped)
        
    Raises:
        HTTPException: If name is invalid
    """
    if not name:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    
    name = name.strip()
    
    if len(name) < 2:
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name} must be at least 2 characters"
        )
    
    if len(name) > MAX_NAME_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name} must be at most {MAX_NAME_LENGTH} characters"
        )
    
    return name


def validate_title(title: str) -> str:
    """
    Validate a booking title.
    
    Args:
        title: Title string to validate
        
    Returns:
        Cleaned title (stripped)
        
    Raises:
        HTTPException: If title is invalid
    """
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    title = title.strip()
    
    if len(title) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Title must be at least 3 characters"
        )
    
    if len(title) > MAX_TITLE_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Title must be at most {MAX_TITLE_LENGTH} characters"
        )
    
    return title


def validate_notes(notes: str | None) -> str | None:
    """
    Validate optional notes field.
    
    Args:
        notes: Notes string to validate (can be None)
        
    Returns:
        Cleaned notes or None
        
    Raises:
        HTTPException: If notes exceed length limit
    """
    if not notes:
        return None
    
    notes = notes.strip()
    
    if len(notes) > MAX_NOTES_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Notes must be at most {MAX_NOTES_LENGTH} characters"
        )
    
    return notes if notes else None


def validate_password(password: str) -> str:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        The password (unchanged)
        
    Raises:
        HTTPException: If password is invalid
    """
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    
    if len(password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
        )
    
    return password


def validate_role(role: str) -> str:
    """
    Validate user role into the two supported classes:
    - attendee
    - organiser
    """
    if not role:
        return "attendee"
    
    role = role.strip().lower()
    normalized_role = ROLE_ALIASES.get(role, role)
    
    if normalized_role not in VALID_ROLES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )
    
    return normalized_role


def sanitize_string(value: str | None) -> str | None:
    """
    Basic sanitization for string inputs.
    Removes null bytes and excessive whitespace.
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string or None
    """
    if value is None:
        return None
    
    # Remove null bytes (security measure)
    value = value.replace('\x00', '')
    
    # Normalize whitespace
    value = ' '.join(value.split())
    
    return value if value else None
