from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.leave_request import LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestResponse, LeaveStatus

class ApproveRequest(BaseModel):
    admin_notes: Optional[str] = None

class DeclineRequest(BaseModel):
    admin_notes: str
from app.core.dependencies import get_current_user, get_current_admin_user
from app.core.exceptions import ValidationError, NotFoundError, AuthorizationError
from app.core.security_utils import sanitize_input
from app.core.logging_config import get_logger
from app.db.dynamodb import (
    create_leave_request, get_leave_request_by_id, get_leave_requests_by_user,
    get_all_leave_requests, update_leave_request, delete_leave_request, create_audit_log
)

logger = get_logger(__name__)

router = APIRouter()

@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request_endpoint(
    leave_request_data: LeaveRequestCreate,
    current_user = Depends(get_current_user)
):
    """Create a new leave request (pending status)."""
    # Validate dates
    if leave_request_data.end_date < leave_request_data.start_date:
        raise ValidationError("End date must be after or equal to start date")
    
    # Sanitize description
    if leave_request_data.description:
        leave_request_data.description = sanitize_input(leave_request_data.description, max_length=5000)
    
    # Create leave request with pending status
    request_data = {
        "user_id": current_user["user_id"],
        "leave_type": leave_request_data.leave_type.value if hasattr(leave_request_data.leave_type, 'value') else leave_request_data.leave_type,
        "start_date": leave_request_data.start_date,
        "end_date": leave_request_data.end_date,
        "description": leave_request_data.description,
        "status": "pending",
        "half_day": leave_request_data.half_day
    }
    
    leave_request = await create_leave_request(request_data)
    await create_audit_log("leave_request_created", current_user["user_id"], {"request_id": leave_request["request_id"]})
    logger.info("Leave request created", request_id=leave_request["request_id"], user_id=current_user["user_id"])
    
    return leave_request

@router.get("/my-requests", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    status: Optional[LeaveStatus] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get current user's leave requests."""
    status_str = status.value if status and hasattr(status, 'value') else status
    requests = await get_leave_requests_by_user(current_user["user_id"], status=status_str)
    return requests

@router.get("/", response_model=List[LeaveRequestResponse])
async def get_all_leave_requests_endpoint(
    status: Optional[LeaveStatus] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user = Depends(get_current_admin_user)
):
    """Get all leave requests (admin only), optionally filtered by status or user."""
    status_str = status.value if status and hasattr(status, 'value') else status
    
    if user_id:
        # Get requests for specific user
        requests = await get_leave_requests_by_user(user_id, status=status_str)
    else:
        # Get all requests
        requests = await get_all_leave_requests(status=status_str)
    
    return requests

@router.get("/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(request_id: str, current_user = Depends(get_current_user)):
    """Get a specific leave request."""
    leave_request = await get_leave_request_by_id(request_id)
    if not leave_request:
        raise NotFoundError("Leave request")
    
    # Users can only view their own requests, unless they're admin
    if current_user["role"] != "admin" and leave_request["user_id"] != current_user["user_id"]:
        raise AuthorizationError("Not authorized to view this leave request")
    
    return leave_request

@router.put("/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: str,
    request_body: ApproveRequest,
    current_user = Depends(get_current_admin_user)
):
    """Approve a leave request (admin only)."""
    leave_request = await get_leave_request_by_id(request_id)
    if not leave_request:
        raise NotFoundError("Leave request")
    
    if leave_request["status"] != "pending":
        raise ValidationError(f"Leave request is already {leave_request['status']}")
    
    # Sanitize admin notes
    admin_notes = request_body.admin_notes
    if admin_notes:
        admin_notes = sanitize_input(admin_notes, max_length=2000)
    
    update_data = {
        "status": "approved",
        "admin_notes": admin_notes,
        "reviewed_at": datetime.utcnow().isoformat(),
        "reviewed_by": current_user["user_id"]
    }
    
    updated_request = await update_leave_request(request_id, update_data)
    await create_audit_log("leave_request_approved", current_user["user_id"], {"request_id": request_id})
    logger.info("Leave request approved", request_id=request_id, admin_user_id=current_user["user_id"])
    
    return updated_request

@router.put("/{request_id}/decline", response_model=LeaveRequestResponse)
async def decline_leave_request(
    request_id: str,
    request_body: DeclineRequest,
    current_user = Depends(get_current_admin_user)
):
    """Decline a leave request (admin only)."""
    leave_request = await get_leave_request_by_id(request_id)
    if not leave_request:
        raise NotFoundError("Leave request")
    
    if leave_request["status"] != "pending":
        raise ValidationError(f"Leave request is already {leave_request['status']}")
    
    # Sanitize admin notes
    admin_notes = sanitize_input(request_body.admin_notes, max_length=2000)
    
    update_data = {
        "status": "declined",
        "admin_notes": admin_notes,
        "reviewed_at": datetime.utcnow().isoformat(),
        "reviewed_by": current_user["user_id"]
    }
    
    updated_request = await update_leave_request(request_id, update_data)
    await create_audit_log("leave_request_declined", current_user["user_id"], {"request_id": request_id})
    logger.info("Leave request declined", request_id=request_id, admin_user_id=current_user["user_id"])
    
    return updated_request

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leave_request_endpoint(
    request_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a leave request (user can delete their own pending requests, admin can delete any)."""
    leave_request = await get_leave_request_by_id(request_id)
    if not leave_request:
        raise NotFoundError("Leave request")
    
    # Users can only delete their own pending requests
    if current_user["role"] != "admin":
        if leave_request["user_id"] != current_user["user_id"]:
            raise AuthorizationError("Not authorized to delete this leave request")
        if leave_request["status"] != "pending":
            raise ValidationError("Only pending requests can be deleted")
    
    await delete_leave_request(request_id)
    await create_audit_log("leave_request_deleted", current_user["user_id"], {"request_id": request_id})
    logger.info("Leave request deleted", request_id=request_id, user_id=current_user["user_id"])
    
    return None

