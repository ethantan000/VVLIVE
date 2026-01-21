"""
Basic API tests for VVLIVE backend
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client with lifespan context"""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test root endpoint returns success"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VVLIVE Backend"
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "features" in data


def test_api_status_endpoint(client):
    """Test API status endpoint"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "quality_state" in data
    assert "preset" in data


def test_api_metrics_endpoint(client):
    """Test API metrics endpoint"""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "bandwidth_mbps" in data
    assert "uplinks" in data
    assert len(data["uplinks"]) == 2
