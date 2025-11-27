"""
Integration tests for API endpoints
Tests include valid requests, invalid requests, and malicious input
"""
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from app import app
from app.data import ROOMS, BOOKINGS, NOTIFICATIONS, Booking
from app.routes import create_notification, process_booking_reminders

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthEndpoints:
    """Test authentication endpoints with various inputs"""
    
    def test_register_valid_user(self):
        """Test registering a new user with valid data"""
        import uuid
        unique_email = f"newuser_{uuid.uuid4().hex[:8]}@test.com"
        response = client.post("/auth/register", json={
            "name": "Test User",
            "email": unique_email,
            "password": "secure_password123",  # At least 8 chars
            "role": "attendee"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == unique_email
    
    def test_register_duplicate_email(self):
        """Test that duplicate email registration fails gracefully"""
        import uuid
        unique_email = f"duplicate_{uuid.uuid4().hex[:8]}@test.com"
        user_data = {
            "name": "Duplicate User",
            "email": unique_email,
            "password": "password12345",  # At least 8 chars
            "role": "attendee"
        }
        
        # Register first time
        response1 = client.post("/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to register again with same email
        response2 = client.post("/auth/register", json=user_data)
        assert response2.status_code == 409  # Conflict
        assert "already registered" in response2.json()["detail"].lower()
    
    def test_register_missing_fields(self):
        """Test registration with missing required fields"""
        invalid_requests = [
            {},  # Empty
            {"name": "Test"},  # Missing email and password
            {"email": "test@test.com"},  # Missing name and password
            {"name": "Test", "email": "test@test.com"},  # Missing password
        ]
        
        for request_data in invalid_requests:
            response = client.post("/auth/register", json=request_data)
            assert response.status_code == 422  # Validation error
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format"""
        response = client.post("/auth/register", json={
            "name": "Test User",
            "email": "not_an_email",
            "password": "password",
            "role": "attendee"
        })
        # Server should reject with 400 (bad request) or 422 (validation error)
        assert response.status_code in [400, 422]
    
    def test_register_sql_injection_attempt(self):
        """Test that SQL injection attempts are handled safely"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd"
        ]
        
        for malicious in malicious_inputs:
            response = client.post("/auth/register", json={
                "name": malicious,
                "email": f"{malicious}@test.com",
                "password": malicious,
                "role": "attendee"
            })
            # Should not crash - either accept or reject gracefully
            assert response.status_code in [201, 400, 422]
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        import uuid
        unique_email = f"logintest_{uuid.uuid4().hex[:8]}@test.com"
        
        # First register a user
        client.post("/auth/register", json={
            "name": "Login Test User",
            "email": unique_email,
            "password": "testpass12345",  # At least 8 chars
            "role": "attendee"
        })
        
        # Then try to login
        response = client.post("/auth/login", json={
            "email": unique_email,
            "password": "testpass12345"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
    
    def test_login_invalid_password(self):
        """Test login with wrong password"""
        response = client.post("/auth/login", json={
            "email": "alicejohnson@st-andrews.ac.uk",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        response = client.post("/auth/login", json={
            "email": "doesnotexist@test.com",
            "password": "anypassword"
        })
        
        assert response.status_code == 401
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        invalid_logins = [
            {},
            {"email": "test@test.com"},  # Missing password
            {"password": "test"},  # Missing email
        ]
        
        for login_data in invalid_logins:
            response = client.post("/auth/login", json=login_data)
            assert response.status_code == 422


class TestRoomsEndpoints:
    """Test room-related endpoints"""
    
    def setup_method(self):
        """Get auth token for protected endpoints"""
        response = client.post("/auth/login", json={
            "email": "alicejohnson@st-andrews.ac.uk",
            "password": "password123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_rooms_authenticated(self):
        """Test listing rooms with authentication"""
        response = client.get("/rooms", headers=self.headers)
        
        assert response.status_code == 200
        rooms = response.json()
        assert isinstance(rooms, list)
        assert len(rooms) > 0
    
    def test_list_rooms_unauthenticated(self):
        """Test that listing rooms without auth fails"""
        response = client.get("/rooms")
        
        assert response.status_code == 401
    
    def test_list_rooms_invalid_token(self):
        """Test listing rooms with invalid token"""
        response = client.get("/rooms", headers={"Authorization": "Bearer invalid_token"})
        
        assert response.status_code == 401


class TestBookingsEndpoints:
    """Test booking-related endpoints"""
    
    def setup_method(self):
        """Get auth token"""
        response = client.post("/auth/login", json={
            "email": "alicejohnson@st-andrews.ac.uk",
            "password": "password123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a fresh attendee for public booking tests
        import uuid
        new_email = f"public_attendee_{uuid.uuid4().hex[:6]}@test.com"
        reg = client.post("/auth/register", json={
            "name": "Public Attendee",
            "email": new_email,
            "password": "attendeepass123",
            "role": "attendee"
        })
        self.public_headers = {"Authorization": f"Bearer {reg.json()['token']}"} if reg.status_code == 201 else self.headers
    
    def test_get_bookings(self):
        """Test getting user bookings"""
        response = client.get("/bookings/upcoming", headers=self.headers)
        
        assert response.status_code == 200
        bookings = response.json()
        assert isinstance(bookings, list)
    
    def test_public_bookings_and_register(self):
        """Attendee should see open meetings and be able to register"""
        public_resp = client.get("/bookings/public", headers=self.public_headers)
        assert public_resp.status_code == 200
        public_bookings = public_resp.json()
        assert isinstance(public_bookings, list)
        if public_bookings:
            booking_id = public_bookings[0]["id"]
            join_resp = client.post(f"/bookings/{booking_id}/register", headers=self.public_headers)
            assert join_resp.status_code == 200
            assert "registered" in join_resp.json().get("message", "").lower()
    
    def test_create_booking_missing_fields(self):
        """Test creating booking with missing fields"""
        invalid_bookings = [
            {},
            {"room_id": 1},  # Missing other fields
            {"title": "Test"},  # Missing room_id
        ]
        
        for booking_data in invalid_bookings:
            response = client.post("/bookings", json=booking_data, headers=self.headers)
            # Should reject with validation error
            assert response.status_code in [400, 422]
    
    def test_create_booking_invalid_room(self):
        """Test creating booking with non-existent room"""
        response = client.post("/bookings", json={
            "id": 999,
            "room_id": 99999,  # Non-existent room
            "organiser_id": 1,
            "attendee_ids": [],
            "title": "Test Booking",
            "start_time": "2025-12-01T09:00:00",
            "end_time": "2025-12-01T10:00:00"
        }, headers=self.headers)
        
        # Should handle gracefully (422 = validation error, which is correct!)
        assert response.status_code in [201, 400, 404, 422]
    
    def test_get_bookings_unauthenticated(self):
        """Test that unauthenticated access is rejected"""
        response = client.get("/bookings/upcoming")
        
        assert response.status_code == 401

    def test_update_booking_sanitization_and_validation(self):
        """Whitespace/overlong titles rejected; valid values are trimmed on update."""
        booking_resp = client.post(
            "/bookings",
            json={
                "room_id": 5,
                "title": "Initial Title",
                "date": "2026-01-10",
                "start_time": "10:00",
                "end_time": "11:00",
                "notes": "Base notes",
            },
            headers=self.headers,
        )
        assert booking_resp.status_code == 201
        booking_id = booking_resp.json()["id"]

        try:
            resp = client.put(
                f"/bookings/{booking_id}",
                json={
                    "room_id": 5,
                    "title": "    ",
                    "date": "2026-01-10",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "notes": "Still fine",
                },
                headers=self.headers,
            )
            assert resp.status_code == 400

            long_title = "A" * 201
            resp = client.put(
                f"/bookings/{booking_id}",
                json={
                    "room_id": 5,
                    "title": long_title,
                    "date": "2026-01-10",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "notes": "Still fine",
                },
                headers=self.headers,
            )
            assert resp.status_code in (400, 422)

            resp = client.put(
                f"/bookings/{booking_id}",
                json={
                    "room_id": 5,
                    "title": "   Trimmed Title   ",
                    "date": "2026-01-10",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "notes": "   spaced notes   ",
                },
                headers=self.headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["title"] == "Trimmed Title"
            assert data["notes"] == "spaced notes"
        finally:
            client.delete(f"/bookings/{booking_id}", headers=self.headers)

    def test_register_blocked_when_pending_fills_capacity(self):
        """Self-registration should fail if pending invites already fill the room."""
        pending_emails = ["benlee@st-andrews.ac.uk"]
        import uuid
        for _ in range(2):
            email = f"pending_{uuid.uuid4().hex[:6]}@test.com"
            reg_resp = client.post("/auth/register", json={
                "name": "Pending User",
                "email": email,
                "password": "password123",
                "role": "attendee"
            })
            assert reg_resp.status_code == 201
            pending_emails.append(email)

        joiner_email = f"joiner_{uuid.uuid4().hex[:6]}@test.com"
        joiner_reg = client.post("/auth/register", json={
            "name": "Joiner User",
            "email": joiner_email,
            "password": "password123",
            "role": "attendee"
        })
        assert joiner_reg.status_code == 201
        joiner_headers = {"Authorization": f"Bearer {joiner_reg.json()['token']}"}

        booking_resp = client.post(
            "/bookings",
            json={
                "room_id": 1,  # capacity 4
                "title": "Capacity Test",
                "date": "2026-02-01",
                "start_time": "09:00",
                "end_time": "10:00",
                "attendee_emails": pending_emails,
            },
            headers=self.headers,
        )
        assert booking_resp.status_code == 201
        booking_id = booking_resp.json()["id"]

        try:
            resp = client.post(f"/bookings/{booking_id}/register", headers=joiner_headers)
            assert resp.status_code == 400
            assert "full capacity" in resp.json()["detail"].lower()
        finally:
            client.delete(f"/bookings/{booking_id}", headers=self.headers)

    def test_update_booking_overlap_returns_conflict(self):
        """Updating a booking into a conflicting slot should return 409."""
        booking1 = client.post(
            "/bookings",
            json={
                "room_id": 6,
                "title": "Slot 1",
                "date": "2026-03-01",
                "start_time": "09:00",
                "end_time": "10:00",
            },
            headers=self.headers,
        )
        booking2 = client.post(
            "/bookings",
            json={
                "room_id": 6,
                "title": "Slot 2",
                "date": "2026-03-01",
                "start_time": "11:00",
                "end_time": "12:00",
            },
            headers=self.headers,
        )
        if booking1.status_code != 201 or booking2.status_code != 201:
            pytest.skip("Could not create setup bookings")

        id1 = booking1.json()["id"]
        id2 = booking2.json()["id"]

        try:
            resp = client.put(
                f"/bookings/{id2}",
                json={
                    "room_id": 6,
                    "title": "Slot 2 moved",
                    "date": "2026-03-01",
                    "start_time": "09:30",
                    "end_time": "10:30",
                },
                headers=self.headers,
            )
            assert resp.status_code == 409
        finally:
            client.delete(f"/bookings/{id1}", headers=self.headers)
            client.delete(f"/bookings/{id2}", headers=self.headers)


class TestNotificationsFlow:
    """Notification lifecycle and reminders."""

    def setup_method(self):
        response = client.post("/auth/login", json={
            "email": "alicejohnson@st-andrews.ac.uk",
            "password": "password123"
        })
        self.headers = {"Authorization": f"Bearer {response.json()['token']}"}

    def test_notification_mark_read_and_delete(self):
        notif = create_notification(
            user_id=1,
            notif_type="booking_updated",
            title="Test Notification",
            message="Please ignore",
            booking_id=None,
        )
        initial_count = len(NOTIFICATIONS)
        try:
            resp = client.get("/notifications", headers=self.headers)
            assert resp.status_code == 200
            ids = [n["id"] for n in resp.json()]
            assert notif.id in ids

            read_resp = client.put(f"/notifications/{notif.id}/read", headers=self.headers)
            assert read_resp.status_code == 200

            resp = client.get("/notifications", headers=self.headers)
            notif_entry = next(n for n in resp.json() if n["id"] == notif.id)
            assert notif_entry["is_read"] is True

            del_resp = client.delete(f"/notifications/{notif.id}", headers=self.headers)
            assert del_resp.status_code == 204

            resp = client.get("/notifications", headers=self.headers)
            ids = [n["id"] for n in resp.json()]
            assert notif.id not in ids
        finally:
            while len(NOTIFICATIONS) > initial_count:
                NOTIFICATIONS.pop()

    def test_booking_reminder_creates_notifications(self, monkeypatch):
        fixed_now = datetime(2026, 4, 1, 12, 0, 0)

        class FixedDateTime(datetime):
            @classmethod
            def utcnow(cls):
                return fixed_now

        monkeypatch.setattr("app.routes.datetime", FixedDateTime)

        start = fixed_now + timedelta(hours=1)
        end = start + timedelta(hours=1)
        booking_id = max((b.id for b in BOOKINGS), default=0) + 1000
        reminder_booking = Booking(
            id=booking_id,
            room_id=1,
            organiser_id=1,
            attendee_ids=[2],
            pending_attendee_ids=[],
            title="Reminder Test",
            notes=None,
            start_time=start,
            end_time=end,
            status="confirmed",
            reminder_sent=False,
        )
        BOOKINGS.append(reminder_booking)

        initial_notif_count = len(NOTIFICATIONS)
        try:
            process_booking_reminders()
            assert len(NOTIFICATIONS) == initial_notif_count + 2  # organiser + attendee
            assert reminder_booking.reminder_sent is True
        finally:
            BOOKINGS.remove(reminder_booking)
            while len(NOTIFICATIONS) > initial_notif_count:
                NOTIFICATIONS.pop()


class TestMaliciousInput:
    """Test server robustness against various attacks"""
    
    def test_extremely_long_strings(self):
        """Test handling of extremely long input strings"""
        long_string = "A" * 1000  # Reduced to reasonable length
        
        response = client.post("/auth/register", json={
            "name": long_string,
            "email": f"longtest@test.com",  # Keep email reasonable
            "password": long_string,
            "role": "attendee"
        })
        
        # Should not crash - either accept or reject gracefully
        assert response.status_code in [201, 400, 422]
    
    def test_special_characters(self):
        """Test handling of special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        response = client.post("/auth/register", json={
            "name": special_chars,
            "email": "special@test.com",
            "password": special_chars,
            "role": "attendee"
        })
        
        # Should handle gracefully
        assert response.status_code in [201, 400, 422]
    
    def test_unicode_characters(self):
        """Test handling of Unicode characters"""
        unicode_text = "测试用户 🚀 Тест"
        
        response = client.post("/auth/register", json={
            "name": unicode_text,
            "email": "unicode@test.com",
            "password": "password",
            "role": "attendee"
        })
        
        # Should handle gracefully
        assert response.status_code in [201, 400, 422]
    
    def test_null_bytes(self):
        """Test handling of null bytes"""
        response = client.post("/auth/login", json={
            "email": "test\x00@test.com",
            "password": "pass\x00word"
        })
        
        # Should not crash
        assert response.status_code in [401, 422]
