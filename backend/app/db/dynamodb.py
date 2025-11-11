import boto3
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
import uuid
from app.core.config import settings
from app.models.user import UserRole
from app.core.logging_config import get_logger
from app.core.exceptions import DatabaseError
from decimal import Decimal

logger = get_logger(__name__)


# Initialize DynamoDB client
dynamodb_kwargs = {
    'region_name': settings.AWS_REGION,
    'endpoint_url': settings.DYNAMODB_ENDPOINT_URL,
    'aws_access_key_id': 'dummy',
    'aws_secret_access_key': 'dummy'
}

dynamodb = boto3.resource('dynamodb', **dynamodb_kwargs)

# Get table references
users_table = dynamodb.Table(settings.DYNAMODB_USERS_TABLE)
timelogs_table = dynamodb.Table(settings.DYNAMODB_TIMELOGS_TABLE)
audit_table = dynamodb.Table(settings.DYNAMODB_AUDIT_TABLE)
holidays_table = dynamodb.Table(settings.DYNAMODB_HOLIDAYS_TABLE)
leave_requests_table = dynamodb.Table(settings.DYNAMODB_LEAVE_REQUESTS_TABLE)

def normalize_timelog_item(item: dict) -> dict:
    """Convert DynamoDB item to a normalized dict with proper types."""
    normalized = {}
    for key, value in item.items():
        if isinstance(value, Decimal):
            normalized[key] = float(value)
        elif isinstance(value, str) and key in ("start_time", "end_time", "created_at", "updated_at"):
            # Parse ISO format datetime strings
            try:
                # Handle various datetime formats
                if value.endswith('Z'):
                    value = value.replace('Z', '+00:00')
                normalized[key] = datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                # If parsing fails, keep as string (shouldn't happen in normal operation)
                normalized[key] = value
        else:
            normalized[key] = value
    # Ensure overtime_hours exists with default 0.0 for backward compatibility
    if "overtime_hours" not in normalized:
        normalized["overtime_hours"] = 0.0
    # Convert to float if it's still a Decimal (shouldn't happen after normalization, but just in case)
    if isinstance(normalized.get("overtime_hours"), Decimal):
        normalized["overtime_hours"] = float(normalized["overtime_hours"])
    # Ensure attendance_type and work_location have defaults for backward compatibility
    if "attendance_type" not in normalized:
        normalized["attendance_type"] = "work"
    return normalized

