from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimeLogCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    break_duration: Optional[float] = 0.0  # in hours
    context: Optional[str] = None  # description of work done

class TimeLogUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    break_duration: Optional[float] = None
    context: Optional[str] = None

class TimeLogResponse(BaseModel):
    log_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    break_duration: float
    total_hours: float
    is_overtime: bool
    context: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TimeLogFilter(BaseModel):
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_overtime: Optional[bool] = None

