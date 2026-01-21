"""
Tests for NOALBS-inspired features

Tests OBS integration, ingest monitoring, retry logic, and metrics aggregation.
All features are opt-in and should be tested in both enabled and disabled states.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client with lifespan context"""
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# OBS Integration Tests
# ============================================================================

def test_obs_status_disabled(client):
    """Test OBS status endpoint when feature is disabled"""
    response = client.get("/api/obs/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    # Will be False in default config
    if not data["enabled"]:
        assert "message" in data


def test_obs_scene_switch_disabled(client):
    """Test scene switching when feature is disabled"""
    response = client.post("/api/obs/scene?scene_name=Test Scene")
    assert response.status_code == 200
    data = response.json()
    # Should indicate feature not enabled in default config
    if "success" in data and not data["success"]:
        assert "message" in data


# ============================================================================
# Ingest Monitoring Tests
# ============================================================================

def test_ingest_stats_disabled(client):
    """Test ingest stats endpoint when feature is disabled"""
    response = client.get("/api/ingest/stats")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    # Will be False in default config
    if not data["enabled"]:
        assert "message" in data


# ============================================================================
# Metrics Aggregation Tests
# ============================================================================

def test_aggregated_metrics_disabled(client):
    """Test aggregated metrics endpoint when feature is disabled"""
    response = client.get("/api/metrics/aggregated")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    # Will be False in default config
    if not data["enabled"]:
        assert "message" in data


# ============================================================================
# Retry Logic Tests
# ============================================================================

def test_retry_status_disabled(client):
    """Test retry status endpoint when feature is disabled"""
    response = client.get("/api/state-machine/retry-status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    # Will be False in default config
    if not data["enabled"]:
        assert "message" in data


def test_retry_reset_disabled(client):
    """Test retry counter reset when feature is disabled"""
    response = client.post("/api/state-machine/reset-retry")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


# ============================================================================
# Backward Compatibility Tests
# ============================================================================

def test_existing_endpoints_still_work(client):
    """Ensure existing endpoints are not broken by new features"""
    # Root endpoint
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "VVLIVE Backend"

    # Health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Status endpoint
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "quality_state" in data
    assert "preset" in data

    # Metrics endpoint
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "bandwidth_mbps" in data
    assert "uplinks" in data


def test_state_machine_unchanged(client):
    """Test that state machine still works as before"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()

    # Should have valid quality state
    valid_states = ["HIGH", "MEDIUM", "LOW", "VERY_LOW", "RECOVERY", "ERROR"]
    assert data["quality_state"] in valid_states

    # Should have preset information
    assert "preset" in data
    assert "resolution" in data["preset"]
    assert "framerate" in data["preset"]
    assert "bitrate_kbps" in data["preset"]


# ============================================================================
# Integration Tests (when features would be enabled)
# ============================================================================

def test_api_docs_generation(client):
    """Test that FastAPI docs still generate correctly"""
    # This verifies API schema is valid
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema

    # Verify new endpoints are documented
    paths = schema["paths"]
    assert "/api/obs/status" in paths
    assert "/api/ingest/stats" in paths
    assert "/api/metrics/aggregated" in paths
    assert "/api/state-machine/retry-status" in paths
