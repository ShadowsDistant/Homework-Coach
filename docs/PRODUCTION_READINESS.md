# Homework Coach - Production Readiness Checklist

Comprehensive checklist and edge case documentation for production deployment.

---

## Production Readiness Checklist

### Code Quality
- [ ] All Python code passes linting (`pylint`, `black`)
- [ ] Type hints added to all function signatures
- [ ] Docstrings present for all public functions
- [ ] Error handling covers all exception paths
- [ ] Logging includes INFO, WARNING, and ERROR levels
- [ ] No hardcoded credentials or API keys
- [ ] All dependencies pinned to specific versions

### Testing
- [ ] Unit tests written for all algorithms
- [ ] Unit tests written for all helpers
- [ ] Integration tests cover multi-turn flows
- [ ] Test coverage > 80% for core logic
- [ ] All tests passing in CI/CD pipeline
- [ ] Manual testing on at least 2 Echo device types
- [ ] Performance tested (cold start < 5s, warm start < 2s)

### Data & Security
- [ ] All user data persisted to DynamoDB only (no Lambda memory)
- [ ] Data encrypted at rest (DynamoDB encryption enabled)
- [ ] Data encrypted in transit (TLS/HTTPS for all API calls)
- [ ] IAM role follows least-privilege principle
- [ ] No PII logged except user_id
- [ ] Data retention policy documented and enforced (TTL on session state)

### API Integration
- [ ] Reminders API error handling covers all HTTP status codes
- [ ] Reminders API permission denial handled gracefully
- [ ] API request timeout set to 5 seconds max
- [ ] API response validation for all fields
- [ ] Fallback behavior if Reminders API unavailable

### Conversation Design
- [ ] All intents have sample utterances (5+ per intent)
- [ ] Dialog model configured for all required slots
- [ ] Reprompt text differs from initial prompt
- [ ] Multi-turn conversations tested for consistency
- [ ] Help intent provides actionable guidance
- [ ] Error messages are conversational, not technical

### Device Support
- [ ] Voice-only Echo devices (no display) fully supported
- [ ] Echo Show devices get APL enhancements
- [ ] Graceful fallback if APL not supported
- [ ] APL documents tested on actual Echo Show
- [ ] Mobile Alexa app tested (if applicable)

### Internationalization (i18n)
- [ ] Interaction model supports en-US (primary)
- [ ] Date/time formatting locale-aware
- [ ] Timezone handling for non-US users
- [ ] Future locales documented (e.g., en-GB, es-ES)

### Monitoring & Logging
- [ ] CloudWatch Logs configured and monitored
- [ ] Error rate alarms set (trigger if > 5% errors)
- [ ] Performance metrics logged (cold start time, handler duration)
- [ ] Structured logging with JSON format
- [ ] Log retention set to 7 days for development, 90 days for production

### Compliance
- [ ] Privacy policy URL valid and links to real policy
- [ ] Terms of Use URL valid and links to real terms
- [ ] COPPA compliance review (if targeting minors - NOT recommended)
- [ ] Skill description accurate and clear
- [ ] No misleading claims about AI capabilities

### Deployment
- [ ] Build script automated and reproducible
- [ ] Deployment documented with exact AWS CLI commands
- [ ] Rollback procedure documented
- [ ] Database migration procedure documented (if schema changes)
- [ ] Health checks automated (Lambda test invocations)

---

## Edge Cases & Handling

### 1. Missing or Invalid Slots

**Scenario**: User provides incomplete information.

```
User:  "Add assignment in Biology"  [missing: title, due date]

System: 
  1. Prompt for missing AssignmentTitle
  2. Prompt for missing DueDate
  3. Optionally prompt for EstimatedMinutes
  4. Confirm and save
```

**Implementation**: Use Alexa dialog manager with multi-slot elicitation.

---

### 2. Ambiguous Class Names

**Scenario**: User says "add homework for Math" but has multiple math classes.

```
Classes: AP Calculus, Honors Algebra II, Precalculus

System Logic:
  1. Check if class_name is exact match → use it
  2. If fuzzy match found (e.g., "Math" matches 3 classes):
     a. Ask user to clarify: "Do you mean AP Calculus, Honors Algebra II, or Precalculus?"
     b. User selects one
  3. Save with exact class name
```

**Implementation**: Fuzzy string matching using `difflib.SequenceMatcher` or Levenshtein distance.

---

### 3. Timezone Handling

**Scenario**: User adds assignment "due tomorrow 5 PM" but is in different timezone than Lambda.

