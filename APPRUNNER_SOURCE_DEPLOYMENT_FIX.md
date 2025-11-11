# App Runner Source Code Deployment - Fix Guide

## Issue

App Runner is trying to build from source code but can't find `apprunner.yaml` in the root directory.

## Solution Options

You have **two options**:

### Option 1: Use ECR (Container Registry) - Recommended ✅

This is the recommended approach since we've already prepared everything for container deployment.

### Option 2: Fix Source Code Deployment

Move `apprunner.yaml` to the root directory and configure it properly.

---

## Option 1: Switch to ECR Deployment (Recommended)

Since you've already built the Docker image, use ECR instead of source code:

### Steps:

1. **Delete the current App Runner service** (or create a new one)
2. **Push Docker image to ECR first** (if not already done):
   ```bash
   cd backend
   ./quick-deploy.sh
   ```

3. **Create new App Runner service**:
   - Go to App Runner Console
   - Click "Create service"
   - Select **"Container registry"** → **"Amazon ECR"** (NOT "Source code repository")
   - Select your ECR repository: `time-tracking-backend`
   - Select image tag: `latest`
   - Configure the rest as before

This is the recommended approach and matches our deployment setup.

---

## Option 2: Fix Source Code Deployment

If you want to use source code deployment, you need to:

### Step 1: Move apprunner.yaml to Root

I've created `apprunner.yaml` in the root directory. However, App Runner's source code deployment has limitations with Docker builds.

### Step 2: Update App Runner Service Configuration

**Better approach**: Switch to ECR deployment instead.

**Why?**
- Source code deployment in App Runner doesn't support complex Docker builds well
- ECR deployment is more reliable and matches our setup
- You've already prepared everything for ECR deployment

---

## Recommended: Use ECR Deployment

### Quick Steps:

1. **Push Docker image to ECR**:
   ```bash
   cd backend
   ./quick-deploy.sh
   ```

2. **Delete current App Runner service** (or create new one)

3. **Create new service with ECR**:
   - Source: **Container registry** → **Amazon ECR**
   - Repository: `time-tracking-backend`
   - Image tag: `latest`
   - Access role: `AppRunnerECRAccessRole`
   - Instance role: `AppRunnerInstanceRole`

4. **Configure environment variables** (same as before)

5. **Deploy**

---

## Why ECR is Better

✅ **More reliable** - Pre-built images are tested  
✅ **Faster deployments** - No build time  
✅ **Matches our setup** - We prepared everything for ECR  
✅ **Better for production** - Container images are versioned  
✅ **Easier debugging** - Test images locally before pushing  

---

## Next Steps

1. **Push Docker image to ECR** (if not done):
   ```bash
   cd backend
   ./quick-deploy.sh
   ```

2. **Create new App Runner service with ECR**:
   - Use "Container registry" instead of "Source code repository"
   - Select your ECR repository
   - Configure environment variables
   - Deploy

3. **Verify deployment**:
   - Check health endpoint
   - Test admin login
   - Verify all functionality

---

## Troubleshooting

### If you want to continue with source code deployment:

1. Make sure `apprunner.yaml` is in the root directory ✅ (I've created it)
2. The file should reference the backend directory correctly
3. However, App Runner source code deployment has limitations with Docker builds

### Recommended: Switch to ECR

Use ECR deployment instead - it's more reliable and matches our prepared setup.

---

## Summary

**Current Issue**: App Runner is configured for source code deployment but needs ECR deployment.

**Solution**: 
1. Push Docker image to ECR (`./quick-deploy.sh`)
2. Create new App Runner service with ECR (not source code)
3. Configure environment variables
4. Deploy

This matches our deployment preparation and is more reliable for production.

