#!/bin/bash
# Quick Deployment Script for AWS App Runner
# This script automates Steps 1-5 of the deployment process

set -e

echo "=========================================="
echo "AWS App Runner Quick Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-time-tracking-backend}"

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI is not installed${NC}"
    echo "Please install AWS CLI first: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker first: https://www.docker.com/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check AWS credentials
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
echo "Configuration:"
echo "  Region: $AWS_REGION"
echo "  Account ID: $AWS_ACCOUNT_ID"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  ECR URL: $ECR_URL"
echo ""

# Step 2: Create ECR repository
echo "Step 2: Creating ECR repository..."
if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &>/dev/null; then
    echo -e "${YELLOW}⚠ Repository already exists${NC}"
else
    aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" > /dev/null
    echo -e "${GREEN}✓ Repository created${NC}"
fi

# Step 3: Login to ECR
echo ""
echo "Step 3: Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URL" > /dev/null
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Step 4: Build Docker image
echo ""
echo "Step 4: Building Docker image..."
echo "This may take a few minutes..."
docker build -f Dockerfile.prod -t "$ECR_REPOSITORY:latest" . > /dev/null
echo -e "${GREEN}✓ Docker image built${NC}"

# Step 5: Tag Docker image
echo ""
echo "Step 5: Tagging Docker image..."
docker tag "$ECR_REPOSITORY:latest" "$ECR_URL:latest"
echo -e "${GREEN}✓ Docker image tagged${NC}"

# Step 6: Push Docker image
echo ""
echo "Step 6: Pushing Docker image to ECR..."
echo "This may take a few minutes..."
docker push "$ECR_URL:latest" > /dev/null
echo -e "${GREEN}✓ Docker image pushed to ECR${NC}"

# Step 7: Generate secret key
echo ""
echo "Step 7: Generating secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ Secret key generated${NC}"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Save this secret key!${NC}"
echo "SECRET_KEY=$SECRET_KEY"
echo ""

# Summary
echo "=========================================="
echo "Deployment Preparation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to AWS App Runner Console: https://console.aws.amazon.com/apprunner/"
echo "2. Create a new service"
echo "3. Select 'Container registry' → 'Amazon ECR'"
echo "4. Select repository: $ECR_REPOSITORY"
echo "5. Configure environment variables:"
echo "   - SECRET_KEY=$SECRET_KEY"
echo "   - ENVIRONMENT=production"
echo "   - AWS_REGION=$AWS_REGION"
echo "6. Set up IAM roles (see DEPLOY_WALKTHROUGH.md)"
echo "7. Deploy!"
echo ""
echo "For detailed instructions, see: DEPLOY_WALKTHROUGH.md"
echo ""

