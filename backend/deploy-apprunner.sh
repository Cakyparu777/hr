#!/bin/bash
set -e

# AWS App Runner Deployment Script
# This script builds and deploys the backend to AWS App Runner

echo "=== AWS App Runner Deployment Script ==="

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-time-tracking-backend}"
APP_RUNNER_SERVICE="${APP_RUNNER_SERVICE:-time-tracking-backend}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID if not provided
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Getting AWS account ID..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo "Error: Could not get AWS account ID. Make sure AWS credentials are configured."
        exit 1
    fi
    echo "AWS Account ID: $AWS_ACCOUNT_ID"
fi

# ECR repository URL
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "Region: $AWS_REGION"
echo "ECR Repository: $ECR_REPOSITORY"
echo "ECR URL: $ECR_URL"
echo "App Runner Service: $APP_RUNNER_SERVICE"
echo ""

# Step 1: Create ECR repository if it doesn't exist
echo "Step 1: Creating ECR repository (if it doesn't exist)..."
aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" 2>/dev/null || \
    aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION"
echo "✓ ECR repository ready"
echo ""

# Step 2: Login to ECR
echo "Step 2: Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URL"
echo "✓ Logged in to ECR"
echo ""

# Step 3: Build Docker image
echo "Step 3: Building Docker image..."
docker build -f Dockerfile.prod -t "$ECR_REPOSITORY:latest" .
echo "✓ Docker image built"
echo ""

# Step 4: Tag Docker image
echo "Step 4: Tagging Docker image..."
docker tag "$ECR_REPOSITORY:latest" "$ECR_URL:latest"
echo "✓ Docker image tagged"
echo ""

# Step 5: Push Docker image to ECR
echo "Step 5: Pushing Docker image to ECR..."
docker push "$ECR_URL:latest"
echo "✓ Docker image pushed to ECR"
echo ""

# Step 6: Update App Runner service (or create if it doesn't exist)
echo "Step 6: Updating App Runner service..."
if aws apprunner describe-service --service-arn "arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${APP_RUNNER_SERVICE}" --region "$AWS_REGION" &>/dev/null; then
    echo "Service exists. Updating..."
    aws apprunner start-deployment \
        --service-arn "arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${APP_RUNNER_SERVICE}" \
        --region "$AWS_REGION"
    echo "✓ App Runner service updated"
else
    echo "Service does not exist. Please create it via AWS Console first."
    echo "Or use the AWS CLI to create it with the apprunner.yaml configuration."
    echo ""
    echo "To create the service, run:"
    echo "  aws apprunner create-service --cli-input-yaml file://apprunner-service-config.yaml"
    echo ""
    echo "Or create it via AWS Console:"
    echo "  1. Go to AWS App Runner console"
    echo "  2. Create new service"
    echo "  3. Select 'Container registry' -> 'Amazon ECR'"
    echo "  4. Select the ECR repository: $ECR_REPOSITORY"
    echo "  5. Configure environment variables (see DEPLOYMENT.md)"
    echo "  6. Deploy"
fi

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Check App Runner service status in AWS Console"
echo "2. Update environment variables in App Runner service configuration"
echo "3. Test the API endpoint"
echo "4. Update frontend to use the new API URL"

