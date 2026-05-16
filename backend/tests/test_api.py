"""
Integration Tests — API Routes
===============================
These tests use FastAPI's TestClient to make real HTTP requests
against the application without needing a running server.

Note: These tests mock the robot client so no actual robot connection
is needed — we are testing that our API routes behave correctly,
not that the robot simulator works.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from robot_client import RobotStatus, RobotConnectionError

client = TestClient(app)


# ── Mock robot status fixture ──────────────────────────────────────────────

MOCK_STATUS = RobotStatus(
    {
        "id": "XR-900",
        "position": {"x": 0, "y": 0},
        "battery": 100.0,
        "status": "IDLE",
    }
)


# ── Health check ───────────────────────────────────────────────────────────


def test_health_check():
    """Health endpoint should always return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Status endpoint ────────────────────────────────────────────────────────


def test_get_status_success():
    """GET /api/status should return robot data when robot is reachable."""
    with patch("main.robot") as mock_robot:
        mock_robot.get_status = AsyncMock(return_value=MOCK_STATUS)
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "XR-900"
        assert data["battery"] == 100.0
        assert data["status"] == "IDLE"


def test_get_status_robot_unreachable():
    """GET /api/status should return error dict when robot is unreachable."""
    with patch("main.robot") as mock_robot:
        mock_robot.get_status = AsyncMock(
            side_effect=RobotConnectionError("Connection refused")
        )
        response = client.get("/api/status")
        assert response.status_code == 200
        assert "error" in response.json()


# ── Move endpoint ──────────────────────────────────────────────────────────


def test_move_valid_coordinates():
    """POST /api/move with valid coordinates should return success message."""
    with patch("main.robot") as mock_robot:
        mock_robot.move = AsyncMock(return_value={"message": "Navigating to (5, 10)"})
        response = client.post("/api/move", params={"x": 5, "y": 10})
        assert response.status_code == 200
        assert "message" in response.json()


def test_move_invalid_coordinates_out_of_range():
    """POST /api/move with coordinates > 20 should return error."""
    with patch("main.robot") as mock_robot:
        mock_robot.move = AsyncMock(
            side_effect=ValueError("Coordinates out of range: (25, 0). Must be 0-20.")
        )
        response = client.post("/api/move", params={"x": 25, "y": 0})
        assert response.status_code == 200
        assert "error" in response.json() or response.status_code == 422


def test_move_invalid_coordinates_negative():
    """POST /api/move with negative coordinates should return error."""
    with patch("main.robot") as mock_robot:
        mock_robot.move = AsyncMock(
            side_effect=ValueError("Coordinates out of range: (-1, 5). Must be 0-20.")
        )
        response = client.post("/api/move", params={"x": -1, "y": 5})
        assert response.status_code == 200
        assert "error" in response.json() or response.status_code == 422


def test_move_robot_unreachable():
    """POST /api/move should return error dict when robot is unreachable."""
    with patch("main.robot") as mock_robot:
        mock_robot.move = AsyncMock(side_effect=RobotConnectionError("Timeout"))
        response = client.post("/api/move", params={"x": 5, "y": 5})
        assert response.status_code == 200
        assert "error" in response.json()


# ── Reset endpoint ─────────────────────────────────────────────────────────


def test_reset_success():
    """POST /api/reset should return success message."""
    with patch("main.robot") as mock_robot:
        mock_robot.reset = AsyncMock(return_value={"message": "Simulation reset."})
        response = client.post("/api/reset")
        assert response.status_code == 200
        assert response.json()["message"] == "Simulation reset."


def test_reset_robot_unreachable():
    """POST /api/reset should return error dict when robot is unreachable."""
    with patch("main.robot") as mock_robot:
        mock_robot.reset = AsyncMock(side_effect=RobotConnectionError("Timeout"))
        response = client.post("/api/reset")
        assert response.status_code == 200
        assert "error" in response.json()
