from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from app.models.timelog import TimeLogCreate, TimeLogUpdate, TimeLogResponse, TimeLogFilter
from app.core.dependencies import get_current_user, get_current_accountant_user
from app.services.timelog_service import create_time_entry, update_time_entry
from app.db.dynamodb import (
    get_timelog_by_id, get_timelogs_by_user, get_all_timelogs,
    delete_timelog, create_audit_log
)

router = APIRouter()

@router.post("/", response_model=TimeLogResponse, status_code=status.HTTP_201_CREATED)
async def create_timelog_endpoint(
    timelog_data: TimeLogCreate,
    current_user = Depends(get_current_user)
):
    """Create a new time log entry."""
    try:
        log = await create_time_entry(
            user_id=current_user["user_id"],
            start_time=timelog_data.start_time,
            end_time=timelog_data.end_time,
            break_duration=timelog_data.break_duration or 0.0,
            context=timelog_data.context
        )
        await create_audit_log("timelog_created", current_user["user_id"], {"log_id": log["log_id"]})
        return log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

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
    current_user = Depends(get_current_accountant_user)
):
    """Get all time logs with filters (accountant/admin only)."""
    logs = await get_all_timelogs(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        is_overtime=is_overtime
    )
    return logs

@router.get("/{log_id}", response_model=TimeLogResponse)
async def get_timelog(log_id: str, current_user = Depends(get_current_user)):
    """Get a specific time log."""
    log = await get_timelog_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time log not found"
        )
    
    # Employees can only view their own logs
    if current_user["role"] == "employee" and log["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time log not found"
        )
    
    # Employees can only edit their own logs
    if current_user["role"] == "employee" and existing_log["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if log is too old to edit (e.g., more than 30 days)
    created_at = datetime.fromisoformat(existing_log["created_at"])
    days_old = (datetime.utcnow() - created_at).days
    if current_user["role"] == "employee" and days_old > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit logs older than 30 days"
        )
    
    try:
        updated_log = await update_time_entry(
            log_id=log_id,
            start_time=timelog_data.start_time,
            end_time=timelog_data.end_time,
            break_duration=timelog_data.break_duration,
            context=timelog_data.context
        )
        await create_audit_log("timelog_updated", current_user["user_id"], {"log_id": log_id})
        return updated_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timelog_endpoint(log_id: str, current_user = Depends(get_current_user)):
    """Delete a time log entry."""
    existing_log = await get_timelog_by_id(log_id)
    if not existing_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time log not found"
        )
    
    # Employees can only delete their own logs
    if current_user["role"] == "employee" and existing_log["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if log is too old to delete
    created_at = datetime.fromisoformat(existing_log["created_at"])
    days_old = (datetime.utcnow() - created_at).days
    if current_user["role"] == "employee" and days_old > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete logs older than 30 days"
        )
    
    success = await delete_timelog(log_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete time log"
        )
    
    await create_audit_log("timelog_deleted", current_user["user_id"], {"log_id": log_id})
    return None

