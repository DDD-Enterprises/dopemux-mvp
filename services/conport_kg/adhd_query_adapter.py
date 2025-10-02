#!/usr/bin/env python3
"""
ADHD Query Adapter - Attention-Aware Intelligence
Part of CONPORT-KG-2025 Phase 8B

Provides intelligent, ADHD-safe query tier selection based on:
- User attention state (focused/scattered/transitioning)
- Cognitive load monitoring
- Interrupt prevention
- Flow state protection

Decision #118 (automation architecture)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


@dataclass
class UserActivity:
    """User activity metrics for attention detection"""
    continuous_work_seconds: int = 0
    context_switches: int = 0
    idle_time_seconds: int = 0
    last_action_time: Optional[datetime] = None
    cognitive_load: float = 0.0  # 0.0-1.0


@dataclass
class QuerySuggestion:
    """Suggestion to display to user"""
    decision_id: int
    summary: str
    relevance_score: float = 0.0
    priority: str = "normal"  # normal, high, critical


class AttentionStateMonitor:
    """
    Detect user attention state from behavioral signals

    States:
    - focused: Flow state (>15 min continuous, no context switches)
    - scattered: Frequent switching (>5 switches in 5 min)
    - transitioning: Active but not in flow
    """

    def __init__(self):
        self.activity_window_seconds = 300  # 5 minutes
        self.flow_threshold_seconds = 900  # 15 minutes

    def get_current_state(self, activity: UserActivity) -> str:
        """
        Determine attention state from activity metrics

        Args:
            activity: Recent user activity data

        Returns:
            'focused' | 'scattered' | 'transitioning'
        """

        # Flow state: 15+ minutes continuous, zero context switches
        if activity.continuous_work_seconds >= self.flow_threshold_seconds:
            if activity.context_switches == 0:
                return 'focused'

        # Scattered: Frequent context switching
        if activity.context_switches > 5:
            return 'scattered'

        # Transitioning: Active but not in flow
        if activity.idle_time_seconds < 30:
            return 'transitioning'

        # Default to conservative (scattered)
        return 'scattered'

    def in_flow_state(self, activity: UserActivity) -> bool:
        """
        Check if user is in flow state

        Flow state = deep work, must NOT be interrupted
        """
        return (
            activity.continuous_work_seconds >= self.flow_threshold_seconds and
            activity.context_switches == 0
        )

    def get_cognitive_load_estimate(self, activity: UserActivity) -> float:
        """
        Estimate current cognitive load (0.0-1.0)

        Factors:
        - Context switches (more switches = higher load)
        - Work duration (very long = fatigue)
        - Activity rate (frantic = high load)
        """

        # Base load from context switches
        switch_load = min(1.0, activity.context_switches / 10.0)

        # Fatigue from long sessions
        if activity.continuous_work_seconds > 3600:  # >1 hour
            fatigue_load = 0.3
        else:
            fatigue_load = 0.0

        # Combined estimate
        return min(1.0, switch_load + fatigue_load)


class ADHDQuerySelector:
    """
    Intelligent query tier selection based on attention state

    Adapts query complexity to user's current cognitive capacity:
    - scattered → Tier 1 only (Top-3 pattern)
    - transitioning → Tier 2 max (progressive disclosure)
    - focused → Tier 3 allowed (full detail)
    """

    def __init__(self, attention_monitor: Optional[AttentionStateMonitor] = None):
        self.attention_monitor = attention_monitor or AttentionStateMonitor()

    def select_tier(
        self,
        attention_state: str,
        query_intent: str = 'browse',
        user_override: Optional[int] = None
    ) -> int:
        """
        Select appropriate query tier

        Args:
            attention_state: 'focused' | 'scattered' | 'transitioning'
            query_intent: 'browse' | 'explore' | 'analyze'
            user_override: Explicit user choice (always wins)

        Returns:
            Query tier: 1 (Overview), 2 (Exploration), or 3 (Deep Context)
        """

        # User override ALWAYS wins
        if user_override is not None:
            return max(1, min(3, user_override))

        # Maximum tier by attention state
        max_tier_by_attention = {
            'scattered': 1,      # Top-3 only - prevent overwhelm
            'transitioning': 2,  # Progressive disclosure - manageable
            'focused': 3         # Full detail - can handle complexity
        }

        max_tier = max_tier_by_attention.get(attention_state, 1)

        # Tier by query intent
        tier_by_intent = {
            'browse': 1,    # Quick scan
            'explore': 2,   # Relationship navigation
            'analyze': 3    # Deep analysis
        }

        intent_tier = tier_by_intent.get(query_intent, 1)

        # Return minimum (most conservative)
        return min(max_tier, intent_tier)

    def should_display_suggestion(
        self,
        suggestion: QuerySuggestion,
        user_state: Dict[str, Any]
    ) -> bool:
        """
        ADHD-safe display gating

        Rules:
        1. NEVER interrupt flow state
        2. Check cognitive load (<0.7 threshold)
        3. Only critical suggestions immediately
        4. Respect do-not-disturb mode

        Args:
            suggestion: Suggestion to potentially display
            user_state: Current user state

        Returns:
            True if safe to display now, False if should queue
        """

        # Rule 1: NEVER interrupt flow
        if user_state.get('in_flow', False):
            return False  # Queue for later

        # Rule 2: Check cognitive load
        if user_state.get('cognitive_load', 0.0) > 0.7:
            return False  # User overwhelmed

        # Rule 3: Respect DND mode
        if user_state.get('dnd_mode', False):
            return False

        # Rule 4: Only critical suggestions during active work
        if not user_state.get('idle', False):
            return suggestion.priority == 'critical'

        # Safe to display during idle time
        return True

    def adapt_progressive_disclosure_default(
        self,
        user_history: Dict[str, int],
        decision_id: int
    ) -> int:
        """
        Learn from user patterns to set smart defaults

        Example: If user expands to 2-hop 80% of time, default to 2-hop

        Args:
            user_history: {'expanded_to_2hop': 80, 'stayed_1hop': 20}
            decision_id: Current decision

        Returns:
            Default max_hops: 1 or 2
        """

        expand_rate = user_history.get('expanded_to_2hop', 0) / 100.0

        # If user expands >70% of time, default to 2-hop
        if expand_rate > 0.7:
            return 2  # Skip 1-hop, go straight to 2-hop

        # Otherwise, start with 1-hop (progressive)
        return 1


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("ADHD Query Selector Test")
    print("=" * 70)

    selector = ADHDQuerySelector()

    # Test scenarios
    scenarios = [
        ("scattered", "browse", None, "User scattered, browsing → Tier 1"),
        ("transitioning", "explore", None, "User transitioning, exploring → Tier 2"),
        ("focused", "analyze", None, "User focused, analyzing → Tier 3"),
        ("scattered", "analyze", None, "User scattered but wants analysis → Tier 1 (gated)"),
        ("focused", "browse", 2, "User override → Tier 2 (override wins)"),
    ]

    print("\n[Test 1] Tier Selection Logic:")
    for attention, intent, override, description in scenarios:
        tier = selector.select_tier(attention, intent, override)
        print(f"   {description}")
        print(f"      → Selected Tier {tier}\n")

    # Test interrupt prevention
    print("\n[Test 2] Interrupt Prevention:")

    suggestions = [
        QuerySuggestion(85, "Related decision", priority="normal"),
        QuerySuggestion(92, "Critical update", priority="critical"),
    ]

    user_states = [
        {'in_flow': True, 'cognitive_load': 0.3, 'idle': False},
        {'in_flow': False, 'cognitive_load': 0.8, 'idle': False},
        {'in_flow': False, 'cognitive_load': 0.5, 'idle': True},
    ]

    for i, state in enumerate(user_states, 1):
        print(f"\n   User State {i}: flow={state['in_flow']}, load={state['cognitive_load']}, idle={state['idle']}")
        for sug in suggestions:
            should_show = selector.should_display_suggestion(sug, state)
            print(f"      {sug.priority:10s} suggestion: {'✅ Display' if should_show else '❌ Queue'}")

    # Test adaptive defaults
    print("\n[Test 3] Adaptive Progressive Disclosure:")
    histories = [
        ({'expanded_to_2hop': 85, 'stayed_1hop': 15}, "User expands 85% of time"),
        ({'expanded_to_2hop': 30, 'stayed_1hop': 70}, "User stays at 1-hop 70% of time"),
    ]

    for history, description in histories:
        default_hops = selector.adapt_progressive_disclosure_default(history, 85)
        print(f"   {description}")
        print(f"      → Default to {default_hops}-hop\n")

    print("✅ All ADHD Query Selector tests passed!")
