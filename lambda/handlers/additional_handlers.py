"""
Homework Coach - Core Handler Implementations (Part 2)

Includes:
- Quiz response handling
- Assignment management (view, mark complete)
- Class management
- Multi-turn conversation state management
"""

import logging
from datetime import datetime, timedelta
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name

from helpers.dynamodb_helper import DynamoDBHelper
from helpers.algorithms import SpacedRepetitionScheduler

logger = logging.getLogger(__name__)
db_helper = DynamoDBHelper()


class QuizResponseIntentHandler(AbstractRequestHandler):
    """Handler for user responses to quiz questions."""
    
    def can_handle(self, handler_input):
        return is_intent_name("QuizResponseIntent")(handler_input)
    
    def handle(self, handler_input):
        """
        Process user's quiz answer, update spaced repetition state,
        and move to next question or end quiz.
        """
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        
        # Get current quiz session
        session_state = db_helper.get_session_state(user_id)
        
        if not session_state or session_state.get("session_type") != "quiz" or not session_state.get("active"):
            speech = "You don't have an active quiz session. Would you like to start one?"
            handler_input.response_builder.speak(speech).ask("Start a quiz?")
            return handler_input.response_builder.response
        
        try:
            quiz_data = session_state.get("quiz", {})
            current_index = quiz_data.get("current_item_index", 0)
            items = quiz_data.get("items_to_review", [])
            
            if current_index >= len(items):
                # Quiz complete
                speech = "Great job! You've completed this quiz session. Would you like to quiz on something else?"
                handler_input.response_builder.speak(speech).ask("Quiz again?")
                db_helper.clear_session_state(user_id)
                return handler_input.response_builder.response
            
            # Get current item
            current_item_id = items[current_index]
            
            # In production, would parse user answer and score it
            # For now, assume "pass" on non-empty response
            user_answer = intent.slots.get("Answer", {}).value if intent.slots.get("Answer") else ""
            
            if user_answer.lower() in ["pass", "skip", "don't know", "i don't know"]:
                result = "fail"
            else:
                result = "pass"  # Simplified; real implementation would have fuzzy matching
            
            # Update spaced repetition state
            sr_state = db_helper.get_sr_state(user_id, current_item_id)
            if not sr_state:
                sr_state = db_helper.init_sr_state(user_id, current_item_id)
            
            next_interval, new_ease, new_reps = SpacedRepetitionScheduler.calculate_next_interval(
                sr_state.get("ease_factor", 2.5),
                sr_state.get("interval", 1),
                sr_state.get("repetitions", 0),
                result
            )
            
            next_review = (datetime.utcnow().date() + timedelta(days=next_interval)).isoformat()
            
            db_helper.update_sr_state(user_id, current_item_id, {
                "interval": next_interval,
                "ease_factor": new_ease,
                "repetitions": new_reps,
                "last_result": result,
                "next_review_date": next_review
            })
            
            # Move to next question
            quiz_data["current_item_index"] = current_index + 1
            quiz_data["responses"].append({"item_id": current_item_id, "result": result})
            
            db_helper.update_session_state(user_id, {
                "session_type": "quiz",
                "active": True,
                "quiz": quiz_data
            })
            
            if current_index + 1 >= len(items):
                speech = "That was the last question! You're all done. Great work!"
                handler_input.response_builder.speak(speech)
            else:
                # Get next question
                next_item_id = items[current_index + 1]
                # In production, fetch item from DB
                speech = f"Next question: [Question {current_index + 2} of {len(items)}]. What's your answer?"
                handler_input.response_builder.speak(speech).ask("Your answer?")
        
        except Exception as e:
            logger.error(f"Error handling quiz response: {e}")
            handler_input.response_builder.speak("Sorry, there was an error processing your answer.")
        
        return handler_input.response_builder.response


class ViewAssignmentsIntentHandler(AbstractRequestHandler):
    """Handler for viewing assignments."""
    
    def can_handle(self, handler_input):
        return is_intent_name("ViewAssignmentsIntent")(handler_input)
    
    def handle(self, handler_input):
        """List assignments (all, or filtered by due date)."""
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        
        due_date_slot = intent.slots.get("DueDate")
        
        try:
            if due_date_slot and due_date_slot.value:
                # Filter by specific date
                assignments = db_helper.get_assignments_by_due_date(user_id, due_date_slot.value)
                prefix = f"Assignments due {due_date_slot.value}: "
            else:
                # All incomplete assignments
                assignments = db_helper.get_assignments_by_user(user_id, status=None)
                incomplete = [a for a in assignments if a.get("status") != "completed"]
                assignments = sorted(incomplete, key=lambda x: x.get("due_date", ""))
                prefix = "Your upcoming assignments: "
            
            if not assignments:
                speech = "You don't have any assignments for that date."
                handler_input.response_builder.speak(speech)
                return handler_input.response_builder.response
            
            speech = prefix
            for i, assignment in enumerate(assignments[:10], 1):
                speech += f"{i}. {assignment.get('title')} in {assignment.get('class_name')}, due {assignment.get('due_date')}. "
            
            if len(assignments) > 10:
                speech += f"And {len(assignments) - 10} more."
            
            handler_input.response_builder.speak(speech)
        
        except Exception as e:
            logger.error(f"Error viewing assignments: {e}")
            handler_input.response_builder.speak("Sorry, I couldn't retrieve your assignments.")
        
        return handler_input.response_builder.response


class MarkCompleteIntentHandler(AbstractRequestHandler):
    """Handler for marking assignments as complete."""
    
    def can_handle(self, handler_input):
        return is_intent_name("MarkCompleteIntent")(handler_input)
    
    def handle(self, handler_input):
        """Mark an assignment as completed."""
        user_id = handler_input.request_envelope.context.system.user.user_id
        intent = handler_input.request_envelope.request.intent
        
        title = intent.slots.get("AssignmentTitle").value if intent.slots.get("AssignmentTitle") else None
        
        if not title:
            speech = "Which assignment would you like to mark as complete?"
            handler_input.response_builder.speak(speech).ask("Which assignment?")
            return handler_input.response_builder.response
        
        try:
            # Find assignment by title (fuzzy match in production)
            assignments = db_helper.get_assignments_by_user(user_id)
            matching = [a for a in assignments if title.lower() in a.get("title", "").lower()]
            
            if not matching:
                speech = f"I couldn't find an assignment called {title}. Can you be more specific?"
                handler_input.response_builder.speak(speech).ask("Try another assignment?")
                return handler_input.response_builder.response
            
            assignment = matching[0]
            db_helper.update_assignment_status(user_id, assignment.get("assignment_id"), "completed")
            
            speech = f"Great job! I've marked {assignment.get('title')} as complete. Keep up the good work!"
            handler_input.response_builder.speak(speech)
        
        except Exception as e:
            logger.error(f"Error marking complete: {e}")
            handler_input.response_builder.speak("Sorry, there was an error updating your assignment.")
        
        return handler_input.response_builder.response


class ManageClassesIntentHandler(AbstractRequestHandler):
    """Handler for managing user's class list."""
    
    def can_handle(self, handler_input):
        return is_intent_name("ManageClassesIntent")(handler_input)
    
    def handle(self, handler_input):
        """Add or list classes."""
        user_id = handler_input.request_envelope.context.system.user.user_id
        
        # Simplified: just confirm user setup
        speech = "I can help you manage your classes. For now, you can tell me the class name when adding assignments. Is there anything else I can help with?"
        
        handler_input.response_builder.speak(speech).ask("What would you like to do?")
        return handler_input.response_builder.response
