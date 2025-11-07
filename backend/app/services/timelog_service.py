from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings
from app.db.dynamodb import create_timelog, update_timelog, get_timelog_by_id, get_holidays_as_dates

def calculate_hours(start_time: datetime, end_time: datetime, break_duration: float = 0.0) -> float:
    """Calculate total hours worked."""
    if end_time <= start_time:
        raise ValueError("End time must be after start time")
    delta = end_time - start_time
    total_seconds = delta.total_seconds()
    total_hours = (total_seconds / 3600) - break_duration
    return max(0, round(total_hours, 2))

async def is_overtime(total_hours: float, start_time: datetime) -> bool:
    """Check if the hours worked exceed the overtime threshold or if it is a holiday."""
    holidays = await get_holidays_as_dates()
    if start_time.date() in holidays:
        return True
    return total_hours > settings.OVERTIME_THRESHOLD_HOURS

async def create_time_entry(user_id: str, start_time: datetime, end_time: datetime, 
                           break_duration: float = 0.0, context: Optional[str] = None) -> dict:
    """Create a new time entry with automatic calculations."""
    total_hours = calculate_hours(start_time, end_time, break_duration)
    overtime = await is_overtime(total_hours, start_time)
    
    timelog_data = {
        "user_id": user_id,
        "start_time": start_time,
        "end_time": end_time,
        "break_duration": break_duration,
        "total_hours": total_hours,
        "is_overtime": overtime,
        "context": context
    }
    
    return await create_timelog(timelog_data)

async def update_time_entry(log_id: str, start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None,
                            break_duration: Optional[float] = None,
                            context: Optional[str] = None) -> Optional[dict]:
    """Update a time entry with recalculated hours."""
    existing_log = await get_timelog_by_id(log_id)
    if not existing_log:
        return None
    
    # Use existing values if not provided
    start = start_time or datetime.fromisoformat(existing_log["start_time"])
    end = end_time or datetime.fromisoformat(existing_log["end_time"])
    break_dur = break_duration if break_duration is not None else existing_log.get("break_duration", 0.0)
    
    # Recalculate
    total_hours = calculate_hours(start, end, break_dur)
    overtime = await is_overtime(total_hours, start)
    
    update_data = {
        "start_time": start,
        "end_time": end,
        "break_duration": break_dur,
        "total_hours": total_hours,
        "is_overtime": overtime
    }
    
    # Include context if explicitly provided (None means don't update, empty string means clear)
    if context is not None:
        update_data["context"] = context if context else ""
    
    return await update_timelog(log_id, update_data)

