# AWS App Runner Deployment Guide

This guide walks you through deploying the Time Tracking application backend to AWS App Runner.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Docker** installed
4. **DynamoDB tables** created (or use init script)
5. **ECR repository** (created automatically by deploy script)

## Step 1: Prepare AWS Resources

### 1.1 Create DynamoDB Tables

The tables will be created automatically on first startup, or you can create them manually:

```bash
# Option 1: Let the application create them on startup (recommended)
# The init_db.py script runs automatically on startup

# Option 2: Create them manually via AWS Console or CLI
aws dynamodb create-table \
    --table-name time_tracking_users \
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=email,AttributeType=S \
    --key-schema AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes IndexName=email-index,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL} \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### 1.2 Create IAM Roles for App Runner

App Runner needs two IAM roles:

1. **ECR Access Role** - Allows App Runner to pull images from ECR
2. **Instance Role** - Allows the application to access AWS services (DynamoDB)

#### Create ECR Access Role:

```bash
# Create trust policy
cat > apprunner-ecr-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name AppRunnerECRAccessRole \
    --assume-role-policy-document file://apprunner-ecr-trust-policy.json

# Attach ECR read policy
aws iam attach-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
```

#### Create Instance Role:

```bash
# Create trust policy
cat > apprunner-instance-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "tasks.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name AppRunnerInstanceRole \
    --assume-role-policy-document file://apprunner-instance-trust-policy.json

# Create and attach DynamoDB access policy
cat > dynamodb-access-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem",
        "dynamodb:DescribeTable",
        "dynamodb:CreateTable"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/time_tracking_*",
        "arn:aws:dynamodb:us-east-1:*:table/time_tracking_*/index/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name AppRunnerInstanceRole \
    --policy-name DynamoDBAccess \
    --policy-document file://dynamodb-access-policy.json
```

## Step 2: Generate Secret Key

Generate a secure secret key for JWT tokens:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save this value - you'll need it for the App Runner environment variables.

## Step 3: Configure Environment Variables

You'll need to set the following environment variables in App Runner:

### Required Variables:

- `SECRET_KEY` - JWT secret key (generate with command above)
- `AWS_REGION` - AWS region (e.g., `us-east-1`)
- `ENVIRONMENT` - Set to `production`

### Optional Variables (with defaults):

- `DYNAMODB_USERS_TABLE` - Default: `time_tracking_users`
- `DYNAMODB_TIMELOGS_TABLE` - Default: `time_tracking_logs`
- `DYNAMODB_AUDIT_TABLE` - Default: `time_tracking_audit`
- `DYNAMODB_HOLIDAYS_TABLE` - Default: `time_tracking_holidays`
- `DYNAMODB_LEAVE_REQUESTS_TABLE` - Default: `time_tracking_leave_requests`
- `CORS_ORIGINS` - Comma-separated list of allowed origins (e.g., `https://yourdomain.com,https://www.yourdomain.com`)

### AWS Credentials:

You have two options:

1. **Use IAM Role** (Recommended) - Attach the instance role to App Runner service
2. **Use Environment Variables** - Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

If using IAM role, you don't need to set `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`.

## Step 4: Deploy to App Runner

### Option 1: Using Deployment Script (Recommended)

```bash
# Make script executable
chmod +x deploy-apprunner.sh

# Set environment variables (optional)
export AWS_REGION=us-east-1
export ECR_REPOSITORY=time-tracking-backend
export APP_RUNNER_SERVICE=time-tracking-backend

# Run deployment script
./deploy-apprunner.sh
```

### Option 2: Manual Deployment

#### 4.1 Create ECR Repository

```bash
aws ecr create-repository --repository-name time-tracking-backend --region us-east-1
```

#### 4.2 Login to ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 4.3 Build and Push Docker Image

```bash
# Build image
docker build -f Dockerfile.prod -t time-tracking-backend:latest .

# Tag image
docker tag time-tracking-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/time-tracking-backend:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/time-tracking-backend:latest
```

#### 4.4 Create App Runner Service

1. Go to AWS App Runner console
2. Click "Create service"
3. Select "Container registry" -> "Amazon ECR"
4. Select your ECR repository and image tag
5. Configure service:
   - **Service name**: `time-tracking-backend`
   - **Virtual CPU**: 1 vCPU
   - **Memory**: 2 GB
   - **Port**: 8000
   - **Health check path**: `/health`
6. Set environment variables (see Step 3)
7. Configure IAM roles (ECR access role and instance role)
8. Review and create service

## Step 5: Verify Deployment

### 5.1 Check Service Status

```bash
aws apprunner describe-service --service-arn <service-arn> --region us-east-1
```

### 5.2 Test Health Endpoint

```bash
# Get service URL
SERVICE_URL=$(aws apprunner describe-service --service-arn <service-arn> --region us-east-1 --query 'Service.ServiceUrl' --output text)

# Test health endpoint
curl $SERVICE_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### 5.3 Test API Endpoint

```bash
# Test API root
curl $SERVICE_URL/

# Test API docs
curl $SERVICE_URL/docs
```

## Step 6: Update Frontend

Update the frontend to use the new API URL:

1. Update `frontend/.env.production`:
```env
REACT_APP_API_URL=https://<app-runner-service-url>
```

2. Build and deploy frontend to S3 + CloudFront (see frontend deployment guide)

## Step 7: Create Default Admin User

The application will automatically create a default admin user on first startup:

- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ IMPORTANT**: Change this password immediately after first login!

Alternatively, create an admin user manually:

```bash
# SSH into App Runner container (if possible) or use a separate script
python create_admin.py admin@yourdomain.com SecurePassword123! "Admin User"
```

## Troubleshooting

### Service Won't Start

1. Check CloudWatch logs for errors
2. Verify environment variables are set correctly
3. Check IAM roles have correct permissions
4. Verify DynamoDB tables exist

### Can't Connect to DynamoDB

1. Verify IAM instance role has DynamoDB permissions
2. Check AWS region is correct
3. Verify table names match environment variables

### CORS Errors

1. Update `CORS_ORIGINS` environment variable with your frontend URL
2. Restart App Runner service after updating environment variables

### Health Check Failing

1. Verify port is set to 8000
2. Check health check path is `/health`
3. Review application logs for errors

## Cost Optimization

- **Scale to zero**: Configure App Runner to scale to zero during inactivity
- **Auto-scaling**: App Runner automatically scales based on traffic
- **Monitor costs**: Set up AWS Cost Explorer alerts

## Security Best Practices

1. **Use IAM roles** instead of access keys when possible
2. **Rotate secrets** regularly
3. **Enable CloudWatch logging** for monitoring
4. **Use HTTPS only** (App Runner provides this automatically)
5. **Set up WAF** for additional security (optional)

## Next Steps

1. Set up CI/CD pipeline for automatic deployments
2. Configure custom domain for App Runner service
3. Set up monitoring and alerts
4. Configure backup strategy for DynamoDB
5. Set up staging environment for testing

## Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [AWS App Runner Pricing](https://aws.amazon.com/apprunner/pricing/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

