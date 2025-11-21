import requests
import json

class APIClient:
    """talk to back end"""
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def set_token(self, token):
        """Set authentication token"""
        self.token = token
        if token:
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}
    
    def make_request(self, method, endpoint, data=None):
        """Make API request with error handling"""
        # For demo purposes, return mock data
        # Replace with actual API calls when backend is ready
        return self._get_mock_data(method, endpoint, data)
    
    def _get_mock_data(self, method, endpoint, data):
        """Provide mock data for demonstration --> speak to back end""" 
        if endpoint == "/auth/login":
            return {
                "token": "mock_jwt_token",
                "user": {
                    "name": data.get("email", "User").split("@")[0],
                    "email": data.get("email", ""),
                    "role": "user"
                }
            }
        
        elif endpoint == "/bookings/upcoming":
            return [
                {
                    "id": 1,
                    "title": "Team Meeting", 
                    "room_name": "Conference Room A", 
                    "date": "2025-01-15", 
                    "start_time": "14:00", 
                    "end_time": "15:00",
                    "current_attendees": 3,
                    "capacity": 10,
                    "is_organizer": True,
                    "status": "Confirmed"
                },
                {
                    "id": 2,
                    "title": "Project Review", 
                    "room_name": "Meeting Room B", 
                    "date": "2025-01-16", 
                    "start_time": "11:00", 
                    "end_time": "12:00",
                    "current_attendees": 2,
                    "capacity": 8,
                    "is_organizer": False,
                    "status": "Confirmed"
                }
            ]
        
        elif endpoint == "/bookings/organized":
            return [
                {
                    "id": 1,
                    "title": "Team Meeting", 
                    "room_name": "Conference Room A", 
                    "date": "2025-01-15", 
                    "start_time": "14:00", 
                    "end_time": "15:00",
                    "current_attendees": 3,
                    "capacity": 10
                }
            ]
        
        elif endpoint.startswith("/rooms/available"):
            return [
                {"id": 1, "name": "Conference Room A", "capacity": 10, "facilities": ["Projector", "Whiteboard"]},
                {"id": 2, "name": "Meeting Room B", "capacity": 6, "facilities": ["TV", "Whiteboard"]},
                {"id": 3, "name": "Seminar Room C", "capacity": 20, "facilities": ["Projector", "Sound System"]}
            ]
        
        elif endpoint == "/rooms":
            return [
                {"id": 1, "name": "Conference Room A", "capacity": 10, "facilities": ["Projector", "Whiteboard"], "building": "Main Building"},
                {"id": 2, "name": "Meeting Room B", "capacity": 6, "facilities": ["TV", "Whiteboard"], "building": "Main Building"},
                {"id": 3, "name": "Seminar Room C", "capacity": 20, "facilities": ["Projector", "Sound System"], "building": "Science Building"},
                {"id": 4, "name": "Study Room D", "capacity": 4, "facilities": [], "building": "Library"}
            ]
        
        elif endpoint == "/user/profile":
            return {
                "name": "Demo User",
                "email": "demo@university.edu",
                "role": "Student"
            }
        
        elif endpoint == "/bookings" and method == "POST":
            return {"success": True, "booking_id": 1001}
        
        return None
    
    # Auth endpoints
    def login(self, email, password):
        return self.make_request("POST", "/auth/login", {"email": email, "password": password})
    
    # Booking endpoints
    def get_upcoming_bookings(self):
        return self.make_request("GET", "/bookings/upcoming")
    
    def get_organized_bookings(self):
        return self.make_request("GET", "/bookings/organized")
    
    def create_booking(self, booking_data):
        return self.make_request("POST", "/bookings", booking_data)
    
    def update_booking(self, booking_id, booking_data):
        return self.make_request("PUT", f"/bookings/{booking_id}", booking_data)
    
    def cancel_booking(self, booking_id):
        return self.make_request("DELETE", f"/bookings/{booking_id}")
    
    # Room endpoints
    def get_available_rooms(self, date, start_time, end_time):
        params = {"date": date, "start_time": start_time, "end_time": end_time}
        return self.make_request("GET", "/rooms/available", params)
    
    def get_all_rooms(self):
        return self.make_request("GET", "/rooms")
    
    # User endpoints
    def get_user_profile(self):
        return self.make_request("GET", "/user/profile")
