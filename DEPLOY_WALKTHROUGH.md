# AWS App Runner Deployment - Step-by-Step Walkthrough

This guide will walk you through deploying your Time Tracking application to AWS App Runner from start to finish.

## 📋 Prerequisites Checklist

Before you begin, make sure you have:

- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI installed and configured (`aws --version`)
- [ ] Docker installed and running (`docker --version`)
- [ ] Git repository cloned locally
- [ ] Basic knowledge of AWS services (DynamoDB, IAM, ECR)

---

## Step 1: Set Up AWS CLI (If Not Already Done)

### 1.1 Install AWS CLI

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download from: https://aws.amazon.com/cli/
```

### 1.2 Configure AWS CLI

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Get this from AWS Console → IAM → Users → Your User → Security Credentials
- **AWS Secret Access Key**: Get this when creating the access key
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

### 1.3 Verify Configuration

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and user ARN.

---

## Step 2: Create DynamoDB Tables

### Option A: Let the Application Create Tables (Recommended)

The application will automatically create tables on first startup. Skip to Step 3.

### Option B: Create Tables Manually

If you prefer to create tables manually:

```bash
# Set your region
export AWS_REGION=us-east-1

# Create Users table
aws dynamodb create-table \
    --table-name time_tracking_users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"email-index\",\"KeySchema\":[{\"AttributeName\":\"email\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION

# Create TimeLogs table
aws dynamodb create-table \
    --table-name time_tracking_logs \
    --attribute-definitions \
        AttributeName=log_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=log_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"user_id-index\",\"KeySchema\":[{\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION

# Create Audit table
aws dynamodb create-table \
    --table-name time_tracking_audit \
    --attribute-definitions \
        AttributeName=audit_id,AttributeType=S \
    --key-schema \
        AttributeName=audit_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION

# Create Holidays table
aws dynamodb create-table \
    --table-name time_tracking_holidays \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=date,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"date-index\",\"KeySchema\":[{\"AttributeName\":\"date\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION

# Create Leave Requests table
aws dynamodb create-table \
    --table-name time_tracking_leave_requests \
    --attribute-definitions \
        AttributeName=request_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=status,AttributeType=S \
    --key-schema \
        AttributeName=request_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\":\"user_id-index\",\"KeySchema\":[{\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"status-index\",\"KeySchema\":[{\"AttributeName\":\"status\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"user_id-status-index\",\"KeySchema\":[{\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"status\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" \
    --billing-mode PAY_PER_REQUEST \
    --region $AWS_REGION
```

Verify tables were created:

```bash
aws dynamodb list-tables --region $AWS_REGION
```

---

## Step 3: Create IAM Roles for App Runner

App Runner needs two IAM roles:
1. **ECR Access Role** - Allows App Runner to pull images from ECR
2. **Instance Role** - Allows the application to access DynamoDB

### 3.1 Create ECR Access Role

```bash
# Get your AWS account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Create trust policy file
cat > /tmp/apprunner-ecr-trust-policy.json <<EOF
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

# Create the role
aws iam create-role \
    --role-name AppRunnerECRAccessRole \
    --assume-role-policy-document file:///tmp/apprunner-ecr-trust-policy.json

# Attach the managed policy for ECR access
aws iam attach-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

echo "✓ ECR Access Role created: arn:aws:iam::${AWS_ACCOUNT_ID}:role/AppRunnerECRAccessRole"
```

### 3.2 Create Instance Role (for DynamoDB Access)

```bash
# Create trust policy file
cat > /tmp/apprunner-instance-trust-policy.json <<EOF
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

# Create the role
aws iam create-role \
    --role-name AppRunnerInstanceRole \
    --assume-role-policy-document file:///tmp/apprunner-instance-trust-policy.json

# Create DynamoDB access policy
cat > /tmp/dynamodb-access-policy.json <<EOF
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

# Attach the policy to the role
aws iam put-role-policy \
    --role-name AppRunnerInstanceRole \
    --policy-name DynamoDBAccess \
    --policy-document file:///tmp/dynamodb-access-policy.json

