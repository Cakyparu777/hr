from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash
from app.core.dependencies import get_current_admin_user, get_current_user
from app.db.dynamodb import (
    get_all_users, get_user_by_id, create_user, 
    update_user, delete_user, get_user_by_email
)
from app.db.dynamodb import create_audit_log

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(current_user = Depends(get_current_admin_user)):
    """Get all users (admin only)."""
    users = await get_all_users()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user = Depends(get_current_admin_user)):
    """Get a specific user (admin only)."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user_data: UserCreate, current_user = Depends(get_current_admin_user)):
    """Create a new user (admin only)."""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "role": user_data.role.value,
        "password_hash": get_password_hash(user_data.password)
    }
    
    user = await create_user(user_dict)
    await create_audit_log("user_created", current_user["user_id"], {"created_user_id": user["user_id"]})
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_dict = {}
    if user_data.name is not None:
        update_dict["name"] = user_data.name
    if user_data.email is not None:
        # Check if email is already taken by another user
        email_user = await get_user_by_email(user_data.email)
        if email_user and email_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        update_dict["email"] = user_data.email
    if user_data.role is not None:
        update_dict["role"] = user_data.role.value
    if user_data.password is not None:
        update_dict["password_hash"] = get_password_hash(user_data.password)
    
    updated_user = await update_user(user_id, update_dict)
    await create_audit_log("user_updated", current_user["user_id"], {"updated_user_id": user_id})
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(user_id: str, current_user = Depends(get_current_admin_user)):
    """Delete a user (admin only)."""
    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    existing_user = await get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    await create_audit_log("user_deleted", current_user["user_id"], {"deleted_user_id": user_id})
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_password is required"
        )
    
    update_dict = {"password_hash": get_password_hash(new_password)}
    await update_user(user_id, update_dict)
    await create_audit_log("password_reset", current_user["user_id"], {"reset_user_id": user_id})
    return {"message": "Password reset successfully"}

