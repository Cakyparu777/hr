from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.models.user import UserLogin, UserCreate, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.db.dynamodb import get_user_by_email, create_user, update_user, get_user_by_id, get_user_by_id_with_secret
from app.core.dependencies import get_current_user
from pydantic import BaseModel
from typing import Optional
from botocore.exceptions import ClientError

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user (admin only in production)."""
    # Check if user already exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "role": user_data.role.value,
        "password_hash": get_password_hash(user_data.password)
    }
    
    user = await create_user(user_dict)
    return user

@router.post("/login")
async def login(credentials: UserLogin):
    """Login and get access token."""
    user = await get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    user.pop("password_hash", None)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return current_user



class ChangePassword(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
async def change_password(payload: ChangePassword, current_user = Depends(get_current_user)):
    """User self-service change password."""
    # fetch full user including password_hash
    user = await get_user_by_id_with_secret(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    await update_user(current_user["user_id"], {
        "password_hash": get_password_hash(payload.new_password),
        "must_change_password": False
    })
    return {"message": "Password changed successfully"}

