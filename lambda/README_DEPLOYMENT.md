# Homework Coach - Lambda Deployment Guide

## ⚡ Quick Start

All files needed for the skill are now in this `lambda/` folder.

```bash
cd lambda/
./build.sh                    # Creates homework-coach-lambda.zip
```

Upload `homework-coach-lambda.zip` to AWS Lambda. Done!

---

## 📁 What's Included in This Folder

```
lambda/
├── lambda_function.py              # Main Lambda entry point (450 lines)
├── handlers/
│   └── additional_handlers.py      # Extra intent handlers (200 lines)
├── helpers/
│   ├── algorithms.py              # Core algorithms (380 lines)
│   ├── dynamodb_helper.py         # DynamoDB CRUD (420 lines)
│   ├── reminders_helper.py        # Reminders API integration (220 lines)
│   └── apl_helper.py              # Echo Show display (280 lines)
├── skill-package/                 # SKILL MANIFEST (UPLOAD TO ALEXA CONSOLE)
│   ├── skill.json                 # Manifest file
│   └── interactionModels/custom/
│       └── en-US.json             # Intents, slots, utterances, dialog config
├── requirements.txt               # Python dependencies
├── build.sh                       # Build script
└── README_DEPLOYMENT.md           # This file
```

---

## 🚀 Deployment Workflow

### Phase 1: Build Lambda Package

```bash
cd lambda/
chmod +x build.sh
./build.sh
```

**Output**: `homework-coach-lambda.zip` (contains all code + dependencies + skill files)

### Phase 2: Deploy to AWS Lambda

#### Option A: AWS CLI

```bash
# Set your AWS account ID
ACCOUNT_ID="123456789012"
REGION="us-east-1"

# Create IAM role (one-time)
aws iam create-role \
  --role-name HomeworkCoachLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach DynamoDB policy
aws iam put-role-policy \
  --role-name HomeworkCoachLambdaRole \
  --policy-name DynamoDBAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["dynamodb:*", "logs:*"],
      "Resource": "*"
    }]
  }'

# Create Lambda function
aws lambda create-function \
  --function-name HomeworkCoachSkill \
  --runtime python3.11 \
  --role arn:aws:iam::$ACCOUNT_ID:role/HomeworkCoachLambdaRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://homework-coach-lambda.zip \
  --timeout 60 \
  --memory-size 256 \
  --region $REGION

# Get the ARN (you'll need this for the skill)
aws lambda get-function \
  --function-name HomeworkCoachSkill \
  --region $REGION \
  --query 'Configuration.FunctionArn' \
  --output text
```

#### Option B: AWS Console
1. Go to **AWS Lambda**
2. Click **Create Function**
3. Select **Python 3.11**
4. Create or select **HomeworkCoachLambdaRole**
5. Upload `homework-coach-lambda.zip`
6. **Save** and copy the function ARN

### Phase 3: Upload Skill to Alexa Console

The `skill-package/` folder contains files needed for Alexa Console.

**Option A: Via Alexa Console UI**

1. Go to **Alexa Developer Console**
2. Click **Create Skill**
3. Select **Import Skill**
4. Choose and upload this ZIP:
   ```bash
   zip -r homework-coach-skill.zip \
     skill-package/skill.json \
     skill-package/interactionModels/
   ```

**Option B: Via ASK CLI**

```bash
# If you have ASK CLI installed
cd skill-package/
ask deploy --target skill-package
```

### Phase 4: Connect Lambda to Skill

1. **Alexa Developer Console** → Your Skill → **Build tab**
2. Under **Endpoint**, select **AWS Lambda ARN**
3. Paste your Lambda ARN from Phase 2
4. **Save Endpoint**

### Phase 5: Enable Permissions

1. **Alexa Developer Console** → Your Skill → **Permissions tab**
2. Check: **Alexa Reminders API**
3. **Save**

### Phase 6: Test

In **Alexa Developer Console** → **Test tab**:
- Type: `open homework coach`
- Should respond: "Welcome back! I'm Homework Coach..."

---

## ⚙️ Lambda Function Details

