"""
auth_routes.py — Authentication API endpoints
===============================================
POST /auth/register — create a new viewer account
POST /auth/login    — returns a JWT token
GET  /auth/me       — returns current user info
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    All new accounts are assigned the 'viewer' role by default.
    The default commander account is seeded on startup via environment variables.
    """
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"New user registered: {user.username} (role: {user.role})")
    return {"message": "Account created successfully", "role": user.role}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate and return a JWT token.
    The token encodes the username and role, expires after 60 minutes.
    """
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": user.username, "role": user.role})
    logger.info(f"User logged in: {user.username} (role: {user.role})")
    return TokenResponse(
        access_token=token,
        role=user.role,
        username=user.username,
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }
