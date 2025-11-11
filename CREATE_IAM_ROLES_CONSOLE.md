# Create IAM Roles for App Runner - AWS Console Guide

This guide will walk you through creating the required IAM roles for AWS App Runner using the AWS Console (no CLI needed).

## 📋 Overview

You need to create **2 IAM roles**:

1. **AppRunnerECRAccessRole** - Allows App Runner to pull Docker images from ECR
2. **AppRunnerInstanceRole** - Allows your application to access DynamoDB

---

## Step 1: Create ECR Access Role

This role allows App Runner to pull Docker images from Amazon ECR.

### 1.1 Open IAM Console

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Make sure you're in the correct region (region doesn't matter for IAM)
3. Click **"Roles"** in the left sidebar
4. Click **"Create role"** button

### 1.2 Select Trusted Entity

1. Under **"Select trusted entity"**, choose **"Custom trust policy"**
2. You'll see a JSON editor for the trust policy
3. **Delete** the default content
4. **Paste** this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

5. Click **"Next"**

### 1.3 Add Permissions

1. In the search box, type: **"AppRunnerECRAccess"**
2. Check the box next to **"AWSAppRunnerServicePolicyForECRAccess"**
3. This is a managed policy that provides ECR access
4. Click **"Next"**

### 1.4 Name and Review

1. **Role name**: Enter `AppRunnerECRAccessRole`
2. **Description** (optional): "Allows App Runner to pull Docker images from ECR"
3. Review the permissions:
   - Trusted entity: `build.apprunner.amazonaws.com`
   - Permissions: `AWSAppRunnerServicePolicyForECRAccess`
4. Click **"Create role"**

### 1.5 Verify Role Created

1. You should see a success message
2. The role `AppRunnerECRAccessRole` should appear in your roles list
3. Click on the role name to view details
4. Note the **Role ARN** (you'll need this later):
   ```
   arn:aws:iam::YOUR_ACCOUNT_ID:role/AppRunnerECRAccessRole
   ```

✅ **Step 1 Complete!** You've created the ECR Access Role.

---

## Step 2: Create Instance Role

This role allows your application running in App Runner to access DynamoDB.

### 2.1 Create New Role

1. In the IAM Console, click **"Roles"** in the left sidebar
2. Click **"Create role"** button

### 2.2 Select Trusted Entity

1. Under **"Select trusted entity"**, choose **"Custom trust policy"**
2. You'll see a JSON editor for the trust policy
3. **Delete** the default content
4. **Paste** this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "tasks.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

5. Click **"Next"**

### 2.3 Add Permissions (Skip for Now)

1. **Don't select any permissions yet** - we'll create a custom policy
2. Click **"Next"** (you'll see a warning, that's okay)

### 2.4 Name and Create Role

1. **Role name**: Enter `AppRunnerInstanceRole`
2. **Description** (optional): "Allows App Runner instances to access DynamoDB"
3. Click **"Create role"**

### 2.5 Create Custom DynamoDB Policy

1. After the role is created, click on the role name `AppRunnerInstanceRole`
2. Click on the **"Permissions"** tab
3. Click **"Add permissions"** → **"Create inline policy"**
4. Click on the **"JSON"** tab
5. Replace the content with the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem",
        "dynamodb:DescribeTable",
        "dynamodb:CreateTable"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/time_tracking_*",
        "arn:aws:dynamodb:*:*:table/time_tracking_*/index/*"
      ]
    }
  ]
}
```

6. Click **"Next"** or **"Review policy"**
7. **Policy name**: Enter `DynamoDBAccess`
8. **Description** (optional): "Allows access to time_tracking DynamoDB tables"
9. Click **"Create policy"**

### 2.6 Verify Policy Attached

1. You should see the policy `DynamoDBAccess` attached to the role
2. The role should now have permissions to access DynamoDB tables
3. Note the **Role ARN** (you'll need this later):
   ```
