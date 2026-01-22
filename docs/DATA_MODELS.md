# Homework Coach - Data Models & Schemas

## Overview
This document defines the complete data model for the Homework Coach Alexa Skill, including JSON schemas, DynamoDB table structures, and state management strategies.

---

## 1. User Profile Schema

**Purpose**: Store user preferences, configuration, and metadata.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "User Profile",
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "Alexa user ID (from context.System.user.userId)"
    },
    "display_name": {
      "type": "string",
      "description": "Optional user name for personalization (e.g., 'Alex')"
    },
    "grade_level": {
      "type": "integer",
      "minimum": 9,
      "maximum": 12,
      "description": "High school grade (9-12), optional for content personalization"
    },
    "timezone": {
      "type": "string",
      "description": "IANA timezone (e.g., 'America/New_York')",
      "default": "America/New_York"
    },
    "preferences": {
      "type": "object",
      "properties": {
        "pomodoro_duration_minutes": {
          "type": "integer",
          "default": 25,
          "minimum": 5,
          "maximum": 60
        },
        "break_duration_minutes": {
          "type": "integer",
          "default": 5,
          "minimum": 1,
          "maximum": 30
        },
        "reminder_enabled": {
          "type": "boolean",
          "default": true
        },
        "reminder_time_before_minutes": {
          "type": "integer",
          "default": 1440,
          "description": "Remind X minutes before due date (1440 = 1 day)"
        },
        "quiz_difficulty": {
          "type": "string",
          "enum": ["easy", "medium", "hard", "mixed"],
          "default": "mixed"
        }
      }
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    },
    "last_active": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["user_id", "timezone", "created_at"]
}
```

---

## 2. Class/Subject List Schema

**Purpose**: Store user's enrolled classes/subjects for context in assignments and quizzes.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Class List",
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string"
    },
    "classes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "class_id": {
            "type": "string",
            "description": "UUID for class"
          },
          "name": {
            "type": "string",
            "description": "Class name (e.g., 'AP Biology', 'Honors Algebra II')"
          },
          "teacher": {
            "type": "string",
            "description": "Teacher name (optional)"
          },
          "period": {
            "type": "string",
            "description": "Class period/time (optional)"
          },
          "created_at": {
            "type": "string",
            "format": "date-time"
          }
        },
        "required": ["class_id", "name"]
      }
    }
  },
  "required": ["user_id", "classes"]
}
```

---

## 3. Assignment Schema

