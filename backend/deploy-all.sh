#!/bin/bash
# One-Command Deployment Script for AWS App Runner
# This script does everything: builds, pushes, and creates/updates the App Runner service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AWS App Runner - One-Command Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-time-tracking-backend}"
APP_RUNNER_SERVICE="${APP_RUNNER_SERVICE:-time-tracking-backend}"

# Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
echo ""

if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI is not installed${NC}"
    echo "Please install AWS CLI first: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker first: https://www.docker.com/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials configured${NC}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Region: $AWS_REGION"
echo "  Account ID: $AWS_ACCOUNT_ID"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  ECR URL: $ECR_URL"
echo "  App Runner Service: $APP_RUNNER_SERVICE"
echo ""

# Step 2: Create ECR repository
echo -e "${YELLOW}Step 2: Creating ECR repository...${NC}"
if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &>/dev/null; then
    echo -e "${GREEN}✓ Repository already exists${NC}"
else
    aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" > /dev/null
    echo -e "${GREEN}✓ Repository created${NC}"
fi

# Step 3: Login to ECR
echo ""
echo -e "${YELLOW}Step 3: Logging in to ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URL" > /dev/null
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Step 4: Build Docker image
echo ""
echo -e "${YELLOW}Step 4: Building Docker image...${NC}"
echo "This may take a few minutes..."
docker build -f Dockerfile.prod -t "$ECR_REPOSITORY:latest" . > /dev/null
echo -e "${GREEN}✓ Docker image built${NC}"

# Step 5: Tag Docker image
echo ""
echo -e "${YELLOW}Step 5: Tagging Docker image...${NC}"
docker tag "$ECR_REPOSITORY:latest" "$ECR_URL:latest"
echo -e "${GREEN}✓ Docker image tagged${NC}"

# Step 6: Push Docker image
echo ""
echo -e "${YELLOW}Step 6: Pushing Docker image to ECR...${NC}"
echo "This may take a few minutes..."
docker push "$ECR_URL:latest" > /dev/null
echo -e "${GREEN}✓ Docker image pushed to ECR${NC}"

# Step 7: Generate secret key
echo ""
echo -e "${YELLOW}Step 7: Generating secret key...${NC}"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ Secret key generated${NC}"

# Step 8: Check if App Runner service exists
echo ""
echo -e "${YELLOW}Step 8: Checking App Runner service...${NC}"
SERVICE_ARN=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='${APP_RUNNER_SERVICE}'].ServiceArn" --output text 2>/dev/null || echo "")

if [ -z "$SERVICE_ARN" ]; then
    echo -e "${YELLOW}⚠ Service does not exist. You need to create it manually in AWS Console.${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "1. Go to AWS App Runner Console:"
    echo "   https://console.aws.amazon.com/apprunner/"
    echo ""
    echo "2. Click 'Create service'"
    echo ""
    echo "3. Select 'Container registry' → 'Amazon ECR'"
    echo ""
    echo "4. Select repository: $ECR_REPOSITORY"
    echo "   Image tag: latest"
    echo ""
    echo "5. Configure service:"
    echo "   - Service name: $APP_RUNNER_SERVICE"
    echo "   - CPU: 1 vCPU"
    echo "   - Memory: 2 GB"
    echo "   - Port: 8000"
    echo ""
    echo "6. Set environment variables:"
    echo "   - SECRET_KEY = $SECRET_KEY"
    echo "   - ENVIRONMENT = production"
    echo "   - AWS_REGION = $AWS_REGION"
    echo ""
    echo "7. Set IAM roles:"
    echo "   - Access role: AppRunnerECRAccessRole"
    echo "   - Instance role: AppRunnerInstanceRole"
    echo ""
    echo "8. Click 'Create & deploy'"
    echo ""
    echo -e "${GREEN}✓ Docker image is ready in ECR!${NC}"
    echo ""
    echo -e "${YELLOW}⚠ Save this SECRET_KEY: $SECRET_KEY${NC}"
else
    echo -e "${GREEN}✓ Service exists: $SERVICE_ARN${NC}"
    echo ""
    echo -e "${YELLOW}Step 9: Updating App Runner service...${NC}"
    
    # Trigger a new deployment
    aws apprunner start-deployment \
        --service-arn "$SERVICE_ARN" \
        --region "$AWS_REGION" > /dev/null
    
    echo -e "${GREEN}✓ Deployment started!${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Deployment Status:${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Service ARN: $SERVICE_ARN"
    echo "Deployment in progress..."
    echo ""
    echo "To check status:"
    echo "  aws apprunner describe-service --service-arn $SERVICE_ARN --region $AWS_REGION"
    echo ""
    echo "To view logs:"
    echo "  aws logs tail /aws/apprunner/$APP_RUNNER_SERVICE/service --follow --region $AWS_REGION"
    echo ""
    
    # Get service URL
    SERVICE_URL=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$AWS_REGION" --query 'Service.ServiceUrl' --output text 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
        echo ""
        echo "📍 Access your backend:"
        echo "   API: $SERVICE_URL"
        echo "   Docs: $SERVICE_URL/docs"
        echo "   Health: $SERVICE_URL/health"
        echo ""
    fi
    
    echo -e "${YELLOW}⚠ SECRET_KEY: $SECRET_KEY${NC}"
    echo -e "${YELLOW}⚠ Make sure SECRET_KEY is set in App Runner environment variables!${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Default admin credentials:"
echo "  Email: admin@example.com"
echo "  Password: Admin123!"
echo ""
echo -e "${YELLOW}⚠ Change the admin password after first login!${NC}"
echo ""

