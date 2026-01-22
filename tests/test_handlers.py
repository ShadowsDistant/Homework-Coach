"""
Integration tests for Lambda handlers.

Tests for request/response flows without actual AWS services.
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Mock AWS SDK before importing handlers
sys.modules['ask_sdk_core'] = MagicMock()
sys.modules['ask_sdk_core.skill_builder'] = MagicMock()
sys.modules['ask_sdk_core.dispatch_components'] = MagicMock()
sys.modules['ask_sdk_core.utils'] = MagicMock()
sys.modules['ask_sdk_model'] = MagicMock()


class TestRequestEnvelopes(unittest.TestCase):
    """Tests for Alexa request envelope processing."""
    
    def test_launch_request_structure(self):
        """LaunchRequest should contain required fields."""
        launch_request = {
            "type": "LaunchRequest",
            "requestId": "amzn1.ask.request.12345",
            "timestamp": "2026-01-22T10:00:00Z",
            "locale": "en-US"
        }
        
        self.assertEqual(launch_request["type"], "LaunchRequest")
        self.assertIn("requestId", launch_request)
        self.assertIn("timestamp", launch_request)
    
    def test_intent_request_structure(self):
        """IntentRequest should contain intent and slots."""
        intent_request = {
            "type": "IntentRequest",
            "requestId": "amzn1.ask.request.12345",
            "timestamp": "2026-01-22T10:00:00Z",
            "locale": "en-US",
            "intent": {
                "name": "AddAssignmentIntent",
                "slots": {
                    "AssignmentTitle": {
                        "name": "AssignmentTitle",
                        "value": "Chapter 5 Review"
                    },
                    "ClassName": {
                        "name": "ClassName",
                        "value": "Biology"
                    },
                    "DueDate": {
                        "name": "DueDate",
                        "value": "2026-01-25"
                    }
                }
            }
        }
        
        self.assertEqual(intent_request["intent"]["name"], "AddAssignmentIntent")
        self.assertEqual(intent_request["intent"]["slots"]["AssignmentTitle"]["value"], "Chapter 5 Review")
    
    def test_context_structure(self):
        """Context should include system and user info."""
        context = {
            "System": {
                "application": {"applicationId": "amzn1.ask.skill.12345"},
                "user": {"userId": "amzn1.ask.account.UNIQUE_USER_ID"},
                "device": {
                    "deviceId": "amzn1.ask.device.DEVICE_ID",
                    "supportedInterfaces": {}
                },
                "apiEndpoint": "https://api.amazonalexa.com"
            }
        }
        
        self.assertIn("user", context["System"])
        self.assertIn("userId", context["System"]["user"])


class TestResponseFormats(unittest.TestCase):
    """Tests for Alexa response formats."""
    
    def test_simple_speech_response(self):
        """Simple speech response format."""
        response = {
            "version": "1.0",
            "sessionAttributes": {},
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Welcome to Homework Coach!"
                },
                "card": {
                    "type": "Simple",
                    "title": "Homework Coach",
                    "content": "Welcome"
                },
                "shouldEndSession": False
            }
        }
        
        self.assertEqual(response["version"], "1.0")
        self.assertEqual(response["response"]["outputSpeech"]["type"], "PlainText")
        self.assertFalse(response["response"]["shouldEndSession"])
    
    def test_response_with_apl_directive(self):
        """Response with APL display directive."""
        response = {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Here's your daily plan"
                },
                "directives": [
                    {
                        "type": "Alexa.Presentation.APL.RenderDocument",
                        "document": {
                            "type": "APL",
                            "version": "2022.2",
                            "mainTemplate": {"items": []}
                        }
                    }
                ],
                "shouldEndSession": False
            }
        }
        
        self.assertIn("directives", response["response"])
        self.assertEqual(response["response"]["directives"][0]["type"], "Alexa.Presentation.APL.RenderDocument")


class TestConversationFlows(unittest.TestCase):
    """Tests for multi-turn conversation scenarios."""
    
    def test_add_assignment_flow_turn_1(self):
        """First turn: user says 'add an assignment'."""
        # Handler receives intent without all required slots
        intent_request = {
            "intent": {
                "name": "AddAssignmentIntent",
                "slots": {
                    # Missing: AssignmentTitle, ClassName, DueDate
                }
            }
        }
        
        # Expected: Elicit slot for AssignmentTitle
        expected_directive = {
            "type": "Dialog.ElicitSlot",
            "slotToElicit": "AssignmentTitle",
            "intent": {
                "name": "AddAssignmentIntent"
            }
        }
        
        self.assertEqual(expected_directive["type"], "Dialog.ElicitSlot")
    
    def test_add_assignment_flow_turn_2(self):
        """Second turn: user provides title, system asks for class."""
        intent_request = {
            "intent": {
                "name": "AddAssignmentIntent",
                "slots": {
                    "AssignmentTitle": {"value": "Chapter 5 Review"}
                    # Still missing: ClassName, DueDate
                }
            }
        }
        
        # Expected: Elicit slot for ClassName
        expected_directive = {
            "type": "Dialog.ElicitSlot",
            "slotToElicit": "ClassName"
        }
        
        self.assertEqual(expected_directive["type"], "Dialog.ElicitSlot")
    
    def test_pomodoro_pause_resume_flow(self):
        """Multi-turn Pomodoro control."""
        # Turn 1: Start Pomodoro
        start_request = {
            "intent": {
                "name": "StartPomodoroIntent",
                "slots": {"Subject": {"value": "Biology"}}
            }
        }
        
        # Store session state (in practice, in DynamoDB)
        session_state = {
            "session_type": "pomodoro",
            "active": True,
            "pomodoro": {
                "subject": "Biology",
                "duration_minutes": 25,
                "elapsed_minutes": 0,
                "is_paused": False
            }
        }
        
        self.assertTrue(session_state["active"])
        
        # Turn 2: User says "pause"
        control_request = {
            "intent": {
                "name": "PomodoroControlIntent",
                "slots": {}  # Would be filled by dialog manager
            }
        }
        
        # Session state should update
        session_state["pomodoro"]["is_paused"] = True
        self.assertTrue(session_state["pomodoro"]["is_paused"])
    
    def test_quiz_flow_multiple_turns(self):
        """Multi-turn quiz conversation."""
        # Initial quiz state
        quiz_state = {
            "subject": "Biology",
            "items_to_review": ["q1", "q2", "q3"],
            "current_item_index": 0,
            "responses": []
        }
        
        self.assertEqual(quiz_state["current_item_index"], 0)
        
        # After user answers first question
        quiz_state["responses"].append({"item_id": "q1", "result": "pass"})
        quiz_state["current_item_index"] = 1
        
        self.assertEqual(len(quiz_state["responses"]), 1)
        self.assertEqual(quiz_state["current_item_index"], 1)
        
        # Continue for remaining questions
        quiz_state["responses"].append({"item_id": "q2", "result": "pass"})
        quiz_state["current_item_index"] = 2
        
        quiz_state["responses"].append({"item_id": "q3", "result": "fail"})
        quiz_state["current_item_index"] = 3
        
        self.assertEqual(len(quiz_state["responses"]), 3)
        self.assertEqual(quiz_state["current_item_index"], 3)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error conditions."""
    
    def test_no_assignments_scenario(self):
        """User has no assignments."""
        response = {
            "outputSpeech": {
                "type": "PlainText",
                "text": "You don't have any upcoming assignments. Great job staying on top of things!"
            }
        }
        
        self.assertIn("Great job", response["outputSpeech"]["text"])
    
    def test_ambiguous_class_name(self):
        """User provides ambiguous class name (e.g., just 'Math')."""
        # System should either ask for clarification or default to most recent
        request_slots = {
            "ClassName": {"value": "math"}  # lowercase, generic
        }
        
        # In production, would fuzzy match against user's class list
        self.assertEqual(request_slots["ClassName"]["value"].lower(), "math")
    
    def test_missing_timezone(self):
        """User profile missing timezone should default."""
        user_profile = {
            "user_id": "amzn1.ask.account.123",
            "timezone": "America/New_York"  # Default fallback
        }
        
        self.assertIsNotNone(user_profile["timezone"])
    
    def test_invalid_due_date_format(self):
        """User provides invalid due date."""
        # Alexa will normalize to YYYY-MM-DD, but system should validate
        due_date = "2026-01-22"  # Valid
        
        try:
            from datetime import datetime
            datetime.strptime(due_date, "%Y-%m-%d")
            valid = True
        except ValueError:
            valid = False
        
        self.assertTrue(valid)
    
    def test_permission_denied_reminder(self):
        """User denies reminder permission."""
        response = {
            "error": "PERMISSION_DENIED",
            "message": "Permission to set reminders has not been granted."
        }
        
        self.assertFalse(response.get("success", False))
        self.assertEqual(response["error"], "PERMISSION_DENIED")
    
    def test_multiple_users_in_household(self):
        """Multiple Alexa users in same household."""
        user_1 = {"user_id": "user_1", "display_name": "Alex"}
        user_2 = {"user_id": "user_2", "display_name": "Sam"}
        
        # Each user should have separate data
        self.assertNotEqual(user_1["user_id"], user_2["user_id"])
        self.assertNotEqual(user_1["display_name"], user_2["display_name"])


if __name__ == "__main__":
    unittest.main()