**Purpose**: Store homework assignments with metadata for tracking, reminders, and prioritization.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Assignment",
  "type": "object",
  "properties": {
    "assignment_id": {
      "type": "string",
      "description": "UUID"
    },
    "user_id": {
      "type": "string"
    },
    "class_id": {
      "type": "string",
      "description": "Reference to Class (optional; can be free-form if class not in list)"
    },
    "class_name": {
      "type": "string",
      "description": "Class name (e.g., 'Biology', 'History')"
    },
    "title": {
      "type": "string",
      "description": "Assignment title (e.g., 'Chapter 5 review questions')"
    },
    "description": {
      "type": "string",
      "description": "Optional detailed description"
    },
    "due_date": {
      "type": "string",
      "format": "date",
      "description": "Due date in YYYY-MM-DD format"
    },
    "due_time": {
      "type": "string",
      "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
      "description": "Optional due time in HH:MM format"
    },
    "estimated_minutes": {
      "type": "integer",
      "minimum": 5,
      "maximum": 1440,
      "description": "Estimated time to complete in minutes"
    },
    "status": {
      "type": "string",
      "enum": ["not_started", "in_progress", "completed", "overdue"],
      "default": "not_started"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high"],
      "default": "medium"
    },
    "reminder_id": {
      "type": "string",
      "description": "Alexa Reminders API ID (if reminder created)"
    },
    "reminder_sent_at": {
      "type": "string",
      "format": "date-time"
    },
    "completed_at": {
      "type": "string",
      "format": "date-time"
    },
    "starred": {
      "type": "boolean",
      "default": false
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["assignment_id", "user_id", "class_name", "title", "due_date", "created_at"]
}
```

---

## 4. Study Session Schema

**Purpose**: Log Pomodoro and general study sessions for productivity tracking.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Study Session",
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "UUID"
    },
    "user_id": {
      "type": "string"
    },
    "subject": {
      "type": "string",
      "description": "Class/subject studied"
    },
    "session_type": {
      "type": "string",
      "enum": ["pomodoro", "freeform"],
      "default": "pomodoro"
    },
    "start_time": {
      "type": "string",
      "format": "date-time"
    },
    "end_time": {
      "type": "string",
      "format": "date-time"
    },
    "duration_minutes": {
      "type": "integer"
    },
    "completed": {
      "type": "boolean",
      "description": "Whether session finished normally (not abandoned)"
    },
    "interruptions": {
      "type": "integer",
      "default": 0,
      "description": "Number of times paused/resumed"
    },
    "notes": {
      "type": "string",
      "description": "Optional user notes"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["session_id", "user_id", "subject", "start_time", "completed"]
}
```

---

## 5. Quiz Item Schema

**Purpose**: Store question bank for micro-quizzes with spaced-repetition metadata.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Quiz Item",
  "type": "object",
  "properties": {
    "item_id": {
      "type": "string",
      "description": "UUID"
    },
    "user_id": {
      "type": "string"
    },
    "subject": {
      "type": "string",
      "description": "Class/subject (e.g., 'Biology')"
    },
    "prompt": {
      "type": "string",
      "description": "Question text"
    },
    "answer": {
      "type": "string",
      "description": "Correct answer or key points"
    },
    "type": {
      "type": "string",
      "enum": ["short_answer", "multiple_choice", "true_false"],
      "default": "short_answer"
    },
    "difficulty": {
      "type": "string",
      "enum": ["easy", "medium", "hard"],
      "default": "medium"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "e.g., ['Chapter 3', 'Photosynthesis', 'Midterm Review']"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["item_id", "user_id", "subject", "prompt", "answer"]
}
```

---

## 6. Spaced-Repetition Metadata Schema

**Purpose**: Track SM-2 algorithm state for each quiz item per user.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Spaced Repetition State",
  "type": "object",
  "properties": {
    "sr_id": {
      "type": "string",
      "description": "UUID (could be composite of user_id + item_id)"
    },
    "user_id": {
      "type": "string"
    },
    "item_id": {
      "type": "string",
      "description": "Reference to Quiz Item"
    },
    "interval": {
      "type": "integer",
      "default": 1,
      "description": "Days until next review"
    },
    "ease_factor": {
      "type": "number",
      "default": 2.5,
      "minimum": 1.3,
      "description": "SM-2 ease factor (difficulty multiplier)"
    },
    "repetitions": {
      "type": "integer",
      "default": 0,
      "description": "Number of times reviewed"
    },
    "next_review_date": {
      "type": "string",
      "format": "date",
      "description": "YYYY-MM-DD when item should be reviewed next"
    },
    "last_review_date": {
      "type": "string",
      "format": "date"
    },
    "last_result": {
      "type": "string",
      "enum": ["pass", "fail", "partial"],
      "description": "User's last response quality"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["sr_id", "user_id", "item_id", "created_at"]
}
```

---

## 7. Daily Plan Schema

**Purpose**: Cache today's prioritized assignment list (generated at plan check-in).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Daily Plan",
  "type": "object",
  "properties": {
    "plan_id": {
      "type": "string",
      "description": "UUID"
    },
    "user_id": {
      "type": "string"
    },
    "plan_date": {
      "type": "string",
      "format": "date",
      "description": "YYYY-MM-DD"
    },
    "assignments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "assignment_id": {
            "type": "string"
          },
          "rank": {
            "type": "integer",
            "description": "Priority order (1 = highest)"
          },
          "reason": {
            "type": "string",
            "description": "Why prioritized (e.g., 'Due today', 'Overdue', 'Estimated 2 hours')"
          }
        }
      }
    },
    "total_estimated_minutes": {
      "type": "integer"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["plan_id", "user_id", "plan_date", "generated_at"]
}
```

---

## 8. Session State Schema

**Purpose**: Track active session for multi-turn conversations (Pomodoro timer, quiz session, etc.).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Session State",
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string"
    },
    "session_type": {
      "type": "string",
      "enum": ["pomodoro", "quiz", "plan_checkin", "recap", "none"],
      "default": "none"
    },
    "active": {
      "type": "boolean"
    },
    "pomodoro": {
      "type": "object",
      "properties": {
        "subject": {
          "type": "string"
        },
        "start_time": {
          "type": "string",
          "format": "date-time"
        },
        "duration_minutes": {
          "type": "integer"
        },
        "elapsed_minutes": {
          "type": "integer"
        },
        "paused_at": {
          "type": "string",
          "format": "date-time"
        },
        "is_paused": {
          "type": "boolean"
        },
        "interruptions": {
          "type": "integer"
        }
      }
    },
    "quiz": {
      "type": "object",
      "properties": {
        "subject": {
          "type": "string"
        },
        "items_to_review": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "IDs of quiz items for this session"
        },
        "current_item_index": {
          "type": "integer"
        },
        "responses": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "item_id": {
                "type": "string"
              },
              "result": {
                "type": "string",
                "enum": ["pass", "fail", "partial"]
              }
            }
          }
        }
      }
    },
    "started_at": {
      "type": "string",
      "format": "date-time"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "description": "Session invalidated after 1 hour of inactivity"
    }
  },
  "required": ["user_id", "session_type", "active"]
}
```

---

## 9. Reminder Log Schema

