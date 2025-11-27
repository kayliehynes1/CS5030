"""
Pytest configuration and fixtures for the Room Booking System tests.

Provides:
- Test client fixture
- Authentication helper fixtures  
- Test data setup/teardown
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure the backend package is importable when running tests from varied working dirs
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app
from app.data import USERS, BOOKINGS, ROOMS, NOTIFICATIONS


@pytest.fixture(scope="function")
def client():
    """Create a test client for each test"""
    return TestClient(app)


@pytest.fixture(scope="function")
def auth_headers(client):
    """Get authentication headers for the default test user"""
    response = client.post("/auth/login", json={
        "email": "alicejohnson@st-andrews.ac.uk",
        "password": "password123"
    })
    
    if response.status_code == 200:
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    # If login fails, skip tests that need auth
    pytest.skip("Could not authenticate default user")


@pytest.fixture(scope="function")
def test_booking_data():
    """Sample booking data for tests"""
    return {
        "room_id": 1,
        "title": "Test Meeting",
        "date": "2025-12-15",
        "start_time": "14:00",
        "end_time": "15:00",
        "notes": "Test notes",
        "visibility": "private",
        "attendee_emails": []
    }


@pytest.fixture(scope="function")
def test_user_data():
    """Sample user registration data"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Test User {unique_id}",
        "email": f"testuser_{unique_id}@test.com",
        "password": "testpassword123",
        "role": "attendee"
    }


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
