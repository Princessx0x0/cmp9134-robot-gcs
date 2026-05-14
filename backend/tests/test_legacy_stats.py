"""
Tests for legacy_stats.py — 100% Branch Coverage
==================================================
Covers every path through calc_stats:
- Recon mission (type 1)
- Transport mission with heavy payload (type 2, payload > 50)
- Transport mission with light payload (type 2, payload <= 50)
- Missing required key (expect 400)
- Invalid mission type
- Score exceeds 100 (verify cap)
- Zero distance or battery (base score returns 0)
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legacy_stats import router

# Create a minimal test app with just the legacy router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_recon_mission_success():
    """Type 1 (recon) mission should return a successful score."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 1,
            "dist": 100.0,
            "batt": 50.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mission"] == "recon"
    assert data["final_score"] == 20.0  # (100 * 10) / 50 = 20


def test_transport_mission_heavy_payload():
    """Type 2 (transport) with payload > 50 should apply penalty."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 2,
            "dist": 100.0,
            "batt": 50.0,
            "payload_weight": 60,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mission"] == "transport"
    # base = (100 * 5) / 50 = 10, penalty = 60 * 0.1 = 6, final = 4
    assert data["final_score"] == 4.0


def test_transport_mission_light_payload():
    """Type 2 (transport) with payload <= 50 should not apply penalty."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 2,
            "dist": 100.0,
            "batt": 50.0,
            "payload_weight": 30,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["final_score"] == 10.0  # (100 * 5) / 50 = 10, no penalty


def test_missing_required_key_batt():
    """Pydantic validation returns 422 when required field is missing."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 1,
            "dist": 100.0,
        },
    )
    assert response.status_code == 422


def test_missing_required_key_dist():
    """Pydantic validation returns 422 when required field is missing."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 1,
            "batt": 50.0,
        },
    )
    assert response.status_code == 422


def test_invalid_mission_type():
    """Unknown mission type now returns 400 Bad Request consistently."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 99,
            "dist": 100.0,
            "batt": 50.0,
        },
    )
    assert response.status_code == 400


def test_score_capped_at_100():
    """Score exceeding 100 should be capped at 100."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 1,
            "dist": 10000.0,
            "batt": 1.0,
        },
    )
    assert response.status_code == 200
    assert response.json()["final_score"] == 100.0


def test_zero_distance_returns_zero_score():
    """Zero distance should result in a score of 0."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 1,
            "dist": 0.0,
            "batt": 50.0,
        },
    )
    assert response.status_code == 200
    assert response.json()["final_score"] == 0.0


def test_zero_battery_returns_zero_score():
    """Zero battery should result in a score of 0."""
    response = client.post(
        "/api/mission_stats",
        json={
            "type": 1,
            "dist": 100.0,
            "batt": 0.0,
        },
    )
    assert response.status_code == 200
    assert response.json()["final_score"] == 0.0
