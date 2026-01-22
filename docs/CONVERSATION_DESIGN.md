# Homework Coach - Conversation Design & Example Flows

Complete multi-turn conversation transcripts demonstrating all major use cases.

---

## 1. Daily Planning Check-In

**Scenario**: Student opens the skill to review today's homework assignments.

```
User:     "Alexa, open Homework Coach"

Alexa:    "Welcome back, Alex! I'm Homework Coach, your study partner. You can tell me 
           your daily plan, add assignments, start a Pomodoro session, take a quiz, or 
           get your end-of-day recap. What would you like to do?"

User:     "What's my daily plan?"

Alexa:    "Here's your study plan for today. 
           1. Biology quiz in AP Biology. Overdue (estimated 30 min). 
           2. Chemistry worksheet in Chemistry. Due today (estimated 45 min). 
           3. History essay in World History. Due tomorrow (estimated 2 hours). 
           4. Spanish vocab in Spanish III. Due in 3 days (estimated 20 min). 
           
           Would you like to start a Pomodoro session or add a new assignment?"

User:     "I want to start a Pomodoro for Biology"

Alexa:    "Alright, let's focus on Biology! Starting a 25 minute Pomodoro session. 
           You can say pause, resume, extend, or stop. Let me know when you're done 
           or need a break. Good luck!"
           
           [Echo Show displays timer visual]
```

---

## 2. Starting & Controlling Pomodoro Sessions

**Scenario**: Student starts and manages a study session.

```
User:     "Start a Pomodoro session in Chemistry"

Alexa:    "Alright, let's focus on Chemistry! Starting a 25 minute Pomodoro session. 
           You can say pause, resume, extend, or stop. Good luck!"

[5 minutes pass]

User:     "How much time is left?"

Alexa:    "You have 20 minutes remaining in your Pomodoro session."

[10 more minutes pass]

User:     "I need to pause"

Alexa:    "Paused. You've completed 15 minutes. Just let me know when you're ready 
           to resume."

[3 minutes pass]

User:     "Resume"

Alexa:    "Resuming your 25 minute Pomodoro session. 20 minutes remaining. 
           That's 1 pause so far."

[20 minutes pass - timer complete]

Alexa:    "Time's up! You completed a full 25 minute Pomodoro session on Chemistry 
           with 1 interruption. Great focus! Take a 5 minute break. Would you like 
           to start another session?"

User:     "Stop"

Alexa:    "Got it, I've ended your session. You studied Chemistry for 25 minutes. 
           You can add the time to your daily summary or start another session anytime."
```

---

## 3. Adding an Assignment with Due Date

**Scenario**: Student adds homework assignment via multi-turn dialog.

```
User:     "Add an assignment"

Alexa:    "Sure! What's the assignment called?"

User:     "Chapter 5 reading and review questions"

Alexa:    "Chapter 5 reading and review questions. Which class is this for?"

User:     "Biology"

Alexa:    "Biology. When is it due?"

User:     "Friday"

Alexa:    "Friday, January 24th. How long do you think it will take?"

User:     "About 45 minutes"

Alexa:    "Got it! I've added Chapter 5 reading and review questions for Biology, 
           due Friday, January 24th. Estimated time: 45 minutes. 
           I'll set a reminder for Thursday at 9 AM. 
           Would you like to add another assignment or start studying?"

User:     "Add another"

Alexa:    "What's the assignment called?"

User:     "Math problem set 3-5"

Alexa:    "Math problem set 3-5. Which class?"

User:     "Honors Algebra II"

Alexa:    "Honors Algebra II. When is it due?"

User:     "Tomorrow"

Alexa:    "Tomorrow, January 23rd. How long will it take?"

User:     "30 minutes"

Alexa:    "Got it! I've added Math problem set 3-5 for Honors Algebra II, 
           due tomorrow. Estimated time: 30 minutes. I'll remind you tonight at 6 PM.
           Would you like to add another assignment or start studying?"

User:     "No, thanks"

Alexa:    "Alright. You can ask me for your daily plan, start a Pomodoro, take a quiz, 
           or get your recap anytime. Happy studying!"
```

---

## 4. Micro-Quiz with Spaced Repetition

**Scenario**: Student takes a quiz to test knowledge and reinforce learning.

