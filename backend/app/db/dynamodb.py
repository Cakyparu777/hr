import boto3
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid
from app.core.config import settings
from app.models.user import UserRole


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

async def get_holidays_as_dates() -> List[date]:
    """Get all holidays as a list of date objects."""
    holidays = await get_all_holidays()
    return [datetime.fromisoformat(h["date"]).date() for h in holidays]

async def delete_holiday(holiday_id: str) -> bool:
    """Delete a holiday."""
    try:
        holidays_table.delete_item(Key={"id": holiday_id})
        return True
    except ClientError:
        return False

# User operations
async def create_user(user_data: dict) -> dict:
    """Create a new user in DynamoDB."""
    user_id = str(uuid.uuid4())
    item = {
        "user_id": user_id,
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"],
        "password_hash": user_data["password_hash"],
        "must_change_password": bool(user_data.get("must_change_password", False)),
        "created_at": datetime.utcnow().isoformat()
    }
    users_table.put_item(Item=item)
    item.pop("password_hash")
    return item

async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get a user by ID."""
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            item = response["Item"]
            item.pop("password_hash", None)
            return item
        return None
    except ClientError:
        return None

async def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by email (using GSI)."""
    try:
        response = users_table.query(
            IndexName="email-index",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": email}
        )
        if response.get("Items"):
            item = response["Items"][0]
            return item
        return None
    except ClientError:
        # Fallback to scan if GSI doesn't exist
        response = users_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": email}
        )
        if response.get("Items"):
            item = response["Items"][0]
            return item
        return None

async def get_all_users() -> List[dict]:
    """Get all users."""
    response = users_table.scan()
    users = []
    for item in response.get("Items", []):
        item.pop("password_hash", None)
        users.append(item)
    return users

async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """Update a user."""
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    for key, value in update_data.items():
        if value is not None:
            update_expression_parts.append(f"#{key} = :{key}")
            expression_attribute_values[f":{key}"] = value
            expression_attribute_names[f"#{key}"] = key
    
    if not update_expression_parts:
        return await get_user_by_id(user_id)
    
    update_expression_parts.append("#updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat()
    expression_attribute_names["#updated_at"] = "updated_at"
    
    try:
        users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET " + ", ".join(update_expression_parts),
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="ALL_NEW"
        )
        return await get_user_by_id(user_id)
    except ClientError:
        return None

async def delete_user(user_id: str) -> bool:
    """Delete a user."""
    try:
        users_table.delete_item(Key={"user_id": user_id})
        return True
    except ClientError:
        return False

async def get_user_by_id_with_secret(user_id: str) -> Optional[dict]:
    """Get a user by ID, including secret fields like password_hash."""
    try:
        response = users_table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            return response["Item"]  # do NOT pop password_hash
        return None
    except ClientError:
        return None

from decimal import Decimal

# ... (rest of the imports)

# ... (rest of the file)

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
        "is_overtime": timelog_data["is_overtime"],
        "context": timelog_data.get("context"),
        "created_at": datetime.utcnow().isoformat()
    }
    timelogs_table.put_item(Item=item)
    return item

async def get_timelog_by_id(log_id: str) -> Optional[dict]:
    """Get a time log by ID."""
    try:
        response = timelogs_table.get_item(Key={"log_id": log_id})
        if "Item" in response:
            return response["Item"]
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
        
        return response.get("Items", [])
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
        return response.get("Items", [])

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
    return response.get("Items", [])

async def get_all_timelogs(start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None,
                          user_id: Optional[str] = None,
                          is_overtime: Optional[bool] = None) -> List[dict]:
    """Get all time logs with optional filters."""
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
    
    if filter_parts:
        response = timelogs_table.scan(
            FilterExpression=" AND ".join(filter_parts),
            ExpressionAttributeValues=expression_values
        )
    else:
        response = timelogs_table.scan()
    
    return response.get("Items", [])

async def update_timelog(log_id: str, update_data: dict) -> Optional[dict]:
    """Update a time log."""
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    for key, value in update_data.items():
        if value is not None:
            # Handle datetime conversion
            if isinstance(value, datetime):
                expression_attribute_values[f":{key}"] = value.isoformat()
            elif isinstance(value, float):
                expression_attribute_values[f":{key}"] = Decimal(str(value))
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
    except ClientError:
        return None

async def delete_timelog(log_id: str) -> bool:
    """Delete a time log."""
    try:
        timelogs_table.delete_item(Key={"log_id": log_id})
        return True
    except ClientError:
        return False

# Audit log operations
async def create_audit_log(action: str, user_id: str, details: dict):
    """Create an audit log entry."""
    audit_id = str(uuid.uuid4())
    item = {
        "audit_id": audit_id,
        "action": action,
        "user_id": user_id,
        "details": details,
        "created_at": datetime.utcnow().isoformat()
    }
    audit_table.put_item(Item=item)

