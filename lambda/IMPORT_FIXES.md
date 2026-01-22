# Alexa Console Import Errors - FIXED ✅

## Errors Found & Fixed

### ❌ Error 1: Too many examplePhrases
**Error**: `Size of Array instance at property path "$.manifest.publishingInformation.locales.en-US.examplePhrases" is outside the allowed range: Actual number of items: 5, Maximum number of items: 4.`

**Fix**: Reduced from 5 to 4 example phrases
- Removed: "Alexa, ask Homework Coach for today's recap"
- Kept most important examples

**Before** (5 items):
```json
"examplePhrases": [
  "Alexa, open Homework Coach and check my daily plan",
  "Alexa, ask Homework Coach to start a Pomodoro session in Biology",
  "Alexa, ask Homework Coach to add an assignment due Friday",
  "Alexa, ask Homework Coach to quiz me in History",
  "Alexa, ask Homework Coach for today's recap"
]
```

**After** (4 items):
```json
"examplePhrases": [
  "Alexa, open Homework Coach",
  "Alexa, ask Homework Coach for my daily plan",
  "Alexa, ask Homework Coach to start a Pomodoro session",
  "Alexa, ask Homework Coach to quiz me"
]
```

---

### ❌ Error 2: Unexpected property "privacyPolicyUrl"
**Error**: `Object instance at property path "$.manifest.privacyAndCompliance" has unexpected property: "privacyPolicyUrl".`

**Fix**: Moved privacyPolicyUrl from `privacyAndCompliance` to `locales.en-US` (correct location)

---

### ❌ Error 3: Unexpected property "termsOfUseUrl"
**Error**: `Object instance at property path "$.manifest.privacyAndCompliance" has unexpected property: "termsOfUseUrl".`

**Fix**: Moved termsOfUseUrl from `privacyAndCompliance` to `locales.en-US` (correct location)

---

## Corrected Structure

```json
{
  "manifest": {
    "publishingInformation": {
      "locales": {
        "en-US": {
          "summary": "...",
          "examplePhrases": [
            // 4 items (was 5)
          ],
          "name": "Homework Coach",
          "description": "...",
          "privacyPolicyUrl": "https://example.com/privacy-policy",    // ← Moved here
          "termsOfUseUrl": "https://example.com/terms-of-use"           // ← Moved here
        }
      },
      ...
    },
    ...
    "privacyAndCompliance": {
      "allowsPurchases": false,
      "isExportCompliant": true,
      "containsAds": false,
      "isChildDirected": false,
      "usesPersonalInfo": true
      // privacyPolicyUrl and termsOfUseUrl removed
    }
  }
}
```

---

## Files Ready to Upload

### To AWS Lambda:
- **File**: `lambda/homework-coach-lambda.zip` (20 MB) ✅
- **Status**: REBUILT with fixed skill.json

### To Alexa Developer Console:
- **File**: `lambda/homework-coach-skill.zip` (10 KB) ✅
- **Status**: READY - Contains fixed skill.json + en-US.json

---

## Upload Now

### Step 1: AWS Lambda
```bash
cd /workspaces/Homework-Coach/lambda

aws lambda update-function-code \
  --function-name HomeworkCoachSkill \
  --zip-file fileb://homework-coach-lambda.zip
```

### Step 2: Alexa Developer Console
1. Go to **Build** tab
2. Click **Import Skill**
3. Upload: `lambda/homework-coach-skill.zip`
4. Should import successfully now! ✅

---

## Summary

| Issue | Status |
|-------|--------|
| Too many examplePhrases (5 → 4) | ✅ Fixed |
| privacyPolicyUrl in wrong location | ✅ Fixed |
| termsOfUseUrl in wrong location | ✅ Fixed |
| Deployment packages rebuilt | ✅ Done |
| Ready to import to Alexa Console | ✅ Yes |

All validation errors have been corrected. The skill should now import successfully to Alexa Developer Console!
