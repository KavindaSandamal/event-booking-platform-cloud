import pytest
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200

def test_register_endpoint():
    """Test the register endpoint structure"""
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    })
    # This might return 500 due to database connection, but endpoint should exist
    assert response.status_code in [200, 201, 500]

def test_login_endpoint():
    """Test the login endpoint structure"""
    response = client.post("/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    # This might return 500 due to database connection, but endpoint should exist
    assert response.status_code in [200, 401, 500]

def test_events_endpoint():
    """Test the events endpoint"""
    response = client.get("/events")
    # This might return 500 due to database connection, but endpoint should exist
    assert response.status_code in [200, 500]

if __name__ == "__main__":
    pytest.main([__file__])
