# 🚀 QUICK START - Upload Everything from Lambda Folder

## 📋 What You Have Now

Everything needed is in the **`lambda/`** folder. You can upload directly from here.

```
lambda/
├── homework-coach-lambda.zip     ← **ALREADY BUILT** (ready to upload to AWS Lambda)
├── skill-package/                ← Contains skill definition for Alexa Console
│   ├── skill.json
│   └── interactionModels/custom/en-US.json
├── lambda_function.py            ← Main handler code
├── handlers/                     ← Additional handlers
├── helpers/                      ← Business logic (algorithms, DynamoDB, Reminders, APL)
├── requirements.txt              ← Python dependencies
└── *.md                          ← Documentation files
```

---

## ✅ Two-Step Upload Process

### Step 1️⃣: Upload Lambda Code to AWS

**File**: `lambda/homework-coach-lambda.zip` (already created)

**Upload Method A - AWS CLI**:
```bash
cd /workspaces/Homework-Coach/lambda

aws lambda update-function-code \
  --function-name HomeworkCoachSkill \
  --zip-file fileb://homework-coach-lambda.zip
```

**Upload Method B - AWS Console**:
1. Go to **AWS Lambda** → Your Function
2. Upload ZIP File
3. Select `homework-coach-lambda.zip`
4. Save

**Result**: Lambda function deployed and running ✅

---

### Step 2️⃣: Upload Skill Definition to Alexa Console

**Files**: 
- `lambda/skill-package/skill.json`
- `lambda/skill-package/interactionModels/custom/en-US.json`

**Upload Method A - Via ZIP (Recommended)**:

```bash
cd /workspaces/Homework-Coach/lambda

# Create skill-only ZIP
zip -r homework-coach-skill.zip \
  skill-package/skill.json \
  skill-package/interactionModels/

# This creates homework-coach-skill.zip with:
# ├── skill.json
# └── interactionModels/custom/en-US.json
```

Then in **Alexa Developer Console**:
1. Go to **Build** tab
2. Click **Import Skill**
3. Upload `homework-coach-skill.zip`

**Upload Method B - Manual (Via Console)**:
1. Go to **Alexa Developer Console** → Your Skill → **Build** tab
2. Go to **JSON Editor**
3. Copy contents of `lambda/skill-package/skill.json`
4. Paste into JSON Editor
5. Save

Then:
1. Go to **Interaction Model** section
2. Open the JSON Editor there
3. Copy contents of `lambda/skill-package/interactionModels/custom/en-US.json`
4. Paste and save

**Result**: Skill definition uploaded ✅

---

## 🔗 Connect Them Together

After uploading both:

1. **Alexa Developer Console** → Your Skill → **Build** tab
2. Go to **Endpoint** section
3. Select **AWS Lambda ARN**
4. Paste your Lambda ARN (from AWS Lambda console)
5. **Save Endpoint**

---

## 🎯 That's It!

Your Homework Coach skill is now:
- ✅ Uploaded to AWS Lambda (code + dependencies)
- ✅ Uploaded to Alexa Developer Console (skill definition)
- ✅ Connected together (Lambda ARN in endpoint)

---

## 📚 Documentation Files in Lambda Folder

Need more details? Read these:

| File | Content |
|------|---------|
| **UPLOAD_GUIDE.md** | Detailed upload instructions with all options |
| **README_DEPLOYMENT.md** | Full deployment guide with AWS CLI commands |
| **REORGANIZATION_SUMMARY.md** | What changed and why |
| **README.md** | Legacy reference |

---

## 🧪 Test It

### In Alexa Developer Console
1. Go to **Test** tab
2. Type: `open homework coach`
3. Should respond with greeting

### On Echo Device
1. Say: "Alexa, open Homework Coach"
2. Alexa should greet you

---

## ✨ Everything Works Because

✅ **All code** is in `lambda/lambda_function.py` and `handlers/` and `helpers/`  
✅ **All dependencies** included in `homework-coach-lambda.zip`  
✅ **Skill definition** in `lambda/skill-package/`  
✅ **Build script** automatically packages everything  
✅ **Nothing missing** - it's all here in the lambda folder  

---

## 🔄 If You Need to Update Code

### Update Lambda Code
```bash
cd /workspaces/Homework-Coach/lambda

# Edit your code files...
# (lambda_function.py, handlers/, helpers/, etc.)

# Rebuild and upload
./build.sh

# Upload to AWS
aws lambda update-function-code \
  --function-name HomeworkCoachSkill \
  --zip-file fileb://homework-coach-lambda.zip
```

### Update Skill Definition
```bash
cd /workspaces/Homework-Coach/lambda

# Edit skill-package files...
# (skill.json or en-US.json)

# Recreate skill ZIP
zip -r homework-coach-skill.zip \
  skill-package/skill.json \
  skill-package/interactionModels/

# Import to Alexa Console
```

---

## 📞 Troubleshooting

### "Permission denied" uploading to Lambda
- Make sure AWS credentials are configured: `aws configure`
- Verify function exists: `aws lambda get-function --function-name HomeworkCoachSkill`

### "Could not find file" error
- Run from `lambda/` directory
- Check that `homework-coach-lambda.zip` exists: `ls -lh homework-coach-lambda.zip`

### Alexa says "There was a problem"
- Check Lambda logs: `aws logs tail /aws/lambda/HomeworkCoachSkill --follow`
- Verify Lambda ARN is correct in Alexa Console
- Test Lambda directly in AWS console

### "Skill definition not found" in Alexa Console
- Make sure skill.json and en-US.json are in skill-package/
- Verify ZIP structure: `unzip -l homework-coach-skill.zip`

---

## 🎓 Reference

**Full Documentation**:
- Lambda deployment: See `README_DEPLOYMENT.md`
- Upload process: See `UPLOAD_GUIDE.md`
- What changed: See `REORGANIZATION_SUMMARY.md`

**Key Files**:
- Lambda entry: `lambda/lambda_function.py`
- Skill manifest: `lambda/skill-package/skill.json`
- Intents/slots: `lambda/skill-package/interactionModels/custom/en-US.json`
- Build script: `lambda/build.sh`

---

## ✅ Final Checklist

Before uploading, verify you have:

- [ ] `lambda/homework-coach-lambda.zip` exists (created by `./build.sh`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Alexa Developer Console account set up
- [ ] Lambda function exists in AWS
- [ ] Lambda IAM role has DynamoDB permissions
- [ ] DynamoDB tables created (see `/docs/DEPLOYMENT.md`)

---

**Everything is ready. You can upload from the `lambda/` folder now!** 🚀

Start with Step 1 above - upload the ZIP to AWS Lambda.