```
Lambda Region: us-east-1 (EST)
User Timezone: America/Los_Angeles (PST)
Current Time: 2026-01-22 2:00 PM EST / 2026-01-22 11:00 AM PST

User says: "Add assignment due tomorrow at 5 PM"

System Logic:
  1. Parse due date/time: 2026-01-23 17:00
  2. Get user timezone from profile: America/Los_Angeles
  3. Assume user provided time in their local timezone
  4. Convert to ISO 8601: 2026-01-24T01:00:00Z (9 PM EST)
  5. Store trigger time in user's timezone for reminders
```

**Implementation**: Use `pytz` library for timezone conversions.

---

### 4. Overdue Assignment Detection

**Scenario**: System detects assignment is now overdue.

```
Stored: due_date = "2026-01-20"
Current: today = "2026-01-22"

System Logic on retrieval:
  1. If assignment status = "not_started" AND due_date < today:
     a. Set status to "overdue"
     b. Update in DynamoDB
     c. Prioritize in daily plan
  2. Include in daily plan recap: "1 overdue assignment"
```

**Implementation**: Date comparison in `PlanGenerator.generate_daily_plan()`.

---

### 5. Multiple Users in Household

**Scenario**: Two or more Alexa users in same household.

```
Device: Echo in living room
User 1: Alex (studied 1 hour today)
User 2: Sam (studied 30 min today)

Request 1 (Alex):
  user_id = "amzn1.ask.account.ALEX_ID"
  → Retrieveassignments for ALEX_ID only

Request 2 (Sam):
  user_id = "amzn1.ask.account.SAM_ID"
  → Retrieve assignments for SAM_ID only
```

**Implementation**: Alexa automatically provides `user_id` from context. Database partitioned by `user_id`.

---

### 6. Session Timeout During Pomodoro

**Scenario**: Device loses connection mid-Pomodoro or user goes inactive.

```
Scenario A - Device loses connection (30 seconds)
  1. Session state expires after 1 hour inactivity
  2. Device reconnects after 30s → session still active
  3. User can resume: "Resume"

Scenario B - User abandons Pomodoro for 1+ hour
  1. Session state TTL expires → deleted from DB
  2. User says "Resume"
  3. System: "I don't have an active session. Start a new Pomodoro?"
```

**Implementation**: DynamoDB TTL on `expires_at` field; check session validity before actions.

---

### 7. Reminder Permission Denied

**Scenario**: User doesn't grant or revokes reminder permission.

```
Flow 1 (Permission Not Granted):
  User: "Add assignment due Friday"
  
  System:
    1. Attempt to create reminder → 403 Forbidden
    2. Log error: permission_denied
    3. Add assignment WITHOUT reminder
    4. Respond: "Added your assignment. Note: I can't set reminders yet. 
       Please enable in the Alexa app."

Flow 2 (Permission Revoked Later):
  User: "Update assignment"
  
  System:
    1. Find existing reminder_id in DB
    2. Attempt update → 403 Forbidden
    3. Update assignment, set reminder_id = null
    4. Respond: "Updated. Reminder permission has been revoked."
```

**Implementation**: `RemindersHelper.create_reminder()` returns error dict; handler continues without error.

---

### 8. Database Transaction Failures

**Scenario**: Network error during DynamoDB write.

```
User: "Mark assignment complete"

Flow:
  1. Update assignment status to "completed"
  2. Update SR state for any related quiz items
  3. Log session
  
  If step 2 fails:
    a. Rollback step 1? (DynamoDB doesn't support transactions in basic API)
    b. RECOMMENDATION: Use batch_write or TransactWriteItems
    c. If batch fails, log error and retry with exponential backoff
```

**Implementation**: Use `batch_write_item` or `transact_write_items` for multi-table writes; implement retry logic with jitter.

---

### 9. Invalid Due Date Format

**Scenario**: User provides date in unexpected format.

```
Alexa Slot Parsing (AMAZON.Date):
  Input: "next Friday"    → Parsed as: 2026-01-31
  Input: "2/15"           → Parsed as: 2026-02-15
  Input: "January 30"     → Parsed as: 2026-01-30
  Input: "five days"      → NOT PARSED (falls back to elicitation)

System Logic:
  1. Slot validation: Is value in valid date format (YYYY-MM-DD)?
  2. If not, re-elicit: "I didn't catch the due date. Please say it as a date, like January 30th."
  3. Parse and validate: Is due_date >= today?
  4. If due_date is past, ask: "That's in the past. Did you mean next month?"
```

**Implementation**: Alexa's AMAZON.Date slot type handles most cases; custom validation for edge cases.

---

### 10. Cold Start Performance

**Scenario**: Lambda cold start exceeds Alexa timeout (8 seconds).

```
Typical Timings:
  - Lambda init: 1-2 seconds
  - Import dependencies: 0.5-1 second
  - First request: 2-3 seconds
  - Warm invocation: 0.5-1 second

Optimization:
  1. Use Lambda Provisioned Concurrency (cost trade-off)
  2. Keep dependencies minimal
  3. Remove unused imports
  4. Use lazy loading for helpers
  5. Monitor CloudWatch metrics for cold starts
```

