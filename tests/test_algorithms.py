"""
Unit tests for Homework Coach algorithms and helpers.

Tests for:
- Daily plan generation
- Pomodoro management
- Spaced repetition scheduling
- End-of-day recap
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda'))

from helpers.algorithms import (
    PlanGenerator,
    PomodoroManager,
    SpacedRepetitionScheduler,
    EndOfDayRecap
)


class TestPlanGenerator(unittest.TestCase):
    """Tests for daily plan prioritization logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.today = "2026-01-22"
        self.today_dt = datetime.strptime(self.today, "%Y-%m-%d")
    
    def test_overdue_assignment_prioritized(self):
        """Overdue assignments should appear first."""
        assignments = [
            {
                "assignment_id": "a1",
                "title": "Chapter 5 Review",
                "due_date": "2026-01-20",  # Overdue
                "estimated_minutes": 30,
                "status": "not_started"
            },
            {
                "assignment_id": "a2",
                "title": "Essay",
                "due_date": "2026-01-25",  # Future
                "estimated_minutes": 60,
                "status": "not_started"
            }
        ]
        
        plan = PlanGenerator.generate_daily_plan(assignments, self.today)
        
        self.assertEqual(plan[0]["assignment_id"], "a1", "Overdue should be rank 1")
        self.assertIn("Overdue", plan[0]["reason"])
    
    def test_due_today_after_overdue(self):
        """Due today should come after overdue but before future."""
        assignments = [
            {
                "assignment_id": "a1",
                "title": "Due future",
                "due_date": "2026-01-25",
                "estimated_minutes": 30,
                "status": "not_started"
            },
            {
                "assignment_id": "a2",
                "title": "Due today",
                "due_date": "2026-01-22",
                "estimated_minutes": 30,
                "status": "not_started"
            },
            {
                "assignment_id": "a3",
                "title": "Overdue",
                "due_date": "2026-01-20",
                "estimated_minutes": 30,
                "status": "not_started"
            }
        ]
        
        plan = PlanGenerator.generate_daily_plan(assignments, self.today)
        
        self.assertEqual(plan[0]["assignment_id"], "a3")  # Overdue
        self.assertEqual(plan[1]["assignment_id"], "a2")  # Today
        self.assertEqual(plan[2]["assignment_id"], "a1")  # Future
    
    def test_completed_assignments_excluded(self):
        """Completed assignments should not appear in plan."""
        assignments = [
            {
                "assignment_id": "a1",
                "title": "Completed",
                "due_date": "2026-01-22",
                "estimated_minutes": 30,
                "status": "completed"
            },
            {
                "assignment_id": "a2",
                "title": "Not started",
                "due_date": "2026-01-22",
                "estimated_minutes": 30,
                "status": "not_started"
            }
        ]
        
        plan = PlanGenerator.generate_daily_plan(assignments, self.today)
        
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["assignment_id"], "a2")
    
    def test_shorter_duration_prioritized_within_tier(self):
        """Within same due-date tier, shorter durations first."""
        assignments = [
            {
                "assignment_id": "a1",
                "title": "Long",
                "due_date": "2026-01-24",
                "estimated_minutes": 120,
                "status": "not_started"
            },
            {
                "assignment_id": "a2",
                "title": "Short",
                "due_date": "2026-01-24",
                "estimated_minutes": 30,
                "status": "not_started"
            }
        ]
        
        plan = PlanGenerator.generate_daily_plan(assignments, self.today)
        
        self.assertEqual(plan[0]["assignment_id"], "a2", "Short task should come first")


class TestPomodoroManager(unittest.TestCase):
    """Tests for Pomodoro session management."""
    
    def test_start_session(self):
        """Starting session should set correct initial state."""
        session = PomodoroManager.start_session("Biology", 25)
        
        self.assertEqual(session["subject"], "Biology")
        self.assertEqual(session["duration_minutes"], 25)
        self.assertEqual(session["elapsed_minutes"], 0)
        self.assertFalse(session["is_paused"])
        self.assertEqual(session["interruptions"], 0)
    
    def test_pause_and_resume(self):
        """Pausing and resuming should track interruptions."""
        session = PomodoroManager.start_session("Biology", 25)
        
        # Pause
        session = PomodoroManager.pause_session(session)
        self.assertTrue(session["is_paused"])
        
        # Wait a bit (simulated)
        import time
        time.sleep(0.1)
        
        # Resume
        session = PomodoroManager.resume_session(session)
        self.assertFalse(session["is_paused"])
        self.assertEqual(session["interruptions"], 1)
    
    def test_extend_session(self):
        """Extending session should increase duration."""
        session = PomodoroManager.start_session("Biology", 25)
        session = PomodoroManager.extend_session(session, 5)
        
        self.assertEqual(session["duration_minutes"], 30)


