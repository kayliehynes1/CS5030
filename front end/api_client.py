import json
import requests


class APIClient:
    """HTTP client for the FastAPI backend."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.headers = {}

    def set_token(self, token):
        """Store auth token (not required by the backend but kept for UI state)."""
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def make_request(self, method, endpoint, data=None, params=None):
        """Generic request helper with basic error handling."""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.content:
                return response.json()
            return {"success": True}

        except requests.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("Unauthorized - Invalid email or password")
            elif response.status_code == 404:
                raise Exception("Resource not found")
            elif response.status_code == 400:
                error_msg = response.json().get("detail") if response.content else "Bad request"
                raise Exception(f"Bad request: {error_msg}")
            else:
                raise Exception(f"HTTP {response.status_code}: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from server")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def health(self):
        return self.make_request("GET", "/health")

    def get_users(self):
        return self.make_request("GET", "/users")

    def get_all_rooms(self):
        return self.make_request("GET", "/rooms")

    def get_bookings(self):
        return self.make_request("GET", "/bookings")

    def create_booking(self, booking_data):
        return self.make_request("POST", "/bookings", booking_data)

    def update_booking(self, booking_id, booking_data):
        return self.make_request("PUT", f"/bookings/{booking_id}", booking_data)

    def cancel_booking(self, booking_id):
        return self.make_request("DELETE", f"/bookings/{booking_id}")

    def login(self, email, password):
        return self.make_request("POST", "/auth/login", {"email": email, "password": password})

    def register(self, name, email, password, role="attendee"):
        return self.make_request(
            "POST",
            "/auth/register",
            {"name": name, "email": email, "password": password, "role": role},
        )