arn:aws:iam::463470962760:role/AppRunnerInstanceRole
   ```

✅ **Step 2 Complete!** You've created the Instance Role with DynamoDB permissions.

---

## Step 3: Verify Both Roles

### 3.1 Check Roles List

1. Go to **"Roles"** in the IAM Console
2. You should see both roles:
   - ✅ `AppRunnerECRAccessRole`
   - ✅ `AppRunnerInstanceRole`

### 3.2 Verify ECR Access Role

1. Click on `AppRunnerECRAccessRole`
2. Check **"Trust relationships"** tab:
   - Should show: `build.apprunner.amazonaws.com`
3. Check **"Permissions"** tab:
   - Should have: `AWSAppRunnerServicePolicyForECRAccess`

### 3.3 Verify Instance Role

1. Click on `AppRunnerInstanceRole`
2. Check **"Trust relationships"** tab:
   - Should show: `tasks.apprunner.amazonaws.com`
3. Check **"Permissions"** tab:
   - Should have: `DynamoDBAccess` (inline policy)

---

## Step 4: Get Role ARNs (For App Runner Configuration)

You'll need the Role ARNs when creating the App Runner service.

### 4.1 Get ECR Access Role ARN

1. Click on `AppRunnerECRAccessRole`
2. Copy the **Role ARN** from the top of the page
3. It looks like: `arn:aws:iam::123456789012:role/AppRunnerECRAccessRole`

### 4.2 Get Instance Role ARN

1. Click on `AppRunnerInstanceRole`
2. Copy the **Role ARN** from the top of the page
3. It looks like: `arn:aws:iam::463470962760:role/AppRunnerInstanceRole`

### 4.3 Save Role ARNs

Save these ARNs somewhere safe - you'll need them when creating the App Runner service:
- **ECR Access Role ARN**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/AppRunnerECRAccessRole`
- **Instance Role ARN**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/AppRunnerInstanceRole`

---

## Step 5: Use Roles in App Runner

When you create the App Runner service (in the next steps), you'll use these roles:

1. **Access role**: Select `AppRunnerECRAccessRole`
2. **Instance role**: Select `AppRunnerInstanceRole`

The App Runner console will show these roles in dropdown menus, so you don't need to paste the ARNs manually.

---

## 🎯 Quick Reference

### Role 1: ECR Access Role
- **Name**: `AppRunnerECRAccessRole`
- **Purpose**: Allows App Runner to pull Docker images from ECR
- **Trusted Entity**: `build.apprunner.amazonaws.com`
- **Permissions**: `AWSAppRunnerServicePolicyForECRAccess` (managed policy)

### Role 2: Instance Role
- **Name**: `AppRunnerInstanceRole`
- **Purpose**: Allows application to access DynamoDB
- **Trusted Entity**: `tasks.apprunner.amazonaws.com`
- **Permissions**: `DynamoDBAccess` (inline policy with DynamoDB access)

---

## ✅ Checklist

- [ ] ECR Access Role created (`AppRunnerECRAccessRole`)
- [ ] ECR Access Role has correct trust relationship
- [ ] ECR Access Role has ECR access policy attached
- [ ] Instance Role created (`AppRunnerInstanceRole`)
- [ ] Instance Role has correct trust relationship
- [ ] Instance Role has DynamoDB access policy attached
- [ ] Both role ARNs saved for App Runner configuration

---

## 🆘 Troubleshooting

### Role Not Showing in App Runner Console

If the roles don't appear in the App Runner console dropdown:
1. Make sure you're in the same AWS region
2. Wait a few minutes for the roles to propagate
3. Refresh the App Runner console page
4. Verify the role names are exactly: `AppRunnerECRAccessRole` and `AppRunnerInstanceRole`

### Permission Denied Errors

If you get permission errors:
1. Verify the trust relationships are correct
2. Check that the policies are attached correctly
3. Verify the DynamoDB policy allows access to `time_tracking_*` tables
4. Make sure you're using the correct role ARNs

### DynamoDB Access Denied

If your application can't access DynamoDB:
1. Verify the Instance Role has the DynamoDB policy attached
2. Check that the policy allows access to `time_tracking_*` tables
3. Verify the table names match (e.g., `time_tracking_users`)
4. Check that the region in the policy matches your DynamoDB region

---

## 📚 Next Steps

Now that you've created the IAM roles, you can:

1. ✅ Proceed to create the App Runner service
2. ✅ Use these roles when configuring App Runner
3. ✅ Deploy your application

For the next steps, see:
- [DEPLOY_WALKTHROUGH.md](./DEPLOY_WALKTHROUGH.md) - Complete deployment guide
- [QUICK_START_DEPLOY.md](./QUICK_START_DEPLOY.md) - Quick start guide

---

## 🎉 Roles Created!

You've successfully created both IAM roles needed for App Runner deployment. You're now ready to create the App Runner service!

**Next**: Go to the App Runner console and create your service using these roles.

