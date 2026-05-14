"""
Unit Tests — Coordinate Validation & Robot Client Logic
=======================================================
These tests cover pure logic with no network or database required.
Pattern: Arrange → Act → Assert
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Coordinate validator (mirrors the logic in robot_client.py) ────────────

def is_valid_target(x, y):
    """Validate that coordinates are integers within the 21x21 grid (0-20)."""
    if not isinstance(x, int) or not isinstance(y, int):
        return False
    if x < 0 or x > 20 or y < 0 or y > 20:
        return False
    return True


# ── Tests ──────────────────────────────────────────────────────────────────

def test_valid_coordinates_centre():
    """A coordinate in the middle of the grid should be valid."""
    assert is_valid_target(10, 10) is True


def test_valid_coordinates_origin():
    """The charging station at (0,0) should be a valid target."""
    assert is_valid_target(0, 0) is True


def test_valid_coordinates_max_boundary():
    """The far corner (20,20) is the maximum valid coordinate."""
    assert is_valid_target(20, 20) is True


def test_invalid_coordinates_exceed_max():
    """Coordinates above 20 are outside the grid and must be rejected."""
    assert is_valid_target(21, 0) is False
    assert is_valid_target(0, 21) is False


def test_invalid_coordinates_negative():
    """Negative coordinates are outside the grid and must be rejected."""
    assert is_valid_target(-1, 0) is False
    assert is_valid_target(0, -1) is False


def test_invalid_coordinates_both_out_of_range():
    """Both coordinates out of range should be rejected."""
    assert is_valid_target(150, -10) is False


def test_invalid_coordinates_float():
    """Float coordinates must be rejected — the API requires integers."""
    assert is_valid_target(5.5, 3) is False
    assert is_valid_target(3, 5.5) is False


def test_invalid_coordinates_string():
    """String inputs must be rejected."""
    assert is_valid_target("5", 3) is False
    assert is_valid_target(3, "five") is False


def test_invalid_coordinates_none():
    """None inputs must be rejected."""
    assert is_valid_target(None, 3) is False
    assert is_valid_target(3, None) is False


def test_boundary_just_inside_max():
    """19 is just inside the maximum boundary — should be valid."""
    assert is_valid_target(19, 19) is True


def test_boundary_just_outside_max():
    """21 is just outside the maximum boundary — should be invalid."""
    assert is_valid_target(21, 21) is False


# ── RobotStatus data class tests ───────────────────────────────────────────

from robot_client import RobotStatus


def test_robot_status_parses_correctly():
    """RobotStatus should correctly parse a valid API response."""
    data = {
        "id": "XR-900",
        "position": {"x": 5, "y": 10},
        "battery": 85.0,
        "status": "IDLE",
    }
    status = RobotStatus(data)
    assert status.id == "XR-900"
    assert status.x == 5
    assert status.y == 10
    assert status.battery == 85.0
    assert status.status == "IDLE"


def test_robot_status_to_dict():
    """to_dict() should return a JSON-serializable dictionary."""
    data = {
        "id": "XR-900",
        "position": {"x": 3, "y": 7},
        "battery": 42.5,
        "status": "MOVING",
    }
    status = RobotStatus(data)
    result = status.to_dict()
    assert result["id"] == "XR-900"
    assert result["position"]["x"] == 3
    assert result["position"]["y"] == 7
    assert result["battery"] == 42.5
    assert result["status"] == "MOVING"


def test_robot_status_handles_missing_fields():
    """RobotStatus should use safe defaults if fields are missing."""
    status = RobotStatus({})
    assert status.id == "unknown"
    assert status.x == 0
    assert status.y == 0
    assert status.battery == 0.0
    assert status.status == "UNKNOWN"
