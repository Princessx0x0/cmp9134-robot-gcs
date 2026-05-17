"""
Ground Control Station — FastAPI Backend
==========================================
CMP9134 Robot Management System
"""

import logging
import os
import asyncio

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import create_tables, get_db, SessionLocal
from models import MissionLog
from auth import require_commander, require_viewer, seed_admin
from auth_routes import router as auth_router
from legacy_stats import router as legacy_stats_router
from robot_client import robot, RobotConnectionError

# ── Configuration ──────────────────────────────────────────────────────────
ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
ENABLE_ADVANCED_STATS = os.getenv(
    "FF_ADVANCED_STATS", "false").lower() == "true"

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

# ── App factory ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Ground Control Station",
    description="CMP9134 Robot Management System",
    version="1.0.0",
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(legacy_stats_router)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup_event():
    create_tables()
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


# ── Robot status ───────────────────────────────────────────────────────────
@app.get("/api/status")
async def get_status(current_user=Depends(require_viewer)):
    """Get current robot status. Requires authentication."""
    try:
        status = await robot.get_status()
        return status.to_dict()
    except RobotConnectionError as exc:
        logger.warning("Could not reach robot API: %s", exc)
        return {"error": str(exc)}


# ── Move robot ─────────────────────────────────────────────────────────────
@app.post("/api/move")
async def move_robot(
    x: int,
    y: int,
    current_user=Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Move robot to (x, y). Commander role required."""
    log = MissionLog(
        user_id=current_user.id,
        username=current_user.username,
        command_type="MOVE",
        target_x=x,
        target_y=y,
        outcome="PENDING",
    )
    try:
        result = await robot.move(x, y)
        log.outcome = "SUCCESS"
        return result
    except RobotConnectionError as exc:
        log.outcome = f"ERROR: {str(exc)}"
        logger.warning("Move command failed: %s", exc)
        return {"error": str(exc)}
    except ValueError as exc:
        log.outcome = f"REJECTED: {str(exc)}"
        logger.warning("Invalid coordinates: %s", exc)
        return {"error": str(exc)}
    finally:
        db.add(log)
        db.commit()


# ── Reset simulation ───────────────────────────────────────────────────────
@app.post("/api/reset")
async def reset_robot(
    current_user=Depends(require_commander),
    db: Session = Depends(get_db),
):
    """Reset the simulation. Commander role required."""
    log = MissionLog(
        user_id=current_user.id,
        username=current_user.username,
        command_type="RESET",
        target_x=None,
        target_y=None,
        outcome="PENDING",
    )
    try:
        result = await robot.reset()
        log.outcome = "SUCCESS"
        return result
    except RobotConnectionError as exc:
        log.outcome = f"ERROR: {str(exc)}"
        logger.warning("Reset command failed: %s", exc)
        return {"error": str(exc)}
    finally:
        db.add(log)
        db.commit()


@app.get("/api/map")
async def get_map(current_user=Depends(require_viewer)):
    """Get the full 21x21 obstacle map."""
    try:
        return await robot.get_map()
    except RobotConnectionError as exc:
        return {"error": str(exc)}

# ── Audit logs ─────────────────────────────────────────────────────────────


@app.get("/api/logs")
def get_logs(
    current_user=Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Return the last 50 mission log entries. Requires authentication."""
    logs = db.query(MissionLog).order_by(
        MissionLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": log.id,
            "username": log.username,
            "command": log.command_type,
            "target": (
                f"({log.target_x}, {log.target_y})" if log.target_x is not None else "-"
            ),
            "outcome": log.outcome,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


# ── WebSocket telemetry ────────────────────────────────────────────────────
@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    """Stream live robot telemetry to the frontend at 1Hz."""
    await websocket.accept()
    logger.info("Frontend client connected to telemetry WebSocket")
    try:
        while True:
            try:
                status = await robot.get_status()
                await websocket.send_json(status.to_dict())
            except Exception as e:
                logger.warning(f"Telemetry fetch failed: {e}")
                await websocket.send_json(
                    {
                        "error": "Robot unreachable",
                        "status": "DISCONNECTED",
                    }
                )
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("Frontend client disconnected from telemetry WebSocket")


# ── Feature flag endpoint ──────────────────────────────────────────────────
@app.get("/api/experimental_stats")
def get_experimental_stats():
    """Feature-flagged endpoint. Enable with FF_ADVANCED_STATS=true."""
    if not ENABLE_ADVANCED_STATS:
        return {"error": "Feature not yet available."}
    return {"status": "success", "data": "Advanced stats coming soon."}
