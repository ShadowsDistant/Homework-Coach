"""
Homework Coach Alexa Skill - Main Lambda Handler

Implements core intent handlers for:
- Daily plan check-in
- Adding assignments
- Starting Pomodoro sessions
- Quiz sessions with spaced repetition
- End-of-day recap
- Help and error handling
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime, timedelta

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response

from helpers.algorithms import PlanGenerator, PomodoroManager, SpacedRepetitionScheduler, EndOfDayRecap
from helpers.dynamodb_helper import DynamoDBHelper
from helpers.reminders_helper import RemindersHelper
from helpers.apl_helper import APLHelper

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize helpers
db_helper = DynamoDBHelper()
reminders_helper = RemindersHelper()
apl_helper = APLHelper()

# ============================================================================
# LAUNCH HANDLER
# ============================================================================

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Alexa launch requests."""
    
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):
        """
        Launch: Greet user and offer options (daily plan, add assignment, start Pomodoro, quiz, recap).
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        
        # Get or create user profile
        user = db_helper.get_or_create_user(user_id)
        display_name = user.get("display_name", "there")
        
        speech = f"Welcome back, {display_name}! I'm Homework Coach, your study partner. "
        speech += "You can tell me your daily plan, add assignments, start a Pomodoro session, take a quiz, or get your end-of-day recap. What would you like to do?"
        
        reprompt = "You can ask me to check your daily plan, add an assignment, start a Pomodoro, quiz you, or give you a recap."
        
        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response


# ============================================================================
# DAILY PLAN INTENT
# ============================================================================

class DailyPlanIntentHandler(AbstractRequestHandler):
    """Handler for daily plan check-in."""
    
    def can_handle(self, handler_input):
        return is_intent_name("DailyPlanIntent")(handler_input)
    
    def handle(self, handler_input):
        """
        Get today's assignments, prioritize them, and read plan aloud.
        If device supports APL, also render checklist.
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        today = datetime.utcnow().date().isoformat()
        
        try:
            # Get all active assignments for user
            assignments = db_helper.get_assignments_by_user(user_id, status=None)
            
            # Filter for today and near future
            today_dt = datetime.strptime(today, "%Y-%m-%d")
            relevant_assignments = [
                a for a in assignments
                if a.get("status") != "completed"
                and datetime.strptime(a.get("due_date"), "%Y-%m-%d") <= today_dt + timedelta(days=7)
            ]
            
            if not relevant_assignments:
                speech = "You don't have any upcoming assignments. Great job staying on top of things!"
                handler_input.response_builder.speak(speech)
                return handler_input.response_builder.response
            
            # Generate prioritized plan
            plan = PlanGenerator.generate_daily_plan(relevant_assignments, today)
            
            # Build speech response
            speech = "Here's your study plan for today. "
            for item in plan[:5]:  # Limit to top 5 to keep response concise
                assignment = next((a for a in relevant_assignments if a.get("assignment_id") == item["assignment_id"]), None)
                if assignment:
                    speech += f"{item['rank']}. {assignment.get('title')} in {assignment.get('class_name')}. {item['reason']}. "
            
            if len(plan) > 5:
                speech += f"And {len(plan) - 5} more assignments. "
            
            speech += "Would you like to start a Pomodoro session or add a new assignment?"
            
            handler_input.response_builder.speak(speech).ask("Ready to get started?")
            
            # Add APL visualization if supported
            if apl_helper.supports_apl(handler_input):
                apl_doc = apl_helper.render_assignment_checklist(relevant_assignments[:10])
                apl_helper.add_apl_to_response(handler_input.response_builder, apl_doc)
            
        except Exception as e:
            logger.error(f"Error in DailyPlanIntent: {e}")
            speech = "Sorry, I couldn't retrieve your plan right now. Please try again later."
            handler_input.response_builder.speak(speech)
        
        return handler_input.response_builder.response


# ============================================================================
# ADD ASSIGNMENT INTENT
# ============================================================================

