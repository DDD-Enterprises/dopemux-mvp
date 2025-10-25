"""
F-NEW-7 Phase 3: Cross-Agent Intelligence with Pattern Correlation

Automatically generates insights from cross-agent event correlations.
ADHD Impact: Proactive guidance before problems occur.
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntelligenceType(str, Enum):
    """Types of intelligent insights generated."""
    PATTERN_CLUSTER = "pattern_cluster"  # Complexity hotspots
    COGNITIVE_CODE = "cognitive_code"     # Energy-complexity mismatch
    CONTEXT_SWITCH = "context_switch"     # Workspace switches with uncommitted work
    SEARCH_PATTERN = "search_pattern"     # Repeated search patterns


@dataclass
class IntelligenceInsight:
    """Generated insight from pattern correlation."""
    insight_type: IntelligenceType
    priority: str  # "low", "medium", "high", "critical"
    title: str
    description: str
    recommended_action: str
    triggered_by: List[str]  # Event IDs that triggered this
    confidence: float  # 0.0-1.0
    timestamp: datetime


class PatternCorrelationEngine:
    """
    Correlates events from multiple agents to generate intelligent insights.

    Monitors:
    - Serena: code complexity events
    - ADHD Engine: cognitive state changes
    - Desktop Commander: workspace switches
    - Dope-Context: search patterns
    - Task-Orchestrator: task events
    """

    def __init__(self, window_minutes: int = 30):
        self.window_minutes = window_minutes

        # Sliding windows for different event types
        self.complexity_events = deque(maxlen=50)
        self.cognitive_events = deque(maxlen=50)
        self.workspace_events = deque(maxlen=20)
        self.search_events = deque(maxlen=50)
        self.task_events = deque(maxlen=50)

        # Generated insights (recent)
        self.recent_insights = deque(maxlen=100)

    async def on_event(self, event: Dict) -> Optional[IntelligenceInsight]:
        """
        Process incoming event and check for correlation patterns.

        Returns:
            IntelligenceInsight if pattern detected, None otherwise
        """
        event_type = event.get('type', '')

        # Route to appropriate handler
        if event_type.startswith('code.complexity'):
            return await self._handle_complexity_event(event)
        elif event_type.startswith('cognitive.state'):
            return await self._handle_cognitive_event(event)
        elif event_type.startswith('workspace.switch'):
            return await self._handle_workspace_event(event)
        elif event_type.startswith('search.'):
            return await self._handle_search_event(event)
        elif event_type.startswith('task.'):
            return await self._handle_task_event(event)

        return None

    async def _handle_complexity_event(self, event: Dict) -> Optional[IntelligenceInsight]:
        """Handle code complexity events from Serena."""
        self.complexity_events.append(event)

        # Pattern 1: Complexity Cluster Detection
        # IF 3+ high complexity files in same directory within window
        insight = await self._detect_complexity_cluster()
        if insight:
            return insight

        # Pattern 2: Cognitive-Code Correlation
        # IF high complexity + low energy
        insight = await self._detect_cognitive_code_mismatch()
        if insight:
            return insight

        return None

    async def _handle_cognitive_event(self, event: Dict) -> Optional[IntelligenceInsight]:
        """Handle cognitive state changes from ADHD Engine."""
        self.cognitive_events.append(event)

        # Check for cognitive-code mismatch
        return await self._detect_cognitive_code_mismatch()

    async def _handle_workspace_event(self, event: Dict) -> Optional[IntelligenceInsight]:
        """Handle workspace switches from Desktop Commander."""
        self.workspace_events.append(event)

        # Pattern 3: Context Switch with Uncommitted Work
        return await self._detect_context_switch_risk()

    async def _handle_search_event(self, event: Dict) -> Optional[IntelligenceInsight]:
        """Handle search events from Dope-Context."""
        self.search_events.append(event)

        # Pattern 4: Repeated Search Pattern
        return await self._detect_search_pattern()

    async def _handle_task_event(self, event: Dict) -> Optional[IntelligenceInsight]:
        """Handle task events from Task-Orchestrator."""
        self.task_events.append(event)
        return None  # No task-specific patterns yet

    # =====================================================================
    # Pattern Detection Methods
    # =====================================================================

    async def _detect_complexity_cluster(self) -> Optional[IntelligenceInsight]:
        """
        Pattern 1: Complexity Cluster Detection

        IF Serena detects 3+ high complexity files in same directory
        AND within last 30 minutes
        THEN: Suggest refactoring or documentation
        """
        recent = self._get_recent_events(self.complexity_events, self.window_minutes)

        if len(recent) < 3:
            return None

        # Group by directory
        dir_complexity = {}
        for event in recent:
            file_path = event.get('data', {}).get('file', '')
            if not file_path:
                continue

            # Extract directory
            directory = '/'.join(file_path.split('/')[:-1])
            complexity = event.get('data', {}).get('complexity', 0.0)

            if complexity >= 0.7:  # High complexity threshold
                if directory not in dir_complexity:
                    dir_complexity[directory] = []
                dir_complexity[directory].append((file_path, complexity))

        # Find directories with 3+ high complexity files
        for directory, files in dir_complexity.items():
            if len(files) >= 3:
                avg_complexity = sum(c for _, c in files) / len(files)

                return IntelligenceInsight(
                    insight_type=IntelligenceType.PATTERN_CLUSTER,
                    priority="high",
                    title=f"High complexity cluster detected: {directory}",
                    description=f"Found {len(files)} high-complexity files (avg: {avg_complexity:.2f}) in {directory}. This area may benefit from refactoring or additional documentation.",
                    recommended_action=f"Consider: 1) Refactor complex logic into smaller functions, 2) Add architecture documentation, 3) Create README for {directory}",
                    triggered_by=[e.get('id', '') for e in recent if directory in e.get('data', {}).get('file', '')],
                    confidence=0.85,
                    timestamp=datetime.now()
                )

        return None

    async def _detect_cognitive_code_mismatch(self) -> Optional[IntelligenceInsight]:
        """
        Pattern 2: Cognitive-Code Correlation

        IF ADHD Engine shows energy declining
        AND Serena shows user editing high complexity code (>0.7)
        THEN: Suggest switching to simpler task or taking break
        """
        recent_cognitive = self._get_recent_events(self.cognitive_events, minutes=10)
        recent_complexity = self._get_recent_events(self.complexity_events, minutes=5)

        if not recent_cognitive or not recent_complexity:
            return None

        # Check latest cognitive state
        latest_cognitive = recent_cognitive[-1]
        energy = latest_cognitive.get('data', {}).get('energy', 'medium')

        # Check if working on high complexity
        latest_complexity_event = recent_complexity[-1]
        current_complexity = latest_complexity_event.get('data', {}).get('complexity', 0.0)

        # Mismatch condition
        if energy == 'low' and current_complexity >= 0.7:
            return IntelligenceInsight(
                insight_type=IntelligenceType.COGNITIVE_CODE,
                priority="critical",
                title="Low energy + high complexity task detected",
                description=f"You're working on high-complexity code (complexity: {current_complexity:.2f}) while energy is low. This combination often leads to frustration and errors.",
                recommended_action="Switch to simpler task (complexity <0.3) OR take 10-minute break to recharge",
                triggered_by=[latest_cognitive.get('id', ''), latest_complexity_event.get('id', '')],
                confidence=0.90,
                timestamp=datetime.now()
            )

        return None

    async def _detect_context_switch_risk(self) -> Optional[IntelligenceInsight]:
        """
        Pattern 3: Context Switch Recovery

        IF Desktop Commander detects workspace switch
        AND Last workspace had uncommitted work
        THEN: Remind user of uncommitted changes
        """
        if len(self.workspace_events) < 2:
            return None

        # Get last two workspace events
        events = list(self.workspace_events)
        if len(events) >= 2:
            old_workspace = events[-2].get('data', {}).get('workspace', '')
            new_workspace = events[-1].get('data', {}).get('workspace', '')
            uncommitted_files = events[-2].get('data', {}).get('uncommitted_files', [])

            if uncommitted_files and old_workspace != new_workspace:
                return IntelligenceInsight(
                    insight_type=IntelligenceType.CONTEXT_SWITCH,
                    priority="medium",
                    title=f"Context switch: {old_workspace} → {new_workspace}",
                    description=f"You switched from {old_workspace} which has {len(uncommitted_files)} uncommitted file(s). Remember to commit or stash when you return.",
                    recommended_action=f"Files to review: {', '.join(uncommitted_files[:3])}",
                    triggered_by=[events[-1].get('id', '')],
                    confidence=1.0,
                    timestamp=datetime.now()
                )

        return None

    async def _detect_search_pattern(self) -> Optional[IntelligenceInsight]:
        """
        Pattern 4: Repeated Search Pattern

        IF Dope-Context shows repeated search for same topic
        AND Search results consistent
        THEN: Suggest creating documentation or bookmark
        """
        recent_searches = self._get_recent_events(self.search_events, minutes=60)

        if len(recent_searches) < 3:
            return None

        # Find repeated queries
        query_counts = {}
        for event in recent_searches:
            query = event.get('data', {}).get('query', '').lower()
            if query:
                query_counts[query] = query_counts.get(query, 0) + 1

        # If same query 3+ times
        for query, count in query_counts.items():
            if count >= 3:
                return IntelligenceInsight(
                    insight_type=IntelligenceType.SEARCH_PATTERN,
                    priority="low",
                    title=f"Repeated search pattern: '{query}'",
                    description=f"You've searched for '{query}' {count} times in the last hour. Consider creating documentation or a bookmark for quick reference.",
                    recommended_action=f"Create README in relevant directory OR add bookmark to commonly-searched code",
                    triggered_by=[e.get('id', '') for e in recent_searches if query in e.get('data', {}).get('query', '').lower()],
                    confidence=0.75,
                    timestamp=datetime.now()
                )

        return None

    def _get_recent_events(self, event_queue: deque, minutes: int) -> List[Dict]:
        """Get events from queue within time window."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []

        for event in event_queue:
            timestamp_str = event.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if timestamp >= cutoff:
                        recent.append(event)
                except:
                    pass

        return recent
