# Quick Start: AWS App Runner Deployment

This is a quick reference for deploying to AWS App Runner. For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Prerequisites

- AWS CLI installed and configured
- Docker installed
- AWS account with appropriate permissions

## Quick Deployment

### 1. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save this value for Step 3.

### 2. Deploy

```bash
# Make script executable
chmod +x deploy-apprunner.sh

# Run deployment
./deploy-apprunner.sh
```

### 3. Create App Runner Service (First Time)

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Click "Create service"
3. Select "Container registry" → "Amazon ECR"
4. Select repository: `time-tracking-backend`
5. Configure:
   - **Service name**: `time-tracking-backend`
   - **Virtual CPU**: 1 vCPU
   - **Memory**: 2 GB
   - **Port**: 8000
6. Set environment variables:
   - `SECRET_KEY` = (value from Step 1)
   - `ENVIRONMENT` = `production`
   - `AWS_REGION` = `us-east-1`
   - `CORS_ORIGINS` = `https://yourdomain.com` (your frontend URL)
7. Configure IAM roles (see DEPLOYMENT.md for details)
8. Create service

### 4. Verify

```bash
# Get service URL
aws apprunner list-services --region us-east-1

# Test health endpoint
curl https://<service-url>/health
```

## Environment Variables

Required:
- `SECRET_KEY` - JWT secret (generate with command above)
- `ENVIRONMENT` - Set to `production`

Optional (with defaults):
- `AWS_REGION` - Default: `us-east-1`
- `DYNAMODB_USERS_TABLE` - Default: `time_tracking_users`
- `DYNAMODB_TIMELOGS_TABLE` - Default: `time_tracking_logs`
- `DYNAMODB_AUDIT_TABLE` - Default: `time_tracking_audit`
- `DYNAMODB_HOLIDAYS_TABLE` - Default: `time_tracking_holidays`
- `DYNAMODB_LEAVE_REQUESTS_TABLE` - Default: `time_tracking_leave_requests`
- `CORS_ORIGINS` - Comma-separated list of allowed origins

## Default Admin User

On first startup, a default admin user is created:
- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ Change this password immediately after first login!**

## Cost

- **Monthly**: ~$8-10/month (1 vCPU, 2 GB RAM, always-on)
- **With scale-to-zero**: ~$5-7/month

See [AWS_DEPLOYMENT_COST.md](../AWS_DEPLOYMENT_COST.md) for detailed cost breakdown.

## Troubleshooting

- **Service won't start**: Check CloudWatch logs
- **Can't connect to DynamoDB**: Verify IAM role has DynamoDB permissions
- **CORS errors**: Update `CORS_ORIGINS` environment variable

## Next Steps

1. Set up custom domain
2. Configure CI/CD for automatic deployments
3. Set up monitoring and alerts
4. Deploy frontend to S3 + CloudFront

For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

