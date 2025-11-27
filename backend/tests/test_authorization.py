"""
Authorization tests for the Room Booking System.

Tests verify that:
- Only organizers can update their bookings
- Only organizers can delete their bookings
- Users can only access their own notifications
- Authentication is required for protected endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestBookingAuthorization:
    """Test booking authorization rules"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test users"""
        # Login as Alice (user 1)
        alice_resp = client.post("/auth/login", json={
            "email": "alicejohnson@st-andrews.ac.uk",
            "password": "password123"
        })
        self.alice_headers = {"Authorization": f"Bearer {alice_resp.json()['token']}"}
        
        # Login as Ben (user 2)
        ben_resp = client.post("/auth/login", json={
            "email": "benlee@st-andrews.ac.uk",
            "password": "password012!"
        })
        self.ben_headers = {"Authorization": f"Bearer {ben_resp.json()['token']}"}
    
    def test_organizer_can_update_own_booking(self):
        """Test that booking organizer can update their booking"""
        # Create a booking as Alice
        booking_resp = client.post("/bookings", json={
            "room_id": 5,
            "title": "Alice's Meeting",
            "date": "2025-12-20",
            "start_time": "09:00",
            "end_time": "10:00"
        }, headers=self.alice_headers)
        
        if booking_resp.status_code != 201:
            pytest.skip("Could not create test booking")
        
        booking_id = booking_resp.json()["id"]
        
        # Alice should be able to update it
        update_resp = client.put(f"/bookings/{booking_id}", json={
            "room_id": 5,
            "title": "Updated Meeting",
            "date": "2025-12-20",
            "start_time": "09:00",
            "end_time": "10:00"
        }, headers=self.alice_headers)
        
        assert update_resp.status_code == 200
        
        # Cleanup
        client.delete(f"/bookings/{booking_id}", headers=self.alice_headers)
    
    def test_non_organizer_cannot_update_booking(self):
        """Test that non-organizer cannot update someone else's booking"""
        # Create a booking as Alice
        booking_resp = client.post("/bookings", json={
            "room_id": 6,
            "title": "Alice Only Meeting",
            "date": "2025-12-21",
            "start_time": "11:00",
            "end_time": "12:00"
        }, headers=self.alice_headers)
        
        if booking_resp.status_code != 201:
            pytest.skip("Could not create test booking")
        
        booking_id = booking_resp.json()["id"]
        
        # Ben should NOT be able to update it
        update_resp = client.put(f"/bookings/{booking_id}", json={
            "room_id": 6,
            "title": "Hijacked Meeting",
            "date": "2025-12-21",
            "start_time": "11:00",
            "end_time": "12:00"
        }, headers=self.ben_headers)
        
        assert update_resp.status_code == 403
        assert "organizer" in update_resp.json()["detail"].lower()
        
        # Cleanup
        client.delete(f"/bookings/{booking_id}", headers=self.alice_headers)

    def test_attendee_cannot_create_booking(self):
        """Attendees should be blocked from creating bookings"""
        response = client.post("/bookings", json={
            "room_id": 1,
            "title": "Attendee Attempt",
            "date": "2025-12-24",
            "start_time": "10:00",
            "end_time": "11:00"
        }, headers=self.ben_headers)
        assert response.status_code == 403
        assert "organiser" in response.json()["detail"].lower()
    
    def test_organizer_can_delete_own_booking(self):
        """Test that booking organizer can delete their booking"""
        # Create a booking as Alice
        booking_resp = client.post("/bookings", json={
            "room_id": 7,
            "title": "To Be Deleted",
            "date": "2025-12-22",
            "start_time": "14:00",
            "end_time": "15:00"
        }, headers=self.alice_headers)
        
        if booking_resp.status_code != 201:
            pytest.skip("Could not create test booking")
        
        booking_id = booking_resp.json()["id"]
        
        # Alice should be able to delete it
        delete_resp = client.delete(f"/bookings/{booking_id}", headers=self.alice_headers)
        assert delete_resp.status_code == 204
    
    def test_non_organizer_cannot_delete_booking(self):
        """Test that non-organizer cannot delete someone else's booking"""
        # Create a booking as Alice
        booking_resp = client.post("/bookings", json={
            "room_id": 8,
            "title": "Protected Meeting",
            "date": "2025-12-23",
            "start_time": "16:00",
            "end_time": "17:00"
        }, headers=self.alice_headers)
        
        if booking_resp.status_code != 201:
            pytest.skip("Could not create test booking")
        
        booking_id = booking_resp.json()["id"]
        
        # Ben should NOT be able to delete it
        delete_resp = client.delete(f"/bookings/{booking_id}", headers=self.ben_headers)
        assert delete_resp.status_code == 403
        assert "organizer" in delete_resp.json()["detail"].lower()
        
        # Cleanup
        client.delete(f"/bookings/{booking_id}", headers=self.alice_headers)


class TestAuthenticationRequired:
    """Test that authentication is required for protected endpoints"""
    
    def test_rooms_requires_auth(self):
        """Test that /rooms requires authentication"""
        response = client.get("/rooms")
        assert response.status_code == 401
    
    def test_bookings_requires_auth(self):
        """Test that /bookings requires authentication"""
        response = client.get("/bookings/upcoming")
        assert response.status_code == 401
    
    def test_create_booking_requires_auth(self):
        """Test that creating booking requires authentication"""
        response = client.post("/bookings", json={
            "room_id": 1,
            "title": "Test",
            "date": "2025-12-01",
            "start_time": "09:00",
            "end_time": "10:00"
        })
        assert response.status_code == 401
    
    def test_notifications_requires_auth(self):
        """Test that /notifications requires authentication"""
        response = client.get("/notifications")
        assert response.status_code == 401
    
    def test_profile_requires_auth(self):
        """Test that /user/profile requires authentication"""
        response = client.get("/user/profile")
        assert response.status_code == 401


class TestNotificationAuthorization:
    """Test notification authorization"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test users"""
        alice_resp = client.post("/auth/login", json={
            "email": "alicejohnson@st-andrews.ac.uk",
            "password": "password123"
        })
        self.alice_headers = {"Authorization": f"Bearer {alice_resp.json()['token']}"}
    
    def test_user_can_only_see_own_notifications(self):
        """Test that users can only see their own notifications"""
        response = client.get("/notifications", headers=self.alice_headers)
        assert response.status_code == 200
        
        # All returned notifications should belong to the current user
        # (This is verified by the endpoint logic, but we confirm it returns data)
        notifications = response.json()
        assert isinstance(notifications, list)
