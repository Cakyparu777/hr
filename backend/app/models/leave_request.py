from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class LeaveType(str, Enum):
    """Leave types in Japanese (with English translations)"""
    STATUTORY_HOLIDAY = "statutory_holiday"  # 法定休日
    NON_STATUTORY_HOLIDAY = "non_statutory_holiday"  # 法定外休日
    PAID_LEAVE = "paid_leave"  # 有給休暇
    SPECIAL_LEAVE = "special_leave"  # 特別休暇

class LeaveStatus(str, Enum):
    """Leave request status"""
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"

class LeaveRequestCreate(BaseModel):
    """Create a leave request"""
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    description: str
    half_day: bool = False  # True if it's a half-day leave

class LeaveRequestUpdate(BaseModel):
    """Update a leave request (admin only)"""
    status: LeaveStatus
    admin_notes: Optional[str] = None  # Admin's notes when approving/declining

class LeaveRequestResponse(BaseModel):
    """Leave request response"""
    request_id: str
    user_id: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    description: str
    status: LeaveStatus
    half_day: bool
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # Admin user_id who reviewed
    
    class Config:
        from_attributes = True

