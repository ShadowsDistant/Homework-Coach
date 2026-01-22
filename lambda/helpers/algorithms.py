"""
Core algorithms for Homework Coach skill.

Implements:
- Daily plan generation (prioritization logic)
- Pomodoro flow management
- Spaced repetition (SM-2) scheduler
- End-of-day recap and rollover
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import json


class PlanGenerator:
    """Generate daily prioritized assignment list."""
    
    @staticmethod
    def generate_daily_plan(assignments: List[Dict[str, Any]], today: str) -> List[Dict[str, Any]]:
        """
        Generate prioritized assignment list for today.
        
        Args:
            assignments: List of assignment dicts with due_date, estimated_minutes, status
            today: Current date in YYYY-MM-DD format
            
        Returns:
            List of (assignment_id, rank, reason) sorted by priority
            
        Prioritization rules (in order):
            1. Overdue assignments (due_date < today)
            2. Due today (due_date == today)
            3. Due soon (due_date within 3 days)
            4. Sorted by estimated_minutes (shortest first, within same due-date tier)
        """
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        active_assignments = [a for a in assignments if a.get("status") != "completed"]
        
        def sort_key(assignment: Dict[str, Any]) -> Tuple[int, int, str]:
            due_date_str = assignment.get("due_date")
            due_dt = datetime.strptime(due_date_str, "%Y-%m-%d")
            days_until_due = (due_dt - today_dt).days
            estimated = assignment.get("estimated_minutes", 0)
            
            # Tier 0: overdue (days_until_due < 0)
            # Tier 1: due today (days_until_due == 0)
            # Tier 2: due within 3 days (0 < days_until_due <= 3)
            # Tier 3: due after 3 days (days_until_due > 3)
            
            if days_until_due < 0:
                tier = 0
            elif days_until_due == 0:
                tier = 1
            elif days_until_due <= 3:
                tier = 2
            else:
                tier = 3
            
            return (tier, estimated, due_date_str)
        
        sorted_assignments = sorted(active_assignments, key=sort_key)
        
        plan = []
        for rank, assignment in enumerate(sorted_assignments, start=1):
            due_dt = datetime.strptime(assignment.get("due_date"), "%Y-%m-%d")
            days_until = (due_dt - today_dt).days
            
            if days_until < 0:
                reason = "Overdue"
            elif days_until == 0:
                reason = "Due today"
            elif days_until <= 3:
                reason = f"Due in {days_until} days"
            else:
                reason = f"Due {assignment.get('due_date')}"
            
            reason += f" ({assignment.get('estimated_minutes')} min)"
            
            plan.append({
                "assignment_id": assignment.get("assignment_id"),
                "rank": rank,
                "reason": reason
            })
        
        return plan


class PomodoroManager:
    """Manage Pomodoro session state and logic."""
    
    STANDARD_DURATION = 25  # minutes
    
    @staticmethod
    def start_session(subject: str, duration_minutes: int = STANDARD_DURATION) -> Dict[str, Any]:
        """Initialize a new Pomodoro session."""
        return {
            "subject": subject,
            "start_time": datetime.utcnow().isoformat(),
            "duration_minutes": duration_minutes,
            "elapsed_minutes": 0,
            "is_paused": False,
            "paused_at": None,
            "interruptions": 0
        }
    
    @staticmethod
    def pause_session(session: Dict[str, Any]) -> Dict[str, Any]:
        """Pause an active session."""
        if session.get("is_paused"):
            return session  # Already paused
        
        session["is_paused"] = True
        session["paused_at"] = datetime.utcnow().isoformat()
        return session
    
    @staticmethod
    def resume_session(session: Dict[str, Any]) -> Dict[str, Any]:
        """Resume a paused session."""
        if not session.get("is_paused"):
            return session  # Not paused
        
        if session.get("paused_at"):
            paused_dt = datetime.fromisoformat(session["paused_at"])
            now_dt = datetime.utcnow()
            paused_minutes = (now_dt - paused_dt).total_seconds() / 60
            session["elapsed_minutes"] += paused_minutes
            session["interruptions"] += 1
        
        session["is_paused"] = False
        session["paused_at"] = None
        return session
    
    @staticmethod
    def get_remaining_minutes(session: Dict[str, Any]) -> int:
        """Get remaining minutes in session."""
        start_dt = datetime.fromisoformat(session.get("start_time"))
        now_dt = datetime.utcnow()
        elapsed = (now_dt - start_dt).total_seconds() / 60
        
        if session.get("is_paused"):
            elapsed -= (now_dt - datetime.fromisoformat(session.get("paused_at"))).total_seconds() / 60
        
        remaining = session.get("duration_minutes") - elapsed
        return max(0, int(remaining))
    
    @staticmethod
    def extend_session(session: Dict[str, Any], additional_minutes: int) -> Dict[str, Any]:
        """Extend session duration."""
        session["duration_minutes"] += additional_minutes
        return session


class SpacedRepetitionScheduler:
    """Implement SM-2 spaced repetition algorithm."""
    
    @staticmethod
    def calculate_next_interval(
        ease_factor: float,
        interval: int,
        repetitions: int,
        result: str
    ) -> Tuple[int, float, int]:
        """
        SM-2 algorithm: Calculate next interval, ease factor, and repetitions.
        
        Args:
            ease_factor: Current ease factor (1.3 - 2.5+, typically ~2.5)
            interval: Current interval in days
            repetitions: Count of successful repetitions
            result: "pass", "fail", or "partial"
            
        Returns:
            (next_interval_days, new_ease_factor, new_repetitions)
            
        SM-2 Rules:
        - Result 0-2: Incorrect (fail) → reset interval to 1, decrease ease factor
        - Result 2-4: Correct but hard → increase interval
        - Result 4-5: Correct and easy → increase interval more
        
        Mapping:
        - "fail" or "partial" = response grade 2 (requires immediate relearning)
        - "pass" = response grade 4 (good, middle range)
        """
        # Determine quality of response (0-5 scale per SM-2)
        if result == "fail" or result == "partial":
            quality = 2  # Failed
        else:  # "pass"
            quality = 4  # Perfect/Good
        
        # Update ease factor (never below 1.3)
        new_ease = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        
        # Update interval and repetitions
        if quality < 3:
            # Failed: reset to 1 day
            new_interval = 1
            new_repetitions = 0
        else:
            # Passed
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 3
            else:
                new_interval = int(interval * new_ease)
            
            new_repetitions = repetitions + 1
        
        return new_interval, new_ease, new_repetitions
    
    @staticmethod
    def get_items_due_for_review(sr_states: List[Dict[str, Any]], today: str) -> List[str]:
        """
        Get quiz item IDs that are due for review today.
        
        Args:
            sr_states: List of spaced-repetition state dicts
            today: Current date in YYYY-MM-DD format
            
        Returns:
            List of item_id that should be reviewed today
        """
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        due_items = []
        
        for state in sr_states:
            next_review = state.get("next_review_date")
            if next_review:
                review_dt = datetime.strptime(next_review, "%Y-%m-%d")
                if review_dt <= today_dt:
                    due_items.append(state.get("item_id"))
        
        return due_items


class EndOfDayRecap:
    """Generate end-of-day summary and rollover logic."""
    
    @staticmethod
    def generate_recap(
        sessions_today: List[Dict[str, Any]],
        assignments_completed_today: List[Dict[str, Any]],
        assignments_incomplete: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate end-of-day recap summary.
        
        Args:
            sessions_today: List of study sessions from today
            assignments_completed_today: Completed assignments
            assignments_incomplete: Assignments still pending
            
        Returns:
            Recap dict with statistics
        """
        total_pomodoros = len([s for s in sessions_today if s.get("session_type") == "pomodoro"])
        total_study_minutes = sum(s.get("duration_minutes", 0) for s in sessions_today)
        
        # Group incomplete by due date
        incomplete_by_due = {}
        for assignment in assignments_incomplete:
            due_date = assignment.get("due_date")
            if due_date not in incomplete_by_due:
                incomplete_by_due[due_date] = []
            incomplete_by_due[due_date].append(assignment)
        
        recap = {
            "study_sessions_count": len(sessions_today),
            "pomodoros_count": total_pomodoros,
            "total_study_minutes": total_study_minutes,
            "assignments_completed": len(assignments_completed_today),
            "assignments_remaining": len(assignments_incomplete),
            "incomplete_by_due_date": incomplete_by_due,
            "motivational_message": EndOfDayRecap._generate_message(total_pomodoros, len(assignments_completed_today))
        }
        
        return recap
    
    @staticmethod
    def _generate_message(pomodoros: int, completed: int) -> str:
        """Generate motivational end-of-day message."""
        if pomodoros == 0:
            return "Consider adding a Pomodoro session tomorrow!"
        elif pomodoros >= 5:
            return f"Incredible focus! {pomodoros} Pomodoros is a major accomplishment!"
        elif completed >= 3:
            return f"Great job getting {completed} assignments done today!"
        else:
            return "Keep building those study habits!"
    
    @staticmethod
    def rollover_incomplete_assignments(
        incomplete_assignments: List[Dict[str, Any]],
        today: str
    ) -> List[Dict[str, Any]]:
        """
        Prepare incomplete assignments for next day (no DB changes, just recommendations).
        
        Returns:
            List of assignments with priority flags for next day
        """
        rollover_list = []
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        
        for assignment in incomplete_assignments:
            due_dt = datetime.strptime(assignment.get("due_date"), "%Y-%m-%d")
            days_until = (due_dt - today_dt).days
            
            priority = "high" if days_until <= 1 else ("medium" if days_until <= 3 else "low")
            
            rollover_list.append({
                "assignment_id": assignment.get("assignment_id"),
                "title": assignment.get("title"),
                "priority": priority,
                "days_until_due": days_until
            })
        
        return rollover_list


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    # Test daily plan generation
    sample_assignments = [
        {
            "assignment_id": "a1",
            "title": "Chapter 5 Review",
            "due_date": "2026-01-20",  # overdue
            "estimated_minutes": 30,
            "status": "not_started"
        },
        {
            "assignment_id": "a2",
            "title": "Essay Draft",
            "due_date": "2026-01-22",  # today
            "estimated_minutes": 60,
            "status": "not_started"
        },
        {
            "assignment_id": "a3",
            "title": "Problem Set",
            "due_date": "2026-01-24",  # 2 days
            "estimated_minutes": 45,
            "status": "not_started"
        },
    ]
    
    plan = PlanGenerator.generate_daily_plan(sample_assignments, "2026-01-22")
    print("Daily Plan:")
    for item in plan:
        print(f"  Rank {item['rank']}: {item['reason']}")
    
    # Test Pomodoro
    session = PomodoroManager.start_session("Biology", 25)
    print(f"\nPomodoro Session Started: {session['subject']} for {session['duration_minutes']} min")
    
    # Test SR scheduling
    next_interval, new_ease, new_reps = SpacedRepetitionScheduler.calculate_next_interval(
        ease_factor=2.5,
        interval=1,
        repetitions=0,
        result="pass"
    )
    print(f"\nSR Update (after pass): interval={next_interval}, ease={new_ease:.2f}, reps={new_reps}")
