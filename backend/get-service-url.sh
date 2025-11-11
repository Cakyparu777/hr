#!/bin/bash
# Get App Runner Service URL

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
APP_RUNNER_SERVICE="${APP_RUNNER_SERVICE:-time-tracking-backend}"

echo "Getting App Runner service URL..."
echo ""

# Get service URL
SERVICE_URL=$(aws apprunner list-services --region "$AWS_REGION" --query "ServiceSummaryList[?ServiceName=='${APP_RUNNER_SERVICE}'].ServiceUrl" --output text 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo "⚠ Service not found!"
    echo ""
    echo "The Docker image is in ECR, but the App Runner service hasn't been created yet."
    echo ""
    echo "📋 To create the service:"
    echo "  1. Go to: https://console.aws.amazon.com/apprunner/"
    echo "  2. Click 'Create service'"
    echo "  3. Select 'Container registry' → 'Amazon ECR'"
    echo "  4. Select repository: time-tracking-backend"
    echo "  5. Configure service (see CREATE_APPRUNNER_SERVICE.md for details)"
    echo ""
    echo "📚 See: ../CREATE_APPRUNNER_SERVICE.md for step-by-step instructions"
    echo ""
    exit 1
fi

echo "✅ Backend API URL:"
echo "   $SERVICE_URL"
echo ""
echo "📍 Useful endpoints:"
echo "   Health: $SERVICE_URL/health"
echo "   API Docs: $SERVICE_URL/docs"
echo "   API Root: $SERVICE_URL/"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Email: admin@example.com"
echo "   Password: Admin123!"
echo ""
echo "⚠️  Change the admin password after first login!"
echo ""
echo "📝 Frontend Deployment:"
echo "   The frontend is not deployed yet. You need to:"
echo "   1. Build the frontend: cd ../frontend && npm run build"
echo "   2. Deploy to S3 + CloudFront (see frontend deployment guide)"
echo "   3. Update REACT_APP_API_URL to: $SERVICE_URL"
echo ""