# Holiday operations
async def create_holiday(holiday_data: dict) -> dict:
    """Create a new holiday in DynamoDB."""
    holiday_id = str(uuid.uuid4())
    item = {
        "id": holiday_id,
        "name": holiday_data["name"],
        "date": holiday_data["date"].isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    holidays_table.put_item(Item=item)
    return item

async def get_all_holidays() -> List[dict]:
    """Get all holidays."""
    response = holidays_table.scan()
    return response.get("Items", [])

async def get_holiday_by_date(holiday_date: date) -> Optional[dict]:
    """Get a holiday by date. Since date is not a key, we need to scan and filter."""
    # Use ExpressionAttributeNames to escape reserved keyword "date"
    response = holidays_table.scan(
        FilterExpression="#date = :date",
        ExpressionAttributeNames={"#date": "date"},
        ExpressionAttributeValues={":date": holiday_date.isoformat()}
    )
    items = response.get("Items", [])
    return items[0] if items else None

async def create_holiday_if_not_exists(holiday_data: dict) -> Tuple[dict, bool]:
    """
    Create a holiday only if it doesn't already exist for that date.
    Returns (holiday_dict, was_created: bool)
    """
    holiday_date = holiday_data["date"]
    if isinstance(holiday_date, str):
        holiday_date = datetime.fromisoformat(holiday_date).date()
    elif isinstance(holiday_date, datetime):
        holiday_date = holiday_date.date()
    
    existing = await get_holiday_by_date(holiday_date)
    if existing:
        return existing, False  # Return existing holiday, not created
    
    # Create new holiday
    new_holiday = await create_holiday(holiday_data)
    return new_holiday, True  # Return new holiday, was created

async def get_holidays_as_dates() -> List[date]:
    """Get all holidays as a list of date objects."""
    holidays = await get_all_holidays()
    return [datetime.fromisoformat(h["date"]).date() for h in holidays]

async def delete_holiday(holiday_id: str) -> bool:
    """Delete a holiday by ID."""
    try:
        holidays_table.delete_item(Key={"id": holiday_id})
        return True
    except ClientError as e:
        logger.error("Failed to delete holiday", holiday_id=holiday_id, error=str(e))
        raise DatabaseError("Failed to delete holiday") from e

# User operations
async def create_user(user_data: dict) -> dict:
    """Create a new user in DynamoDB."""
    user_id = str(uuid.uuid4())
    item = {
        "user_id": user_id,
        "name": user_data["name"],
        "email": user_data["email"],
        "password_hash": user_data["password_hash"],
        "role": user_data["role"],
        "must_change_password": user_data.get("must_change_password", False),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None
    }
    users_table.put_item(Item=item)
    return item

async def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by email."""
    try:
        response = users_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": email}
        )
        items = response.get("Items", [])
        return items[0] if items else None
    except ClientError:
        return None

async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get a user by ID."""
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            return response["Item"]
        return None
    except ClientError:
        return None

async def get_user_by_id_with_secret(user_id: str) -> Optional[dict]:
    """Get a user by ID including password hash (for authentication)."""
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            return response["Item"]
        return None
    except ClientError:
        return None

async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """Update a user."""
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    for key, value in update_data.items():
        if value is not None:
            expression_attribute_values[f":{key}"] = value
            update_expression_parts.append(f"#{key} = :{key}")
            expression_attribute_names[f"#{key}"] = key
    
    if not update_expression_parts:
        return await get_user_by_id(user_id)
    
    update_expression_parts.append("#updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
    expression_attribute_names["#updated_at"] = "updated_at"
    
    update_expression = "SET " + ", ".join(update_expression_parts)
    
    try:
        users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="ALL_NEW"
        )
        return await get_user_by_id(user_id)
    except ClientError as e:
        logger.error("Failed to update user", user_id=user_id, error=str(e))
        raise DatabaseError("Failed to update user") from e

async def delete_user(user_id: str) -> bool:
    """Delete a user."""
    try:
        users_table.delete_item(Key={"user_id": user_id})
        return True
    except ClientError as e:
        logger.error("Failed to delete user", user_id=user_id, error=str(e))
        raise DatabaseError("Failed to delete user") from e

async def get_all_users(page: Optional[int] = None, page_size: Optional[int] = None,
                        last_evaluated_key: Optional[Dict[str, Any]] = None) -> tuple[List[dict], Optional[Dict[str, Any]]]:
    """Get all users with pagination."""
    scan_kwargs = {}
    
    if page_size:
        scan_kwargs["Limit"] = page_size
    if last_evaluated_key:
        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key
    
    try:
        response = users_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        last_key = response.get("LastEvaluatedKey")
        
        return items, last_key
    except ClientError as e:
        logger.error("Failed to get users", error=str(e), error_code=e.response.get("Error", {}).get("Code"))
        raise DatabaseError("Failed to retrieve users") from e

# TimeLog operations
async def create_timelog(timelog_data: dict) -> dict:
    """Create a new time log."""
    log_id = str(uuid.uuid4())
    item = {
        "log_id": log_id,
        "user_id": timelog_data["user_id"],
        "start_time": timelog_data["start_time"].isoformat(),
        "end_time": timelog_data["end_time"].isoformat(),
        "break_duration": Decimal(str(timelog_data.get("break_duration", 0.0))),
        "total_hours": Decimal(str(timelog_data["total_hours"])),
        "is_overtime": timelog_data.get("is_overtime", False),
        "overtime_hours": Decimal(str(timelog_data.get("overtime_hours", 0.0))),
        "context": timelog_data.get("context"),
        "attendance_type": timelog_data.get("attendance_type", "work"),
        "work_location": timelog_data.get("work_location"),
        "created_at": datetime.utcnow().isoformat()
    }
    timelogs_table.put_item(Item=item)
    return normalize_timelog_item(item)

async def get_timelog_by_id(log_id: str) -> Optional[dict]:
    """Get a time log by ID."""
    try:
        response = timelogs_table.get_item(Key={"log_id": log_id})
        if "Item" in response:
            return normalize_timelog_item(response["Item"])
        return None
    except ClientError:
        return None

async def get_timelogs_by_user(user_id: str, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> List[dict]:
    """Get time logs for a user."""
    try:
        # Query using GSI on user_id
        key_condition = "user_id = :user_id"
        expression_values = {":user_id": user_id}
        
        if start_date or end_date:
            filter_expression_parts = []
            if start_date:
                filter_expression_parts.append("start_time >= :start_date")
                expression_values[":start_date"] = start_date.isoformat()
            if end_date:
                filter_expression_parts.append("start_time <= :end_date")
                expression_values[":end_date"] = end_date.isoformat()
            
            response = timelogs_table.query(
                IndexName="user_id-index",
                KeyConditionExpression=key_condition,
                FilterExpression=" AND ".join(filter_expression_parts) if filter_expression_parts else None,
                ExpressionAttributeValues=expression_values
            )
        else:
            response = timelogs_table.query(
                IndexName="user_id-index",
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values
            )
        
        items = response.get("Items", [])
        return [normalize_timelog_item(item) for item in items]
    except ClientError:
        # Fallback to scan if GSI doesn't exist
        filter_expression = "user_id = :user_id"
        expression_values = {":user_id": user_id}
        
        if start_date:
            filter_expression += " AND start_time >= :start_date"
            expression_values[":start_date"] = start_date.isoformat()
        if end_date:
            filter_expression += " AND start_time <= :end_date"
            expression_values[":end_date"] = end_date.isoformat()
        
        response = timelogs_table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_values
        )
        items = response.get("Items", [])
        return [normalize_timelog_item(item) for item in items]

async def get_timelogs_by_user_and_exact_time(user_id: str, start_time: datetime, end_time: datetime) -> List[dict]:
    """Get time logs for a user within an exact start and end time."""
    response = timelogs_table.query(
        IndexName="user_id-index",
        KeyConditionExpression="user_id = :user_id",
        FilterExpression="start_time = :start_time AND end_time = :end_time",
        ExpressionAttributeValues={
            ":user_id": user_id,
            ":start_time": start_time.isoformat(),
            ":end_time": end_time.isoformat(),
        }
    )
    items = response.get("Items", [])
    return [normalize_timelog_item(item) for item in items]

async def get_all_timelogs(
    start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None,
                          user_id: Optional[str] = None,
    is_overtime: Optional[bool] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    last_evaluated_key: Optional[Dict[str, Any]] = None
) -> tuple[List[dict], Optional[Dict[str, Any]]]:
    """
    Get all time logs with optional filters and pagination.
    
    Returns:
        Tuple of (items, last_evaluated_key for pagination)
    """
    filter_parts = []
    expression_values = {}
    
    if user_id:
        filter_parts.append("user_id = :user_id")
        expression_values[":user_id"] = user_id
    if start_date:
        filter_parts.append("start_time >= :start_date")
        expression_values[":start_date"] = start_date.isoformat()
    if end_date:
        filter_parts.append("start_time <= :end_date")
        expression_values[":end_date"] = end_date.isoformat()
    if is_overtime is not None:
        filter_parts.append("is_overtime = :is_overtime")
        expression_values[":is_overtime"] = is_overtime
    
    scan_kwargs = {}
    if filter_parts:
        scan_kwargs["FilterExpression"] = " AND ".join(filter_parts)
        scan_kwargs["ExpressionAttributeValues"] = expression_values
    
    # Add pagination
    if page_size:
        scan_kwargs["Limit"] = page_size
    if last_evaluated_key:
        scan_kwargs["ExclusiveStartKey"] = last_evaluated_key
    
    try:
        response = timelogs_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        last_key = response.get("LastEvaluatedKey")
        
        # Normalize all items
        normalized_items = [normalize_timelog_item(item) for item in items]
        return normalized_items, last_key
    except ClientError as e:
        logger.error("Failed to get timelogs", error=str(e), error_code=e.response.get("Error", {}).get("Code"))
        raise DatabaseError("Failed to retrieve time logs") from e

async def update_timelog(log_id: str, update_data: dict) -> Optional[dict]:
    """Update a time log."""
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    for key, value in update_data.items():
        # Handle None values - skip them
        if value is None:
            continue
            
        # Handle datetime conversion
        if isinstance(value, datetime):
            expression_attribute_values[f":{key}"] = value.isoformat()
        elif isinstance(value, bool):
            # Handle boolean values first (before number check)
            expression_attribute_values[f":{key}"] = value
        elif isinstance(value, (float, int)):
            # Convert float/int to Decimal for DynamoDB
            expression_attribute_values[f":{key}"] = Decimal(str(value))
        elif isinstance(value, str) and key in ("attendance_type", "work_location"):
            # Handle string values for attendance_type and work_location
            expression_attribute_values[f":{key}"] = value
        else:
            # Allow empty strings for context (user can clear it)
            expression_attribute_values[f":{key}"] = value
        update_expression_parts.append(f"#{key} = :{key}")
        expression_attribute_names[f"#{key}"] = key
    
    if not update_expression_parts:
        return await get_timelog_by_id(log_id)
    
    update_expression_parts.append("#updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
    expression_attribute_names["#updated_at"] = "updated_at"
    
    # Build update expression
    update_expression = "SET " + ", ".join(update_expression_parts)
    
    try:
        timelogs_table.update_item(
            Key={"log_id": log_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="ALL_NEW"
        )
        return await get_timelog_by_id(log_id)
    except ClientError as e:
        logger.error("Failed to update timelog", log_id=log_id, error=str(e))
        raise DatabaseError("Failed to update time log") from e

async def delete_timelog(log_id: str) -> bool:
    """Delete a time log."""
    try:
        timelogs_table.delete_item(Key={"log_id": log_id})
        return True
    except ClientError as e:
        logger.error("Failed to delete timelog", log_id=log_id, error=str(e))
        raise DatabaseError("Failed to delete time log") from e

# Audit log operations
async def create_audit_log(action: str, user_id: str, details: dict):
    """Create an audit log entry."""
    try:
        audit_id = str(uuid.uuid4())
        item = {
            "audit_id": audit_id,
            "action": action,
            "user_id": user_id,
            "details": str(details),
            "timestamp": datetime.utcnow().isoformat()
        }
        audit_table.put_item(Item=item)
    except ClientError as e:
        logger.error("Failed to create audit log", error=str(e))
        # Don't raise - audit logging should not break the main flow

# Leave Request operations
async def create_leave_request(leave_request_data: dict) -> dict:
    """Create a new leave request."""
    request_id = str(uuid.uuid4())
    item = {
        "request_id": request_id,
        "user_id": leave_request_data["user_id"],
        "leave_type": leave_request_data["leave_type"],
        "start_date": leave_request_data["start_date"].isoformat(),
        "end_date": leave_request_data["end_date"].isoformat(),
        "description": leave_request_data["description"],
        "status": leave_request_data.get("status", "pending"),
        "half_day": leave_request_data.get("half_day", False),
        "admin_notes": leave_request_data.get("admin_notes"),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
        "reviewed_at": None,
        "reviewed_by": None
    }
    leave_requests_table.put_item(Item=item)
    return item

async def get_leave_request_by_id(request_id: str) -> Optional[dict]:
    """Get a leave request by ID."""
    try:
        response = leave_requests_table.get_item(Key={"request_id": request_id})
        if "Item" in response:
            return response["Item"]
        return None
    except ClientError as e:
        logger.error("Failed to get leave request by ID", request_id=request_id, error=str(e))
        raise DatabaseError("Failed to retrieve leave request") from e

async def get_leave_requests_by_user(user_id: str, status: Optional[str] = None) -> List[dict]:
    """Get leave requests for a user, optionally filtered by status."""
    try:
        if status:
            # Use GSI to query by user_id and status
            response = leave_requests_table.query(
                IndexName="user_id-status-index",
                KeyConditionExpression="user_id = :user_id AND #status = :status",
                ExpressionAttributeValues={
                    ":user_id": user_id,
                    ":status": status
                },
                ExpressionAttributeNames={
                    "#status": "status"
                }
            )
        else:
            # Query by user_id only
            response = leave_requests_table.query(
                IndexName="user_id-index",
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={
                    ":user_id": user_id
                }
            )
        return response.get("Items", [])
    except ClientError as e:
        logger.error("Failed to get leave requests by user", user_id=user_id, error=str(e))
        raise DatabaseError("Failed to retrieve leave requests") from e

async def get_all_leave_requests(status: Optional[str] = None) -> List[dict]:
    """Get all leave requests, optionally filtered by status."""
    try:
        if status:
            # Use GSI to query by status
            response = leave_requests_table.query(
                IndexName="status-index",
                KeyConditionExpression="#status = :status",
                ExpressionAttributeValues={
                    ":status": status
                },
                ExpressionAttributeNames={
                    "#status": "status"
                }
            )
        else:
            # Scan all requests
            response = leave_requests_table.scan()
        return response.get("Items", [])
    except ClientError as e:
        logger.error("Failed to get all leave requests", error=str(e))
        raise DatabaseError("Failed to retrieve leave requests") from e

async def update_leave_request(request_id: str, update_data: dict) -> Optional[dict]:
    """Update a leave request."""
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    for key, value in update_data.items():
        if value is None:
            continue
            
        if isinstance(value, datetime):
            expression_attribute_values[f":{key}"] = value.isoformat()
        elif isinstance(value, bool):
            expression_attribute_values[f":{key}"] = value
        else:
            expression_attribute_values[f":{key}"] = value
        update_expression_parts.append(f"#{key} = :{key}")
        expression_attribute_names[f"#{key}"] = key
    
    if not update_expression_parts:
        return await get_leave_request_by_id(request_id)
    
    update_expression_parts.append("#updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
    expression_attribute_names["#updated_at"] = "updated_at"
    
    update_expression = "SET " + ", ".join(update_expression_parts)
    
    try:
        leave_requests_table.update_item(
            Key={"request_id": request_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="ALL_NEW"
        )
        return await get_leave_request_by_id(request_id)
    except ClientError as e:
        logger.error("Failed to update leave request", request_id=request_id, error=str(e))
        raise DatabaseError("Failed to update leave request") from e

async def delete_leave_request(request_id: str) -> bool:
    """Delete a leave request."""
    try:
        leave_requests_table.delete_item(Key={"request_id": request_id})
        return True
    except ClientError as e:
        logger.error("Failed to delete leave request", request_id=request_id, error=str(e))
        raise DatabaseError("Failed to delete leave request") from e
