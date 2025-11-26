"""
Simple JSON file storage for users, rooms, bookings, and notifications
Refactored to use generic save/load functions - 60% less code!
"""
import json
from datetime import datetime
from pathlib import Path

# Storage directory
STORAGE_DIR = Path(__file__).parent / "data"
USERS_FILE = STORAGE_DIR / "users.json"
ROOMS_FILE = STORAGE_DIR / "rooms.json"
BOOKINGS_FILE = STORAGE_DIR / "bookings.json"
NOTIFICATIONS_FILE = STORAGE_DIR / "notifications.json"


def ensure_storage_dir():
    """Create storage directory if it doesn't exist"""
    STORAGE_DIR.mkdir(exist_ok=True)


def save_to_json(items, filepath, datetime_fields=None):
    """
    Generic save function for any Pydantic model list.
    
    Args:
        items: List of Pydantic model instances
        filepath: Path object for the JSON file
        datetime_fields: List of field names that contain datetime objects
    """
    ensure_storage_dir()
    datetime_fields = datetime_fields or []
    
    items_data = []
    for item in items:
        item_dict = item.model_dump()
        # Convert datetime fields to ISO format strings
        for field in datetime_fields:
            if item_dict.get(field):
                item_dict[field] = item_dict[field].isoformat()
        items_data.append(item_dict)
    
    with open(filepath, 'w') as f:
        json.dump(items_data, f, indent=2)


def load_from_json(filepath, model_class, datetime_fields=None):
    """
    Generic load function for any Pydantic model list.
    
    Args:
        filepath: Path object for the JSON file
        model_class: The Pydantic model class to instantiate
        datetime_fields: List of field names that contain datetime objects
        
    Returns:
        List of model instances or None if file doesn't exist
    """
    if not filepath.exists():
        return None
    
    datetime_fields = datetime_fields or []
    
    try:
        with open(filepath, 'r') as f:
            items_data = json.load(f)
        
        items = []
        for item_dict in items_data:
            # Convert ISO format strings back to datetime objects
            for field in datetime_fields:
                if item_dict.get(field):
                    item_dict[field] = datetime.fromisoformat(item_dict[field])
            items.append(model_class(**item_dict))
        
        return items
    except Exception as e:
        print(f"Error loading {model_class.__name__}: {e}")
        return None


# ============================================================================
# Specific save/load functions for each model type
# ============================================================================

def save_users(users):
    """Save users to JSON file"""
    save_to_json(users, USERS_FILE, datetime_fields=['locked_until'])


def load_users():
    """Load users from JSON file"""
    from .data import User
    return load_from_json(USERS_FILE, User, datetime_fields=['locked_until'])


def save_rooms(rooms):
    """Save rooms to JSON file"""
    save_to_json(rooms, ROOMS_FILE)


def load_rooms():
    """Load rooms from JSON file"""
    from .data import Room
    return load_from_json(ROOMS_FILE, Room)


def save_bookings(bookings):
    """Save bookings to JSON file"""
    save_to_json(bookings, BOOKINGS_FILE, datetime_fields=['start_time', 'end_time'])


def load_bookings():
    """Load bookings from JSON file"""
    from .data import Booking
    return load_from_json(BOOKINGS_FILE, Booking, datetime_fields=['start_time', 'end_time'])


def save_notifications(notifications):
    """Save notifications to JSON file"""
    save_to_json(notifications, NOTIFICATIONS_FILE, datetime_fields=['created_at'])


def load_notifications():
    """Load notifications from JSON file"""
    from .data import Notification
    return load_from_json(NOTIFICATIONS_FILE, Notification, datetime_fields=['created_at'])


def initialize_storage():
    """
    Initialize storage - load from files or create with defaults
    """
    from .data import USERS, ROOMS, BOOKINGS, NOTIFICATIONS
    
    # Load users
    loaded_users = load_users()
    if loaded_users is not None:
        USERS.clear()
        USERS.extend(loaded_users)
        print(f"Loaded {len(loaded_users)} users from storage")
    else:
        save_users(USERS)
        print(f"Initialized storage with {len(USERS)} default users")
    
    # Load rooms
    loaded_rooms = load_rooms()
    if loaded_rooms is not None:
        ROOMS.clear()
        ROOMS.extend(loaded_rooms)
        print(f"Loaded {len(loaded_rooms)} rooms from storage")
    else:
        save_rooms(ROOMS)
        print(f"Initialized storage with {len(ROOMS)} default rooms")
    
    # Load bookings
    loaded_bookings = load_bookings()
    if loaded_bookings is not None:
        BOOKINGS.clear()
        BOOKINGS.extend(loaded_bookings)
        print(f"Loaded {len(loaded_bookings)} bookings from storage")
    else:
        save_bookings(BOOKINGS)
        print(f"Initialized storage with {len(BOOKINGS)} default bookings")
    
    # Load notifications
    loaded_notifications = load_notifications()
    if loaded_notifications is not None:
        NOTIFICATIONS.clear()
        NOTIFICATIONS.extend(loaded_notifications)
        print(f"Loaded {len(loaded_notifications)} notifications from storage")
    else:
        save_notifications(NOTIFICATIONS)
        print(f"Initialized storage with {len(NOTIFICATIONS)} default notifications")