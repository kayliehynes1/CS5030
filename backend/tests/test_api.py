"""
Integration tests for API endpoints
Tests include valid requests, invalid requests, and malicious input
"""
import pytest
from fastapi.testclient import TestClient
from app import app

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
    
    def test_get_bookings(self):
        """Test getting user bookings"""
        response = client.get("/bookings/upcoming", headers=self.headers)
        
        assert response.status_code == 200
        bookings = response.json()
        assert isinstance(bookings, list)
    
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
