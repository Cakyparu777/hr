from fastapi import APIRouter, Depends, Query
from typing import List
from app.models.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash
from app.core.security_utils import validate_password_strength, sanitize_string
from app.core.dependencies import get_current_admin_user, get_current_user
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.core.logging_config import get_logger
from app.core.config import settings
from app.db.dynamodb import (
    get_all_users, get_user_by_id, create_user, 
    update_user, delete_user, get_user_by_email
)
from app.db.dynamodb import create_audit_log
from app.db.pagination import validate_pagination_params
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user = Depends(get_current_admin_user)
):
    """Get all users (admin only)."""
    page, page_size = validate_pagination_params(page, page_size)
    users, last_key = await get_all_users(page=page, page_size=page_size)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user = Depends(get_current_admin_user)):
    """Get a specific user (admin only)."""
    user = await get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User")
    return user

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user_endpoint(user_data: UserCreate, current_user = Depends(get_current_admin_user)):
    """Create a new user (admin only)."""
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
    
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "role": user_data.role.value,
        "password_hash": get_password_hash(user_data.password),
        "must_change_password": True
    }
    
    user = await create_user(user_dict)
    await create_audit_log("user_created", current_user["user_id"], {"created_user_id": user["user_id"]})
    logger.info("User created", created_user_id=user["user_id"], created_by=current_user["user_id"])
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str, 
    user_data: UserUpdate, 
    current_user = Depends(get_current_admin_user)
):
    """Update a user (admin only)."""
    existing_user = await get_user_by_id(user_id)
    if not existing_user:
        raise NotFoundError("User")
    
    update_dict = {}
    if user_data.name is not None:
        update_dict["name"] = sanitize_string(user_data.name, max_length=255)
    if user_data.email is not None:
        # Sanitize and normalize email
        email = sanitize_string(user_data.email.lower(), max_length=255)
        # Check if email is already taken by another user
        email_user = await get_user_by_email(email)
        if email_user and email_user["user_id"] != user_id:
            raise ConflictError("Email already registered")
        update_dict["email"] = email
    if user_data.role is not None:
        update_dict["role"] = user_data.role.value
    if user_data.password is not None:
        # Validate password strength
        is_valid, errors = validate_password_strength(user_data.password)
        if not is_valid:
            raise ValidationError(f"Password validation failed: {', '.join(errors)}")
        update_dict["password_hash"] = get_password_hash(user_data.password)
    
    updated_user = await update_user(user_id, update_dict)
    await create_audit_log("user_updated", current_user["user_id"], {"updated_user_id": user_id})
    logger.info("User updated", updated_user_id=user_id, updated_by=current_user["user_id"])
    return updated_user

@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(user_id: str, current_user = Depends(get_current_admin_user)):
    """Delete a user (admin only)."""
    if user_id == current_user["user_id"]:
        raise ValidationError("Cannot delete your own account")
    
    existing_user = await get_user_by_id(user_id)
    if not existing_user:
        raise NotFoundError("User")
    
    await delete_user(user_id)
    await create_audit_log("user_deleted", current_user["user_id"], {"deleted_user_id": user_id})
    logger.info("User deleted", deleted_user_id=user_id, deleted_by=current_user["user_id"])
    return None

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    password_data: dict,
    current_user = Depends(get_current_admin_user)
):
    """Reset a user's password (admin only)."""
    existing_user = await get_user_by_id(user_id)
    if not existing_user:
        raise NotFoundError("User")
    
    new_password = password_data.get("new_password")
    if not new_password:
        raise ValidationError("new_password is required")
    
    # Validate password strength
    is_valid, errors = validate_password_strength(new_password)
    if not is_valid:
        raise ValidationError(f"Password validation failed: {', '.join(errors)}")
    
    update_dict = {"password_hash": get_password_hash(new_password), "must_change_password": True}
    await update_user(user_id, update_dict)
    await create_audit_log("password_reset", current_user["user_id"], {"reset_user_id": user_id})
    logger.info("Password reset", reset_user_id=user_id, reset_by=current_user["user_id"])
    return {"message": "Password reset successfully"}

