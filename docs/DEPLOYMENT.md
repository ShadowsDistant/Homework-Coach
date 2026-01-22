# Homework Coach - Deployment & Import Guide

Complete step-by-step instructions for deploying the Homework Coach skill to AWS and importing into Alexa Developer Console.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create AWS Infrastructure](#create-aws-infrastructure)
3. [Build & Deploy Lambda](#build--deploy-lambda)
4. [Import into Alexa Developer Console](#import-into-alexa-developer-console)
5. [Configuration & Testing](#configuration--testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- AWS CLI v2 ([install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- Python 3.11+ ([install](https://www.python.org/downloads/))
- A valid AWS account with appropriate IAM permissions
- An Alexa Developer account ([sign up](https://developer.amazon.com/alexa))

### AWS Permissions Required
You'll need IAM permissions for:
- Lambda (create function, upload code)
- DynamoDB (create tables, read/write)
- CloudWatch (logging)
- IAM (create roles, attach policies)

### File Structure
```
Homework-Coach/
├── skill-package/
│   ├── skill.json                    # Skill manifest
│   ├── interactionModels/
│   │   └── custom/
│   │       └── en-US.json           # Interaction model
│   └── README.md
├── lambda/
│   ├── lambda_function.py            # Main handler
│   ├── handlers/
│   ├── helpers/
│   ├── requirements.txt
│   ├── build.sh
│   └── README.md
├── tests/
├── docs/
└── README.md
```

---

## Create AWS Infrastructure

### Step 1: Create DynamoDB Tables

Create tables with the following specifications:

```bash
# Set your region (e.g., us-east-1)
REGION="us-east-1"
```

#### Table 1: Users
```bash
aws dynamodb create-table \
  --table-name homework-coach-users \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION
```

#### Table 2: Assignments
```bash
aws dynamodb create-table \
  --table-name homework-coach-assignments \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=assignment_id,AttributeType=S \
    AttributeName=due_date,AttributeType=S \
    AttributeName=status,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=assignment_id,KeyType=RANGE \
  --global-secondary-indexes \
    "[{
      \"IndexName\": \"user_due_date_idx\",
      \"KeySchema\": [{\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"}, {\"AttributeName\": \"due_date\", \"KeyType\": \"RANGE\"}],
      \"Projection\": {\"ProjectionType\": \"ALL\"}
    },
    {
      \"IndexName\": \"user_status_idx\",
      \"KeySchema\": [{\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"}, {\"AttributeName\": \"status\", \"KeyType\": \"RANGE\"}],
      \"Projection\": {\"ProjectionType\": \"ALL\"}
    }]" \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION
```

#### Table 3: Quiz Items
```bash
aws dynamodb create-table \
  --table-name homework-coach-quiz-items \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=item_id,AttributeType=S \
    AttributeName=subject,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=item_id,KeyType=RANGE \
  --global-secondary-indexes \
    "[{
      \"IndexName\": \"user_subject_idx\",
      \"KeySchema\": [{\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"}, {\"AttributeName\": \"subject\", \"KeyType\": \"RANGE\"}],
      \"Projection\": {\"ProjectionType\": \"ALL\"}
    }]" \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION
```

#### Table 4: Spaced Repetition State
```bash
aws dynamodb create-table \
  --table-name homework-coach-sr-state \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=item_id,AttributeType=S \
    AttributeName=next_review_date,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=item_id,KeyType=RANGE \
  --global-secondary-indexes \
    "[{
      \"IndexName\": \"user_review_date_idx\",
      \"KeySchema\": [{\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"}, {\"AttributeName\": \"next_review_date\", \"KeyType\": \"RANGE\"}],
      \"Projection\": {\"ProjectionType\": \"ALL\"}
    }]" \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION
```

#### Table 5: Study Sessions
```bash
aws dynamodb create-table \
  --table-name homework-coach-sessions \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=session_id,AttributeType=S \
    AttributeName=start_time,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=session_id,KeyType=RANGE \
  --global-secondary-indexes \
    "[{
      \"IndexName\": \"user_date_idx\",
      \"KeySchema\": [{\"AttributeName\": \"user_id\", \"KeyType\": \"HASH\"}, {\"AttributeName\": \"start_time\", \"KeyType\": \"RANGE\"}],
      \"Projection\": {\"ProjectionType\": \"ALL\"}
    }]" \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION
```

#### Table 6: Session State
```bash
aws dynamodb create-table \
  --table-name homework-coach-session-state \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification AttributeName=expires_at,Enabled=true \
  --region $REGION
```

**Note**: The TTL configuration requires setting `expires_at` attribute when creating session state items.

### Step 2: Create IAM Role for Lambda

```bash
# Create trust policy document
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
ROLE_NAME="homework-coach-lambda-role"
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --region $REGION
```

### Step 3: Attach DynamoDB Policy to Role

```bash
# Create inline policy for DynamoDB access
cat > /tmp/dynamodb-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/homework-coach-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name homework-coach-dynamodb-policy \
  --policy-document file:///tmp/dynamodb-policy.json \
  --region $REGION

# Get the role ARN (you'll need this later)
ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "Role ARN: $ROLE_ARN"
```

---

## Build & Deploy Lambda

### Step 1: Build Deployment Package

```bash
cd lambda/
chmod +x build.sh
./build.sh
```

This creates `homework-coach-lambda.zip` containing all dependencies and source code.

### Step 2: Deploy Lambda Function

```bash
FUNCTION_NAME="homework-coach-lambda"
REGION="us-east-1"
ZIP_FILE="homework-coach-lambda.zip"

aws lambda create-function \
  --function-name $FUNCTION_NAME \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://$ZIP_FILE \
  --timeout 30 \
  --memory-size 256 \
  --region $REGION

# Get the Lambda ARN (you'll need this for skill configuration)
LAMBDA_ARN=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text)
echo "Lambda ARN: $LAMBDA_ARN"
```

### Step 3: Update Skill Manifest with Lambda ARN

Edit `skill-package/skill.json` and replace the endpoint URI:

```json
{
  "apis": {
    "custom": {
      "endpoint": {
        "uri": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:homework-coach-lambda"
      }
    }
  }
}
```

Replace `ACCOUNT_ID` with your AWS account ID and `us-east-1` with your region.

---

## Import into Alexa Developer Console

### Step 1: Prepare Skill Package for Import

The Alexa Developer Console expects this structure:

```
homework-coach-skill/
├── skill.json
├── interactionModels/
│   └── custom/
│       └── en-US.json
└── README.md
```

### Step 2: Create Deployment Package

```bash
# Create the import package
cd /path/to/Homework-Coach
zip -r homework-coach-skill.zip \
  skill-package/skill.json \
  skill-package/interactionModels/ \
  skill-package/README.md \
  -x "*.DS_Store"

# Verify the package structure
unzip -l homework-coach-skill.zip | head -20
```

### Step 3: Import into Alexa Developer Console

1. Go to [Alexa Developer Console](https://developer.amazon.com/console/ask)
2. Click **Create Skill**
3. Enter skill name: `Homework Coach`
4. Choose **Other** for model (we'll import)
5. Click **Import Skill** and select `homework-coach-skill.zip`
6. The console will extract and validate the manifest and interaction model

### Step 4: Configure Lambda Endpoint

After import:

1. In the **Build** section, go to **Endpoint**
2. Select **AWS Lambda ARN**
3. Enter the Lambda ARN from deployment: `arn:aws:lambda:us-east-1:ACCOUNT_ID:function:homework-coach-lambda`
4. Save

### Step 5: Configure Permissions

In the **Build** section, go to **Permissions**:

1. **Alexa Reminders API**: Enable (required for assignment reminders)
2. **Device Address**: Optional (could be used for timezone inference)

---

## Configuration & Testing

### Step 1: Test in Console Simulator

1. Go to **Test** section in the developer console
2. Skill testing is enabled for development
3. Try utterances:
   - "Open Homework Coach"
   - "Ask Homework Coach for my daily plan"
   - "Tell Homework Coach to add an assignment"

### Step 2: Enable Skills on Device

1. On your Echo device (or Echo Show):
   - Open the Alexa app
   - Go to **Skills & Games**
   - Search for **Homework Coach**
   - Click **Enable to Use**

2. Grant permissions:
   - **Reminders**: Required for setting assignment reminders
   - Click **Settings** → **Connected Home & Devices** → **Reminders**

### Step 3: Manual Testing Script

Test all primary flows:

```bash
#!/bin/bash
# Manual test cases for Homework Coach

echo "1. Daily Plan Check-in"
echo "   Say: 'Alexa, open Homework Coach'"
echo "   Say: 'What's my daily plan?'"
echo ""

echo "2. Add Assignment"
echo "   Say: 'Add an assignment in Biology due Friday'"
echo "   Expected: System asks for assignment title"
echo ""

echo "3. Start Pomodoro"
echo "   Say: 'Start a Pomodoro session in Math'"
echo "   Say: 'Pause'"
echo "   Say: 'Resume'"
echo "   Say: 'Stop'"
echo ""

echo "4. Quiz Session"
echo "   Say: 'Quiz me in Biology'"
echo "   Expected: System presents first question"
echo ""

echo "5. End-of-Day Recap"
echo "   Say: 'Give me my recap'"
echo "   Expected: Summary of today's activity"
echo ""
```

### Step 4: Verify DynamoDB Data

Check that data is being stored correctly:

```bash
# Query user profiles
aws dynamodb scan \
  --table-name homework-coach-users \
  --region us-east-1 \
  --limit 5

# Query assignments for a user
USER_ID="amzn1.ask.account.EXAMPLE_ID"
aws dynamodb query \
  --table-name homework-coach-assignments \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values "{\":uid\": {\"S\": \"$USER_ID\"}}" \
  --region us-east-1
```

### Step 5: Monitor Lambda Logs

```bash
# View Lambda logs in real-time
FUNCTION_NAME="homework-coach-lambda"
aws logs tail /aws/lambda/$FUNCTION_NAME --follow --region us-east-1
```

---

## Troubleshooting

### Issue: "Lambda ARN not found" during import

**Solution**: Verify:
1. Lambda function exists: `aws lambda get-function --function-name homework-coach-lambda`
2. ARN is correct in `skill.json`
3. Lambda role has trust relationship with Alexa service

### Issue: DynamoDB errors ("AccessDeniedException")

**Solution**:
1. Verify IAM role attached to Lambda has DynamoDB permissions
2. Check table names match exactly (case-sensitive)
3. Verify tables exist in the correct region

### Issue: "Reminders permission denied"

**Solution**:
1. User must explicitly grant reminders permission in Alexa app
2. Skill gracefully continues if permission denied (won't crash)
3. Test permission flow in console with debug logging enabled

### Issue: "Interaction model validation failed"

**Solution**:
1. Verify `en-US.json` has valid JSON syntax
2. Check invocation name is unique across your skills
3. Ensure all intents have proper structure

### Issue: "Session timeout" on Pomodoro pause/resume

**Solution**:
1. Session state expires after 1 hour of inactivity
2. User must re-initiate after timeout
3. Consider extending TTL for long study sessions

### Enable Debug Logging

Set environment variable:
```bash
aws lambda update-function-configuration \
  --function-name homework-coach-lambda \
  --environment Variables={LOG_LEVEL=DEBUG} \
  --region us-east-1
```

---

## Certification & Publication

Once testing is complete, submit for certification:

1. Go to **Build** → **Submission**
2. Fill out skill details:
   - Privacy Policy: Link to your privacy policy
   - Terms of Use: Link to your terms
   - Functional Description: Describe what skill does
   - Availability: Select countries/regions
3. Submit for review
4. Amazon typically reviews in 7-14 business days

---

## Post-Deployment Checklist

- [ ] All 6 DynamoDB tables created with correct indexes
- [ ] IAM role created with DynamoDB policy
- [ ] Lambda function deployed with correct handler
- [ ] skill.json updated with Lambda ARN
- [ ] Interaction model imported and validated
- [ ] Reminders permission enabled in console
- [ ] Tested all primary flows in simulator
- [ ] Tested on real Echo device
- [ ] DynamoDB logging shows data being written
- [ ] CloudWatch logs show no errors

---

