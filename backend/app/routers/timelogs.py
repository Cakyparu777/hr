from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import datetime
from app.models.timelog import TimeLogCreate, TimeLogUpdate, TimeLogResponse, TimeLogFilter
from app.core.dependencies import get_current_user, get_current_accountant_user
from app.core.exceptions import ValidationError, NotFoundError, AuthorizationError
from app.core.security_utils import sanitize_input
from app.core.logging_config import get_logger
from app.core.config import settings
from app.services.timelog_service import create_time_entry, update_time_entry
from app.db.dynamodb import (
    get_timelog_by_id, get_timelogs_by_user, get_all_timelogs,
    delete_timelog, create_audit_log
)
from app.db.pagination import validate_pagination_params

logger = get_logger(__name__)

router = APIRouter()

@router.post("/", response_model=TimeLogResponse, status_code=201)
async def create_timelog_endpoint(
    timelog_data: TimeLogCreate,
    current_user = Depends(get_current_user)
):
    """Create a new time log entry."""
    # Sanitize context if provided
    if timelog_data.context:
        timelog_data.context = sanitize_input(timelog_data.context, max_length=10000)
    
    # Validate business rules
    if timelog_data.end_time <= timelog_data.start_time:
        raise ValidationError("End time must be after start time")
    
    total_hours = ((timelog_data.end_time - timelog_data.start_time).total_seconds() / 3600) - (timelog_data.break_duration or 0.0)
    if total_hours > settings.MAX_HOURS_PER_DAY:
        raise ValidationError(f"Cannot log more than {settings.MAX_HOURS_PER_DAY} hours in a day")
    
    if timelog_data.break_duration and timelog_data.break_duration < 0:
        raise ValidationError("Break duration cannot be negative")
    
    # Validate work_location is required when attendance_type is WORK
    from app.models.attendance import AttendanceType
    if timelog_data.attendance_type == AttendanceType.WORK and not timelog_data.work_location:
        raise ValidationError("Work location is required when attendance type is Work (出動)")
    
    try:
        log = await create_time_entry(
            user_id=current_user["user_id"],
            start_time=timelog_data.start_time,
            end_time=timelog_data.end_time,
            break_duration=timelog_data.break_duration or 0.0,
            context=timelog_data.context,
            attendance_type=timelog_data.attendance_type.value if hasattr(timelog_data.attendance_type, 'value') else timelog_data.attendance_type,
            work_location=timelog_data.work_location.value if timelog_data.work_location and hasattr(timelog_data.work_location, 'value') else timelog_data.work_location
        )
        await create_audit_log("timelog_created", current_user["user_id"], {"log_id": log["log_id"]})
        logger.info("Timelog created", log_id=log["log_id"], user_id=current_user["user_id"])
        return log
    except ValueError as e:
        raise ValidationError(str(e))

@router.get("/my-logs", response_model=List[TimeLogResponse])
async def get_my_timelogs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get current user's time logs."""
    logs = await get_timelogs_by_user(
        current_user["user_id"],
        start_date=start_date,
        end_date=end_date
    )
    return logs

@router.get("/", response_model=List[TimeLogResponse])
async def get_all_timelogs_endpoint(
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    is_overtime: Optional[bool] = Query(None),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user = Depends(get_current_accountant_user)
):
    """Get all time logs with filters (accountant/admin only)."""
    # Validate pagination
    page, page_size = validate_pagination_params(page, page_size)
    
    logs, last_key = await get_all_timelogs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        is_overtime=is_overtime,
        page=page,
        page_size=page_size
    )
    return logs

@router.get("/{log_id}", response_model=TimeLogResponse)
async def get_timelog(log_id: str, current_user = Depends(get_current_user)):
    """Get a specific time log."""
    log = await get_timelog_by_id(log_id)
    if not log:
        raise NotFoundError("Time log")
    
    # Employees can only view their own logs
    if current_user["role"] == "employee" and log["user_id"] != current_user["user_id"]:
        raise AuthorizationError("Not enough permissions to view this time log")
    
    return log

