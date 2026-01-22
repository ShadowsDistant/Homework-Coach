"""
Alexa Reminders API helper module for Homework Coach.

Provides abstraction for creating, updating, and deleting reminders.
"""

import boto3
import requests
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RemindersHelper:
    """Helper for Alexa Reminders API operations."""
    
    def __init__(self):
        """Initialize reminders client."""
        pass
    
    @staticmethod
    def get_reminders_endpoint(request_envelope) -> str:
        """
        Extract Reminders API endpoint from request context.
        
        Returns:
            Base URL for Reminders API (e.g., https://api.amazonalexa.com)
        """
        try:
            return request_envelope.context.system.api_endpoint
        except (AttributeError, KeyError):
            return "https://api.amazonalexa.com"
    
    @staticmethod
    def get_api_access_token(request_envelope) -> Optional[str]:
        """
        Extract API access token from request context.
        
        Returns:
            Access token for Reminders API, or None if unavailable
        """
        try:
            return request_envelope.context.system.api_access_token
        except (AttributeError, KeyError):
            return None
    
    @staticmethod
    def create_reminder(
        request_envelope,
        label: str,
        trigger_time: str,
        timezone: str
    ) -> Dict[str, Any]:
        """
        Create an Alexa reminder for user.
        
        Args:
            request_envelope: Alexa request envelope
            label: Reminder text (e.g., "Biology assignment due")
            trigger_time: Time trigger in ISO 8601 format or human-readable
            timezone: User's timezone (e.g., 'America/New_York')
            
        Returns:
            Response dict with reminder_id, or error dict
            
        Raises:
            Exception on API error or permission denied
        """
        endpoint = RemindersHelper.get_reminders_endpoint(request_envelope)
        token = RemindersHelper.get_api_access_token(request_envelope)
        
        if not token:
            logger.warning("No API access token available; reminder permission may not be granted")
            return {
                "success": False,
                "error": "PERMISSION_DENIED",
                "message": "Reminder permission not granted. User must enable Reminders permission in Alexa app."
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Build reminder payload
        payload = {
            "label": label,
            "trigger": {
                "type": "SCHEDULED_ABSOLUTE",
                "scheduledTime": trigger_time
            },
            "timezone": timezone
        }
        
        try:
            url = f"{endpoint}/v1/alerts/reminders"
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Created reminder: {data.get('alertToken')}")
                return {
                    "success": True,
                    "reminder_id": data.get("alertToken"),
                    "label": label
                }
            elif response.status_code == 403:
                logger.warning("Reminders permission denied or revoked")
                return {
                    "success": False,
                    "error": "PERMISSION_DENIED",
                    "message": "Permission to set reminders has not been granted."
                }
            else:
                logger.error(f"Reminders API error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"API_ERROR_{response.status_code}",
                    "message": response.text
                }
        
        except requests.exceptions.Timeout:
            logger.error("Reminders API request timeout")
            return {
                "success": False,
                "error": "TIMEOUT",
                "message": "Request to create reminder timed out"
            }
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return {
                "success": False,
                "error": "UNKNOWN_ERROR",
                "message": str(e)
            }
    
    @staticmethod
    def update_reminder(
        request_envelope,
        reminder_id: str,
        label: str,
        trigger_time: str,
        timezone: str
    ) -> Dict[str, Any]:
        """
        Update an existing reminder.
        
        Args:
            request_envelope: Alexa request envelope
            reminder_id: ID of reminder to update
            label: New reminder text
            trigger_time: New trigger time in ISO 8601 format
            timezone: User's timezone
            
        Returns:
            Response dict with success status
        """
        endpoint = RemindersHelper.get_reminders_endpoint(request_envelope)
        token = RemindersHelper.get_api_access_token(request_envelope)
        
        if not token:
            return {
                "success": False,
                "error": "PERMISSION_DENIED",
                "message": "Reminder permission not granted"
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "label": label,
            "trigger": {
                "type": "SCHEDULED_ABSOLUTE",
                "scheduledTime": trigger_time
            },
            "timezone": timezone
        }
        
        try:
            url = f"{endpoint}/v1/alerts/reminders/{reminder_id}"
            response = requests.put(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 204:
                logger.info(f"Updated reminder: {reminder_id}")
                return {
                    "success": True,
                    "reminder_id": reminder_id
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "PERMISSION_DENIED"
                }
            else:
                logger.error(f"Reminders API error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"API_ERROR_{response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            return {
                "success": False,
                "error": "UNKNOWN_ERROR",
                "message": str(e)
            }
    
    @staticmethod
    def delete_reminder(
        request_envelope,
        reminder_id: str
    ) -> Dict[str, Any]:
        """
        Delete an existing reminder.
        
        Args:
            request_envelope: Alexa request envelope
            reminder_id: ID of reminder to delete
            
        Returns:
            Response dict with success status
        """
        endpoint = RemindersHelper.get_reminders_endpoint(request_envelope)
        token = RemindersHelper.get_api_access_token(request_envelope)
        
        if not token:
            return {
                "success": False,
                "error": "PERMISSION_DENIED"
            }
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            url = f"{endpoint}/v1/alerts/reminders/{reminder_id}"
            response = requests.delete(url, headers=headers, timeout=5)
            
            if response.status_code == 204:
                logger.info(f"Deleted reminder: {reminder_id}")
                return {
                    "success": True,
                    "reminder_id": reminder_id
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "PERMISSION_DENIED"
                }
            else:
                logger.error(f"Reminders API error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"API_ERROR_{response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return {
                "success": False,
                "error": "UNKNOWN_ERROR"
            }
    
    @staticmethod
    def format_trigger_time(due_date: str, due_time: Optional[str], timezone: str, minutes_before: int = 1440) -> str:
        """
        Format trigger time for Reminders API from due date/time and advance notice.
        
        Args:
            due_date: Due date in YYYY-MM-DD format
            due_time: Optional due time in HH:MM format
            timezone: User's timezone
            minutes_before: Minutes before due time to remind (default 1 day)
            
        Returns:
            ISO 8601 trigger time string
            
        Example:
            due_date="2026-01-30", due_time="17:00", minutes_before=1440
            → "2026-01-29T17:00:00.000" (reminder day before at 5 PM)
        """
        try:
            if due_time:
                due_datetime_str = f"{due_date}T{due_time}:00"
            else:
                due_datetime_str = f"{due_date}T09:00:00"  # Default 9 AM if no time specified
            
            due_dt = datetime.fromisoformat(due_datetime_str)
            from datetime import timedelta
            trigger_dt = due_dt - timedelta(minutes=minutes_before)
            
            # Format as ISO 8601 without timezone (Alexa expects local time)
            return trigger_dt.strftime("%Y-%m-%dT%H:%M:%S.000")
        except Exception as e:
            logger.error(f"Error formatting trigger time: {e}")
            # Fallback: return original due date at 9 AM
            return f"{due_date}T09:00:00.000"