class AddAssignmentIntentHandler(AbstractRequestHandler):
    """Handler for adding new assignments."""
    
    def can_handle(self, handler_input):
        return is_intent_name("AddAssignmentIntent")(handler_input)
    
    def handle(self, handler_input):
        """
        Capture assignment details (class, title, due date, estimated time).
        Use dialog model to elicit missing slots.
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        slots = intent.slots
        
        # Dialog elicitation: ensure required slots are filled
        if not all([slots.get("ClassName"), slots.get("AssignmentTitle"), slots.get("DueDate")]):
            logger.info("Missing required slots; prompting for more info")
            handler_input.response_builder.add_elicit_slot_directive(
                intent_name="AddAssignmentIntent",
                slots=slots,
                slot_to_elicit=None  # Let dialog manager handle next elicitation
            )
            return handler_input.response_builder.response
        
        # Extract slot values
        class_name = slots.get("ClassName").value if slots.get("ClassName") else "Class"
        title = slots.get("AssignmentTitle").value if slots.get("AssignmentTitle") else "Assignment"
        due_date = slots.get("DueDate").value if slots.get("DueDate") else None
        estimated_minutes = int(slots.get("EstimatedMinutes").value) if slots.get("EstimatedMinutes") else 30
        
        try:
            # Validate due date
            if not due_date:
                raise ValueError("Due date is required")
            
            # Add assignment to database
            assignment = db_helper.add_assignment(
                user_id,
                {
                    "class_name": class_name,
                    "title": title,
                    "due_date": due_date,
                    "estimated_minutes": estimated_minutes
                }
            )
            
            # Create reminder if enabled
            user = db_helper.get_or_create_user(user_id)
            if user.get("preferences", {}).get("reminder_enabled"):
                timezone = user.get("timezone", "America/New_York")
                reminder_minutes = user.get("preferences", {}).get("reminder_time_before_minutes", 1440)
                
                trigger_time = RemindersHelper.format_trigger_time(due_date, None, timezone, reminder_minutes)
                reminder_result = RemindersHelper.create_reminder(
                    handler_input.request_envelope,
                    f"{title} in {class_name} is due",
                    trigger_time,
                    timezone
                )
                
                if reminder_result.get("success"):
                    reminder_id = reminder_result.get("reminder_id")
                    db_helper.update_assignment_status(user_id, assignment.get("assignment_id"), "not_started")
                    logger.info(f"Reminder created for assignment {assignment.get('assignment_id')}")
            
            speech = f"Got it! I've added {title} for {class_name}, due {due_date}. Estimated time: {estimated_minutes} minutes. "
            speech += "Would you like to add another assignment or start studying?"
            
            handler_input.response_builder.speak(speech).ask("What's next?")
        
        except Exception as e:
            logger.error(f"Error adding assignment: {e}")
            speech = f"Sorry, I couldn't add that assignment. Error: {str(e)}"
            handler_input.response_builder.speak(speech)
        
        return handler_input.response_builder.response


# ============================================================================
# START POMODORO INTENT
# ============================================================================

class StartPomodoroIntentHandler(AbstractRequestHandler):
    """Handler for starting Pomodoro sessions."""
    
    def can_handle(self, handler_input):
        return is_intent_name("StartPomodoroIntent")(handler_input)
    
    def handle(self, handler_input):
        """
        Start a Pomodoro session with optional subject.
        Save session state for pause/resume/complete controls.
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        slots = intent.slots
        
        subject = slots.get("Subject").value if slots.get("Subject") else "Study"
        
        try:
            # Get user preferences for duration
            user = db_helper.get_or_create_user(user_id)
            duration = user.get("preferences", {}).get("pomodoro_duration_minutes", 25)
            
            # Create Pomodoro session
            pomodoro = PomodoroManager.start_session(subject, duration)
            
            # Store session state for multi-turn conversation
            db_helper.update_session_state(
                user_id,
                {
                    "session_type": "pomodoro",
                    "active": True,
                    "pomodoro": pomodoro
                }
            )
            
            # Log session to database
            db_helper.create_study_session(
                user_id,
                {
                    "subject": subject,
                    "session_type": "pomodoro",
                    "start_time": pomodoro.get("start_time"),
                    "duration_minutes": duration
                }
            )
            
            speech = f"Alright, let's focus on {subject}! Starting a {duration} minute Pomodoro session. "
            speech += "You can say pause, resume, extend, or stop. Let me know when you're done or need a break. Good luck!"
            
            handler_input.response_builder.speak(speech)
            
            # Add APL visualization if supported
            if apl_helper.supports_apl(handler_input):
                apl_doc = apl_helper.render_pomodoro_timer(subject, duration, 0)
                apl_helper.add_apl_to_response(handler_input.response_builder, apl_doc)
        
        except Exception as e:
            logger.error(f"Error starting Pomodoro: {e}")
            speech = "Sorry, I couldn't start your Pomodoro session. Please try again."
            handler_input.response_builder.speak(speech)
        
        return handler_input.response_builder.response


# ============================================================================
# POMODORO CONTROL INTENT
# ============================================================================

