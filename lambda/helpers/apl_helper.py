"""
APL (Alexa Presentation Language) helper for Homework Coach.

Provides APL documents and rendering for Echo Show devices,
with graceful fallback for voice-only devices.
"""

import json
from typing import Dict, List, Any

class APLHelper:
    """Helper for generating APL documents."""
    
    @staticmethod
    def supports_apl(handler_input) -> bool:
        """Check if device supports APL display."""
        try:
            return handler_input.request_envelope.context.system.device.supported_interfaces.alexa_presentation_apl is not None
        except (AttributeError, TypeError):
            return False
    
    @staticmethod
    def render_assignment_checklist(assignments: List[Dict[str, Any]]) -> str:
        """
        Generate APL document for today's assignment checklist.
        
        Args:
            assignments: List of assignment dicts with title, due_date, estimated_minutes, status
            
        Returns:
            JSON string of APL document (for Echo Show)
        """
        items = []
        for assignment in assignments:
            status_icon = "✓" if assignment.get("status") == "completed" else "○"
            items.append({
                "type": "Container",
                "direction": "row",
                "items": [
                    {
                        "type": "Text",
                        "text": status_icon,
                        "fontSize": "24dp",
                        "color": "#2196F3",
                        "width": "40dp"
                    },
                    {
                        "type": "Container",
                        "grow": 1,
                        "items": [
                            {
                                "type": "Text",
                                "text": assignment.get("title", "Untitled"),
                                "fontSize": "18dp",
                                "weight": "bold",
                                "color": "#212121"
                            },
                            {
                                "type": "Text",
                                "text": f"{assignment.get('class_name', '')} • {assignment.get('estimated_minutes', 0)} min • Due {assignment.get('due_date', '')}",
                                "fontSize": "12dp",
                                "color": "#757575"
                            }
                        ]
                    }
                ],
                "spacing": "medium",
                "paddingBottom": "12dp"
            })
        
        apl_doc = {
            "type": "APL",
            "version": "2022.2",
            "theme": "dark",
            "mainTemplate": {
                "parameters": ["payload"],
                "items": [
                    {
                        "type": "Container",
                        "width": "100%",
                        "height": "100%",
                        "direction": "column",
                        "items": [
                            {
                                "type": "Text",
                                "text": "Today's Plan",
                                "fontSize": "32dp",
                                "weight": "bold",
                                "color": "#1976D2",
                                "paddingBottom": "20dp"
                            },
                            {
                                "type": "ScrollView",
                                "grow": 1,
                                "items": [
                                    {
                                        "type": "Container",
                                        "items": items
                                    }
                                ]
                            }
                        ],
                        "paddingLeft": "20dp",
                        "paddingRight": "20dp",
                        "paddingTop": "20dp",
                        "paddingBottom": "20dp"
                    }
                ]
            }
        }
        
        return json.dumps(apl_doc)
    
    @staticmethod
    def render_pomodoro_timer(subject: str, duration_minutes: int, elapsed_minutes: int) -> str:
        """
        Generate APL document for Pomodoro timer display.
        
        Args:
            subject: Subject being studied
            duration_minutes: Total duration (typically 25)
            elapsed_minutes: Minutes elapsed so far
            
        Returns:
            JSON string of APL document
        """
        remaining = max(0, duration_minutes - elapsed_minutes)
        progress_percent = int((elapsed_minutes / duration_minutes) * 100)
        
        apl_doc = {
            "type": "APL",
            "version": "2022.2",
            "theme": "dark",
            "mainTemplate": {
                "parameters": ["payload"],
                "items": [
                    {
                        "type": "Container",
                        "width": "100%",
                        "height": "100%",
                        "direction": "column",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "items": [
                            {
                                "type": "Text",
                                "text": "Pomodoro Session",
                                "fontSize": "28dp",
                                "weight": "bold",
                                "color": "#FF6B6B",
                                "paddingBottom": "10dp"
                            },
                            {
                                "type": "Text",
                                "text": subject or "Study",
                                "fontSize": "20dp",
                                "color": "#CCCCCC",
                                "paddingBottom": "30dp"
                            },
                            {
                                "type": "Text",
                                "text": f"{remaining}:{elapsed_minutes:02d}",
                                "fontSize": "72dp",
                                "weight": "bold",
                                "color": "#4CAF50",
                                "fontFamily": "monospace"
                            },
                            {
                                "type": "Text",
                                "text": f"{progress_percent}% complete",
                                "fontSize": "14dp",
                                "color": "#999999",
                                "paddingTop": "20dp"
                            }
                        ]
                    }
                ]
            }
        }
        
        return json.dumps(apl_doc)
    
    @staticmethod
    def render_quiz_question(question_text: str, question_number: int, total_questions: int) -> str:
        """
        Generate APL document for quiz question display.
        
        Args:
            question_text: The question prompt
            question_number: Current question number
            total_questions: Total questions in this quiz session
            
        Returns:
            JSON string of APL document
        """
        apl_doc = {
            "type": "APL",
            "version": "2022.2",
            "theme": "dark",
            "mainTemplate": {
                "parameters": ["payload"],
                "items": [
                    {
                        "type": "Container",
                        "width": "100%",
                        "height": "100%",
                        "direction": "column",
                        "paddingLeft": "20dp",
                        "paddingRight": "20dp",
                        "paddingTop": "30dp",
                        "paddingBottom": "30dp",
                        "items": [
                            {
                                "type": "Text",
                                "text": f"Question {question_number} of {total_questions}",
                                "fontSize": "14dp",
                                "color": "#FF9800",
                                "paddingBottom": "20dp"
                            },
                            {
                                "type": "Container",
                                "grow": 1,
                                "alignItems": "center",
                                "justifyContent": "center",
                                "items": [
                                    {
                                        "type": "Text",
                                        "text": question_text,
                                        "fontSize": "24dp",
                                        "weight": "bold",
                                        "color": "#FFFFFF",
                                        "textAlign": "center",
                                        "textAlignVertical": "center"
                                    }
                                ]
                            },
                            {
                                "type": "Text",
                                "text": "Say your answer when ready",
                                "fontSize": "14dp",
                                "color": "#BBBBBB",
                                "textAlign": "center",
                                "paddingTop": "20dp"
                            }
                        ]
                    }
                ]
            }
        }
        
        return json.dumps(apl_doc)
    
    @staticmethod
    def render_end_of_day_recap(recap_data: Dict[str, Any]) -> str:
        """
        Generate APL document for end-of-day recap display.
        
        Args:
            recap_data: Dict with pomodoros_count, assignments_completed, total_study_minutes
            
        Returns:
            JSON string of APL document
        """
        pomodoros = recap_data.get("pomodoros_count", 0)
        completed = recap_data.get("assignments_completed", 0)
        total_minutes = recap_data.get("total_study_minutes", 0)
        
        apl_doc = {
            "type": "APL",
            "version": "2022.2",
            "theme": "dark",
            "mainTemplate": {
                "parameters": ["payload"],
                "items": [
                    {
                        "type": "Container",
                        "width": "100%",
                        "height": "100%",
                        "direction": "column",
                        "paddingLeft": "20dp",
                        "paddingRight": "20dp",
                        "paddingTop": "30dp",
                        "paddingBottom": "30dp",
                        "alignItems": "center",
                        "items": [
                            {
                                "type": "Text",
                                "text": "Day Summary",
                                "fontSize": "32dp",
                                "weight": "bold",
                                "color": "#4CAF50",
                                "paddingBottom": "30dp"
                            },
                            {
                                "type": "Container",
                                "width": "80%",
                                "direction": "column",
                                "items": [
                                    APLHelper._stat_row(f"🍅 Pomodoros", str(pomodoros)),
                                    APLHelper._stat_row(f"✓ Completed", str(completed)),
                                    APLHelper._stat_row(f"⏱ Study Time", f"{total_minutes} min")
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        return json.dumps(apl_doc)
    
    @staticmethod
    def _stat_row(label: str, value: str) -> Dict[str, Any]:
        """Helper to create a statistic row for recap."""
        return {
            "type": "Container",
            "direction": "row",
            "justifyContent": "space-between",
            "paddingBottom": "16dp",
            "items": [
                {
                    "type": "Text",
                    "text": label,
                    "fontSize": "18dp",
                    "color": "#BBBBBB"
                },
                {
                    "type": "Text",
                    "text": value,
                    "fontSize": "18dp",
                    "weight": "bold",
                    "color": "#00BCD4"
                }
            ]
        }
    
    @staticmethod
    def add_apl_to_response(response_builder, apl_document: str) -> None:
        """
        Add APL document to response builder if device supports it.
        
        Args:
            response_builder: Alexa response builder
            apl_document: JSON string of APL document
        """
        try:
            response_builder.add_directive({
                "type": "Alexa.Presentation.APL.RenderDocument",
                "document": json.loads(apl_document)
            })
        except Exception as e:
            # Silently fail if APL not supported; voice response will be used
            pass
