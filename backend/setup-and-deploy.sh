#!/bin/bash
# Complete Setup and Deployment Script
# This script creates everything needed and deploys the application

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Complete Setup and Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-time-tracking-backend}"
APP_RUNNER_SERVICE="${APP_RUNNER_SERVICE:-time-tracking-backend}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo -e "${BLUE}Configuration:${NC}"
echo "  Region: $AWS_REGION"
echo "  Account ID: $AWS_ACCOUNT_ID"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  App Runner Service: $APP_RUNNER_SERVICE"
echo ""

# Check if IAM roles exist
echo -e "${YELLOW}Checking IAM roles...${NC}"
ACCESS_ROLE_ARN=$(aws iam get-role --role-name AppRunnerECRAccessRole --query 'Role.Arn' --output text 2>/dev/null || echo "")
INSTANCE_ROLE_ARN=$(aws iam get-role --role-name AppRunnerInstanceRole --query 'Role.Arn' --output text 2>/dev/null || echo "")

if [ -z "$ACCESS_ROLE_ARN" ] || [ -z "$INSTANCE_ROLE_ARN" ]; then
    echo -e "${YELLOW}⚠ IAM roles not found.${NC}"
    echo "Please create them first using: CREATE_IAM_ROLES_CONSOLE_FIXED.md"
    echo "Or run the IAM setup script if available."
    exit 1
fi

echo -e "${GREEN}✓ IAM roles found${NC}"
echo "  Access Role: $ACCESS_ROLE_ARN"
echo "  Instance Role: $INSTANCE_ROLE_ARN"
echo ""

# Generate secret key
echo -e "${YELLOW}Generating secret key...${NC}"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}✓ Secret key generated${NC}"
echo ""

# Deploy using deploy-all.sh
echo -e "${YELLOW}Deploying application...${NC}"
echo ""

# Check if App Runner service exists
SERVICE_ARN=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='${APP_RUNNER_SERVICE}'].ServiceArn" --output text 2>/dev/null || echo "")

if [ -z "$SERVICE_ARN" ]; then
    echo -e "${YELLOW}Service does not exist. Creating with CloudFormation...${NC}"
    
    # Create CloudFormation stack
    STACK_NAME="${APP_RUNNER_SERVICE}-stack"
    
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://apprunner-cloudformation.yaml \
        --parameters \
            ParameterKey=ECRRepositoryUri,ParameterValue="$ECR_URL" \
            ParameterKey=ECRImageTag,ParameterValue=latest \
            ParameterKey=AccessRoleArn,ParameterValue="$ACCESS_ROLE_ARN" \
            ParameterKey=InstanceRoleArn,ParameterValue="$INSTANCE_ROLE_ARN" \
            ParameterKey=SecretKey,ParameterValue="$SECRET_KEY" \
            ParameterKey=Environment,ParameterValue=production \
            ParameterKey=AwsRegion,ParameterValue="$AWS_REGION" \
            ParameterKey=ServiceName,ParameterValue="$APP_RUNNER_SERVICE" \
        --region "$AWS_REGION" \
        --capabilities CAPABILITY_NAMED_IAM > /dev/null
    
    echo -e "${GREEN}✓ CloudFormation stack created${NC}"
    echo "Waiting for stack creation to complete..."
    
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"
    
    # Get service URL
    SERVICE_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query "Stacks[0].Outputs[?OutputKey=='ServiceUrl'].OutputValue" --output text)
    
    echo -e "${GREEN}✓ App Runner service created!${NC}"
    echo ""
    echo "Service URL: $SERVICE_URL"
else
    echo -e "${GREEN}✓ Service exists. Updating...${NC}"
    
    # Use deploy-all.sh to update
    ./deploy-all.sh
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service URL: $SERVICE_URL"
echo ""
echo "Default admin credentials:"
echo "  Email: admin@example.com"
echo "  Password: Admin123!"
echo ""
echo -e "${YELLOW}⚠ Change the admin password after first login!${NC}"
echo ""

