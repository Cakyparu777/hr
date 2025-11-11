"""
Initialize DynamoDB tables - can be run on startup to ensure tables exist.
"""
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import time

# Initialize DynamoDB client
dynamodb_kwargs = {
    'region_name': settings.AWS_REGION,
    'aws_access_key_id': settings.AWS_ACCESS_KEY_ID or 'dummy',
    'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY or 'dummy'
}

# Add endpoint URL for DynamoDB Local if provided
if settings.DYNAMODB_ENDPOINT_URL:
    dynamodb_kwargs['endpoint_url'] = settings.DYNAMODB_ENDPOINT_URL

dynamodb = boto3.resource('dynamodb', **dynamodb_kwargs)

def table_exists(table_name):
    """Check if a table exists."""
    try:
        table = dynamodb.Table(table_name)
        table.load()
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        raise

def create_table_if_not_exists(table_name, key_schema, attribute_definitions, gsi=None):
    """Create a DynamoDB table if it doesn't exist."""
    if table_exists(table_name):
        print(f"Table {table_name} already exists.")
        return
    
    try:
        create_table_kwargs = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        if gsi:
            create_table_kwargs['GlobalSecondaryIndexes'] = gsi
        
        print(f"Creating table {table_name}...")
        table = dynamodb.create_table(**create_table_kwargs)
        table.wait_until_exists()
        print(f"✓ Table {table_name} created successfully!")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists.")
        else:
            print(f"Error creating table {table_name}: {e}")
            raise

def init_tables():
    """Initialize all required DynamoDB tables."""
    print("Initializing DynamoDB tables...")
    
    # Wait for DynamoDB to be ready (if using local)
    if settings.DYNAMODB_ENDPOINT_URL:
        max_retries = 60  # Increased retries
        retry_count = 0
        print("Waiting for DynamoDB to be ready...")
        while retry_count < max_retries:
            try:
                # Try to list tables to check connectivity
                list(dynamodb.tables.all())
                print("✓ DynamoDB is ready!")
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"✗ Could not connect to DynamoDB after {max_retries} retries")
                    print(f"  Endpoint: {settings.DYNAMODB_ENDPOINT_URL}")
                    print(f"  Error: {e}")
                    return
                if retry_count % 10 == 0:  # Print every 10 retries
                    print(f"  Still waiting... ({retry_count}/{max_retries})")
                time.sleep(2)  # Wait 2 seconds between retries
    
    # Users table
    create_table_if_not_exists(
        table_name=settings.DYNAMODB_USERS_TABLE,
        key_schema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'email-index',
            'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    # TimeLogs table
    create_table_if_not_exists(
        table_name=settings.DYNAMODB_TIMELOGS_TABLE,
        key_schema=[{'AttributeName': 'log_id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'log_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'user_id-index',
            'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    # Audit table
    create_table_if_not_exists(
        table_name=settings.DYNAMODB_AUDIT_TABLE,
        key_schema=[{'AttributeName': 'audit_id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'audit_id', 'AttributeType': 'S'}
        ]
    )
    
    # Holidays table
    create_table_if_not_exists(
        table_name=settings.DYNAMODB_HOLIDAYS_TABLE,
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'date', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'date-index',
            'KeySchema': [{'AttributeName': 'date', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    # Leave Requests table
    create_table_if_not_exists(
        table_name=settings.DYNAMODB_LEAVE_REQUESTS_TABLE,
        key_schema=[{'AttributeName': 'request_id', 'KeyType': 'HASH'}],
        attribute_definitions=[
            {'AttributeName': 'request_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'user_id-index',
            'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        },
        {
            'IndexName': 'status-index',
            'KeySchema': [{'AttributeName': 'status', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        },
        {
            'IndexName': 'user_id-status-index',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'status', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    print("✓ All tables initialized!")

if __name__ == "__main__":
    init_tables()