@router.put("/{log_id}", response_model=TimeLogResponse)
async def update_timelog_endpoint(
    log_id: str,
    timelog_data: TimeLogUpdate,
    current_user = Depends(get_current_user)
):
    """Update a time log entry."""
    existing_log = await get_timelog_by_id(log_id)
    if not existing_log:
        raise NotFoundError("Time log")
    
    # Employees can only edit their own logs
    if current_user["role"] == "employee" and existing_log["user_id"] != current_user["user_id"]:
        raise AuthorizationError("Not enough permissions to edit this time log")
    
    # Check if log is too old to edit
    created_at = datetime.fromisoformat(existing_log["created_at"])
    days_old = (datetime.utcnow() - created_at).days
    if current_user["role"] == "employee" and days_old > settings.MAX_EDIT_DAYS:
        raise ValidationError(f"Cannot edit logs older than {settings.MAX_EDIT_DAYS} days")
    
    # Sanitize context if provided
    if timelog_data.context is not None:
        timelog_data.context = sanitize_input(timelog_data.context, max_length=10000) if timelog_data.context else ""
    
    # Validate business rules if times are being updated
    if timelog_data.start_time and timelog_data.end_time:
        if timelog_data.end_time <= timelog_data.start_time:
            raise ValidationError("End time must be after start time")
    
    # Validate work_location if attendance_type is being set to WORK
    from app.models.attendance import AttendanceType
    final_attendance_type = timelog_data.attendance_type if timelog_data.attendance_type is not None else existing_log.get("attendance_type", "work")
    if final_attendance_type == AttendanceType.WORK.value or (isinstance(final_attendance_type, AttendanceType) and final_attendance_type == AttendanceType.WORK):
        if timelog_data.work_location is None and existing_log.get("work_location") is None:
            raise ValidationError("Work location is required when attendance type is Work (出動)")
    
    try:
        updated_log = await update_time_entry(
            log_id=log_id,
            start_time=timelog_data.start_time,
            end_time=timelog_data.end_time,
            break_duration=timelog_data.break_duration,
            context=timelog_data.context,
            attendance_type=timelog_data.attendance_type.value if timelog_data.attendance_type and hasattr(timelog_data.attendance_type, 'value') else timelog_data.attendance_type,
            work_location=timelog_data.work_location.value if timelog_data.work_location and hasattr(timelog_data.work_location, 'value') else timelog_data.work_location
        )
        await create_audit_log("timelog_updated", current_user["user_id"], {"log_id": log_id})
        logger.info("Timelog updated", log_id=log_id, user_id=current_user["user_id"])
        return updated_log
    except ValueError as e:
        raise ValidationError(str(e))

@router.delete("/{log_id}", status_code=204)
async def delete_timelog_endpoint(log_id: str, current_user = Depends(get_current_user)):
    """Delete a time log entry."""
    from app.services.timelog_service import calculate_daily_overtime
    
    existing_log = await get_timelog_by_id(log_id)
    if not existing_log:
        raise NotFoundError("Time log")
    
    # Employees can only delete their own logs
    if current_user["role"] == "employee" and existing_log["user_id"] != current_user["user_id"]:
        raise AuthorizationError("Not enough permissions to delete this time log")
    
    # Check if log is too old to delete
    # Handle created_at - it might be a datetime object (from normalize_timelog_item) or a string
    created_at_value = existing_log.get("created_at")
    if isinstance(created_at_value, datetime):
        # If it's timezone-aware, convert to UTC naive datetime
        if created_at_value.tzinfo is not None:
            created_at = created_at_value.replace(tzinfo=None)
        else:
            created_at = created_at_value
    elif isinstance(created_at_value, str):
        try:
            created_at = datetime.fromisoformat(created_at_value.replace('Z', '+00:00'))
            # Convert to naive UTC if timezone-aware
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)
        except (ValueError, AttributeError):
            # Fallback: use current time if created_at is invalid
            created_at = datetime.utcnow()
    else:
        # Fallback: use current time if created_at is missing or invalid
        created_at = datetime.utcnow()
    
    days_old = (datetime.utcnow() - created_at).days
    if current_user["role"] == "employee" and days_old > settings.MAX_EDIT_DAYS:
        raise ValidationError(f"Cannot delete logs older than {settings.MAX_EDIT_DAYS} days")
    
    # Get the date for overtime recalculation before deleting
    # Handle start_time - it might be a datetime object or a string
    start_time_value = existing_log.get("start_time")
    if isinstance(start_time_value, datetime):
        start_time = start_time_value
        # Convert to naive UTC if timezone-aware for consistency
        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)
    elif isinstance(start_time_value, str):
        try:
            start_time = datetime.fromisoformat(start_time_value.replace('Z', '+00:00'))
            # Convert to naive UTC if timezone-aware
            if start_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=None)
        except (ValueError, AttributeError):
            raise ValidationError("Invalid start_time in time log")
    else:
        raise ValidationError("Invalid start_time in time log")
    
    user_id = existing_log["user_id"]
    
    await delete_timelog(log_id)
    
    # Recalculate overtime for all remaining logs on this day
    await calculate_daily_overtime(user_id, start_time)
    
    await create_audit_log("timelog_deleted", current_user["user_id"], {"log_id": log_id})
    logger.info("Timelog deleted", log_id=log_id, user_id=current_user["user_id"])
    return None