```
User:     "Quiz me in Biology"

Alexa:    "Great! Let's quiz you on Biology. I have 5 questions due for review today. 
           Here's the first one: What are the products of photosynthesis?"

User:     "Glucose and oxygen"

Alexa:    "Excellent! That's correct. Next question (2 of 5): 
           What's the term for organisms that make their own food?"

User:     "Autotrophs"

Alexa:    "Perfect! Question 3 of 5: Describe the role of mitochondria in a cell."

User:     "Um... energy production?"

Alexa:    "Close! The more complete answer is that mitochondria are the powerhouse 
           of the cell - they break down glucose to produce ATP, which provides energy 
           for cellular functions. Let's keep going. Question 4 of 5: 
           What is the difference between mitosis and meiosis?"

User:     "Pass"

Alexa:    "No problem, we'll review that one later. Question 5 of 5 (final): 
           What are the main types of blood cells?"

User:     "Red blood cells, white blood cells, and platelets"

Alexa:    "Perfect! You've completed all 5 questions. 
           Results: 3 correct, 1 partial, 1 skipped. 
           
           Great job! Your quiz responses have been saved. I've updated your 
           review schedule - the questions you got right will show up again in 
           about a week. The question you're less sure about will come back in 
           2-3 days. 
           
           Would you like to quiz on another subject or get back to your assignments?"

User:     "No, I'm done"

Alexa:    "Great work! Your quiz session has been logged. Keep studying!"
```

---

## 5. Viewing & Managing Assignments

**Scenario**: Student checks current assignments and marks one complete.

```
User:     "Show me my assignments"

Alexa:    "Here are your upcoming assignments:
           1. Math problem set 3-5 in Honors Algebra II, due tomorrow (30 min)
           2. Chapter 5 reading and review questions in Biology, due Friday (45 min)
           3. World History essay in World History, due next Monday (2 hours)
           4. Spanish vocabulary in Spanish III, due Wednesday (20 min)
           
           Would you like to mark any as complete or add a new one?"

User:     "Mark the math problem set complete"

Alexa:    "Great job! I've marked Math problem set 3-5 as complete. 
           You've finished 1 assignment today. Keep up the good work!"

User:     "Show me what's due today"

Alexa:    "You don't have any assignments due today. Your next assignment is 
           Math problem set 3-5 (30 min) due tomorrow. 
           Would you like to add something or start a Pomodoro?"

User:     "Show assignments due Friday"

Alexa:    "You have 1 assignment due Friday:
           Chapter 5 reading and review questions in Biology (45 minutes)
           
           Estimated total time: 45 minutes. When would you like to tackle this?"
```

---

## 6. End-of-Day Recap & Rollover

**Scenario**: Student gets daily summary and sees what's rolling over to next day.

```
User:     "Give me my recap"

Alexa:    "Let's see how your day went! You completed 3 Pomodoro sessions, 
           finished 2 assignments, and studied for a total of 1 hour and 15 minutes. 
           Incredible focus! That's a major accomplishment!
           
           You still have 5 assignments pending:
           - Math problem set 3-5 in Honors Algebra II (30 min) - due tomorrow - HIGH PRIORITY
           - Chapter 5 reading in Biology (45 min) - due Friday
           - World History essay (2 hours) - due Monday
           - Spanish vocabulary (20 min) - due Wednesday
           - Physics lab report (90 min) - due next Tuesday
           
           Focus on these 1 high-priority item tomorrow. Get some rest and I'll 
           see you tomorrow!"

User:     "Goodnight"

Alexa:    "Sleep well! You earned it. See you tomorrow, Alex!"
```

---

## 7. Error Handling & Reprompts

**Scenario**: User provides incomplete or ambiguous information.