### Entry Point
```python
# lambda_function.py
def lambda_handler(event, context):
    return get_skill().invoke(event, context)
```

### Handlers (in lambda_function.py + handlers/additional_handlers.py)

| Intent | Handler | Purpose |
|--------|---------|---------|
| LaunchRequest | LaunchRequestHandler | Greeting + menu |
| DailyPlanIntent | DailyPlanIntentHandler | Show prioritized assignments |
| AddAssignmentIntent | AddAssignmentIntentHandler | Capture homework + create reminder |
| StartPomodoroIntent | StartPomodoroIntentHandler | Begin 25-min focus session |
| PomodoroControlIntent | PomodoroControlIntentHandler | Pause/resume/extend Pomodoro |
| QuizIntent | QuizIntentHandler | Start spaced-rep quiz |
| QuizResponseIntent | QuizResponseIntentHandler | Score quiz answer + update SR |
| ViewAssignmentsIntent | ViewAssignmentsIntentHandler | List assignments by filter |
| MarkCompleteIntent | MarkCompleteIntentHandler | Mark assignment done |
| RecapIntent | RecapIntentHandler | End-of-day summary |
| HelpIntent | HelpIntentHandler | Show available commands |
| CancelIntent | CancelIntentHandler | End skill gracefully |
| FallbackIntent | FallbackIntentHandler | Handle unrecognized requests |

### Helper Modules

#### `helpers/algorithms.py`
- **PlanGenerator**: Prioritizes assignments by (overdue → today → soon → far, within tier by duration)
- **PomodoroManager**: Tracks session state (start, pause, resume, extend) with interruption count
- **SpacedRepetitionScheduler**: SM-2 algorithm for quiz review scheduling
- **EndOfDayRecap**: Aggregates session metrics, flags high-priority items for next day

#### `helpers/dynamodb_helper.py`
CRUD operations for 6 DynamoDB tables:
- `homework-coach-users`: User profiles, timezone, preferences
- `homework-coach-assignments`: Assignments with class, due date, time estimate
- `homework-coach-quiz-items`: Quiz questions with correct answer
- `homework-coach-sr-state`: Spaced-rep scheduling state (SM-2 parameters)
- `homework-coach-sessions`: Completed study sessions with metrics
- `homework-coach-session-state`: Active session cache (Pomodoro, quiz state)

#### `helpers/reminders_helper.py`
- Calls Alexa Reminders API: `/v1/alerts/reminders`
- Handles permission denied (graceful fallback: assignment still created)
- Supports custom reminder times and timezone conversion

#### `helpers/apl_helper.py`
- Generates Alexa Presentation Language (APL) documents for Echo Show
- 4 document types: assignment checklist, Pomodoro timer, quiz question, recap stats
- Falls back to voice-only if device doesn't support APL

---

## 🔐 Security & Permissions

### IAM Role Permissions (Minimum Required)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/homework-coach-*"
      ]
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
```

### Alexa Permissions

The skill requests:
- **Reminders API** (user must grant in Alexa app)
- **Timezone** (auto-detected, user can override)

---

## 🛠️ Environment Variables (Set in Lambda)

| Variable | Value | Purpose |
|----------|-------|---------|
| `DYNAMODB_REGION` | `us-east-1` | DynamoDB region |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

Set in **AWS Lambda** → Your Function → **Configuration** → **Environment Variables**

---

## 📦 Python Dependencies

From `requirements.txt`:
- `ask-sdk-core>=1.34.0` — Alexa Skills Kit
- `boto3>=1.26.0` — AWS SDK
- `requests>=2.28.0` — HTTP client (Reminders API)
- `python-dateutil>=2.8.0` — Date utilities

These are automatically installed by `./build.sh` and included in the ZIP.

---

## 🧪 Local Testing

### Run Unit Tests

```bash
cd ..
pip install -r lambda/requirements.txt
python -m pytest tests/test_algorithms.py -v
python -m pytest tests/test_handlers.py -v
```

### Simulate Lambda Locally

```bash
python -c "
import sys
sys.path.insert(0, 'lambda')
from lambda_function import lambda_handler

