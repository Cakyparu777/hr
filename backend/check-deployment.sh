#!/bin/bash
# Check Deployment Status

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-time-tracking-backend}"
APP_RUNNER_SERVICE="${APP_RUNNER_SERVICE:-time-tracking-backend}"

echo "=========================================="
echo "Deployment Status Check"
echo "=========================================="
echo ""

# Check ECR
echo "1. Checking ECR repository..."
if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" --region "$AWS_REGION" &>/dev/null; then
    echo "   ✅ ECR repository exists: $ECR_REPOSITORY"
    
    # Check if image exists
    IMAGES=$(aws ecr describe-images --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" --query 'imageDetails | length(@)' --output text 2>/dev/null || echo "0")
    if [ "$IMAGES" -gt 0 ]; then
        echo "   ✅ Docker image exists in ECR"
        LATEST_IMAGE=$(aws ecr describe-images --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" --query 'sort_by(imageDetails, &imagePushedAt)[-1].imageTags[0]' --output text 2>/dev/null || echo "latest")
        echo "   📦 Latest image tag: $LATEST_IMAGE"
    else
        echo "   ⚠️  No images found in ECR repository"
    fi
else
    echo "   ❌ ECR repository not found: $ECR_REPOSITORY"
fi

echo ""

# Check App Runner Service
echo "2. Checking App Runner service..."
SERVICE_ARN=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='${APP_RUNNER_SERVICE}'].ServiceArn" --output text 2>/dev/null || echo "")
SERVICE_URL=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='${APP_RUNNER_SERVICE}'].ServiceUrl" --output text 2>/dev/null || echo "")

if [ -z "$SERVICE_ARN" ]; then
    echo "   ⚠️  App Runner service not found: $APP_RUNNER_SERVICE"
    echo "   📋 Next step: Create the service in AWS Console"
    echo "   📚 See: ../CREATE_APPRUNNER_SERVICE.md"
else
    echo "   ✅ App Runner service exists: $APP_RUNNER_SERVICE"
    
    if [ -n "$SERVICE_URL" ]; then
        echo "   🔗 Service URL: $SERVICE_URL"
        
        # Check service status
        SERVICE_STATUS=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$AWS_REGION" --query 'Service.Status' --output text 2>/dev/null || echo "UNKNOWN")
        echo "   📊 Status: $SERVICE_STATUS"
        
        if [ "$SERVICE_STATUS" = "RUNNING" ]; then
            echo "   ✅ Service is running!"
            echo ""
            echo "   📍 Access your backend:"
            echo "      API: $SERVICE_URL"
            echo "      Docs: $SERVICE_URL/docs"
            echo "      Health: $SERVICE_URL/health"
        else
            echo "   ⏳ Service is $SERVICE_STATUS (may still be deploying)"
        fi
    fi
fi

echo ""

# Check IAM Roles
echo "3. Checking IAM roles..."
ACCESS_ROLE=$(aws iam get-role --role-name AppRunnerECRAccessRole --query 'Role.RoleName' --output text 2>/dev/null || echo "")
INSTANCE_ROLE=$(aws iam get-role --role-name AppRunnerInstanceRole --query 'Role.RoleName' --output text 2>/dev/null || echo "")

if [ -n "$ACCESS_ROLE" ]; then
    echo "   ✅ ECR Access Role exists: $ACCESS_ROLE"
else
    echo "   ❌ ECR Access Role not found: AppRunnerECRAccessRole"
    echo "   📚 See: ../IAM_ROLES_SETUP.md"
fi

if [ -n "$INSTANCE_ROLE" ]; then
    echo "   ✅ Instance Role exists: $INSTANCE_ROLE"
else
    echo "   ❌ Instance Role not found: AppRunnerInstanceRole"
    echo "   📚 See: ../IAM_ROLES_SETUP.md"
fi

echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

if [ -n "$SERVICE_URL" ]; then
    echo "✅ Backend is deployed and running!"
    echo "   URL: $SERVICE_URL"
    echo ""
    echo "⏳ Frontend is not deployed yet"
    echo "   Deploy with: cd ../frontend && ./deploy-s3.sh"
else
    echo "⏳ Backend Docker image is in ECR"
    echo "📋 Next step: Create App Runner service"
    echo "   See: ../CREATE_APPRUNNER_SERVICE.md"
    echo ""
    echo "⏳ Frontend is not deployed yet"
fi

echo ""

