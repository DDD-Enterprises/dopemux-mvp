"""
Working Memory Support

Capture fleeting thoughts/ideas and provide context reminders for ADHD users.

ADHD Challenge Addressed:
- Poor working memory (forgetting what you were doing mid-task)
- Fleeting thoughts disappear before they can be captured
- Difficulty holding multiple pieces of context in mind
- Losing track of original goal when interrupted
- Forgetting brilliant ideas within seconds

Features:
- Quick thought capture (minimal friction)
- Context breadcrumbs (remember where you were)
- Idea preservation (save fleeting insights)
- Automatic context restoration after interruptions
- Smart reminders of forgotten context
- Integration with ConPort for persistence
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class ThoughtType(Enum):
    """Types of captured thoughts."""
    IDEA = "idea"  # Sudden insight or idea
    TODO = "todo"  # Task to do later
    QUESTION = "question"  # Question to research
    REMINDER = "reminder"  # Thing to remember
    CONTEXT = "context"  # Current work context
    INTERRUPTION = "interruption"  # Interruption note


class ContextType(Enum):
    """Types of context to track."""
    FILE = "file"  # Current file being edited
    TASK = "task"  # Current task
    GOAL = "goal"  # Current goal/objective
    CODE_LOCATION = "code_location"  # Specific code location
    DECISION = "decision"  # Decision being made
    PROBLEM = "problem"  # Problem being solved


@dataclass
class CapturedThought:
    """A captured fleeting thought or idea."""
    thought_id: str
    content: str
    thought_type: ThoughtType
    timestamp: datetime
    
    # Context
    current_file: Optional[str] = None
    current_task: Optional[str] = None
    current_line: Optional[int] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    completed: bool = False
    archived: bool = False
    
    # Integration
    conport_id: Optional[str] = None  # If synced to ConPort
    
    def is_actionable(self) -> bool:
        """Check if thought requires action."""
        return self.thought_type in [
            ThoughtType.TODO,
            ThoughtType.QUESTION,
            ThoughtType.REMINDER
        ]
    
    def is_urgent(self) -> bool:
        """Check if thought is urgent."""
        return self.priority in ["high", "urgent"]


@dataclass
class ContextBreadcrumb:
    """Breadcrumb to remember context."""
    breadcrumb_id: str
    context_type: ContextType
    description: str
    timestamp: datetime
    
    # Context details
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    task_id: Optional[str] = None
    goal: Optional[str] = None
    
    # What was being done
    action: Optional[str] = None  # "editing", "debugging", "implementing"
    reason: Optional[str] = None  # Why this context was important
    
    # Auto-generated hints
    hints: List[str] = field(default_factory=list)
    
    def generate_reminder_text(self) -> str:
        """Generate human-readable reminder."""
        parts = [f"You were {self.action}" if self.action else "You were working on"]
        
        if self.file_path:
            parts.append(f"in {self.file_path}")
        
        if self.function_name:
            parts.append(f"(function: {self.function_name})")
        
        if self.line_number:
            parts.append(f"at line {self.line_number}")
        
        if self.goal:
            parts.append(f"\nGoal: {self.goal}")
        
        if self.reason:
            parts.append(f"\nReason: {self.reason}")
        
        return " ".join(parts)


@dataclass
class InterruptionRecord:
    """Record of an interruption and context before/after."""
    interruption_id: str
    interrupted_at: datetime
    resumed_at: Optional[datetime] = None
    
    # Context before interruption
    context_before: Optional[ContextBreadcrumb] = None
    active_thoughts: List[CapturedThought] = field(default_factory=list)
    
    # What caused interruption
    interruption_type: str = "unknown"  # "meeting", "notification", "context_switch"
    interruption_source: Optional[str] = None
    
    # Recovery
    context_restored: bool = False
    recovery_hint_shown: bool = False


class WorkingMemorySupport:
    """
    ADHD-aware working memory support system.
    
    Features:
    - Quick thought capture (<2 seconds from idea to saved)
    - Context breadcrumbs (remember where you were)
    - Automatic interruption detection
    - Context restoration after interruptions
    - Smart reminders of forgotten context
    - Integration with ConPort for persistence
    """
    
    # Maximum time between breadcrumbs (auto-create if exceeded)
    BREADCRUMB_INTERVAL = timedelta(minutes=15)
    
    # Time threshold for detecting interruption
    INTERRUPTION_THRESHOLD = timedelta(minutes=5)
    
    def __init__(
        self,
        user_id: str,
        bridge_client=None,  # AsyncDopeconBridgeClient
        workspace_id: Optional[str] = None
    ):
        """
        Initialize working memory support.
        
        Args:
            user_id: User identifier
            bridge_client: DopeconBridge client for persistence
            workspace_id: Current workspace ID
        """
        self.user_id = user_id
        self.bridge_client = bridge_client
        self.workspace_id = workspace_id or user_id
        
        # Storage
        self.thoughts: List[CapturedThought] = []
        self.breadcrumbs: List[ContextBreadcrumb] = []
        self.interruptions: List[InterruptionRecord] = []
        
        # Current state
        self.current_context: Optional[ContextBreadcrumb] = None
        self.last_breadcrumb_time: Optional[datetime] = None
        self.active_interruption: Optional[InterruptionRecord] = None
        
        logger.info(f"WorkingMemorySupport initialized for user {user_id}")
    
    async def quick_capture(
        self,
        content: str,
        thought_type: ThoughtType = ThoughtType.IDEA,
        priority: str = "normal",
        tags: Optional[List[str]] = None
    ) -> CapturedThought:
        """
        Ultra-fast thought capture (ADHD-optimized for minimal friction).
        
        Design: <2 seconds from idea to saved
        - No forms, no fields
        - Just content + optional quick tags
        - Auto-detect thought type from content
        - Auto-capture current context
        
        Args:
            content: The thought/idea (free text)
            thought_type: Type of thought (auto-detected if not specified)
            priority: Priority level
            tags: Optional tags for organization
        
        Returns:
            CapturedThought with auto-populated context
        
        Examples:
            >>> await memory.quick_capture("TODO: Fix that bug in auth.py")
            >>> await memory.quick_capture("What if we used Redis for caching?")
            >>> await memory.quick_capture("Remember: Meeting at 3pm")
        """
        # Auto-detect thought type from content if not specified
        if thought_type == ThoughtType.IDEA:
            content_lower = content.lower()
            if content_lower.startswith(("todo:", "to do:", "task:")):
                thought_type = ThoughtType.TODO
            elif content_lower.startswith(("question:", "?", "how ", "why ", "what ")):
                thought_type = ThoughtType.QUESTION
            elif content_lower.startswith(("remind:", "remember:", "don't forget")):
                thought_type = ThoughtType.REMINDER
        
        thought = CapturedThought(
            thought_id=f"TH-{len(self.thoughts)+1}",
            content=content,
            thought_type=thought_type,
            timestamp=datetime.now(),
            tags=tags or [],
            priority=priority
        )
        
        # Auto-capture current context
        if self.current_context:
            thought.current_file = self.current_context.file_path
            thought.current_task = self.current_context.task_id
            thought.current_line = self.current_context.line_number
        
        # Store
        self.thoughts.append(thought)
        
        logger.info(
            f"Captured {thought_type.value}: '{content[:50]}...' "
            f"(priority: {priority})"
        )
        
        # Persist to ConPort
        if self.bridge_client:
            try:
                entry = await self.bridge_client.log_custom_data(
                    workspace_id=self.workspace_id,
                    category="working_memory",
                    key=f"thought_{thought.thought_id}",
                    value={
                        "content": content,
                        "type": thought_type.value,
                        "priority": priority,
                        "tags": tags or [],
                        "context": {
                            "file": thought.current_file,
                            "task": thought.current_task,
                            "line": thought.current_line
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                )
                thought.conport_id = entry.get("id")
                logger.debug(f"Thought persisted to ConPort: {thought.conport_id}")
            except Exception as e:
                logger.error(f"Failed to persist thought to ConPort: {e}")
        
        return thought
    
    async def drop_breadcrumb(
        self,
        description: str,
        context_type: ContextType = ContextType.TASK,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        function_name: Optional[str] = None,
        task_id: Optional[str] = None,
        goal: Optional[str] = None,
        action: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ContextBreadcrumb:
        """
        Drop a context breadcrumb to remember where you are.
        
        Use when:
        - Starting a new task
        - Diving into a specific code location
        - Making an important decision
        - Before a known interruption (meeting)
        
        Args:
            description: Brief description of context
            context_type: Type of context
            file_path: Current file (if applicable)
            line_number: Current line (if applicable)
            function_name: Current function (if applicable)
            task_id: Related task ID
            goal: Current goal/objective
            action: What you're doing ("editing", "debugging", etc.)
            reason: Why this is important
        
        Returns:
            ContextBreadcrumb
        
        Examples:
            >>> await memory.drop_breadcrumb(
            ...     "Implementing OAuth2 client",
            ...     context_type=ContextType.TASK,
            ...     file_path="auth.py",
            ...     line_number=156,
            ...     goal="Get OAuth working for production",
            ...     action="implementing"
            ... )
        """
        breadcrumb = ContextBreadcrumb(
            breadcrumb_id=f"BC-{len(self.breadcrumbs)+1}",
            context_type=context_type,
            description=description,
            timestamp=datetime.now(),
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            task_id=task_id,
            goal=goal,
            action=action,
            reason=reason
        )
        
        # Generate hints for context restoration
        breadcrumb.hints = self._generate_context_hints(breadcrumb)
        
        # Store
        self.breadcrumbs.append(breadcrumb)
        self.current_context = breadcrumb
        self.last_breadcrumb_time = datetime.now()
        
        logger.info(f"Dropped breadcrumb: {description}")
        
        # Persist to ConPort
        if self.bridge_client:
            try:
                await self.bridge_client.log_custom_data(
                    workspace_id=self.workspace_id,
                    category="working_memory",
                    key=f"breadcrumb_{breadcrumb.breadcrumb_id}",
                    value={
                        "description": description,
                        "type": context_type.value,
                        "file": file_path,
                        "line": line_number,
                        "function": function_name,
                        "task": task_id,
                        "goal": goal,
                        "action": action,
                        "reason": reason,
                        "hints": breadcrumb.hints,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to persist breadcrumb to ConPort: {e}")
        
        return breadcrumb
    
    def _generate_context_hints(self, breadcrumb: ContextBreadcrumb) -> List[str]:
        """Generate helpful hints for context restoration."""
        hints = []
        
        if breadcrumb.file_path:
            hints.append(f"Open {breadcrumb.file_path}")
        
        if breadcrumb.line_number:
            hints.append(f"Go to line {breadcrumb.line_number}")
        
        if breadcrumb.function_name:
            hints.append(f"Find function {breadcrumb.function_name}")
        
        if breadcrumb.task_id:
            hints.append(f"Related task: {breadcrumb.task_id}")
        
        if breadcrumb.action:
            hints.append(f"You were {breadcrumb.action}")
        
        return hints
    
    async def detect_interruption(
        self,
        interruption_type: str,
        source: Optional[str] = None
    ) -> InterruptionRecord:
        """
        Detect and record an interruption.
        
        Called when:
        - User switches to another task
        - Meeting notification appears
        - Long idle period detected
        - Context switch happens
        
        Args:
            interruption_type: Type of interruption
            source: What caused the interruption
        
        Returns:
            InterruptionRecord with current context saved
        """
        interruption = InterruptionRecord(
            interruption_id=f"INT-{len(self.interruptions)+1}",
            interrupted_at=datetime.now(),
            context_before=self.current_context,
            interruption_type=interruption_type,
            interruption_source=source
        )
        
        # Capture active (uncompleted) thoughts
        interruption.active_thoughts = [
            t for t in self.thoughts
            if t.is_actionable() and not t.completed and not t.archived
        ]
        
        # Store
        self.interruptions.append(interruption)
        self.active_interruption = interruption
        
        logger.warning(
            f"Interruption detected: {interruption_type} "
            f"(context saved: {self.current_context.description if self.current_context else 'none'})"
        )
        
        # Persist to ConPort
        if self.bridge_client:
            try:
                await self.bridge_client.log_decision(
                    workspace_id=self.workspace_id,
                    summary=f"Interruption: {interruption_type}",
                    rationale=(
                        f"Context before: {self.current_context.description if self.current_context else 'none'}"
                    ),
                    implementation_details={
                        "type": interruption_type,
                        "source": source,
                        "active_thoughts_count": len(interruption.active_thoughts),
                        "timestamp": datetime.now().isoformat()
                    },
                    tags=["interruption", interruption_type]
                )
            except Exception as e:
                logger.error(f"Failed to log interruption to ConPort: {e}")
        
        return interruption
    
    async def restore_context(
        self,
        show_hints: bool = True
    ) -> Optional[ContextBreadcrumb]:
        """
        Restore context after interruption.
        
        Called when:
        - User returns to work after meeting
        - Resuming after context switch
        - Explicitly requested by user
        
        Args:
            show_hints: Whether to show restoration hints
        
        Returns:
            ContextBreadcrumb if context available, None otherwise
        
        Example output:
            "You were implementing OAuth2 client in auth.py at line 156
             Goal: Get OAuth working for production
             Hints:
             - Open auth.py
             - Go to line 156
             - Find function setup_oauth_client
             - You were implementing"
        """
        if not self.current_context:
            logger.info("No context to restore")
            return None
        
        # Mark interruption as resumed
        if self.active_interruption:
            self.active_interruption.resumed_at = datetime.now()
            self.active_interruption.context_restored = True
            self.active_interruption.recovery_hint_shown = show_hints
            self.active_interruption = None
        
        logger.info(f"Restoring context: {self.current_context.description}")
        
        if show_hints:
            # Generate restoration message
            reminder = self.current_context.generate_reminder_text()
            
            if self.current_context.hints:
                reminder += "\n\nHints:\n" + "\n".join(
                    f"  - {hint}" for hint in self.current_context.hints
                )
            
            logger.info(f"Context restoration:\n{reminder}")
        
        return self.current_context
    
    async def get_active_thoughts(
        self,
        include_completed: bool = False,
        priority_filter: Optional[str] = None
    ) -> List[CapturedThought]:
        """
        Get active (uncompleted) thoughts.
        
        Args:
            include_completed: Include completed thoughts
            priority_filter: Filter by priority ("high", "urgent", etc.)
        
        Returns:
            List of active thoughts
        """
        thoughts = self.thoughts
        
        if not include_completed:
            thoughts = [t for t in thoughts if not t.completed and not t.archived]
        
        if priority_filter:
            thoughts = [t for t in thoughts if t.priority == priority_filter]
        
        # Sort by priority and timestamp
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        thoughts.sort(
            key=lambda t: (priority_order.get(t.priority, 2), t.timestamp),
            reverse=False
        )
        
        return thoughts
    
    async def remind_forgotten_context(self) -> Optional[str]:
        """
        Check if user might have forgotten context and generate reminder.
        
        Triggers:
        - No breadcrumb for >15 minutes
        - Active thoughts but no recent breadcrumb
        - Context switch detected but no restoration
        
        Returns:
            Reminder message if context might be forgotten, None otherwise
        """
        # Check time since last breadcrumb
        if (
            self.last_breadcrumb_time and
            datetime.now() - self.last_breadcrumb_time > self.BREADCRUMB_INTERVAL
        ):
            active_thoughts = await self.get_active_thoughts()
            
            if active_thoughts:
                reminder = (
                    f"💭 Reminder: You have {len(active_thoughts)} active thoughts:\n"
                )
                for i, thought in enumerate(active_thoughts[:3], 1):
                    reminder += f"  {i}. [{thought.thought_type.value}] {thought.content[:60]}...\n"
                
                if len(active_thoughts) > 3:
                    reminder += f"  ... and {len(active_thoughts) - 3} more\n"
                
                if self.current_context:
                    reminder += f"\nLast context: {self.current_context.description}"
                
                return reminder
        
        # Check for unrestored interruption
        if self.active_interruption and not self.active_interruption.context_restored:
            time_since = datetime.now() - self.active_interruption.interrupted_at
            
            if time_since > self.INTERRUPTION_THRESHOLD:
                reminder = (
                    f"💭 You were interrupted {time_since.seconds // 60} minutes ago\n"
                )
                
                if self.active_interruption.context_before:
                    reminder += (
                        f"Context: {self.active_interruption.context_before.description}\n"
                        "Would you like to restore context?"
                    )
                
                return reminder
        
        return None
    
    async def mark_thought_completed(self, thought_id: str) -> bool:
        """
        Mark a thought as completed.
        
        Args:
            thought_id: Thought ID to mark complete
        
        Returns:
            True if marked, False if not found
        """
        for thought in self.thoughts:
            if thought.thought_id == thought_id:
                thought.completed = True
                logger.info(f"Marked thought {thought_id} as completed")
                
                # Update in ConPort
                if self.bridge_client and thought.conport_id:
                    try:
                        await self.bridge_client.update_custom_data(
                            workspace_id=self.workspace_id,
                            category="working_memory",
                            key=f"thought_{thought.thought_id}",
                            value={"completed": True}
                        )
                    except Exception as e:
                        logger.error(f"Failed to update thought in ConPort: {e}")
                
                return True
        
        return False
    
    async def archive_thought(self, thought_id: str) -> bool:
        """
        Archive a thought (remove from active list but keep in history).
        
        Args:
            thought_id: Thought ID to archive
        
        Returns:
            True if archived, False if not found
        """
        for thought in self.thoughts:
            if thought.thought_id == thought_id:
                thought.archived = True
                logger.info(f"Archived thought {thought_id}")
                return True
        
        return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get working memory statistics.
        
        Returns:
            {
                "total_thoughts": 45,
                "active_thoughts": 8,
                "completed_thoughts": 37,
                "total_breadcrumbs": 12,
                "total_interruptions": 3,
                "average_interruption_duration": "8 minutes",
                "thoughts_by_type": {...},
                "most_used_tags": [...]
            }
        """
        active = await self.get_active_thoughts()
        completed = [t for t in self.thoughts if t.completed]
        
        # Thoughts by type
        thoughts_by_type = {}
        for t in self.thoughts:
            thoughts_by_type[t.thought_type.value] = (
                thoughts_by_type.get(t.thought_type.value, 0) + 1
            )
        
        # Tag frequency
        tag_freq = {}
        for t in self.thoughts:
            for tag in t.tags:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1
        
        most_used_tags = sorted(
            tag_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Interruption stats
        completed_interruptions = [
            i for i in self.interruptions if i.resumed_at
        ]
        
        avg_interruption_duration = None
        if completed_interruptions:
            total_duration = sum(
                (i.resumed_at - i.interrupted_at).total_seconds()
                for i in completed_interruptions
            )
            avg_minutes = int((total_duration / len(completed_interruptions)) / 60)
            avg_interruption_duration = f"{avg_minutes} minutes"
        
        return {
            "total_thoughts": len(self.thoughts),
            "active_thoughts": len(active),
            "completed_thoughts": len(completed),
            "total_breadcrumbs": len(self.breadcrumbs),
            "total_interruptions": len(self.interruptions),
            "average_interruption_duration": avg_interruption_duration,
            "thoughts_by_type": thoughts_by_type,
            "most_used_tags": most_used_tags
        }
