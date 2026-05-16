"""
models.py — SQLAlchemy ORM models
===================================
Defines the database tables for Users and Mission Logs.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MissionLog(Base):
    __tablename__ = "mission_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    command_type = Column(String, nullable=False)
    target_x = Column(Integer, nullable=True)
    target_y = Column(Integer, nullable=True)
    outcome = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
