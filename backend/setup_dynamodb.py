"""
Script to set up DynamoDB tables for the time tracking system.
Run this script once to create the necessary tables.
"""
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

# Initialize DynamoDB client
dynamodb_kwargs = {
    'region_name': settings.AWS_REGION,
}

# Add credentials if provided
if settings.AWS_ACCESS_KEY_ID:
    dynamodb_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
if settings.AWS_SECRET_ACCESS_KEY:
    dynamodb_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY

# Add endpoint URL for DynamoDB Local if provided
if settings.DYNAMODB_ENDPOINT_URL:
    dynamodb_kwargs['endpoint_url'] = settings.DYNAMODB_ENDPOINT_URL

dynamodb = boto3.resource('dynamodb', **dynamodb_kwargs)

def create_table(table_name, key_schema, attribute_definitions, gsi=None):
    """Create a DynamoDB table."""
    try:
        create_table_kwargs = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        # Only add GlobalSecondaryIndexes if provided
        if gsi:
            create_table_kwargs['GlobalSecondaryIndexes'] = gsi
        
        table = dynamodb.create_table(**create_table_kwargs)
        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"Table {table_name} created successfully!")
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists.")
        else:
            print(f"Error creating table {table_name}: {e}")
            raise

def setup_tables():
    """Set up all required DynamoDB tables."""
    print("Setting up DynamoDB tables...")
    
    # Users table
    create_table(
        table_name=settings.DYNAMODB_USERS_TABLE,
        key_schema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'email-index',
            'KeySchema': [
                {'AttributeName': 'email', 'KeyType': 'HASH'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    # TimeLogs table
    create_table(
        table_name=settings.DYNAMODB_TIMELOGS_TABLE,
        key_schema=[
            {'AttributeName': 'log_id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'log_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'user_id-index',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    # Audit table
    create_table(
        table_name=settings.DYNAMODB_AUDIT_TABLE,
        key_schema=[
            {'AttributeName': 'audit_id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'audit_id', 'AttributeType': 'S'}
        ]
    )

    # Holidays table
    create_table(
        table_name=settings.DYNAMODB_HOLIDAYS_TABLE,
        key_schema=[
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'date', 'AttributeType': 'S'}
        ],
        gsi=[{
            'IndexName': 'date-index',
            'KeySchema': [
                {'AttributeName': 'date', 'KeyType': 'HASH'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }]
    )
    
    print("\nAll tables set up successfully!")

if __name__ == "__main__":
    setup_tables()

