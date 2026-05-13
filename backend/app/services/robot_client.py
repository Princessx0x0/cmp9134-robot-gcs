"""
RobotClient - Singleton + Facade Pattern
========================================
Singleton: Only one instance exists across the entire application.
Facade: Hides HTTP complexity behind clean methods like move(x, y).
"""

import logging
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)

ROBOT_API_URL = "http://robot-sim:5000"


class RobotStatus:
    """Data class representing the robot current state."""

    def __init__(self, data: dict):
        self.id: str = data.get("id", "unknown")
        self.x: int = data.get("position", {}).get("x", 0)
        self.y: int = data.get("position", {}).get("y", 0)
        self.battery: float = data.get("battery", 0.0)
        self.status: str = data.get("status", "UNKNOWN")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "position": {"x": self.x, "y": self.y},
            "battery": self.battery,
            "status": self.status,
        }


class RobotClient:
    """
    Facade over the Virtual Robot REST API.
    Use RobotClient.get_instance() - do not instantiate directly.
    """

    _instance: Optional["RobotClient"] = None

    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=ROBOT_API_URL,
            timeout=httpx.Timeout(10.0),
        )
        self._connected = False
        logger.info(f"RobotClient initialised - target: {ROBOT_API_URL}")

    @classmethod
    def get_instance(cls) -> "RobotClient":
        """Return the single shared instance, creating it if needed."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    async def get_status(self) -> RobotStatus:
        """GET /api/status - returns robot position, battery and status."""
        try:
            response = await self._client.get("/api/status")
            response.raise_for_status()
            self._connected = True
            return RobotStatus(response.json())
        except httpx.RequestError as e:
            self._connected = False
            logger.error(f"Robot unreachable on get_status: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    async def move(self, x: int, y: int) -> dict:
        """POST /api/move - moves robot to (x, y). Coordinates must be 0-20."""
        if not (0 <= x <= 20 and 0 <= y <= 20):
            raise ValueError(
                f"Coordinates out of range: ({x}, {y}). Must be 0-20.")
        try:
            response = await self._client.post("/api/move", json={"x": x, "y": y})
            response.raise_for_status()
            self._connected = True
            logger.info(f"Move command sent: ({x}, {y})")
            return response.json()
        except httpx.RequestError as e:
            self._connected = False
            logger.error(f"Robot unreachable on move({x}, {y}): {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True,
    )
    async def reset(self) -> dict:
        """POST /api/reset - resets simulation to initial state."""
        try:
            response = await self._client.post("/api/reset")
            response.raise_for_status()
            self._connected = True
            logger.info("Reset command sent")
            return response.json()
        except httpx.RequestError as e:
            self._connected = False
            logger.error(f"Robot unreachable on reset: {e}")
            raise

    async def get_map(self) -> dict:
        """GET /api/map - returns full 21x21 grid. 0=free, 1=obstacle."""
        try:
            response = await self._client.get("/api/map")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._connected = False
            logger.error(f"Robot unreachable on get_map: {e}")
            raise

    async def get_sensor_data(self) -> dict:
        """GET /api/sensor - returns N/S/E/W distances and 360 lidar array."""
        try:
            response = await self._client.get("/api/sensor")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._connected = False
            logger.error(f"Robot unreachable on get_sensor_data: {e}")
            raise

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def close(self):
        """Close the HTTP client cleanly on app shutdown."""
        await self._client.aclose()
        logger.info("RobotClient closed")
