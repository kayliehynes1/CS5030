"""
API Client for Room Booking System

Note: This module does NOT need 'import json' because:
- We use response.json() which is a requests library method
- We catch ValueError which is the parent class of JSONDecodeError
- The backend (storage.py) handles actual JSON file operations
"""
import requests


class APIClient:
    """Talk to backend API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def set_token(self, token):
        """Set authentication token"""
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    def make_request(self, method, endpoint, data=None, params=None):
        """Generic request helper with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data if method != "GET" else None,
                params=params if method == "GET" else None,
                timeout=10
            )
            response.raise_for_status()
            return response.json() if response.content else {"success": True}
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.HTTPError as e:
            error_detail = "Bad request"
            if response.content:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                except:
                    error_detail = response.text[:100] if response.text else "Bad request"
            
            error_map = {
                401: "Unauthorized - Invalid email or password",
                404: "Resource not found",
                400: f"Bad request: {error_detail}"
            }
            raise Exception(error_map.get(response.status_code, f"HTTP {response.status_code}: {error_detail}"))
        except ValueError:
            raise Exception("Invalid JSON response from server")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    # Auth endpoints
    def health(self):
        return self.make_request("GET", "/health")
    
    def login(self, email, password):
        return self.make_request("POST", "/auth/login", {"email": email, "password": password})
    
    def register(self, name, email, password, role="student"):
        return self.make_request("POST", "/auth/register",
                                {"name": name, "email": email, "password": password, "role": role})
    
    # Booking endpoints
    def get_upcoming_bookings(self):
        return self.make_request("GET", "/bookings/upcoming")
    
    def get_past_bookings(self):
        return self.make_request("GET", "/bookings/past")
    
    def get_organized_bookings(self):
        return self.make_request("GET", "/bookings/organized")
    
    def create_booking(self, booking_data):
        return self.make_request("POST", "/bookings", booking_data)
    
    def update_booking(self, booking_id, booking_data):
        return self.make_request("PUT", f"/bookings/{booking_id}", booking_data)
    
    def cancel_booking(self, booking_id, reason=None):
        """Cancel a booking with optional reason"""
        return self.make_request("DELETE", f"/bookings/{booking_id}", {"reason": reason})
    
    def get_booking(self, booking_id):
        return self.make_request("GET", f"/bookings/{booking_id}")
    
    def accept_invitation(self, booking_id):
        return self.make_request("POST", f"/bookings/{booking_id}/accept")
    
    def decline_invitation(self, booking_id, reason=None):
        """Decline an invitation with optional reason"""
        return self.make_request("POST", f"/bookings/{booking_id}/decline", {"reason": reason})
    
    # Room endpoints
    def get_available_rooms(self, date, start_time, end_time):
        params = {"date": date, "start_time": start_time, "end_time": end_time}
        return self.make_request("GET", "/rooms/available", params=params)
    
    def get_all_rooms(self):
        return self.make_request("GET", "/rooms")
    
    # User endpoints
    def get_user_profile(self):
        return self.make_request("GET", "/user/profile")
    
    def get_users(self):
        """Get all users (for attendee selection)"""
        return self.make_request("GET", "/users")
    
    # Notification endpoints
    def get_notifications(self):
        """Get all notifications for current user"""
        return self.make_request("GET", "/notifications")
    
    def get_unread_notification_count(self):
        """Get count of unread notifications"""
        return self.make_request("GET", "/notifications/unread/count")
    
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        return self.make_request("PUT", f"/notifications/{notification_id}/read")
    
    def delete_notification(self, notification_id):
        """Delete a notification"""
        return self.make_request("DELETE", f"/notifications/{notification_id}")