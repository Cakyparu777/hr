# DynamoDB Setup Guide

## Option 1: Use DynamoDB Local (Recommended for Development)

DynamoDB Local is a downloadable version of DynamoDB that lets you write and test applications without accessing the DynamoDB web service.

### Installation

**Using Docker (Easiest):**
```bash
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local
```

**Using Homebrew:**
```bash
brew install dynamodb-local
dynamodb-local
```

### Configuration

The `.env` file is already configured to use DynamoDB Local:
```
DYNAMODB_ENDPOINT_URL=http://localhost:8000
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
```

### Create Tables

After starting DynamoDB Local, run:
```bash
python setup_dynamodb.py
```

## Option 2: Use AWS DynamoDB (Production)

### Setup AWS Credentials

1. **Using AWS CLI:**
```bash
aws configure
```

2. **Or set environment variables:**
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

3. **Or update `.env` file:**
```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
DYNAMODB_ENDPOINT_URL=  # Leave empty for AWS
```

### Create Tables in AWS

1. Go to AWS Console → DynamoDB
2. Create tables manually, or
3. Run `python setup_dynamodb.py` (will create in AWS if credentials are set)

## Quick Start with DynamoDB Local

```bash
# 1. Start DynamoDB Local
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local

# 2. Create tables
cd backend
source venv/bin/activate
python setup_dynamodb.py

# 3. Create admin user
python create_admin.py admin@admin.com password "Admin User"
```

## Troubleshooting

- **NoCredentialsError**: Make sure DynamoDB Local is running or AWS credentials are configured
- **Table not found**: Run `python setup_dynamodb.py` to create tables
- **Connection refused**: Check if DynamoDB Local is running on port 8000

