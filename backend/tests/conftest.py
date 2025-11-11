"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "role": "employee"
    }

