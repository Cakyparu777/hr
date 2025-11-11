# Switch App Runner to ECR Deployment

## Quick Fix Steps

### Step 1: Push Docker Image to ECR

```bash
cd backend
./quick-deploy.sh
```

This will:
- Build the Docker image
- Push it to ECR
- Generate a secret key for you

### Step 2: Delete Current App Runner Service

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Find your service: `time-tracking-backend`
3. Click on it
4. Click **"Delete"** (or create a new one with a different name)

### Step 3: Create New App Runner Service with ECR

1. Click **"Create service"**
2. Select **"Container registry"** → **"Amazon ECR"** (NOT "Source code repository")
3. Select repository: `time-tracking-backend`
4. Select image tag: `latest`
5. Configure service:
   - **Service name**: `time-tracking-backend`
   - **Virtual CPU**: 1 vCPU
   - **Memory**: 2 GB
   - **Port**: 8000
6. Set environment variables:
   - `SECRET_KEY` = (from quick-deploy.sh output)
   - `ENVIRONMENT` = `production`
   - `AWS_REGION` = `us-east-1`
   - `CORS_ORIGINS` = (your frontend URL)
7. Set IAM roles:
   - **Access role**: `AppRunnerECRAccessRole`
   - **Instance role**: `AppRunnerInstanceRole`
8. Click **"Create & deploy"**

### Step 4: Wait for Deployment

Wait 5-10 minutes for the service to deploy.

### Step 5: Test

```bash
# Get service URL from App Runner console
export SERVICE_URL="https://your-service-url.us-east-1.awsapprunner.com"

# Test health
curl $SERVICE_URL/health

# Test admin login
curl -X POST $SERVICE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

## ✅ Admin Account

**Yes, the admin account is created automatically!**

The `start_prod.sh` script runs `create_default_admin.py` on startup, which creates:
- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ Change this password immediately after first login!**

You'll see this in the App Runner logs:
```
✓ Default admin user created!
  Email: admin@example.com
  Password: Admin123!
  ⚠️  Please change the password after first login!
```

## Why ECR is Better

✅ **More reliable** - Pre-built images  
✅ **Faster** - No build time  
✅ **Matches our setup** - We prepared everything for ECR  
✅ **Better for production** - Versioned images  
✅ **Easier debugging** - Test locally first  

---

**Ready to switch?** Run `./quick-deploy.sh` and follow the steps above!

