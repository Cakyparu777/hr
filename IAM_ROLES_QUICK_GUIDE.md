# IAM Roles Setup - Quick Visual Guide

## 🎯 What You're Creating

**Role 1**: `AppRunnerECRAccessRole` - Lets App Runner pull Docker images  
**Role 2**: `AppRunnerInstanceRole` - Lets your app access DynamoDB

---

## 📝 Role 1: AppRunnerECRAccessRole

### Step-by-Step:

1. **Go to IAM Console**
   - Open: https://console.aws.amazon.com/iam/
   - Click **"Roles"** (left sidebar)
   - Click **"Create role"**

2. **Select Trusted Entity (Custom Trust Policy)**
   - Choose **"Custom trust policy"**
   - You'll see a JSON editor
   - **Delete** the default content
   - **Paste** this trust policy (for ECR Access Role):

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

   - Click **"Next"**

3. **Add Permissions**
   - Search: **"AppRunnerECRAccess"**
   - ✅ Check: **"AWSAppRunnerServicePolicyForECRAccess"**
   - Click **"Next"**

4. **Name the Role**
   - Role name: `AppRunnerECRAccessRole`
   - Description: "Allows App Runner to pull Docker images from ECR"
   - Click **"Create role"**

✅ **Done!** Role 1 is created.

---

## 📝 Role 2: AppRunnerInstanceRole

### Step-by-Step:

1. **Create Role**
   - In IAM Console, click **"Roles"**
   - Click **"Create role"**

2. **Select Trusted Entity (Custom Trust Policy)**
   - Choose **"Custom trust policy"**
   - You'll see a JSON editor
   - **Delete** the default content
   - **Paste** this trust policy:

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

   - Click **"Next"**

3. **Skip Permissions (for now)**
   - Don't select any permissions
   - Click **"Next"** (ignore warning)

4. **Name the Role**
   - Role name: `AppRunnerInstanceRole`
   - Description: "Allows App Runner instances to access DynamoDB"
   - Click **"Create role"**

5. **Add DynamoDB Policy**
   - Click on the role name: `AppRunnerInstanceRole`
   - Click **"Permissions"** tab
   - Click **"Add permissions"** → **"Create inline policy"**
   - Click **"JSON"** tab
   - **Delete** the default content
   - **Paste** this policy:

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

   - Click **"Next"**
   - Policy name: `DynamoDBAccess`
   - Click **"Create policy"**

✅ **Done!** Role 2 is created.

---

## ✅ Verify Both Roles

1. Go to **"Roles"** in IAM Console
2. You should see:
   - ✅ `AppRunnerECRAccessRole`
   - ✅ `AppRunnerInstanceRole`

---

## 🎯 What to Use in App Runner

When creating the App Runner service, you'll select:
- **Access role**: `AppRunnerECRAccessRole`
- **Instance role**: `AppRunnerInstanceRole`

The App Runner console will show these in dropdown menus - just select them!

---

## 🔍 Quick Check

### Role 1 Should Have:
- ✅ Trust relationship: `build.apprunner.amazonaws.com`
- ✅ Permission: `AWSAppRunnerServicePolicyForECRAccess`

### Role 2 Should Have:
- ✅ Trust relationship: `tasks.apprunner.amazonaws.com`
- ✅ Permission: `DynamoDBAccess` (inline policy)

---

## 🆘 Troubleshooting

**Roles not showing in App Runner?**
- Wait 2-3 minutes for propagation
- Refresh the page
- Check role names are exactly: `AppRunnerECRAccessRole` and `AppRunnerInstanceRole`

**Permission errors?**
- Verify trust relationships are correct
- Check policies are attached
- Make sure DynamoDB policy allows `time_tracking_*` tables

---

## 📚 Full Guide

For detailed instructions with screenshots, see:
- [CREATE_IAM_ROLES_CONSOLE.md](./CREATE_IAM_ROLES_CONSOLE.md)

---

## 🎉 Next Steps

Now that roles are created:
1. ✅ Proceed to create App Runner service
2. ✅ Select these roles when configuring App Runner
3. ✅ Deploy your application!

**Ready to deploy?** See [DEPLOY_WALKTHROUGH.md](./DEPLOY_WALKTHROUGH.md)