# Test LaunchRequest
event = {
    'request': {'type': 'LaunchRequest'},
    'context': {'System': {'application': {'applicationId': 'amzn1.ask.skill.test'}}}
}
response = lambda_handler(event, {})
print(response)
"
```

---

## ⚠️ Troubleshooting

### "Module not found" Error
- Ensure `./build.sh` completed successfully
- Check that `pip install` has no errors
- Verify ZIP contains `lambda_function.py` at root level

### DynamoDB Errors (Timeout, Access Denied)
- Create DynamoDB tables first (see `/docs/DEPLOYMENT.md`)
- Verify Lambda execution role has DynamoDB permissions
- Check table names match code (should start with `homework-coach-`)

### Reminders API Errors
- **403 Forbidden**: User hasn't granted permission (handled gracefully)
- **400 Bad Request**: Trigger time format wrong (must be ISO 8601)
- Check `reminders_helper.py` for error logging

### Cold Start Latency (2-3 seconds)
- Normal for Lambda on first invocation
- Solution: Use **Provisioned Concurrency** for production

### Skill Says "There was a problem with the requested skill"
- Check Lambda logs: `aws logs tail /aws/lambda/HomeworkCoachSkill --follow`
- Verify Lambda ARN in Alexa Console matches actual function
- Test Lambda directly in AWS console

---

## 🔄 Updating Code

### Update Lambda Code

1. Edit files in `lambda/` (e.g., `lambda_function.py`)
2. Run `./build.sh`
3. Upload new ZIP to AWS Lambda:
   ```bash
   aws lambda update-function-code \
     --function-name HomeworkCoachSkill \
     --zip-file fileb://homework-coach-lambda.zip
   ```
4. Changes deploy immediately

### Update Interaction Model

1. Edit `skill-package/interactionModels/custom/en-US.json`
2. Rebuild skill ZIP:
   ```bash
   zip -r homework-coach-skill.zip \
     skill-package/skill.json \
     skill-package/interactionModels/
   ```
3. Import to Alexa Console
4. **No Lambda update needed**

---

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
aws logs tail /aws/lambda/HomeworkCoachSkill --follow

# Last 100 lines
aws logs tail /aws/lambda/HomeworkCoachSkill --max-items 100
```

### Key Metrics to Monitor

- **Invocations**: Total function calls
- **Errors**: Failed invocations
- **Duration**: Average response time
- **Throttles**: Rate-limited requests (shouldn't happen with on-demand Lambda)
- **Concurrent Executions**: Simultaneous users

### CloudWatch Dashboard Example

```bash
aws cloudwatch put-metric-data \
  --namespace HomeworkCoach \
  --metric-name StudySessionsCompleted \
  --value 42
```

---

## 🎓 Reference

| Document | Purpose |
|----------|---------|
| `../docs/DATA_MODELS.md` | DynamoDB schema + JSON structures |
| `../docs/CONVERSATION_DESIGN.md` | Multi-turn flow examples |
| `../docs/DEPLOYMENT.md` | Full AWS setup (tables, IAM, etc.) |
| `../docs/PRODUCTION_READINESS.md` | Edge cases + monitoring checklist |
| `../README.md` | Project overview |
| `skill-package/skill.json` | Skill metadata (manifest) |
| `skill-package/interactionModels/custom/en-US.json` | Intents, slots, utterances |

---

## ✅ Deployment Checklist

- [ ] Create DynamoDB tables (6 tables, see `/docs/DEPLOYMENT.md`)
- [ ] Create IAM role with DynamoDB permissions
- [ ] Run `./build.sh` (creates ZIP)
- [ ] Deploy to AWS Lambda
- [ ] Note Lambda ARN
- [ ] Upload skill-package to Alexa Console
- [ ] Connect Lambda ARN in Alexa Console → Endpoint
- [ ] Enable Reminders permission in Alexa Console
- [ ] Test in Alexa Console simulator
- [ ] Test on physical Echo device
- [ ] Enable in Alexa app
- [ ] Live!

---

**Need help?** See `../docs/DEPLOYMENT.md` for detailed step-by-step instructions and troubleshooting.