class PomodoroControlIntentHandler(AbstractRequestHandler):
    """Handler for controlling active Pomodoro (pause, resume, extend, stop)."""
    
    def can_handle(self, handler_input):
        return is_intent_name("PomodoroControlIntent")(handler_input)
    
    def handle(self, handler_input):
        """Handle Pomodoro pause, resume, extend, or stop."""
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        
        # Get current session state
        session_state = db_helper.get_session_state(user_id)
        
        if not session_state or session_state.get("session_type") != "pomodoro" or not session_state.get("active"):
            speech = "You don't have an active Pomodoro session. Would you like to start one?"
            handler_input.response_builder.speak(speech).ask("Start a Pomodoro?")
            return handler_input.response_builder.response
        
        try:
            pomodoro = session_state.get("pomodoro", {})
            slots = intent.slots
            
            # Determine command
            if handler_input.request_envelope.request.intent.name == "PomodoroControlIntent":
                # Could have multiple slot values; check intent name or use context
                command = "unknown"
                
                # Map based on common keywords in slots (simplified)
                # In production, would use explicit intents or slot values
                speech_text = handler_input.request_envelope.request.intent.slots.get("Minutes", {}).value if handler_input.request_envelope.request.intent.slots.get("Minutes") else ""
                
                # This is simplified; in production use explicit slot analysis
                speech = "Pomodoro control request received."
            else:
                speech = "I didn't catch that. Say pause, resume, or stop."
            
            handler_input.response_builder.speak(speech)
        
        except Exception as e:
            logger.error(f"Error controlling Pomodoro: {e}")
            handler_input.response_builder.speak("Sorry, there was an error. Please try again.")
        
        return handler_input.response_builder.response


# ============================================================================
# QUIZ INTENT
# ============================================================================

class QuizIntentHandler(AbstractRequestHandler):
    """Handler for quiz sessions with spaced repetition."""
    
    def can_handle(self, handler_input):
        return is_intent_name("QuizIntent")(handler_input)
    
    def handle(self, handler_input):
        """
        Start a quiz session, selecting items due for review today.
        Enter multi-turn quiz conversation.
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        slots = intent.slots
        
        subject = slots.get("Subject").value if slots.get("Subject") else None
        today = datetime.utcnow().date().isoformat()
        
        try:
            if not subject:
                speech = "Which subject would you like to quiz on? You can say Biology, History, Math, or any of your classes."
                handler_input.response_builder.speak(speech).ask("What subject?")
                return handler_input.response_builder.response
            
            # Get quiz items due for review in this subject
            sr_states = db_helper.get_items_due_for_review(user_id, today)
            
            # Filter by subject and get item details
            quiz_items = []
            for sr_state in sr_states:
                item = db_helper.get_quiz_items_by_subject(user_id, subject)
                quiz_items.extend([i for i in item if i.get("item_id") == sr_state.get("item_id")])
            
            if not quiz_items:
                speech = f"You don't have any quiz items due for review in {subject} today. "
                speech += "Would you like to add some study questions or quiz on another subject?"
                handler_input.response_builder.speak(speech).ask("What would you like to do?")
                return handler_input.response_builder.response
            
            # Initialize quiz session
            quiz_session = {
                "subject": subject,
                "items_to_review": [item.get("item_id") for item in quiz_items],
                "current_item_index": 0,
                "responses": []
            }
            
            db_helper.update_session_state(
                user_id,
                {
                    "session_type": "quiz",
                    "active": True,
                    "quiz": quiz_session
                }
            )
            
            # Present first question
            current_item = quiz_items[0]
            speech = f"Great! Let's quiz you on {subject}. I have {len(quiz_items)} questions. Here's the first one: "
            speech += f"{current_item.get('prompt')} "
            speech += "What's your answer?"
            
            handler_input.response_builder.speak(speech).ask("Your answer?")
            
            # Add APL visualization if supported
            if apl_helper.supports_apl(handler_input):
                apl_doc = apl_helper.render_quiz_question(
                    current_item.get("prompt"),
                    1,
                    len(quiz_items)
                )
                apl_helper.add_apl_to_response(handler_input.response_builder, apl_doc)
        
        except Exception as e:
            logger.error(f"Error starting quiz: {e}")
            speech = "Sorry, I couldn't start the quiz right now. Please try again later."
            handler_input.response_builder.speak(speech)
        
        return handler_input.response_builder.response


# ============================================================================
# RECAP INTENT
# ============================================================================

class RecapIntentHandler(AbstractRequestHandler):
    """Handler for end-of-day recap."""
    
    def can_handle(self, handler_input):
        return is_intent_name("RecapIntent")(handler_input)
    
    def handle(self, handler_input):
        """
        Generate end-of-day summary: Pomodoros completed, assignments done, time studied.
        Suggest incomplete items for tomorrow.
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        today = datetime.utcnow().date().isoformat()
        
        try:
            # Get sessions from today
            from datetime import timedelta
            tomorrow = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
            sessions_today = db_helper.get_sessions_by_date(user_id, today, tomorrow)
            
            # Get assignments
            all_assignments = db_helper.get_assignments_by_user(user_id)
            completed_today = [a for a in all_assignments if a.get("status") == "completed" and a.get("completed_at", "").startswith(today)]
            incomplete = [a for a in all_assignments if a.get("status") != "completed"]
            
            # Generate recap
            recap = EndOfDayRecap.generate_recap(sessions_today, completed_today, incomplete)
            
            # Build speech
            speech = recap.get("motivational_message", "Great effort today!") + " "
            speech += f"You completed {recap.get('pomodoros_count', 0)} Pomodoro sessions, "
            speech += f"finished {recap.get('assignments_completed', 0)} assignments, "
            speech += f"and studied for {recap.get('total_study_minutes', 0)} minutes. "
            
            if incomplete:
                speech += f"You have {len(incomplete)} assignments still pending. "
                rollover = EndOfDayRecap.rollover_incomplete_assignments(incomplete, today)
                high_priority = [r for r in rollover if r.get("priority") == "high"]
                if high_priority:
                    speech += f"Focus on these {len(high_priority)} high-priority items tomorrow."
            
            speech += " Get some rest and I'll see you tomorrow!"
            
            handler_input.response_builder.speak(speech)
            
            # Add APL visualization if supported
            if apl_helper.supports_apl(handler_input):
                apl_doc = apl_helper.render_end_of_day_recap(recap)
                apl_helper.add_apl_to_response(handler_input.response_builder, apl_doc)
        
        except Exception as e:
            logger.error(f"Error generating recap: {e}")
            speech = "Sorry, I couldn't generate your recap right now. Try again later."
            handler_input.response_builder.speak(speech)
        
        return handler_input.response_builder.response


