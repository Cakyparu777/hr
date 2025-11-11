from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from app.core.config import settings
from app.db.dynamodb import create_timelog, update_timelog, get_timelog_by_id, get_holidays_as_dates, get_timelogs_by_user_and_exact_time, get_timelogs_by_user

def calculate_hours(start_time: datetime, end_time: datetime, break_duration: float = 0.0) -> float:
    """Calculate total hours worked."""
    if end_time <= start_time:
        raise ValueError("End time must be after start time")
    delta = end_time - start_time
    total_seconds = delta.total_seconds()
    total_hours = (total_seconds / 3600) - break_duration
    return max(0, round(total_hours, 2))

async def is_overtime_day(start_time: datetime) -> bool:
    """Check if a day is automatically overtime (weekends or holidays)."""
    holidays = await get_holidays_as_dates()
    if start_time.date() in holidays:
        return True
    # Weekend (Saturday=5, Sunday=6)
    if start_time.weekday() >= 5:
        return True
    return False

async def calculate_daily_overtime(user_id: str, date: datetime) -> None:
    """
    Recalculate overtime for all logs on a specific day based on daily totals.
    Overtime = max(0, total_hours - (entries * OVERTIME_THRESHOLD_HOURS))
    Distributes overtime proportionally across all logs for that day.
    Only applies to WORK attendance type logs.
    """
    # Get all logs for this user (we'll filter by date in Python to handle timezones correctly)
    all_user_logs = await get_timelogs_by_user(user_id)
    
    # Filter logs for the specific date and WORK attendance type only
    same_day_logs = []
    target_date = date.date() if isinstance(date, datetime) else date
    
    for log in all_user_logs:
        start_time = log.get("start_time")
        if not start_time:
            continue
        
        # Only process WORK attendance type logs for overtime calculation
        attendance_type = log.get("attendance_type", "work")
        if attendance_type != "work":
            continue
        
        # Handle both datetime objects and strings
        if isinstance(start_time, datetime):
            log_date = start_time.date()
        elif isinstance(start_time, str):
            try:
                log_date = datetime.fromisoformat(start_time.replace('Z', '+00:00')).date()
            except:
                continue
        else:
            continue
        
        # Check if log is on the target date
        if log_date == target_date:
            same_day_logs.append(log)
    
    if not same_day_logs:
        return
    
    # Check if it's a weekend or holiday (all hours are overtime)
    is_holiday_or_weekend = await is_overtime_day(date if isinstance(date, datetime) else datetime.combine(date, datetime.min.time()))
    
    # Calculate daily totals (only for WORK logs)
    total_entries = len(same_day_logs)
    total_hours = sum(float(log.get("total_hours", 0)) for log in same_day_logs)
    
    # Calculate overtime
    if is_holiday_or_weekend:
        # All hours are overtime on weekends/holidays
        daily_overtime_hours = total_hours
    else:
        # Expected hours = entries * threshold
        expected_hours = total_entries * settings.OVERTIME_THRESHOLD_HOURS
        # Overtime = excess hours beyond expected
        daily_overtime_hours = max(0, total_hours - expected_hours)
    
    # Distribute overtime proportionally across logs
    # Each log gets: (log_hours / total_hours) * daily_overtime_hours
    for log in same_day_logs:
        log_hours = float(log.get("total_hours", 0))
        
        if total_hours > 0 and daily_overtime_hours > 0:
            # Proportional distribution
            overtime_hours = round((log_hours / total_hours) * daily_overtime_hours, 2)
        else:
            overtime_hours = 0.0
        
        is_overtime = overtime_hours > 0
        
        # Update the log with new overtime calculations
        update_data = {
            "is_overtime": is_overtime,
            "overtime_hours": overtime_hours
        }
        
        await update_timelog(log["log_id"], update_data)

