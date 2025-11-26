"""
Simple JSON file storage for users, rooms, and bookings
"""
import json
import os
from datetime import datetime
from typing import List
from pathlib import Path

# Storage directory
STORAGE_DIR = Path(__file__).parent / "data"
USERS_FILE = STORAGE_DIR / "users.json"
ROOMS_FILE = STORAGE_DIR / "rooms.json"
BOOKINGS_FILE = STORAGE_DIR / "bookings.json"

def ensure_storage_dir():
    """Create storage directory if it doesn't exist"""
    STORAGE_DIR.mkdir(exist_ok=True)

def save_users(users):
    """Save users to JSON file"""
    ensure_storage_dir()
    users_data = []
    for user in users:
        user_dict = user.model_dump()
        # Convert datetime to string if present
        if user_dict.get('locked_until'):
            user_dict['locked_until'] = user_dict['locked_until'].isoformat()
        users_data.append(user_dict)
    
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def load_users():
    """Load users from JSON file"""
    if not USERS_FILE.exists():
        return None
    
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
        
        # Convert back to User objects
        from .data import User
        users = []
        for user_dict in users_data:
            # Convert locked_until string back to datetime
            if user_dict.get('locked_until'):
                user_dict['locked_until'] = datetime.fromisoformat(user_dict['locked_until'])
            users.append(User(**user_dict))
        
        return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return None

def save_rooms(rooms):
    """Save rooms to JSON file"""
    ensure_storage_dir()
    rooms_data = [room.model_dump() for room in rooms]
    
    with open(ROOMS_FILE, 'w') as f:
        json.dump(rooms_data, f, indent=2)

def load_rooms():
    """Load rooms from JSON file"""
    if not ROOMS_FILE.exists():
        return None
    
    try:
        with open(ROOMS_FILE, 'r') as f:
            rooms_data = json.load(f)
        
        from .data import Room
        return [Room(**room_dict) for room_dict in rooms_data]
    except Exception as e:
        print(f"Error loading rooms: {e}")
        return None

def save_bookings(bookings):
    """Save bookings to JSON file"""
    ensure_storage_dir()
    bookings_data = []
    for booking in bookings:
        booking_dict = booking.model_dump()
        # Convert datetime to string
        booking_dict['start_time'] = booking_dict['start_time'].isoformat()
        booking_dict['end_time'] = booking_dict['end_time'].isoformat()
        bookings_data.append(booking_dict)
    
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings_data, f, indent=2)

def load_bookings():
    """Load bookings from JSON file"""
    if not BOOKINGS_FILE.exists():
        return None
    
    try:
        with open(BOOKINGS_FILE, 'r') as f:
            bookings_data = json.load(f)
        
        from .data import Booking
        bookings = []
        for booking_dict in bookings_data:
            # Convert string back to datetime
            booking_dict['start_time'] = datetime.fromisoformat(booking_dict['start_time'])
            booking_dict['end_time'] = datetime.fromisoformat(booking_dict['end_time'])
            bookings.append(Booking(**booking_dict))
        
        return bookings
    except Exception as e:
        print(f"Error loading bookings: {e}")
        return None

def initialize_storage():
    """
    Initialize storage - load from files or create with defaults
    """
    from .data import USERS, ROOMS, BOOKINGS
    
    # Load users
    loaded_users = load_users()
    if loaded_users is not None:
        USERS.clear()
        USERS.extend(loaded_users)
        print(f"Loaded {len(loaded_users)} users from storage")
    else:
        # Save default users
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