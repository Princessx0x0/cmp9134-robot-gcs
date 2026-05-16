"""
auth.py — Authentication & Authorisation
==========================================
Handles:
- Password hashing with bcrypt
- JWT token creation and verification
- FastAPI dependencies for protecting routes
- RBAC: require_commander, require_viewer
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import User

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ── Password hashing ────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── JWT Bearer scheme ────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer()


# ── Pydantic schemas ────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


# ── Helper functions ────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependencies ────────────────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT and return the current user. Raises 401 if invalid."""
    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_commander(current_user: User = Depends(get_current_user)) -> User:
    """Raises 403 if the user is not a commander."""
    if current_user.role != "commander":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Commander role required for this action",
        )
    return current_user


def require_viewer(current_user: User = Depends(get_current_user)) -> User:
    """Allows any authenticated user (viewer or commander)."""
    return current_user


# ── Seed default admin account ──────────────────────────────────────────────
def seed_admin(db: Session):
    """
    Create a default Commander account on startup if none exists.
    Credentials come from environment variables — never hardcoded.
    """
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")

    existing = db.query(User).filter(User.username == admin_username).first()
    if not existing:
        admin = User(
            username=admin_username,
            password_hash=hash_password(admin_password),
            role="commander",
        )
        db.add(admin)
        db.commit()
        logger.info(f"Default commander account created: {admin_username}")
    else:
        logger.info(f"Admin account already exists: {admin_username}")
