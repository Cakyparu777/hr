# Create IAM Roles for App Runner - AWS Console Guide

This guide shows you how to create the required IAM roles for AWS App Runner using **Custom Trust Policy** (since App Runner might not appear in the service list).

## 📋 Overview

You need to create **2 IAM roles**:

1. **AppRunnerECRAccessRole** - Allows App Runner to pull Docker images from ECR
2. **AppRunnerInstanceRole** - Allows your application to access DynamoDB

---

## Step 1: Create ECR Access Role

This role allows App Runner to pull Docker images from Amazon ECR.

### 1.1 Open IAM Console

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click **"Roles"** in the left sidebar
3. Click **"Create role"** button

### 1.2 Select Trusted Entity (Custom Trust Policy)

**Important**: Since App Runner might not appear in the service list, we'll use "Custom trust policy".

1. Under **"Select trusted entity"**, click **"Custom trust policy"**
2. You'll see a JSON editor with some default content
3. **Delete** all the default content
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
   - If you can't find it, search for: **"ECRAccess"**
   - Look for: **"AWSAppRunnerServicePolicyForECRAccess"**
3. This is a managed policy that provides ECR access
4. Click **"Next"**

### 1.4 Name and Review

1. **Role name**: Enter `AppRunnerECRAccessRole`
2. **Description** (optional): "Allows App Runner to pull Docker images from ECR"
3. Review the configuration:
   - Trust policy: `build.apprunner.amazonaws.com`
   - Permissions: `AWSAppRunnerServicePolicyForECRAccess`
4. Click **"Create role"**

### 1.5 Verify Role Created

1. You should see a success message
2. The role `AppRunnerECRAccessRole` should appear in your roles list
3. Click on the role name to view details
4. Verify the **Trust relationships** tab shows: `build.apprunner.amazonaws.com`

✅ **Step 1 Complete!** You've created the ECR Access Role.

---

## Step 2: Create Instance Role

This role allows your application running in App Runner to access DynamoDB.

### 2.1 Create New Role

1. In the IAM Console, click **"Roles"** in the left sidebar
2. Click **"Create role"** button

### 2.2 Select Trusted Entity (Custom Trust Policy)

1. Under **"Select trusted entity"**, click **"Custom trust policy"**
2. You'll see a JSON editor with some default content
3. **Delete** all the default content
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

### 2.3 Skip Permissions (We'll Add Custom Policy)

1. **Don't select any permissions yet** - we'll create a custom policy
2. Click **"Next"** (you might see a warning about no permissions - that's okay)

### 2.4 Name and Create Role

1. **Role name**: Enter `AppRunnerInstanceRole`
2. **Description** (optional): "Allows App Runner instances to access DynamoDB"
3. Click **"Create role"**

### 2.5 Create Custom DynamoDB Policy

1. After the role is created, click on the role name `AppRunnerInstanceRole`
2. Click on the **"Permissions"** tab
3. Click **"Add permissions"** → **"Create inline policy"**
4. Click on the **"JSON"** tab
5. **Delete** all the default content
6. **Paste** this policy:

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

7. Click **"Next"** or **"Review policy"**
8. **Policy name**: Enter `DynamoDBAccess`
9. **Description** (optional): "Allows access to time_tracking DynamoDB tables"
10. Click **"Create policy"**

### 2.6 Verify Policy Attached

1. You should see the policy `DynamoDBAccess` attached to the role
2. The role should now have permissions to access DynamoDB tables
3. Verify the **Trust relationships** tab shows: `tasks.apprunner.amazonaws.com`

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

## Step 4: Use Roles in App Runner

When you create the App Runner service, you'll use these roles:

1. **Access role**: Select `AppRunnerECRAccessRole`
2. **Instance role**: Select `AppRunnerInstanceRole`

The App Runner console will show these roles in dropdown menus when you create the service.

---

## 🎯 Quick Reference

### Trust Policy for Role 1 (ECR Access)
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

### Trust Policy for Role 2 (Instance Role)
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

### DynamoDB Policy (Inline Policy for Role 2)
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

---

## ✅ Checklist

- [ ] Role 1 created: `AppRunnerECRAccessRole`
- [ ] Role 1 has trust policy with `build.apprunner.amazonaws.com`
- [ ] Role 1 has ECR access policy attached
- [ ] Role 2 created: `AppRunnerInstanceRole`
- [ ] Role 2 has trust policy with `tasks.apprunner.amazonaws.com`
- [ ] Role 2 has DynamoDB access policy attached
- [ ] Both roles visible in IAM Console

---

## 🆘 Troubleshooting

### Can't Find "App Runner" in Service List

**Solution**: Use "Custom trust policy" instead and manually paste the trust policy JSON (as shown above).

### Can't Find ECR Access Policy

If you can't find `AWSAppRunnerServicePolicyForECRAccess`:
1. Make sure you're searching in the "AWS managed policies" section
2. Try searching for just "ECRAccess" or "AppRunner"
3. Alternatively, you can attach it after creating the role:
   - Go to the role → Permissions → Add permissions → Attach policies
   - Search for "AWSAppRunnerServicePolicyForECRAccess"

### Role Not Showing in App Runner Console

If the roles don't appear in the App Runner console:
1. Wait 2-3 minutes for the roles to propagate
2. Refresh the App Runner console page
3. Verify the role names are exactly: `AppRunnerECRAccessRole` and `AppRunnerInstanceRole`
4. Make sure you're in the same AWS region

### Permission Denied Errors

If you get permission errors:
1. Verify the trust relationships are correct
2. Check that the policies are attached correctly
3. Verify the DynamoDB policy allows access to `time_tracking_*` tables
4. Make sure the service principal names are exactly:
   - `build.apprunner.amazonaws.com` (for ECR access role)
   - `tasks.apprunner.amazonaws.com` (for instance role)

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

You've successfully created both IAM roles needed for App Runner deployment using Custom Trust Policy. You're now ready to create the App Runner service!

**Next**: Go to the App Runner console and create your service using these roles.