```
User:     "Add homework"

Alexa:    "Sure! What's the assignment called?"

User:     [No response for 8 seconds]

Alexa:    "I'm still waiting. What's the assignment you need to add?"

User:     "Never mind"

Alexa:    "No problem. You can add an assignment anytime. 
           What else can I help you with?"

---

User:     "Start a Pomodoro"

Alexa:    "What subject would you like to study? You can say Biology, History, 
           Math, or any of your classes."

User:     "Um, science?"

Alexa:    "I'm not sure which science class. Do you mean AP Biology, 
           Chemistry, or Physics?"

User:     "Chemistry"

Alexa:    "Alright, let's focus on Chemistry! Starting a 25 minute Pomodoro session..."

---

User:     "Quiz me"

Alexa:    "Which subject would you like to quiz on? You can say Biology, History, 
           Math, or any of your classes."

User:     "Something easy"

Alexa:    "I'm not sure which subject that is. You have quiz items due in: 
           Biology, History, Algebra, Spanish, and Chemistry. Which one?"

User:     "History"

Alexa:    "Perfect! Let's quiz you on History. I have 3 questions due for review today..."
```

---

## 8. Permission Denied Flows

**Scenario**: User hasn't granted reminder permission.

```
User:     "Add an assignment due Friday"

Alexa:    "Great! I've added your assignment. However, I notice you haven't granted 
           permission for reminders yet. 
           
           Would you like me to send you reminders for due dates? 
           You can enable this in the Alexa app under Skills Settings. 
           (Don't worry - your assignment has been saved either way!)"

[If user later enables permission]

Alexa:    "Perfect! I've enabled reminders. From now on, I'll remind you 24 hours 
           before each assignment is due."
```

---

## 9. Multi-User Household

**Scenario**: Multiple students in same household.

```
Device:   "Alexa, open Homework Coach"

Alexa:    "Which person is this for? I can help Alex, Sam, or Jordan."

User:     "Alex"

Alexa:    "Welcome back, Alex! Your daily plan includes 3 assignments..."

---

Device:   "Alexa, what's my daily plan?"

Alexa:    "Which person would you like the daily plan for?"

User:     "Sam"

Alexa:    "Here's Sam's daily plan. Sam has 2 assignments due today..."
```

---

## 10. Timezone & Reminder Timing

**Scenario**: User with custom timezone and reminder preferences.

```
User:     "Open Homework Coach"

Alexa:    [First time] "I notice you're in a new location. What's your timezone?"

User:     "Pacific Time"

Alexa:    "Got it, I'll use Pacific Time for reminders. I'll remind you the day 
           before assignments are due, in the morning. 
           You can change this anytime by saying 'update my preferences'."

---

[Later, user adds assignment]

User:     "Add assignment in Spanish due Friday"

Alexa:    "I've added your Spanish assignment due Friday, January 24th. 
           Since you're in Pacific Time, I'll remind you Thursday morning at 9 AM. 
           Is that good?"

User:     "Change it to 7 AM"

Alexa:    "Updated! I'll remind you Thursday at 7 AM. Got it!"
```

---

## 11. Help & Navigation

**Scenario**: User asks for help or guidance.

```
User:     "Help"

Alexa:    "I'm Homework Coach, your study partner. Here's what you can do:
           - Ask for your DAILY PLAN to see today's assignments prioritized
           - ADD AN ASSIGNMENT with class, title, and due date
           - START A POMODORO SESSION to study with focus
           - QUIZ ME to test your knowledge with spaced repetition
           - GET MY RECAP to see today's progress and tomorrow's focus
           
           What would you like to do?"

User:     "Tell me more about Pomodoro"

Alexa:    "Pomodoro is a study technique where you work focused for 25 minutes, 
           then take a 5 minute break. I'll time the session and track your 
           interruptions. You can pause, resume, extend, or stop anytime. 
           It's great for building focus and getting things done!
           
           Would you like to start one?"
```

---

## Dialogue Manager Configuration

The skill uses Alexa's built-in dialog management for slot elicitation:

```json
{
  "dialog": {
    "intents": [
      {
        "name": "AddAssignmentIntent",
        "confirmationRequired": false,
        "prompts": {
          "elicitation": {
            "AssignmentTitle": "What's the assignment called?",
            "ClassName": "Which class is this for?",
            "DueDate": "When is it due?",
            "EstimatedMinutes": "How long do you think it will take?"
          }
        }
      }
    ]
  }
}
```

---

## Response Variation

Responses vary based on:
- **User preferences** (Pomodoro duration, reminder timing)
- **Context** (time of day, recent activity)
- **Device type** (voice-only vs Echo Show with APL visuals)
- **Motivation level** (encouraging on low-progress days, celebratory on high-progress days)

---