**Implementation**: Review Lambda metrics; add provisioned concurrency if > 30% cold starts.

---

### 11. Spaced Repetition Edge Cases

**Scenario**: SM-2 algorithm edge cases.

```
Case A: First-time quiz (ease_factor = 2.5, interval = 1, reps = 0)
  - User passes → interval = 3 days, reps = 1
  - User fails → interval = 1 day, reps = 0

Case B: Item reviewed many times (ease_factor = 1.3, interval = 365, reps = 100)
  - User passes → interval ≈ 475 days (1.3 * 365)
  - User fails → interval = 1 day, ease factor stays at 1.3 (minimum)

Case C: Next review date calculation (prevent going backwards)
  - today = 2026-01-22
  - item next_review_date = 2026-01-20 (due date in the past!)
  - Query for due_review should include past dates
  - System shows as "due for review"
```

**Implementation**: See `SpacedRepetitionScheduler.calculate_next_interval()` for SM-2 logic.

---

### 12. Ambiguous Quiz Responses

**Scenario**: User's quiz answer is hard to score.

```
Question: "What are photosynthesis products?"

User Answer: "Oxygen"
Expected: "Glucose and oxygen" or at least "glucose" and/or "oxygen"

Scoring Logic:
  - Exact match OR major keywords present → "pass"
  - Partial keywords only → "partial"
  - No match / "I don't know" / "pass" → "fail"

Implementation:
  1. Tokenize both answer and expected
  2. Calculate overlap percentage
  3. If > 70% overlap → "pass"
  4. If 30-70% → "partial"
  5. If < 30% → "fail"
```

**Production Note**: For v1, keep scoring simple. Consider ML-based scoring in v2.

---

### 13. Concurrent Quiz Sessions

**Scenario**: User says "quiz me in Biology" while already in a quiz session.

```
Existing Session: Quiz in History (question 2 of 5)

User: "Quiz me in Biology"

System Logic:
  1. Check session state: session_type = "quiz", active = True
  2. Previous session still active?
     a. Ask: "You're currently in a History quiz. Finish it or start over?"
     b. User says "Start over" → clear old session, start new one
     c. User says "Resume" → continue History quiz

Implementation:
  - Check `get_session_state()` before creating new session
  - If active session exists, prompt to confirm switch
```

---

### 14. Extreme Estimated Time

**Scenario**: User provides unrealistic time estimate.

```
User: "Add assignment estimated 500 hours"

System Logic:
  1. Accept any positive integer (no validation upper bound in v1)
  2. In daily plan: Show actual estimate (500 hours!)
  3. In prioritization: Account for time (might rank lower due to duration)
  
Future Enhancement (v2):
  - Warn if > 480 minutes (8 hours)
  - Suggest more realistic time frame
```

---

### 15. Database Query Performance

**Scenario**: User with 1000+ assignments queries daily plan.

```
Query: SELECT * FROM assignments WHERE user_id = 'XXXX' AND status != 'completed'
Result: 500 incomplete assignments

Optimization:
  1. Use GSI (user_due_date_idx) instead of scan
  2. Limit query to next 30 days: due_date >= today AND due_date <= today + 30
  3. Cache result in session state (valid for 1 hour)
  4. Implement pagination if > 100 results

Performance Target: < 500ms query time
```

**Implementation**: Review DynamoDB query patterns; use GSI efficiently.

---

## Monitoring & Alerting

### Key Metrics

```
1. Lambda Metrics
   - Invocations: Total requests
   - Errors: Failed invocations
   - Duration: Handler execution time
   - Cold starts: Frequency and impact

2. DynamoDB Metrics
   - ConsumedReadCapacityUnits
   - ConsumedWriteCapacityUnits
   - UserErrors: Validation errors, throttling
   - SuccessfulRequestLatency

3. Reminders API Metrics
   - create_reminder success rate
   - HTTP 403 (permission denied) frequency
   - API latency

4. Application Metrics
   - User count (unique user_ids)
   - Sessions per user
   - Quiz completion rate
   - Pomodoro completion rate
```

### Alerting Thresholds

```json
{
  "LambdaErrorRate": {
    "threshold": 0.05,
    "severity": "WARNING",
    "message": "Lambda error rate > 5%"
  },
  "DynamoDBThrottling": {
    "threshold": 1,
    "severity": "CRITICAL",
    "message": "DynamoDB throttling detected"
  },
  "ReminderPermissionDenial": {
    "threshold": 0.2,
    "severity": "INFO",
    "message": "> 20% of reminder creation attempts denied"
  },
  "LambdaColdStartLatency": {
    "threshold": 5000,
    "severity": "WARNING",
    "message": "Cold start > 5 seconds"
  }
}
```

---
