"""
Integration Tests — API Routes
===============================
Tests all API endpoints with proper authentication headers.
"""
from robot_client import RobotStatus, RobotConnectionError
from auth import hash_password, create_access_token
from models import User
from database import get_db, Base
from main import app
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

MOCK_STATUS = RobotStatus(
    {
        "id": "XR-900",
        "position": {"x": 0, "y": 0},
        "battery": 100.0,
        "status": "IDLE",
    }
)


def get_commander_token():
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    existing = db.query(User).filter(User.username == "test_commander").first()
    if not existing:
        user = User(
            username="test_commander",
            password_hash=hash_password("password123"),
            role="commander",
        )
        db.add(user)
        db.commit()
    db.close()
    return create_access_token({"sub": "test_commander", "role": "commander"})


def get_viewer_token():
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    existing = db.query(User).filter(User.username == "test_viewer").first()
    if not existing:
        user = User(
            username="test_viewer",
            password_hash=hash_password("password123"),
            role="viewer",
        )
        db.add(user)
        db.commit()
    db.close()
    return create_access_token({"sub": "test_viewer", "role": "viewer"})


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_new_user():
    import time
    response = client.post("/auth/register", json={
        "username": f"newuser_{int(time.time())}",
        "password": "password123",
    })
    assert response.status_code == 201


def test_register_duplicate_user():
    client.post(
        "/auth/register",
        json={
            "username": "duplicateuser",
            "password": "password123",
        },
    )
    response = client.post(
        "/auth/register",
        json={
            "username": "duplicateuser",
            "password": "password123",
        },
    )
    assert response.status_code == 409


def test_login_valid_credentials():
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "password": "password123",
        },
    )
    response = client.post(
        "/auth/login",
        json={
            "username": "loginuser",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials():
    response = client.post(
        "/auth/login",
        json={
            "username": "loginuser",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


def test_get_status_unauthenticated():
    response = client.get("/api/status")
    assert response.status_code == 401


def test_get_status_success():
    token = get_viewer_token()
    with patch("main.robot") as mock_robot:
        mock_robot.get_status = AsyncMock(return_value=MOCK_STATUS)
        response = client.get(
            "/api/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == "XR-900"


def test_get_status_robot_unreachable():
    token = get_viewer_token()
    with patch("main.robot") as mock_robot:
        mock_robot.get_status = AsyncMock(
            side_effect=RobotConnectionError("Connection refused")
        )
        response = client.get(
            "/api/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "error" in response.json()


def test_move_unauthenticated():
    response = client.post("/api/move", params={"x": 5, "y": 5})
    assert response.status_code == 401


def test_move_viewer_forbidden():
    token = get_viewer_token()
    response = client.post(
        "/api/move",
        params={"x": 5, "y": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_move_valid_coordinates():
    token = get_commander_token()
    with patch("main.robot") as mock_robot:
        mock_robot.move = AsyncMock(
            return_value={"message": "Navigating to (5, 10)"})
        response = client.post(
            "/api/move",
            params={"x": 5, "y": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


def test_move_robot_unreachable():
    token = get_commander_token()
    with patch("main.robot") as mock_robot:
        mock_robot.move = AsyncMock(
            side_effect=RobotConnectionError("Timeout"))
        response = client.post(
            "/api/move",
            params={"x": 5, "y": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "error" in response.json()


def test_reset_unauthenticated():
    response = client.post("/api/reset")
    assert response.status_code == 401


def test_reset_viewer_forbidden():
    token = get_viewer_token()
    response = client.post(
        "/api/reset",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_reset_success():
    token = get_commander_token()
    with patch("main.robot") as mock_robot:
        mock_robot.reset = AsyncMock(
            return_value={"message": "Simulation reset."})
        response = client.post(
            "/api/reset",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


def test_get_logs_unauthenticated():
    response = client.get("/api/logs")
    assert response.status_code == 401


def test_get_logs_authenticated():
    token = get_viewer_token()
    response = client.get(
        "/api/logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
