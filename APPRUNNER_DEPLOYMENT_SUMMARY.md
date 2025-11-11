# AWS App Runner Deployment - Summary

## ✅ What's Been Prepared

Your application is now ready for AWS App Runner deployment! Here's what has been set up:

### 1. Configuration Files

- **`apprunner.yaml`** - App Runner service configuration
- **`Dockerfile.prod`** - Production-optimized Dockerfile
- **`start_prod.sh`** - Production startup script
- **`.dockerignore`** - Excludes unnecessary files from Docker build
- **`apprunner-service-config.yaml`** - Service configuration template

### 2. Code Updates

- **CORS Configuration** - Updated to support comma-separated origins from environment variables
- **DynamoDB Client** - Updated to use IAM roles (default) or credentials (fallback)
- **Production Startup** - Automatically initializes database tables and creates default admin user

### 3. Deployment Scripts

- **`deploy-apprunner.sh`** - Automated deployment script
- **`DEPLOYMENT.md`** - Comprehensive deployment guide
- **`README-APPRUNNER.md`** - Quick start guide

## 🚀 Quick Start

### 1. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Deploy

```bash
cd backend
chmod +x deploy-apprunner.sh
./deploy-apprunner.sh
```

### 3. Create App Runner Service

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Create new service from ECR
3. Select your repository: `time-tracking-backend`
4. Configure environment variables (see below)
5. Set up IAM roles (see DEPLOYMENT.md)
6. Deploy!

## 📋 Required Environment Variables

### Required:
- `SECRET_KEY` - JWT secret key (generate with command above)
- `ENVIRONMENT` - Set to `production`

### Optional (with defaults):
- `AWS_REGION` - Default: `us-east-1`
- `CORS_ORIGINS` - Comma-separated list (e.g., `https://yourdomain.com`)
- `DYNAMODB_*_TABLE` - Table names (defaults provided)

### AWS Credentials:
- **Recommended**: Use IAM role (no credentials needed)
- **Alternative**: Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

## 💰 Cost Estimate

- **Monthly**: ~$8-10/month (1 vCPU, 2 GB RAM, always-on)
- **With scale-to-zero**: ~$5-7/month
- **Plus**: DynamoDB (~$0.70/month) + S3/CloudFront (~$0.90/month)
- **Total**: ~$10-13/month

See [AWS_DEPLOYMENT_COST.md](./AWS_DEPLOYMENT_COST.md) for detailed breakdown.

## 📁 Files Created

```
backend/
├── apprunner.yaml                 # App Runner configuration
├── Dockerfile.prod                # Production Dockerfile
├── start_prod.sh                  # Production startup script
├── deploy-apprunner.sh            # Deployment script
├── apprunner-service-config.yaml  # Service config template
├── DEPLOYMENT.md                  # Detailed deployment guide
├── README-APPRUNNER.md            # Quick start guide
└── .dockerignore                  # Docker ignore file
```

## 🔧 Key Features

### Production-Ready
- ✅ Non-root user for security
- ✅ Health checks configured
- ✅ Automatic database initialization
- ✅ Default admin user creation
- ✅ Production logging
- ✅ CORS configuration

### AWS Optimized
- ✅ IAM role support (no credentials needed)
- ✅ DynamoDB integration
- ✅ CloudWatch logging
- ✅ Auto-scaling ready
- ✅ HTTPS included (App Runner provides)

### Easy Deployment
- ✅ One-command deployment script
- ✅ Automated ECR push
- ✅ Environment variable support
- ✅ Health check endpoint
- ✅ Comprehensive documentation

## 📖 Documentation

- **Quick Start**: See [backend/README-APPRUNNER.md](./backend/README-APPRUNNER.md)
- **Detailed Guide**: See [backend/DEPLOYMENT.md](./backend/DEPLOYMENT.md)
- **Cost Analysis**: See [AWS_DEPLOYMENT_COST.md](./AWS_DEPLOYMENT_COST.md)

## 🔐 Security Notes

1. **Secret Key**: Generate a secure secret key (never use default)
2. **IAM Roles**: Use IAM roles instead of access keys when possible
3. **CORS**: Set `CORS_ORIGINS` to your frontend domain only
4. **Default Admin**: Change default admin password immediately after deployment
5. **Environment**: Set `ENVIRONMENT=production` in App Runner

## 🎯 Next Steps

1. **Deploy Backend**: Run `./deploy-apprunner.sh`
2. **Create Service**: Set up App Runner service in AWS Console
3. **Configure Environment**: Set environment variables
4. **Test Deployment**: Verify health endpoint works
5. **Deploy Frontend**: Deploy frontend to S3 + CloudFront
6. **Update Frontend**: Point frontend to App Runner URL
7. **Set Up Monitoring**: Configure CloudWatch alarms
8. **Set Up CI/CD**: Automate deployments (optional)

## 🐛 Troubleshooting

### Service Won't Start
- Check CloudWatch logs
- Verify environment variables
- Check IAM role permissions

### Can't Connect to DynamoDB
- Verify IAM role has DynamoDB permissions
- Check AWS region is correct
- Verify table names match

### CORS Errors
- Update `CORS_ORIGINS` environment variable
- Restart service after updating

For more troubleshooting, see [backend/DEPLOYMENT.md](./backend/DEPLOYMENT.md).

## 📞 Support

For detailed instructions, see:
- [DEPLOYMENT.md](./backend/DEPLOYMENT.md) - Full deployment guide
- [README-APPRUNNER.md](./backend/README-APPRUNNER.md) - Quick reference
- [AWS App Runner Docs](https://docs.aws.amazon.com/apprunner/)

---

**Ready to deploy?** Run `./deploy-apprunner.sh` and follow the prompts!