async def create_time_entry(user_id: str, start_time: datetime, end_time: datetime, 
                           break_duration: float = 0.0, context: Optional[str] = None,
                           attendance_type: str = "work", work_location: Optional[str] = None) -> dict:
    """Create a new time entry with automatic calculations."""
    # Disallow duplicate exact time
    existing_logs = await get_timelogs_by_user_and_exact_time(user_id, start_time, end_time)
    if existing_logs:
        raise ValueError("A time log with the exact start and end time already exists for this user.")

    # Enforce max 1 log per day only if configured
    if not settings.ALLOW_MULTIPLE_LOGS_PER_DAY:
        day_start = datetime(start_time.year, start_time.month, start_time.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        same_day_logs = await get_timelogs_by_user(user_id, start_date=day_start, end_date=day_end)
        if same_day_logs:
            raise ValueError("Only one time log is allowed per day.")

    total_hours = calculate_hours(start_time, end_time, break_duration)
    
    # Initially set overtime to False and overtime_hours to 0
    # Will be recalculated after creation based on daily totals
    # Note: Overtime calculation only applies to WORK attendance type
    timelog_data = {
        "user_id": user_id,
        "start_time": start_time,
        "end_time": end_time,
        "break_duration": break_duration,
        "total_hours": total_hours,
        "is_overtime": False,
        "overtime_hours": 0.0,
        "context": context,
        "attendance_type": attendance_type,
        "work_location": work_location
    }
    
    log = await create_timelog(timelog_data)
    
    # Recalculate overtime for all logs on this day (only for WORK attendance type)
    # Overtime only applies to work days, not leave days
    if attendance_type == "work":
        await calculate_daily_overtime(user_id, start_time)
    
    # Get the updated log with recalculated overtime
    updated_log = await get_timelog_by_id(log["log_id"])
    return updated_log or log

async def update_time_entry(log_id: str, start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None,
                            break_duration: Optional[float] = None,
                            context: Optional[str] = None,
                            attendance_type: Optional[str] = None,
                            work_location: Optional[str] = None) -> Optional[dict]:
    """Update a time entry with recalculated hours."""
    existing_log = await get_timelog_by_id(log_id)
    if not existing_log:
        return None
    
    # Use existing values if not provided
    start = start_time or datetime.fromisoformat(existing_log["start_time"])
    end = end_time or datetime.fromisoformat(existing_log["end_time"])
    break_dur = break_duration if break_duration is not None else existing_log.get("break_duration", 0.0)

    # Enforce max 1 log per day only if configured (exclude current log)
    if not settings.ALLOW_MULTIPLE_LOGS_PER_DAY:
        day_start = datetime(start.year, start.month, start.day, 0, 0, 0)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        same_day_logs = await get_timelogs_by_user(existing_log["user_id"], start_date=day_start, end_date=day_end)
        if any(l["log_id"] != log_id for l in same_day_logs):
            raise ValueError("Only one time log is allowed per day.")

    # Recalculate total hours
    total_hours = calculate_hours(start, end, break_dur)
    
    # Get the date for overtime recalculation
    date_for_recalc = start
    
    # Get attendance_type from update or existing log
    final_attendance_type = attendance_type if attendance_type is not None else existing_log.get("attendance_type", "work")
    
    update_data = {
        "start_time": start,
        "end_time": end,
        "break_duration": break_dur,
        "total_hours": total_hours,
        # Overtime will be recalculated below
    }
    
    # Include context if explicitly provided (None means don't update, empty string means clear)
    if context is not None:
        update_data["context"] = context if context else ""
    
    # Include attendance_type and work_location if provided
    if attendance_type is not None:
        update_data["attendance_type"] = attendance_type
    if work_location is not None:
        update_data["work_location"] = work_location
    
    # Update the log
    updated_log = await update_timelog(log_id, update_data)
    
    # Recalculate overtime for all logs on this day (only for WORK attendance type)
    if final_attendance_type == "work":
        await calculate_daily_overtime(existing_log["user_id"], date_for_recalc)
    
    # Get the updated log with recalculated overtime
    final_log = await get_timelog_by_id(log_id)
    return final_log