class TestSpacedRepetition(unittest.TestCase):
    """Tests for SM-2 spaced repetition algorithm."""
    
    def test_first_pass_creates_3_day_interval(self):
        """First pass should set interval to 3 days (SM-2 rule)."""
        interval, ease, reps = SpacedRepetitionScheduler.calculate_next_interval(
            ease_factor=2.5,
            interval=1,
            repetitions=0,
            result="pass"
        )
        
        self.assertEqual(interval, 3)
        self.assertEqual(reps, 1)
        self.assertGreater(ease, 2.5)
    
    def test_fail_resets_interval(self):
        """Failing should reset interval to 1 and decrease ease factor."""
        interval, ease, reps = SpacedRepetitionScheduler.calculate_next_interval(
            ease_factor=2.5,
            interval=10,
            repetitions=5,
            result="fail"
        )
        
        self.assertEqual(interval, 1, "Interval should reset to 1 on fail")
        self.assertEqual(reps, 0, "Repetitions should reset to 0 on fail")
        self.assertLess(ease, 2.5, "Ease factor should decrease")
    
    def test_ease_factor_minimum(self):
        """Ease factor should never drop below 1.3."""
        interval, ease, reps = SpacedRepetitionScheduler.calculate_next_interval(
            ease_factor=1.3,
            interval=1,
            repetitions=0,
            result="fail"
        )
        
        self.assertGreaterEqual(ease, 1.3, "Ease factor minimum is 1.3")
    
    def test_items_due_for_review(self):
        """Should identify items due for review on given date."""
        today = "2026-01-22"
        sr_states = [
            {
                "item_id": "i1",
                "next_review_date": "2026-01-22",  # Today
                "subject": "Biology"
            },
            {
                "item_id": "i2",
                "next_review_date": "2026-01-25",  # Future
                "subject": "Biology"
            },
            {
                "item_id": "i3",
                "next_review_date": "2026-01-20",  # Past
                "subject": "History"
            }
        ]
        
        due = SpacedRepetitionScheduler.get_items_due_for_review(sr_states, today)
        
        self.assertIn("i1", due)
        self.assertIn("i3", due)
        self.assertNotIn("i2", due)


class TestEndOfDayRecap(unittest.TestCase):
    """Tests for end-of-day recap generation."""
    
    def test_recap_calculation(self):
        """Recap should correctly count sessions and assignments."""
        sessions = [
            {"session_type": "pomodoro", "duration_minutes": 25, "completed": True},
            {"session_type": "pomodoro", "duration_minutes": 25, "completed": True},
            {"session_type": "freeform", "duration_minutes": 30, "completed": True}
        ]
        
        completed = [
            {"assignment_id": "a1", "title": "Task 1", "due_date": "2026-01-22"},
            {"assignment_id": "a2", "title": "Task 2", "due_date": "2026-01-22"}
        ]
        
        incomplete = [
            {"assignment_id": "a3", "title": "Task 3", "due_date": "2026-01-23"}
        ]
        
        recap = EndOfDayRecap.generate_recap(sessions, completed, incomplete)
        
        self.assertEqual(recap["pomodoros_count"], 2)
        self.assertEqual(recap["assignments_completed"], 2)
        self.assertEqual(recap["total_study_minutes"], 80)
        self.assertEqual(recap["assignments_remaining"], 1)
    
    def test_rollover_incomplete_assignments(self):
        """Incomplete assignments should be marked for rollover."""
        today = "2026-01-22"
        incomplete = [
            {
                "assignment_id": "a1",
                "title": "Due tomorrow",
                "due_date": "2026-01-23"
            },
            {
                "assignment_id": "a2",
                "title": "Due in week",
                "due_date": "2026-01-29"
            }
        ]
        
        rollover = EndOfDayRecap.rollover_incomplete_assignments(incomplete, today)
        
        # Due tomorrow should be high priority
        tomorrow_item = [r for r in rollover if r["assignment_id"] == "a1"][0]
        self.assertEqual(tomorrow_item["priority"], "high")
        
        # Due in week should be low priority
        week_item = [r for r in rollover if r["assignment_id"] == "a2"][0]
        self.assertEqual(week_item["priority"], "low")


class TestIntegration(unittest.TestCase):
    """Integration tests for multi-component flows."""
    
    def test_daily_flow_scenario(self):
        """Test complete daily workflow: plan → Pomodoro → recap."""
        today = "2026-01-22"
        
        # 1. Generate daily plan
        assignments = [
            {
                "assignment_id": "a1",
                "title": "Bio quiz",
                "due_date": "2026-01-22",
                "estimated_minutes": 20,
                "status": "not_started"
            },
            {
                "assignment_id": "a2",
                "title": "History essay",
                "due_date": "2026-01-23",
                "estimated_minutes": 60,
                "status": "not_started"
            }
        ]
        
        plan = PlanGenerator.generate_daily_plan(assignments, today)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["assignment_id"], "a1", "Bio quiz due today should be first")
        
        # 2. Start Pomodoro
        session = PomodoroManager.start_session("Biology", 25)
        self.assertFalse(session["is_paused"])
        
        # 3. Generate end-of-day recap
        completed = [assignments[0]]
        incomplete = [assignments[1]]
        sessions = [session]
        
        recap = EndOfDayRecap.generate_recap(sessions, completed, incomplete)
        self.assertEqual(recap["assignments_completed"], 1)
        self.assertEqual(recap["assignments_remaining"], 1)


if __name__ == "__main__":
    unittest.main()