**Purpose**: Track reminder creation and delivery for audit/debugging.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Reminder Log",
  "type": "object",
  "properties": {
    "log_id": {
      "type": "string",
      "description": "UUID"
    },
    "user_id": {
      "type": "string"
    },
    "assignment_id": {
      "type": "string"
    },
    "reminder_id": {
      "type": "string",
      "description": "ID returned by Alexa Reminders API"
    },
    "reminder_label": {
      "type": "string"
    },
    "scheduled_for": {
      "type": "string",
      "format": "date-time",
      "description": "When reminder is scheduled to fire"
    },
    "status": {
      "type": "string",
      "enum": ["created", "confirmed", "failed", "acknowledged"],
      "default": "created"
    },
    "error_message": {
      "type": "string",
      "description": "If status = failed"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["log_id", "user_id", "reminder_id"]
}
```

---

## DynamoDB Table Design

### Table 1: UserProfile
- **Table Name**: `homework-coach-users`
- **Partition Key**: `user_id` (String)
- **Sort Key**: None
- **GSI**: `last_active_idx` → Query recent users
- **TTL**: None (user data retained indefinitely)

### Table 2: Assignments
- **Table Name**: `homework-coach-assignments`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `assignment_id` (String)
- **GSI 1**: `user_due_date_idx` (PK: `user_id`, SK: `due_date`) → Query by due date
- **GSI 2**: `user_status_idx` (PK: `user_id`, SK: `status`) → Query by status
- **TTL**: `archived_at` (auto-delete after 30 days for completed/archived)

### Table 3: StudySessions
- **Table Name**: `homework-coach-sessions`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `session_id` (String)
- **GSI**: `user_date_idx` (PK: `user_id`, SK: `start_time`) → Query by date range
- **TTL**: None

### Table 4: QuizItems
- **Table Name**: `homework-coach-quiz-items`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `item_id` (String)
- **GSI**: `user_subject_idx` (PK: `user_id`, SK: `subject`) → Query by subject
- **TTL**: None

### Table 5: SpacedRepetition
- **Table Name**: `homework-coach-sr-state`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `item_id` (String) [composite key = user_id#item_id]
- **GSI**: `user_review_date_idx` (PK: `user_id`, SK: `next_review_date`) → Query items due for review today
- **TTL**: None

### Table 6: SessionState
- **Table Name**: `homework-coach-session-state`
- **Partition Key**: `user_id` (String)
- **Sort Key**: None
- **TTL**: `expires_at` (auto-delete inactive sessions after 1 hour)

### Table 7: ReminderLog
- **Table Name**: `homework-coach-reminder-log`
- **Partition Key**: `user_id` (String)
- **Sort Key**: `log_id` (String)
- **GSI**: `reminder_id_idx` (GSI with reminder_id as PK) → Lookup by reminder ID
- **TTL**: None (retained for debugging; consider archiving after 90 days in production)

---

## State Management & Multi-Turn Conversation Flow

### Pomodoro Session State Flow
1. User says "Start a Pomodoro session in Biology"
2. System creates/updates `SessionState` (type: `pomodoro`, active: true)
3. Stores subject, start_time, duration_minutes (25), elapsed_minutes (0), is_paused (false)
4. Repeats: User can say "pause", "resume", "stop", "extend by 5 minutes"
5. On "stop" or timer complete: Write to `StudySessions` table, clear from `SessionState`

### Quiz Session State Flow
1. User says "Quiz me in Biology"
2. System queries `SpacedRepetition` table for items where user_id = X AND subject = "Biology" AND next_review_date <= today
3. Creates `SessionState` (type: `quiz`, active: true), initializes items_to_review array, current_item_index = 0
4. Reads first item from `QuizItems`, presents question
5. User responds; system logs response in session state
6. Repeats until all items reviewed
7. On session end: Update all `SpacedRepetition` items with new ease_factor, interval, next_review_date; write to `StudySessions`

### Daily Plan Check-In Flow
1. User says "What's my plan for today?"
2. System queries `Assignments` where user_id = X AND (due_date = today OR status = "overdue")
3. Generates prioritized list (sort by: overdue first, then due today, then by estimated_minutes)
4. Stores in `DailyPlan` table, reads aloud
5. System offers to start Pomodoro or add new assignment

---

## Privacy & Data Retention

- **User Profile**: Retained indefinitely; user can request deletion (CCPA/GDPR compliance)
- **Assignments**: Retained indefinitely; archived assignments deleted after 30 days
- **Quiz Items & SR State**: Retained indefinitely for learning analytics
- **Study Sessions**: Retained 1 year for performance tracking
- **Session State**: Auto-deleted after session expires (1 hour inactivity) or completion
- **Reminder Log**: Retained 90 days for debugging
- **No PII in logs**: Store only user_id, timestamps, and anonymized event types

---

