from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.attendance import AttendanceType, WorkLocation

class TimeLogCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    break_duration: Optional[float] = 0.0  # in hours
    context: Optional[str] = None  # description of work done
    attendance_type: AttendanceType = AttendanceType.WORK  # 出動, 法定休日, 有給休暇, 特別休暇
    work_location: Optional[WorkLocation] = None  # 自社, 客先, 在宅 (required when attendance_type is WORK)

class TimeLogUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    break_duration: Optional[float] = None
    context: Optional[str] = None
    attendance_type: Optional[AttendanceType] = None
    work_location: Optional[WorkLocation] = None

class TimeLogResponse(BaseModel):
    log_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    break_duration: float
    total_hours: float
    is_overtime: bool
    overtime_hours: float = 0.0  # Hours that are overtime for this entry
    context: Optional[str] = None
    attendance_type: AttendanceType = AttendanceType.WORK
    work_location: Optional[WorkLocation] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TimeLogFilter(BaseModel):
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_overtime: Optional[bool] = None

