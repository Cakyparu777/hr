from fastapi import APIRouter, Depends, Request
from app.models.user import UserLogin, UserCreate, UserResponse
from app.core.security import (
    verify_password, get_password_hash, create_token_pair,
    decode_refresh_token, create_access_token
)
from app.core.security_utils import validate_password_strength, sanitize_string
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError, ValidationError, NotFoundError, ConflictError
)
from app.core.logging_config import get_logger
from app.db.dynamodb import (
    get_user_by_email, create_user, update_user,
    get_user_by_id, get_user_by_id_with_secret
)
from app.core.dependencies import get_current_user
from pydantic import BaseModel
from typing import Optional

logger = get_logger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(request: Request, user_data: UserCreate):
    """Register a new user (admin only in production)."""
    # Sanitize input
    user_data.name = sanitize_string(user_data.name, max_length=255)
    user_data.email = sanitize_string(user_data.email.lower(), max_length=255)
    
    # Validate password strength
    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        raise ValidationError(f"Password validation failed: {', '.join(errors)}")
    
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise ConflictError("Email already registered")
    
    # Create user
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "role": user_data.role.value,
        "password_hash": get_password_hash(user_data.password)
    }
    
    user = await create_user(user_dict)
    logger.info("User registered", user_id=user["user_id"], email=user_data.email)
    return user

@router.post("/login")
async def login(request: Request, credentials: UserLogin):
    """Login and get access token."""
    # Sanitize email
    credentials.email = sanitize_string(credentials.email.lower(), max_length=255)
    
    user = await get_user_by_email(credentials.email)
    if not user:
        logger.warning("Login attempt with invalid email", email=credentials.email)
        raise AuthenticationError("Incorrect email or password")
    
    if not verify_password(credentials.password, user["password_hash"]):
        logger.warning("Login attempt with invalid password", email=credentials.email, user_id=user["user_id"])
        raise AuthenticationError("Incorrect email or password")
    
    # Create token pair (access + refresh)
    tokens = create_token_pair(user["user_id"], user["role"])
    
    user.pop("password_hash", None)
    logger.info("User logged in", user_id=user["user_id"], email=credentials.email)
    
    return {
        **tokens,
        "user": user
    }

@router.post("/refresh")
async def refresh_token(request: Request, refresh_token_data: dict):
    """Refresh access token using refresh token."""
    refresh_token = refresh_token_data.get("refresh_token")
    if not refresh_token:
        raise ValidationError("refresh_token is required")
    
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise AuthenticationError("Invalid or expired refresh token")
    
    user_id = payload.get("sub")
    role = payload.get("role")
    
    if not user_id or not role:
        raise AuthenticationError("Invalid token payload")
    
    # Verify user still exists
    user = await get_user_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")
    
    # Create new access token
    access_token = create_access_token(data={"sub": user_id, "role": role})
    
    logger.info("Token refreshed", user_id=user_id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return current_user


class ChangePassword(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
async def change_password(
    payload: ChangePassword,
    current_user = Depends(get_current_user)
):
    """User self-service change password."""
    # Validate new password strength
    is_valid, errors = validate_password_strength(payload.new_password)
    if not is_valid:
        raise ValidationError(f"Password validation failed: {', '.join(errors)}")
    
    # Fetch full user including password_hash
    user = await get_user_by_id_with_secret(current_user["user_id"])
    if not user:
        raise NotFoundError("User")

    if not verify_password(payload.current_password, user["password_hash"]):
        logger.warning("Password change failed: incorrect current password", user_id=current_user["user_id"])
        raise ValidationError("Current password is incorrect")

    await update_user(current_user["user_id"], {
        "password_hash": get_password_hash(payload.new_password),
        "must_change_password": False
    })
    
    logger.info("Password changed", user_id=current_user["user_id"])
    return {"message": "Password changed successfully"}