echo "✓ Instance Role created: arn:aws:iam::${AWS_ACCOUNT_ID}:role/AppRunnerInstanceRole"
```

**Note**: If you get an error that the role already exists, that's okay - it means it was created previously.

---

## Step 4: Generate Secret Key

Generate a secure secret key for JWT tokens:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Save this value** - you'll need it in Step 7 when configuring App Runner.

Example output:
```
xK9mP2qR7vT4wY8zA1bC3dE5fG6hI7jK8lM9nO0pQ1rS2tU3vW4xY5zA6bC7d
```

---

## Step 5: Build and Push Docker Image to ECR

### 5.1 Navigate to Project Directory

```bash
cd /Users/tuguldur.ganbaatar/Desktop/work
cd backend
```

### 5.2 Set Environment Variables

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPOSITORY=time-tracking-backend
export ECR_URL=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}

echo "Region: $AWS_REGION"
echo "Account ID: $AWS_ACCOUNT_ID"
echo "ECR Repository: $ECR_REPOSITORY"
echo "ECR URL: $ECR_URL"
```

### 5.3 Create ECR Repository

```bash
# Check if repository exists
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

echo "✓ ECR repository ready"
```

### 5.4 Login to ECR

```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

echo "✓ Logged in to ECR"
```

### 5.5 Build Docker Image

```bash
# Build the production Docker image
docker build -f Dockerfile.prod -t $ECR_REPOSITORY:latest .

echo "✓ Docker image built"
```

### 5.6 Tag Docker Image

```bash
docker tag $ECR_REPOSITORY:latest $ECR_URL:latest

echo "✓ Docker image tagged"
```

### 5.7 Push Docker Image to ECR

```bash
docker push $ECR_URL:latest

echo "✓ Docker image pushed to ECR"
```

### 5.8 Verify Image in ECR

```bash
aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_REGION

echo "✓ Image verified in ECR"
```

---

## Step 6: Create App Runner Service via AWS Console

### 6.1 Open AWS App Runner Console

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Make sure you're in the correct region (e.g., `us-east-1`)
3. Click **"Create service"**

### 6.2 Configure Source

1. Select **"Container registry"**
2. Select **"Amazon ECR"**
3. Click **"Browse"** and select your repository: `time-tracking-backend`
4. Select image tag: **`latest`**
5. Select deployment trigger: **"Automatic"** (deploys on image push)

### 6.3 Configure Service Settings

1. **Service name**: `time-tracking-backend`
2. **Virtual CPU**: `1 vCPU`
3. **Memory**: `2 GB`
4. **Port**: `8000`
5. **Environment variables**: Click **"Add environment variable"** and add:

   | Key | Value |
   |-----|-------|
   | `ENVIRONMENT` | `production` |
   | `AWS_REGION` | `us-east-1` |
   | `SECRET_KEY` | `<paste the secret key from Step 4>` |
   | `CORS_ORIGINS` | `https://yourdomain.com` (or leave empty for now) |
   | `DYNAMODB_USERS_TABLE` | `time_tracking_users` |
   | `DYNAMODB_TIMELOGS_TABLE` | `time_tracking_logs` |
   | `DYNAMODB_AUDIT_TABLE` | `time_tracking_audit` |
   | `DYNAMODB_HOLIDAYS_TABLE` | `time_tracking_holidays` |
   | `DYNAMODB_LEAVE_REQUESTS_TABLE` | `time_tracking_leave_requests` |

   **Important**: Replace `https://yourdomain.com` with your actual frontend URL, or leave it empty and update later.

### 6.4 Configure IAM Roles

1. **Access role**: Select `AppRunnerECRAccessRole` (created in Step 3.1)
2. **Instance role**: Select `AppRunnerInstanceRole` (created in Step 3.2)

### 6.5 Configure Health Check

1. **Health check path**: `/health`
2. **Health check interval**: `10` seconds
3. **Health check timeout**: `5` seconds
4. **Healthy threshold**: `1`
5. **Unhealthy threshold**: `5`

### 6.6 Configure Auto Scaling (Optional)

1. **Min instances**: `1`
2. **Max instances**: `5` (or your preferred max)
3. **Concurrency**: `100` requests per instance

### 6.7 Review and Create

1. Review all settings
2. Click **"Create & deploy"**

### 6.8 Wait for Deployment

The service will take 5-10 minutes to deploy. You can watch the progress in the console.

---

## Step 7: Get Service URL

Once the service is deployed:

1. Go to the App Runner service page
2. Copy the **Service URL** (e.g., `https://abc123.us-east-1.awsapprunner.com`)
3. Save this URL - you'll need it for the frontend