# ============================================================================
# BUILT-IN INTENT HANDLERS
# ============================================================================

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for help requests."""
    
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    
    def handle(self, handler_input):
        speech = (
            "I'm Homework Coach, your study partner. Here's what you can do: "
            "Ask for your daily plan, add an assignment with a due date, start a Pomodoro study session, "
            "take a quiz to test your knowledge, or get your end-of-day recap. "
            "What would you like to do?"
        )
        handler_input.response_builder.speak(speech).ask("How can I help you study?")
        return handler_input.response_builder.response


class CancelAndStopIntentHandler(AbstractRequestHandler):
    """Handler for cancel and stop requests."""
    
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name("AMAZON.StopIntent")(handler_input)
    
    def handle(self, handler_input):
        speech = "Goodbye! Keep working hard on your studies!"
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for fallback intent."""
    
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)
    
    def handle(self, handler_input):
        speech = (
            "I'm not sure what you meant. You can ask me to check your daily plan, add an assignment, "
            "start a Pomodoro session, take a quiz, or get your recap. What would you like?"
        )
        handler_input.response_builder.speak(speech).ask("Try again?")
        return handler_input.response_builder.response


# ============================================================================
# EXCEPTION HANDLER
# ============================================================================

class GenericExceptionHandler(AbstractExceptionHandler):
    """Generic exception handler."""
    
    def can_handle(self, handler_input, exception):
        return True
    
    def handle(self, handler_input, exception):
        logger.error(f"Unhandled exception: {exception}", exc_info=True)
        speech = "Sorry, something went wrong. Please try again later."
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


# ============================================================================
# SKILL BUILDER & LAMBDA HANDLER
# ============================================================================

def get_skill():
    """Build and return the Alexa skill."""
    sb = SkillBuilder()
    
    # Request handlers
    sb.add_request_handler(LaunchRequestHandler())
    sb.add_request_handler(DailyPlanIntentHandler())
    sb.add_request_handler(AddAssignmentIntentHandler())
    sb.add_request_handler(StartPomodoroIntentHandler())
    sb.add_request_handler(PomodoroControlIntentHandler())
    sb.add_request_handler(QuizIntentHandler())
    sb.add_request_handler(RecapIntentHandler())
    sb.add_request_handler(HelpIntentHandler())
    sb.add_request_handler(CancelAndStopIntentHandler())
    sb.add_request_handler(FallbackIntentHandler())
    
    # Exception handler
    sb.add_exception_handler(GenericExceptionHandler())
    
    return sb.create()


# Lambda entry point
def lambda_handler(event, context):
    """AWS Lambda handler."""
    logger.info(f"Incoming event: {json.dumps(event)}")
    skill = get_skill()
    return skill(event, context)
