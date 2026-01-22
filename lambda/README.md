# Homework Coach Alexa Skill - Python Backend
## Lambda Deployment

### Project Structure
```
lambda/
├── lambda_function.py          # Main Lambda handler (entry point)
├── handlers/
│   └── additional_handlers.py  # Extra intent handlers
├── helpers/
│   ├── algorithms.py           # Core business logic
│   ├── dynamodb_helper.py      # DynamoDB operations
│   ├── reminders_helper.py     # Alexa Reminders API
│   └── apl_helper.py           # APL rendering
└── requirements.txt            # Python dependencies
```

### Runtime
- **Python**: 3.11
- **Architecture**: arm64 or x86_64

### Environment Variables
- `DYNAMODB_REGION`: AWS region for DynamoDB (default: `us-east-1`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### IAM Role Permissions Required
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
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:ACCOUNT_ID:table/homework-coach-*"
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

### Handler
- **Function Name**: `homework-coach-lambda`
- **Handler**: `lambda_function.lambda_handler`
- **Timeout**: 30 seconds
- **Memory**: 256 MB
