# Fix App Runner Deployment Error

## 🔴 Current Error

```
Failed to build your application source code. Reason: App Runner configuration file apprunner.yaml not found.
```

## ✅ Solution: Two Options

You have two options to fix this:

### Option 1: Use ECR Deployment (Recommended) ⭐

**Why?** We've already prepared everything for ECR deployment, and it's more reliable.

### Option 2: Fix Source Code Deployment

Add `apprunner.yaml` to the root directory (I've already created it for you).

---

## Option 1: Switch to ECR Deployment (Recommended)

### Why ECR is Better:

✅ **More reliable** - Pre-built and tested Docker images  
✅ **Faster** - No build time during deployment  
✅ **Matches our setup** - We prepared everything for ECR  
✅ **Better for production** - Versioned container images  
✅ **Easier debugging** - Test images locally before pushing  

### Steps to Switch:

1. **Push Docker image to ECR** (if not already done):
   ```bash
   cd backend
   ./quick-deploy.sh
   ```

2. **Delete current App Runner service** (or create a new one)

3. **Create new App Runner service**:
   - Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
   - Click **"Create service"**
   - Select **"Container registry"** → **"Amazon ECR"** (NOT "Source code repository")
   - Select your ECR repository: `time-tracking-backend`
   - Select image tag: `latest`
   - Configure:
     - **Service name**: `time-tracking-backend`
     - **CPU**: 1 vCPU
     - **Memory**: 2 GB
     - **Port**: 8000
   - Set environment variables (see below)
   - Set IAM roles:
     - **Access role**: `AppRunnerECRAccessRole`
     - **Instance role**: `AppRunnerInstanceRole`
   - Click **"Create & deploy"**

### Environment Variables for ECR Deployment:

Required:
- `SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `ENVIRONMENT` - Set to `production`
- `AWS_REGION` - Set to `us-east-1`

Optional (with defaults):
- `CORS_ORIGINS` - Your frontend URL (comma-separated)
- `DYNAMODB_*_TABLE` - Table names (defaults provided)

**Note**: You don't need `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` if you're using IAM roles (recommended).

---

## Option 2: Fix Source Code Deployment

### Step 1: Commit apprunner.yaml to Repository

I've created `apprunner.yaml` in the root directory. You need to commit and push it:

```bash
# Add apprunner.yaml to git
git add apprunner.yaml

# Commit
git commit -m "Add apprunner.yaml for App Runner source deployment"

# Push to prod branch
git push origin prod
```

### Step 2: Update App Runner Service

1. Go to App Runner Console
2. Go to your service
3. Click **"Configuration"** tab
4. Update the source configuration:
   - **Source directory**: `/` (root)
   - **Build command**: (leave default)
   - **Start command**: (leave default)

### Step 3: Redeploy

App Runner should automatically detect the new `apprunner.yaml` file and redeploy.

### Limitations of Source Code Deployment:

⚠️ **Docker builds in App Runner are limited**  
⚠️ **Slower deployments** (builds on every deploy)  
⚠️ **Less reliable** (build failures during deployment)  
⚠️ **Harder to debug** (can't test builds locally easily)  

---

## 🎯 Recommended: Use ECR Deployment

**I recommend switching to ECR deployment** because:

1. ✅ We've already prepared everything for ECR
2. ✅ More reliable for production
3. ✅ Faster deployments
4. ✅ Better debugging capabilities
5. ✅ Matches our deployment setup

### Quick Switch to ECR:

```bash
# 1. Push Docker image to ECR
cd backend
./quick-deploy.sh

# 2. Create new App Runner service with ECR
# (Follow steps in Option 1 above)
```

---

## 📋 Admin Account Creation

**Yes, the admin account is created automatically!** 

The `start_prod.sh` script runs `create_default_admin.py` on startup, which creates:

- **Email**: `admin@example.com`
- **Password**: `Admin123!`

**⚠️ IMPORTANT**: Change this password immediately after first login!

This happens automatically when the App Runner service starts, whether you use ECR or source code deployment.

---

## 🔍 Verify Deployment

After deployment (ECR or source code):

1. **Check health endpoint**:
   ```bash
   curl https://your-service-url.us-east-1.awsapprunner.com/health
   ```

2. **Test admin login**:
   ```bash
   curl -X POST https://your-service-url.us-east-1.awsapprunner.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@example.com",
       "password": "Admin123!"
     }'
   ```

3. **Check logs**:
   - Go to App Runner Console → Your Service → Logs
   - Look for: "✓ Default admin user created!"

---

## 🆘 Troubleshooting

### If ECR deployment fails:

1. Verify Docker image was pushed:
   ```bash
   aws ecr describe-images --repository-name time-tracking-backend --region us-east-1
   ```

2. Check IAM roles are correct:
   - Access role: `AppRunnerECRAccessRole`
   - Instance role: `AppRunnerInstanceRole`

3. Verify environment variables are set correctly

### If source code deployment fails:

1. Verify `apprunner.yaml` is in the root directory
2. Check the file is committed and pushed to the `prod` branch
3. Verify the build commands in `apprunner.yaml` are correct
4. Check App Runner logs for specific error messages

---

## 📚 Next Steps

1. **Choose deployment method** (ECR recommended)
2. **Push Docker image to ECR** (if using ECR)
3. **Create/update App Runner service**
4. **Configure environment variables**
5. **Deploy and verify**
6. **Test admin login**
7. **Change default admin password**

---

## ✅ Summary

- **Current issue**: App Runner can't find `apprunner.yaml` for source code deployment
- **Solution 1** (Recommended): Switch to ECR deployment
- **Solution 2**: Add `apprunner.yaml` to root and commit to repository
- **Admin account**: Created automatically on startup
- **Next step**: Choose ECR deployment and follow the steps above

**Ready to deploy?** Use ECR deployment for the best experience!

