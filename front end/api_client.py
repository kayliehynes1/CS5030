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
    
    def make_request(self, method, endpoint, data=None, params=None):
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            # Return JSON response if available
            if response.content:
                return response.json()
            return {"success": True}
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.HTTPError as e:
            # Handle specific HTTP error codes
            if response.status_code == 401:
                raise Exception("Unauthorized - Invalid or expired token")
            elif response.status_code == 403:
                raise Exception("Forbidden - Insufficient permissions")
            elif response.status_code == 404:
                raise Exception("Resource not found")
            elif response.status_code == 400:
                error_msg = response.json().get("error", "Bad request")
                raise Exception(f"Bad request: {error_msg}")
            else:
                raise Exception(f"HTTP {response.status_code}: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from server")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    # Auth endpoints
    def login(self, email, password):
        """Authenticate user and get token"""
        return self.make_request("POST", "/auth/login", {
            "email": email,
            "password": password
        })
    
    def register(self, email, password, name):
        """Register new user"""
        return self.make_request("POST", "/auth/register", {
            "email": email,
            "password": password,
            "name": name
        })
    
    def logout(self):
        """Logout user"""
        response = self.make_request("POST", "/auth/logout")
        self.set_token(None)
        return response
    
    # Booking endpoints
    def get_upcoming_bookings(self):
        """Get user's upcoming bookings"""
        return self.make_request("GET", "/bookings/upcoming")
    
    def get_organized_bookings(self):
        """Get bookings organized by user"""
        return self.make_request("GET", "/bookings/organized")
    
    def get_booking(self, booking_id):
        """Get specific booking details"""
        return self.make_request("GET", f"/bookings/{booking_id}")
    
    def create_booking(self, booking_data):
        """Create new booking
        
        booking_data should include:
        - room_id: int
        - title: str
        - date: str (YYYY-MM-DD)
        - start_time: str (HH:MM)
        - end_time: str (HH:MM)
        - attendees: list (optional)
        """
        return self.make_request("POST", "/bookings", booking_data)
    
    def update_booking(self, booking_id, booking_data):
        """Update existing booking"""
        return self.make_request("PUT", f"/bookings/{booking_id}", booking_data)
    
    def cancel_booking(self, booking_id):
        """Cancel booking"""
        return self.make_request("DELETE", f"/bookings/{booking_id}")
    
    def add_attendee(self, booking_id, email):
        """Add attendee to booking"""
        return self.make_request("POST", f"/bookings/{booking_id}/attendees", {
            "email": email
        })
    
    def remove_attendee(self, booking_id, email):
        """Remove attendee from booking"""
        return self.make_request("DELETE", f"/bookings/{booking_id}/attendees", {
            "email": email
        })
    
    # Room endpoints
    def get_available_rooms(self, date, start_time, end_time, capacity=None):
        """Get available rooms for specific time slot"""
        params = {
            "date": date,
            "start_time": start_time,
            "end_time": end_time
        }
        if capacity:
            params["capacity"] = capacity
        return self.make_request("GET", "/rooms/available", params=params)
    
    def get_all_rooms(self):
        """Get all rooms"""
        return self.make_request("GET", "/rooms")
    
    def get_room(self, room_id):
        """Get specific room details"""
        return self.make_request("GET", f"/rooms/{room_id}")
    
    def get_room_schedule(self, room_id, date):
        """Get room's schedule for specific date"""
        return self.make_request("GET", f"/rooms/{room_id}/schedule", params={"date": date})
    
    # User endpoints
    def get_user_profile(self):
        """Get current user profile"""
        return self.make_request("GET", "/user/profile")
    
    def update_user_profile(self, profile_data):
        """Update user profile"""
        return self.make_request("PUT", "/user/profile", profile_data)
    
    
        

    
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
        result= self.make_request("DELETE", f"/bookings/{booking_id}")
        print(f"Delete booking {booking_id} result: {result}")
        return result
    
    # Room endpoints
    def get_available_rooms(self, date, start_time, end_time):
        params = {"date": date, "start_time": start_time, "end_time": end_time}
        return self.make_request("GET", "/rooms/available", params)
    
    def get_all_rooms(self):
        return self.make_request("GET", "/rooms")
    
    # User endpoints
    def get_user_profile(self):
        return self.make_request("GET", "/user/profile")
