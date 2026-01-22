"""
DynamoDB helper module for Homework Coach.

Provides abstracted CRUD operations for:
- User profiles
- Assignments
- Quiz items
- Spaced repetition state
- Study sessions
- Session state
"""

import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

class DynamoDBHelper:
    """Helper for DynamoDB operations."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize DynamoDB client."""
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.client = boto3.client("dynamodb", region_name=region)
    
    # ========== USER PROFILE OPERATIONS ==========
    
    def get_or_create_user(self, user_id: str, display_name: str = None, timezone: str = "America/New_York") -> Dict[str, Any]:
        """Get user profile or create if not exists."""
        table = self.dynamodb.Table("homework-coach-users")
        
        try:
            response = table.get_item(Key={"user_id": user_id})
            if "Item" in response:
                return response["Item"]
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
        
        # Create new user
        now = datetime.utcnow().isoformat()
        user = {
            "user_id": user_id,
            "display_name": display_name or "Student",
            "timezone": timezone,
            "preferences": {
                "pomodoro_duration_minutes": 25,
                "break_duration_minutes": 5,
                "reminder_enabled": True,
                "reminder_time_before_minutes": 1440,
                "quiz_difficulty": "mixed"
            },
            "created_at": now,
            "updated_at": now,
            "last_active": now
        }
        
        try:
            table.put_item(Item=user)
            logger.info(f"Created user profile for {user_id}")
            return user
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            raise
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences."""
        table = self.dynamodb.Table("homework-coach-users")
        
        try:
            response = table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET preferences = :p, updated_at = :t",
                ExpressionAttributeValues={
                    ":p": preferences,
                    ":t": datetime.utcnow().isoformat()
                },
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes", {})
        except Exception as e:
            logger.error(f"Error updating preferences for {user_id}: {e}")
            raise
    
    # ========== ASSIGNMENT OPERATIONS ==========
    
    def add_assignment(self, user_id: str, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new assignment."""
        table = self.dynamodb.Table("homework-coach-assignments")
        
        assignment = {
            "user_id": user_id,
            "assignment_id": str(uuid.uuid4()),
            "class_name": assignment_data.get("class_name"),
            "title": assignment_data.get("title"),
            "description": assignment_data.get("description", ""),
            "due_date": assignment_data.get("due_date"),
            "due_time": assignment_data.get("due_time"),
            "estimated_minutes": assignment_data.get("estimated_minutes", 30),
            "status": "not_started",
            "priority": assignment_data.get("priority", "medium"),
            "reminder_id": None,
            "reminder_sent_at": None,
            "completed_at": None,
            "starred": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            table.put_item(Item=assignment)
            logger.info(f"Added assignment {assignment['assignment_id']} for user {user_id}")
            return assignment
        except Exception as e:
            logger.error(f"Error adding assignment: {e}")
            raise
    
    def get_assignments_by_user(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all assignments for user, optionally filtered by status."""
        table = self.dynamodb.Table("homework-coach-assignments")
        
        try:
            response = table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": user_id}
            )
            
            assignments = response.get("Items", [])
            
            if status:
                assignments = [a for a in assignments if a.get("status") == status]
            
            return assignments
        except Exception as e:
            logger.error(f"Error querying assignments for {user_id}: {e}")
            raise
    
    def get_assignments_by_due_date(self, user_id: str, due_date: str) -> List[Dict[str, Any]]:
        """Get assignments due on specific date using GSI."""
        table = self.dynamodb.Table("homework-coach-assignments")
        
        try:
            response = table.query(
                IndexName="user_due_date_idx",
                KeyConditionExpression="user_id = :uid AND due_date = :dd",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":dd": due_date
                }
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error querying assignments by due date: {e}")
            raise
    
    def update_assignment_status(self, user_id: str, assignment_id: str, status: str) -> Dict[str, Any]:
        """Update assignment status (not_started, in_progress, completed, overdue)."""
        table = self.dynamodb.Table("homework-coach-assignments")
        
        try:
            completed_at = datetime.utcnow().isoformat() if status == "completed" else None
            
            update_expr = "SET #status = :s, updated_at = :t"
            expr_values = {
                ":s": status,
                ":t": datetime.utcnow().isoformat()
            }
            
            if completed_at:
                update_expr += ", completed_at = :c"
                expr_values[":c"] = completed_at
            
            response = table.update_item(
                Key={"user_id": user_id, "assignment_id": assignment_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues=expr_values,
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes", {})
        except Exception as e:
            logger.error(f"Error updating assignment status: {e}")
            raise
    
    def delete_assignment(self, user_id: str, assignment_id: str) -> bool:
        """Delete assignment."""
        table = self.dynamodb.Table("homework-coach-assignments")
        
        try:
            table.delete_item(Key={"user_id": user_id, "assignment_id": assignment_id})
            logger.info(f"Deleted assignment {assignment_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting assignment: {e}")
            raise
    
    # ========== QUIZ ITEM OPERATIONS ==========
    
    def add_quiz_item(self, user_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add quiz item to question bank."""
        table = self.dynamodb.Table("homework-coach-quiz-items")
        
        item = {
            "user_id": user_id,
            "item_id": str(uuid.uuid4()),
            "subject": item_data.get("subject"),
            "prompt": item_data.get("prompt"),
            "answer": item_data.get("answer"),
            "type": item_data.get("type", "short_answer"),
            "difficulty": item_data.get("difficulty", "medium"),
            "tags": item_data.get("tags", []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            table.put_item(Item=item)
            logger.info(f"Added quiz item {item['item_id']} for user {user_id}")
            return item
        except Exception as e:
            logger.error(f"Error adding quiz item: {e}")
            raise
    
    def get_quiz_items_by_subject(self, user_id: str, subject: str) -> List[Dict[str, Any]]:
        """Get quiz items for a subject using GSI."""
        table = self.dynamodb.Table("homework-coach-quiz-items")
        
        try:
            response = table.query(
                IndexName="user_subject_idx",
                KeyConditionExpression="user_id = :uid AND subject = :subj",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":subj": subject
                }
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error querying quiz items by subject: {e}")
            raise
    
    # ========== SPACED REPETITION OPERATIONS ==========
    
    def init_sr_state(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Initialize spaced repetition state for new quiz item."""
        table = self.dynamodb.Table("homework-coach-sr-state")
        
        sr_state = {
            "user_id": user_id,
            "item_id": item_id,
            "interval": 1,
            "ease_factor": 2.5,
            "repetitions": 0,
            "next_review_date": datetime.utcnow().date().isoformat(),
            "last_review_date": None,
            "last_result": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            table.put_item(Item=sr_state)
            logger.info(f"Initialized SR state for item {item_id}, user {user_id}")
            return sr_state
        except Exception as e:
            logger.error(f"Error initializing SR state: {e}")
            raise
    
    def get_sr_state(self, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get spaced repetition state for item."""
        table = self.dynamodb.Table("homework-coach-sr-state")
        
        try:
            response = table.get_item(Key={"user_id": user_id, "item_id": item_id})
            return response.get("Item")
        except Exception as e:
            logger.error(f"Error retrieving SR state: {e}")
            raise
    
    def get_items_due_for_review(self, user_id: str, review_date: str) -> List[Dict[str, Any]]:
        """Get items due for review on specific date using GSI."""
        table = self.dynamodb.Table("homework-coach-sr-state")
        
        try:
            response = table.query(
                IndexName="user_review_date_idx",
                KeyConditionExpression="user_id = :uid AND next_review_date <= :rd",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":rd": review_date
                }
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error querying items for review: {e}")
            raise
    
    def update_sr_state(self, user_id: str, item_id: str, sr_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update spaced repetition state after quiz attempt."""
        table = self.dynamodb.Table("homework-coach-sr-state")
        
        try:
            update_expr = "SET interval = :i, ease_factor = :e, repetitions = :r, last_review_date = :lrd, last_result = :lr, next_review_date = :nrd, updated_at = :t"
            
            response = table.update_item(
                Key={"user_id": user_id, "item_id": item_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues={
                    ":i": sr_update.get("interval", 1),
                    ":e": sr_update.get("ease_factor", 2.5),
                    ":r": sr_update.get("repetitions", 0),
                    ":lrd": datetime.utcnow().date().isoformat(),
                    ":lr": sr_update.get("last_result"),
                    ":nrd": sr_update.get("next_review_date"),
                    ":t": datetime.utcnow().isoformat()
                },
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes", {})
        except Exception as e:
            logger.error(f"Error updating SR state: {e}")
            raise
    
    # ========== STUDY SESSION OPERATIONS ==========
    
    def create_study_session(self, user_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create study session record."""
        table = self.dynamodb.Table("homework-coach-sessions")
        
        session = {
            "user_id": user_id,
            "session_id": str(uuid.uuid4()),
            "subject": session_data.get("subject"),
            "session_type": session_data.get("session_type", "pomodoro"),
            "start_time": session_data.get("start_time", datetime.utcnow().isoformat()),
            "end_time": None,
            "duration_minutes": session_data.get("duration_minutes", 25),
            "completed": False,
            "interruptions": 0,
            "notes": ""
        }
        
        try:
            table.put_item(Item=session)
            logger.info(f"Created session {session['session_id']} for user {user_id}")
            return session
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def complete_study_session(self, user_id: str, session_id: str, completed: bool = True, interruptions: int = 0) -> Dict[str, Any]:
        """Mark study session as complete."""
        table = self.dynamodb.Table("homework-coach-sessions")
        
        try:
            response = table.update_item(
                Key={"user_id": user_id, "session_id": session_id},
                UpdateExpression="SET #end = :e, completed = :c, interruptions = :i",
                ExpressionAttributeNames={"#end": "end_time"},
                ExpressionAttributeValues={
                    ":e": datetime.utcnow().isoformat(),
                    ":c": completed,
                    ":i": interruptions
                },
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes", {})
        except Exception as e:
            logger.error(f"Error completing session: {e}")
            raise
    
    def get_sessions_by_date(self, user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get sessions within date range using GSI."""
        table = self.dynamodb.Table("homework-coach-sessions")
        
        try:
            response = table.query(
                IndexName="user_date_idx",
                KeyConditionExpression="user_id = :uid AND start_time BETWEEN :start AND :end",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":start": start_date,
                    ":end": end_date
                }
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error querying sessions by date: {e}")
            raise
    
    # ========== SESSION STATE OPERATIONS ==========
    
    def get_session_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state (for active Pomodoro/quiz/etc)."""
        table = self.dynamodb.Table("homework-coach-session-state")
        
        try:
            response = table.get_item(Key={"user_id": user_id})
            return response.get("Item")
        except Exception as e:
            logger.error(f"Error retrieving session state: {e}")
            return None
    
    def update_session_state(self, user_id: str, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update or create session state."""
        table = self.dynamodb.Table("homework-coach-session-state")
        
        state = {
            "user_id": user_id,
            "session_type": state_data.get("session_type", "none"),
            "active": state_data.get("active", False),
            "pomodoro": state_data.get("pomodoro"),
            "quiz": state_data.get("quiz"),
            "started_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        try:
            table.put_item(Item=state)
            logger.info(f"Updated session state for {user_id}")
            return state
        except Exception as e:
            logger.error(f"Error updating session state: {e}")
            raise
    
    def clear_session_state(self, user_id: str) -> bool:
        """Clear session state."""
        table = self.dynamodb.Table("homework-coach-session-state")
        
        try:
            table.delete_item(Key={"user_id": user_id})
            logger.info(f"Cleared session state for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing session state: {e}")
            raise