---

## Step 8: Test the Deployment

### 8.1 Test Health Endpoint

```bash
# Replace with your actual service URL
export SERVICE_URL="https://your-service-url.us-east-1.awsapprunner.com"

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

### 8.2 Test API Root

```bash
curl $SERVICE_URL/
```

Expected response:
```json
{
  "message": "Time Tracking API",
  "version": "1.0.0"
}
```

### 8.3 Test API Documentation

Open in browser:
```
https://your-service-url.us-east-1.awsapprunner.com/docs
```

You should see the Swagger UI documentation.

### 8.4 Test Default Admin User

The application automatically creates a default admin user on first startup:

- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ IMPORTANT**: Change this password immediately after first login!

Test login:
```bash
curl -X POST $SERVICE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

Expected response:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

---

## Step 9: Update CORS Origins (If Needed)

If you need to update CORS origins after deployment:

1. Go to App Runner service
2. Click **"Configuration"** tab
3. Click **"Edit"** next to "Environment variables"
4. Update `CORS_ORIGINS` with your frontend URL(s)
5. Click **"Save changes"**
6. Wait for the new deployment to complete

---

## Step 10: Monitor and Troubleshoot

### 10.1 View Logs

1. Go to App Runner service
2. Click **"Logs"** tab
3. View real-time logs from CloudWatch

Or via AWS CLI:
```bash
aws logs tail /aws/apprunner/time-tracking-backend/service --follow --region us-east-1
```

### 10.2 Check Service Status

```bash
aws apprunner describe-service \
    --service-arn <service-arn> \
    --region us-east-1
```

### 10.3 Common Issues

#### Service Won't Start
- Check CloudWatch logs for errors
- Verify environment variables are set correctly
- Check IAM roles have correct permissions

#### Can't Connect to DynamoDB
- Verify IAM instance role has DynamoDB permissions
- Check AWS region is correct
- Verify table names match environment variables

#### CORS Errors
- Update `CORS_ORIGINS` environment variable
- Restart service after updating
- Check browser console for specific CORS error

#### Health Check Failing
- Verify port is set to 8000
- Check health check path is `/health`
- Review application logs for errors

---

## Step 11: Update Frontend (Next Steps)

Once the backend is deployed:

1. Update frontend `.env.production`:
   ```env
   REACT_APP_API_URL=https://your-service-url.us-east-1.awsapprunner.com
   ```

2. Build frontend:
   ```bash
   cd frontend
   npm run build
   ```

3. Deploy frontend to S3 + CloudFront (see frontend deployment guide)

---

## Step 12: Set Up Custom Domain (Optional)

1. Go to App Runner service
2. Click **"Custom domains"** tab
3. Click **"Add domain"**
4. Enter your domain name
5. Follow the DNS configuration instructions
6. Wait for SSL certificate provisioning (can take 30 minutes)

---

## 🎉 Deployment Complete!

Your backend is now deployed to AWS App Runner! 

### What's Next?

1. ✅ Test all API endpoints
2. ✅ Update frontend to use new API URL
3. ✅ Deploy frontend to S3 + CloudFront
4. ✅ Set up monitoring and alerts
5. ✅ Configure custom domain (optional)
6. ✅ Set up CI/CD for automatic deployments (optional)

### Cost Estimate

- **App Runner**: ~$8/month (1 vCPU, 2 GB RAM)
- **DynamoDB**: ~$0.70/month
- **S3 + CloudFront**: ~$0.90/month
- **Total**: ~$10-13/month

### Useful Commands

```bash
# Get service URL
aws apprunner describe-service --service-arn <arn> --query 'Service.ServiceUrl' --output text

# View logs
aws logs tail /aws/apprunner/time-tracking-backend/service --follow

# Update environment variables
aws apprunner update-service --service-arn <arn> --source-configuration '...'

# List services
aws apprunner list-services
```

---

## 📚 Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [App Runner Pricing](https://aws.amazon.com/apprunner/pricing/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Project Deployment Guide](./backend/DEPLOYMENT.md)

---

## 🆘 Need Help?

If you encounter any issues:

1. Check CloudWatch logs for error messages
2. Verify all environment variables are set correctly
3. Check IAM roles have correct permissions
4. Review the troubleshooting section above
5. Check AWS App Runner service status in the console

Happy deploying! 🚀

