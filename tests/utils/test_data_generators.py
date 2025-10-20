#!/usr/bin/env python3
"""
Test Data Generators
====================

Factory functions for generating realistic test data across Architecture 3.0 components.

**ADHD-Aware Data Generation**:
- Tasks with varying complexity levels (0.0-1.0)
- ADHD states with realistic energy/attention patterns
- Time-based scenarios (morning energy spike, afternoon dip, hyperfocus)
- Event sequences with proper timestamps
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random
import uuid


class TaskGenerator:
    """Generate realistic task data for testing."""

    TASK_TITLES = [
        "Implement authentication middleware",
        "Fix memory leak in session handler",
        "Write unit tests for ConPort adapter",
        "Refactor database connection pooling",
        "Update API documentation",
        "Deploy to staging environment",
        "Review pull request #123",
        "Optimize Redis caching strategy",
        "Debug production error logs",
        "Plan Architecture 4.0 features"
    ]

    TASK_DESCRIPTIONS = [
        "Add JWT token validation with refresh logic",
        "Profile memory usage and identify leak source",
        "Achieve 80%+ test coverage on critical paths",
        "Implement connection pooling with health checks",
        "Generate API docs from OpenAPI spec",
        "Deploy latest changes to staging and validate",
        "Code review focusing on security and performance",
        "Implement Redis caching with 60-second TTL",
        "Analyze error patterns and fix root causes",
        "Research and document next-phase features"
    ]

    PRIORITIES = ["critical", "high", "medium", "low"]
    STATUSES = ["TODO", "IN_PROGRESS", "BLOCKED", "DONE"]
    TAGS = [
        ["backend", "security"],
        ["performance", "optimization"],
        ["testing", "quality"],
        ["infrastructure", "devops"],
        ["documentation"],
        ["deployment", "staging"],
        ["code-review", "collaboration"],
        ["caching", "redis"],
        ["debugging", "production"],
        ["planning", "architecture"]
    ]

    @staticmethod
    def generate_task(
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        complexity: Optional[float] = None,
        include_dependencies: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a realistic task with ADHD metadata.

        Args:
            task_id: Override task ID (default: random UUID)
            status: Override status (default: random)
            priority: Override priority (default: random)
            complexity: Override complexity 0.0-1.0 (default: random based on title)
            include_dependencies: Add dependency list
        """
        idx = random.randint(0, len(TaskGenerator.TASK_TITLES) - 1)

        # Generate complexity based on task type if not provided
        if complexity is None:
            complexity = TaskGenerator._calculate_complexity(TaskGenerator.TASK_TITLES[idx])

        # Estimate duration based on complexity (10-180 minutes)
        estimated_duration = int(20 + (complexity * 160))

        task = {
            "task_id": task_id or f"task-{uuid.uuid4().hex[:8]}",
            "title": TaskGenerator.TASK_TITLES[idx],
            "description": TaskGenerator.TASK_DESCRIPTIONS[idx],
            "status": status or random.choice(TaskGenerator.STATUSES),
            "priority": priority or random.choice(TaskGenerator.PRIORITIES),
            "complexity": round(complexity, 2),
            "estimated_duration": estimated_duration,
            "progress": 0.0 if status == "TODO" else random.uniform(0.0, 1.0),
            "tags": TaskGenerator.TAGS[idx],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if include_dependencies:
            # 30% chance of having dependencies
            if random.random() < 0.3:
                num_deps = random.randint(1, 3)
                task["dependencies"] = [f"task-{uuid.uuid4().hex[:8]}" for _ in range(num_deps)]
            else:
                task["dependencies"] = []

        return task

    @staticmethod
    def _calculate_complexity(title: str) -> float:
        """Calculate task complexity based on title keywords."""
        # Simple heuristic: certain keywords indicate higher complexity
        high_complexity_keywords = ["implement", "refactor", "optimize", "debug", "architecture"]
        medium_complexity_keywords = ["fix", "update", "review", "plan"]
        low_complexity_keywords = ["write", "deploy", "document"]

        title_lower = title.lower()

        if any(kw in title_lower for kw in high_complexity_keywords):
            return random.uniform(0.6, 0.9)
        elif any(kw in title_lower for kw in medium_complexity_keywords):
            return random.uniform(0.3, 0.6)
        else:
            return random.uniform(0.1, 0.3)

    @staticmethod
    def generate_task_list(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Generate a list of tasks."""
        return [TaskGenerator.generate_task(**kwargs) for _ in range(count)]


class ADHDStateGenerator:
    """Generate realistic ADHD state data with time-aware patterns."""

    ENERGY_LEVELS = ["very_low", "low", "medium", "high", "hyperfocus"]
    ATTENTION_LEVELS = ["scattered", "transitioning", "focused", "hyperfocused"]

    # Time-based patterns (hour of day -> typical energy/attention)
    TIME_PATTERNS = {
        # Morning (6-9): Rising energy
        range(6, 9): {"energy": ["low", "medium"], "attention": ["transitioning", "focused"]},
        # Peak morning (9-12): High energy
        range(9, 12): {"energy": ["medium", "high"], "attention": ["focused", "hyperfocused"]},
        # Afternoon dip (12-15): Lower energy
        range(12, 15): {"energy": ["low", "medium"], "attention": ["scattered", "transitioning"]},
        # Afternoon recovery (15-18): Rising energy
        range(15, 18): {"energy": ["medium", "high"], "attention": ["focused"]},
        # Evening (18-21): Variable
        range(18, 21): {"energy": ["medium", "low"], "attention": ["transitioning", "focused"]},
        # Late night (21-24): Declining or hyperfocus
        range(21, 24): {"energy": ["low", "hyperfocus"], "attention": ["scattered", "hyperfocused"]}
    }

    @staticmethod
    def generate_state(
        timestamp: Optional[datetime] = None,
        energy_level: Optional[str] = None,
        attention_level: Optional[str] = None,
        time_since_break: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate ADHD state with realistic time-based patterns.

        Args:
            timestamp: Time of state measurement (default: now)
            energy_level: Override energy level
            attention_level: Override attention level
            time_since_break: Minutes since last break (default: random 0-90)
        """
        ts = timestamp or datetime.now()
        hour = ts.hour

        # Find matching time pattern
        time_pattern = None
        for hour_range, pattern in ADHDStateGenerator.TIME_PATTERNS.items():
            if hour in hour_range:
                time_pattern = pattern
                break

        # Use time-based defaults or random if no pattern
        if time_pattern:
            energy = energy_level or random.choice(time_pattern["energy"])
            attention = attention_level or random.choice(time_pattern["attention"])
        else:
            energy = energy_level or random.choice(ADHDStateGenerator.ENERGY_LEVELS)
            attention = attention_level or random.choice(ADHDStateGenerator.ATTENTION_LEVELS)

        # Calculate time since break
        if time_since_break is None:
            time_since_break = random.randint(0, 90)

        # Recommend break if time exceeds thresholds
        break_recommended = (
            time_since_break > 60 or  # 60+ minutes
            (energy in ["very_low", "low"] and time_since_break > 45) or  # Low energy + 45 min
            (attention == "scattered" and time_since_break > 30)  # Scattered attention + 30 min
        )

        # Session duration correlates with energy/attention
        if energy in ["high", "hyperfocus"] and attention in ["focused", "hyperfocused"]:
            session_duration = random.randint(45, 120)  # Long productive session
        elif energy in ["medium"] and attention in ["focused"]:
            session_duration = random.randint(25, 60)  # Standard session
        else:
            session_duration = random.randint(10, 30)  # Short, interrupted session

        return {
            "energy_level": energy,
            "attention_level": attention,
            "time_since_break": time_since_break,
            "break_recommended": break_recommended,
            "current_session_duration": session_duration,
            "timestamp": ts.isoformat()
        }

    @staticmethod
    def generate_state_sequence(duration_hours: int = 8, interval_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Generate a sequence of ADHD states over time (e.g., full workday).

        Args:
            duration_hours: Total duration in hours
            interval_minutes: Measurement interval in minutes
        """
        states = []
        start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9 AM
        current_time = start_time
        time_since_last_break = 0

        while current_time < start_time + timedelta(hours=duration_hours):
            # Simulate breaks every 60-90 minutes
            if time_since_last_break > random.randint(60, 90):
                time_since_last_break = 0

            state = ADHDStateGenerator.generate_state(
                timestamp=current_time,
                time_since_break=time_since_last_break
            )
            states.append(state)

            current_time += timedelta(minutes=interval_minutes)
            time_since_last_break += interval_minutes

        return states


class EventGenerator:
    """Generate realistic event data for Redis Streams testing."""

    EVENT_TYPES = [
        "task.created",
        "task.updated",
        "task.completed",
        "task.blocked",
        "session.started",
        "session.ended",
        "break.started",
        "break.ended",
        "focus.gained",
        "focus.lost"
    ]

    @staticmethod
    def generate_event(
        event_type: Optional[str] = None,
        task_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        include_data: bool = True
    ) -> Dict[str, Any]:
        """
        Generate event for Redis Streams.

        Args:
            event_type: Override event type
            task_id: Associated task ID
            timestamp: Event timestamp
            include_data: Include event-specific data payload
        """
        ts = timestamp or datetime.now()
        evt_type = event_type or random.choice(EventGenerator.EVENT_TYPES)
        tid = task_id or f"task-{uuid.uuid4().hex[:8]}"

        event = {
            "event_type": evt_type,
            "task_id": tid,
            "timestamp": ts.isoformat(),
            "event_id": f"evt-{uuid.uuid4().hex[:8]}"
        }

        if include_data:
            event["data"] = EventGenerator._generate_event_data(evt_type, tid)

        return event

    @staticmethod
    def _generate_event_data(event_type: str, task_id: str) -> Dict[str, Any]:
        """Generate event-specific data payload."""
        if event_type == "task.created":
            return {
                "title": random.choice(TaskGenerator.TASK_TITLES),
                "priority": random.choice(TaskGenerator.PRIORITIES),
                "status": "TODO"
            }
        elif event_type == "task.updated":
            return {
                "status": random.choice(TaskGenerator.STATUSES),
                "progress": round(random.uniform(0.0, 1.0), 2)
            }
        elif event_type == "task.completed":
            return {
                "status": "DONE",
                "progress": 1.0,
                "completion_time": datetime.now().isoformat()
            }
        elif event_type == "task.blocked":
            return {
                "status": "BLOCKED",
                "blocker": f"Waiting on task-{uuid.uuid4().hex[:8]}"
            }
        elif event_type in ["session.started", "session.ended"]:
            return {
                "session_id": f"session-{uuid.uuid4().hex[:8]}",
                "energy_level": random.choice(ADHDStateGenerator.ENERGY_LEVELS),
                "attention_level": random.choice(ADHDStateGenerator.ATTENTION_LEVELS)
            }
        elif event_type in ["break.started", "break.ended"]:
            return {
                "break_type": random.choice(["short", "long", "pomodoro"]),
                "duration_minutes": random.randint(5, 25)
            }
        elif event_type in ["focus.gained", "focus.lost"]:
            return {
                "focus_duration": random.randint(10, 120),
                "trigger": random.choice(["notification", "distraction", "completion", "natural"])
            }
        else:
            return {}

    @staticmethod
    def generate_event_sequence(count: int = 10, start_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Generate a realistic sequence of events over time."""
        events = []
        current_time = start_time or datetime.now()

        for i in range(count):
            event = EventGenerator.generate_event(timestamp=current_time)
            events.append(event)
            # Events occur every 2-10 minutes
            current_time += timedelta(minutes=random.randint(2, 10))

        return events


class RecommendationGenerator:
    """Generate realistic task recommendations."""

    RECOMMENDATION_REASONS = [
        "Low complexity matches current focus level",
        "High priority task requires immediate attention",
        "Similar to recently completed task",
        "Builds on current momentum",
        "Good follow-up to previous task",
        "Energy level supports complex work",
        "Attention level ideal for detail work",
        "Time available matches estimated duration",
        "No dependencies blocking this task",
        "High impact, low effort opportunity"
    ]

    @staticmethod
    def generate_recommendation(
        task: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate task recommendation with reasoning.

        Args:
            task: Task to recommend (default: generate random)
            confidence: Override confidence score 0.0-1.0
            priority: Override priority rank 1-5
        """
        task_data = task or TaskGenerator.generate_task()

        return {
            "task_id": task_data["task_id"],
            "title": task_data["title"],
            "reason": random.choice(RecommendationGenerator.RECOMMENDATION_REASONS),
            "confidence": confidence or round(random.uniform(0.6, 0.95), 2),
            "priority": priority or random.randint(1, 5),
            "complexity": task_data["complexity"],
            "estimated_duration": task_data["estimated_duration"]
        }

    @staticmethod
    def generate_recommendation_list(count: int = 5) -> List[Dict[str, Any]]:
        """Generate a ranked list of task recommendations."""
        recommendations = []
        for i in range(count):
            rec = RecommendationGenerator.generate_recommendation(priority=i+1)
            recommendations.append(rec)
        return recommendations
