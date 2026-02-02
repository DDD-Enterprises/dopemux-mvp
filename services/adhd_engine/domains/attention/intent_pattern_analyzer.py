"""
Intent Pattern Analyzer

Analyzes patterns in user prompts to detect ADHD-relevant behaviors:
- Repeated context switches
- Procrastination signals (research without action)
- Task switching carousel
- Feature request accumulation without completion

Runs as part of the EventListener event handling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class IntentSignal:
    """Individual intent signal from prompt analysis."""
    signal_type: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PatternMatch:
    """Detected pattern match."""
    pattern_type: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str]
    recommendation: str
    severity: str = "medium"  # low, medium, high


class IntentPatternAnalyzer:
    """
    Analyze patterns across multiple prompts/intents to detect ADHD-relevant behaviors.
    
    Patterns detected:
    - CONTEXT_SWITCH_CAROUSEL: Rapid switching between unrelated topics
    - RESEARCH_RABBIT_HOLE: Many research prompts without output
    - FEATURE_ACCUMULATION: Many new features requested without completion
    - SCOPE_CREEP: Expanding scope mid-task
    - PERFECTIONISM_LOOP: Repeated refinement without shipping
    """
    
    def __init__(self, window_minutes: int = 30, min_signals: int = 5):
        """
        Initialize pattern analyzer.
        
        Args:
            window_minutes: Analysis window in minutes
            min_signals: Minimum signals before pattern detection
        """
        self.window_minutes = window_minutes
        self.min_signals = min_signals
        
        # Rolling buffer of intents
        self._intents: List[Dict[str, Any]] = []
        
        # Pattern thresholds
        self._thresholds = {
            "context_switches_high": 5,      # 5 switches in 30 min = high
            "context_switches_critical": 8,  # 8 switches = critical
            "research_without_output": 10,   # 10 research prompts, 0 outputs
            "new_features_threshold": 4,     # 4 new features without completion
            "same_topic_refinements": 6,     # 6 refinements = perfectionism
        }
    
    def add_intent(self, intent: Dict[str, Any]) -> List[PatternMatch]:
        """
        Add a new intent and check for patterns.
        
        Args:
            intent: Intent data from prompt analysis
            
        Returns:
            List of detected patterns
        """
        # Add timestamp if missing
        if "timestamp" not in intent:
            intent["timestamp"] = datetime.now().isoformat()
        
        self._intents.append(intent)
        
        # Prune old intents
        self._prune_old_intents()
        
        # Check for patterns if we have enough data
        if len(self._intents) < self.min_signals:
            return []
        
        return self._detect_patterns()
    
    def _prune_old_intents(self):
        """Remove intents older than window."""
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        
        self._intents = [
            i for i in self._intents
            if self._parse_timestamp(i.get("timestamp")) > cutoff
        ]
    
    def _parse_timestamp(self, ts) -> datetime:
        """Parse timestamp string or return datetime."""
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now()
    
    def _detect_patterns(self) -> List[PatternMatch]:
        """Detect all patterns in current window."""
        patterns = []
        
        # Check each pattern type
        pattern = self._check_context_switch_carousel()
        if pattern:
            patterns.append(pattern)
        
        pattern = self._check_research_rabbit_hole()
        if pattern:
            patterns.append(pattern)
        
        pattern = self._check_feature_accumulation()
        if pattern:
            patterns.append(pattern)
        
        pattern = self._check_perfectionism_loop()
        if pattern:
            patterns.append(pattern)
        
        return patterns
    
    def _check_context_switch_carousel(self) -> Optional[PatternMatch]:
        """Detect rapid context switching between topics."""
        signals = [i.get("signals", {}) for i in self._intents]
        
        context_switches = sum(
            1 for s in signals
            if s.get("is_context_switch", False)
        )
        
        if context_switches >= self._thresholds["context_switches_critical"]:
            return PatternMatch(
                pattern_type="context_switch_carousel",
                confidence=0.9,
                evidence=[
                    f"{context_switches} context switches in {self.window_minutes} min",
                    "Rapid topic jumping detected"
                ],
                recommendation="Take a 10-minute break and pick ONE task to focus on",
                severity="high"
            )
        elif context_switches >= self._thresholds["context_switches_high"]:
            return PatternMatch(
                pattern_type="context_switch_carousel",
                confidence=0.7,
                evidence=[f"{context_switches} context switches detected"],
                recommendation="Attention is fragmented. Consider a short reset.",
                severity="medium"
            )
        
        return None
    
    def _check_research_rabbit_hole(self) -> Optional[PatternMatch]:
        """Detect research without output."""
        signals = [i.get("signals", {}) for i in self._intents]
        
        research_prompts = sum(
            1 for s in signals
            if s.get("is_research_query", False)
        )
        
        output_prompts = sum(
            1 for s in signals
            if s.get("is_output_action", False)  # code writing, commits, etc.
        )
        
        if research_prompts >= self._thresholds["research_without_output"] and output_prompts == 0:
            return PatternMatch(
                pattern_type="research_rabbit_hole",
                confidence=0.85,
                evidence=[
                    f"{research_prompts} research/reading prompts",
                    "0 output actions (code, commits, notes)"
                ],
                recommendation="Time to apply what you've learned! Write a 5-minute summary.",
                severity="medium"
            )
        
        return None
    
    def _check_feature_accumulation(self) -> Optional[PatternMatch]:
        """Detect many new feature requests without completion."""
        signals = [i.get("signals", {}) for i in self._intents]
        
        new_features = sum(
            1 for s in signals
            if s.get("is_new_feature_request", False)
        )
        
        completions = sum(
            1 for s in signals
            if s.get("is_completion", False) or s.get("is_shipping", False)
        )
        
        if new_features >= self._thresholds["new_features_threshold"] and completions == 0:
            return PatternMatch(
                pattern_type="feature_accumulation",
                confidence=0.8,
                evidence=[
                    f"{new_features} new feature requests",
                    f"{completions} completions"
                ],
                recommendation="Finish current work before starting new features!",
                severity="high"
            )
        
        return None
    
    def _check_perfectionism_loop(self) -> Optional[PatternMatch]:
        """Detect repeated refinement on same topic."""
        # Extract topics/files from prompts
        topics: Dict[str, int] = defaultdict(int)
        
        for intent in self._intents:
            signals = intent.get("signals", {})
            
            # Track refinement signals
            if signals.get("is_refinement", False):
                topic = signals.get("topic", "unknown")
                topics[topic] += 1
        
        # Check for any topic with many refinements
        for topic, count in topics.items():
            if count >= self._thresholds["same_topic_refinements"]:
                return PatternMatch(
                    pattern_type="perfectionism_loop",
                    confidence=0.75,
                    evidence=[
                        f"'{topic}' refined {count} times",
                        "Diminishing returns on further refinement"
                    ],
                    recommendation="Good enough is good enough! Ship it and iterate.",
                    severity="medium"
                )
        
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current intent patterns."""
        signals = [i.get("signals", {}) for i in self._intents]
        
        return {
            "total_intents": len(self._intents),
            "window_minutes": self.window_minutes,
            "context_switches": sum(1 for s in signals if s.get("is_context_switch")),
            "research_queries": sum(1 for s in signals if s.get("is_research_query")),
            "new_features": sum(1 for s in signals if s.get("is_new_feature_request")),
            "completions": sum(1 for s in signals if s.get("is_completion")),
            "refinements": sum(1 for s in signals if s.get("is_refinement")),
        }
    
    def clear(self):
        """Clear all stored intents."""
        self._intents.clear()


def create_intent_analyzer(window_minutes: int = 30) -> IntentPatternAnalyzer:
    """
    Factory function to create intent pattern analyzer.
    
    Args:
        window_minutes: Analysis window in minutes
        
    Returns:
        Configured IntentPatternAnalyzer
    """
    return IntentPatternAnalyzer(window_minutes=window_minutes)
