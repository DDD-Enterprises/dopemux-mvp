"""
Role Manager: Role-based tool access and escalation management

The Role Manager handles the definition, validation, and transition logic for
different user roles in the MetaMCP system. Each role defines a specific set
of default tools, token budgets, and escalation patterns optimized for different
development workflows while maintaining ADHD accommodations.

Key Features:
- Pre-defined roles: developer, researcher, planner, reviewer, ops, architect, debugger
- Dynamic escalation rules for temporary tool access
- Role transition validation and workflow support
- ADHD-optimized role configurations with cognitive load considerations
- Integration with token budgets and tool mounting policies

Design Principles:
- Least-privilege: Roles start with minimal necessary tools
- Progressive disclosure: Additional tools available through escalation
- Context-aware: Role suggestions based on current task and context
- Flexible: Support for custom roles and overrides
"""

import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EscalationTrigger(Enum):
    """Types of escalation triggers"""
    MANUAL = "manual"              # User-requested escalation
    AUTO_TASK = "auto_task"        # Triggered by task type detection
    AUTO_CONTEXT = "auto_context"  # Triggered by code context analysis
    AUTO_ERROR = "auto_error"      # Triggered by error patterns
    CALENDAR = "calendar"          # Triggered by calendar events


@dataclass
class EscalationRule:
    """Configuration for role escalation rules"""
    additional_tools: List[str]
    max_duration: int  # seconds
    auto_trigger: bool = False
    approval_required: bool = False
    priority: str = "normal"  # normal, high, emergency
    description: str = ""

    @property
    def duration_minutes(self) -> int:
        return self.max_duration // 60


@dataclass
class Role:
    """Role definition with tools, budgets, and escalation rules"""
    name: str
    description: str
    default_tools: List[str]
    token_budget: int
    escalation_triggers: Dict[str, EscalationRule] = field(default_factory=dict)

    # ADHD-specific settings
    cognitive_complexity: str = "medium"  # low, medium, high
    context_switching_cost: str = "medium"  # low, medium, high
    focus_mode_recommended: bool = False

    # Workflow integration
    typical_session_duration: int = 3600  # seconds (1 hour default)
    break_reminder_interval: int = 1500   # seconds (25 minutes - Pomodoro)

    # Role relationships
    escalates_to: List[str] = field(default_factory=list)      # Roles this can escalate to
    escalates_from: List[str] = field(default_factory=list)    # Roles that can escalate to this
    workflow_transitions: List[str] = field(default_factory=list)  # Natural workflow progression

    @property
    def all_possible_tools(self) -> Set[str]:
        """Get all tools accessible through default + escalations"""
        tools = set(self.default_tools)
        for escalation in self.escalation_triggers.values():
            tools.update(escalation.additional_tools)
        return tools

    @property
    def complexity_score(self) -> int:
        """Calculate complexity score for ADHD cognitive load assessment"""
        base_score = len(self.default_tools)

        if self.cognitive_complexity == "high":
            base_score *= 1.5
        elif self.cognitive_complexity == "low":
            base_score *= 0.7

        return int(base_score)


class RoleManager:
    """
    Manages role definitions, transitions, and escalation logic.

    The RoleManager provides the core role-based access control for the MetaMCP
    system, ensuring users have access to appropriate tools while maintaining
    cognitive load optimization for ADHD developers.
    """

    def __init__(self, policy_config: Dict[str, Any]):
        self.policy_config = policy_config
        self.roles: Dict[str, Role] = {}
        self.role_suggestions_cache: Dict[str, Any] = {}

        # Load roles from configuration
        self._load_roles_from_config()

        # Role transition analytics
        self.transition_patterns: Dict[tuple, int] = {}
        self.escalation_frequency: Dict[str, int] = {}

        logger.info(f"RoleManager initialized with {len(self.roles)} roles")

    def _load_roles_from_config(self) -> None:
        """Load role definitions from policy configuration"""
        profiles = self.policy_config.get('profiles', {})

        for role_name, role_config in profiles.items():
            escalation_rules = {}

            # Convert escalation triggers to EscalationRule objects
            escalation_triggers = role_config.get('escalation_triggers', {})
            for trigger_name, trigger_config in escalation_triggers.items():
                escalation_rules[trigger_name] = EscalationRule(
                    additional_tools=trigger_config.get('additional_tools', []),
                    max_duration=trigger_config.get('max_duration', 1800),
                    auto_trigger=trigger_config.get('auto_trigger', False),
                    approval_required=trigger_config.get('approval_required', False),
                    priority=trigger_config.get('priority', 'normal'),
                    description=trigger_config.get('description', f"Escalation for {trigger_name}")
                )

            # Create role object
            role = Role(
                name=role_name,
                description=role_config.get('description', f"{role_name} role"),
                default_tools=role_config.get('default_tools', []),
                token_budget=role_config.get('token_budget', 10000),
                escalation_triggers=escalation_rules
            )

            # Set ADHD-specific properties based on role characteristics
            self._configure_adhd_properties(role)

            # Set workflow relationships
            self._configure_workflow_relationships(role)

            self.roles[role_name] = role

        logger.info(f"Loaded {len(self.roles)} role definitions")

    def _configure_adhd_properties(self, role: Role) -> None:
        """Configure ADHD-specific properties based on role characteristics"""
        # Cognitive complexity based on tool count and type
        tool_count = len(role.default_tools)
        total_possible_tools = len(role.all_possible_tools)

        if tool_count <= 3:
            role.cognitive_complexity = "low"
        elif tool_count >= 6 or total_possible_tools >= 10:
            role.cognitive_complexity = "high"
        else:
            role.cognitive_complexity = "medium"

        # Context switching cost based on role type
        if role.name in ['architect', 'researcher']:
            role.context_switching_cost = "high"  # Deep thinking roles
            role.focus_mode_recommended = True
            role.typical_session_duration = 7200  # 2 hours
        elif role.name in ['ops', 'debugger']:
            role.context_switching_cost = "low"   # Quick action roles
            role.typical_session_duration = 1800  # 30 minutes
        else:
            role.context_switching_cost = "medium"
            role.typical_session_duration = 3600  # 1 hour

    def _configure_workflow_relationships(self, role: Role) -> None:
        """Configure natural workflow transitions between roles"""
        workflow_map = {
            'researcher': ['planner', 'architect'],
            'planner': ['developer', 'architect'],
            'architect': ['developer', 'reviewer'],
            'developer': ['reviewer', 'debugger'],
            'reviewer': ['developer', 'ops'],
            'debugger': ['developer', 'ops'],
            'ops': ['developer', 'reviewer']
        }

        role.workflow_transitions = workflow_map.get(role.name, [])

        # Set escalation relationships
        if role.name == 'developer':
            role.escalates_to = ['architect', 'debugger']
        elif role.name == 'researcher':
            role.escalates_to = ['architect']
        elif role.name == 'planner':
            role.escalates_to = ['architect', 'researcher']

    async def get_role(self, role_name: str) -> Optional[Role]:
        """Get role configuration by name"""
        return self.roles.get(role_name)

    async def list_roles(self) -> List[Role]:
        """Get all available roles"""
        return list(self.roles.values())

    async def get_roles_by_complexity(self, max_complexity: str = "medium") -> List[Role]:
        """Get roles filtered by cognitive complexity (ADHD accommodation)"""
        complexity_order = {"low": 1, "medium": 2, "high": 3}
        max_level = complexity_order.get(max_complexity, 2)

        return [
            role for role in self.roles.values()
            if complexity_order.get(role.cognitive_complexity, 2) <= max_level
        ]

    async def suggest_role_for_context(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Suggest appropriate role based on current context.

        This helps ADHD users by reducing decision overhead and providing
        contextually appropriate tool access.
        """
        # Extract context clues
        file_patterns = context.get('file_patterns', [])
        task_description = context.get('task_description', '').lower()
        recent_errors = context.get('recent_errors', [])
        calendar_event = context.get('upcoming_event')
        time_of_day = context.get('time_of_day', datetime.now().hour)

        # Score roles based on context
        role_scores = {}

        for role_name, role in self.roles.items():
            score = 0

            # File pattern matching
            if 'test' in file_patterns or 'spec' in file_patterns:
                if role_name == 'developer':
                    score += 3
            elif any(ext in file_patterns for ext in ['.md', '.rst', '.txt']):
                if role_name in ['researcher', 'planner']:
                    score += 3
            elif any(ext in file_patterns for ext in ['.py', '.js', '.ts', '.go']):
                if role_name == 'developer':
                    score += 2

            # Task description keywords
            task_keywords = {
                'developer': ['implement', 'code', 'build', 'create', 'fix'],
                'researcher': ['research', 'analyze', 'investigate', 'study', 'explore'],
                'planner': ['plan', 'organize', 'schedule', 'roadmap', 'strategy'],
                'reviewer': ['review', 'check', 'validate', 'audit', 'assess'],
                'debugger': ['debug', 'troubleshoot', 'diagnose', 'error', 'issue'],
                'ops': ['deploy', 'infrastructure', 'monitor', 'scale', 'operations'],
                'architect': ['design', 'architecture', 'structure', 'framework', 'pattern']
            }

            keywords = task_keywords.get(role_name, [])
            for keyword in keywords:
                if keyword in task_description:
                    score += 2

            # Error context
            if recent_errors and role_name == 'debugger':
                score += 3

            # Calendar context
            if calendar_event:
                event_title = calendar_event.get('title', '').lower()
                if 'standup' in event_title and role_name == 'developer':
                    score += 2
                elif 'review' in event_title and role_name == 'reviewer':
                    score += 3
                elif 'planning' in event_title and role_name == 'planner':
                    score += 3

            # Time of day preferences (ADHD consideration)
            if 6 <= time_of_day < 10:  # Morning - good for deep work
                if role_name in ['researcher', 'architect']:
                    score += 1
            elif 10 <= time_of_day < 15:  # Midday - good for implementation
                if role_name == 'developer':
                    score += 1
            elif 15 <= time_of_day < 18:  # Afternoon - good for review
                if role_name in ['reviewer', 'debugger']:
                    score += 1

            role_scores[role_name] = score

        # Return highest scoring role, or None if no clear winner
        if not role_scores:
            return None

        best_role = max(role_scores.items(), key=lambda x: x[1])

        # Only suggest if score is meaningful (> 1)
        if best_role[1] > 1:
            self.role_suggestions_cache[str(hash(str(context)))] = {
                'suggested_role': best_role[0],
                'confidence': best_role[1],
                'timestamp': datetime.now()
            }
            return best_role[0]

        return None

    async def validate_role_transition(self, from_role: Optional[str], to_role: str) -> bool:
        """
        Validate if a role transition is allowed and appropriate.

        This prevents jarring transitions that could be disruptive for ADHD users
        while still allowing necessary workflow changes.
        """
        # Always allow initial role assignment
        if from_role is None:
            return True

        # Always allow transition to same role
        if from_role == to_role:
            return True

        # Check if target role exists
        if to_role not in self.roles:
            return False

        from_role_obj = self.roles.get(from_role)
        to_role_obj = self.roles.get(to_role)

        if not from_role_obj or not to_role_obj:
            return False

        # Check workflow transitions (natural progressions)
        if to_role in from_role_obj.workflow_transitions:
            return True

        # Check escalation relationships
        if to_role in from_role_obj.escalates_to:
            return True

        # Allow transition if complexity difference is not too high (ADHD consideration)
        complexity_map = {"low": 1, "medium": 2, "high": 3}
        from_complexity = complexity_map.get(from_role_obj.cognitive_complexity, 2)
        to_complexity = complexity_map.get(to_role_obj.cognitive_complexity, 2)

        # Don't allow jumps that are too cognitively demanding
        if to_complexity - from_complexity > 1:
            logger.warning(f"Role transition {from_role} -> {to_role} blocked: cognitive complexity jump too high")
            return False

        # Record transition pattern for learning
        self.transition_patterns[(from_role, to_role)] = self.transition_patterns.get((from_role, to_role), 0) + 1

        return True

    async def get_escalation_options(self, role_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get available escalation options for a role based on current context.

        This provides ADHD users with clear, limited options to reduce decision paralysis.
        """
        role = self.roles.get(role_name)
        if not role:
            return []

        escalation_options = []

        for trigger_name, escalation in role.escalation_triggers.items():
            # Check if escalation is contextually relevant
            relevance_score = await self._assess_escalation_relevance(trigger_name, context)

            if relevance_score > 0:
                escalation_options.append({
                    'trigger': trigger_name,
                    'description': escalation.description,
                    'additional_tools': escalation.additional_tools,
                    'duration_minutes': escalation.duration_minutes,
                    'auto_trigger': escalation.auto_trigger,
                    'approval_required': escalation.approval_required,
                    'priority': escalation.priority,
                    'relevance_score': relevance_score
                })

        # Sort by relevance and limit to max 3 options (ADHD accommodation)
        escalation_options.sort(key=lambda x: x['relevance_score'], reverse=True)
        return escalation_options[:3]

    async def _assess_escalation_relevance(self, trigger_name: str, context: Dict[str, Any]) -> int:
        """Assess how relevant an escalation option is to current context"""
        score = 0

        # Context clues for different escalation types
        task_description = context.get('task_description', '').lower()
        recent_errors = context.get('recent_errors', [])
        file_patterns = context.get('file_patterns', [])

        if trigger_name == 'test_failure':
            if recent_errors or 'test' in task_description:
                score += 3
        elif trigger_name == 'complex_arch':
            if any(word in task_description for word in ['architecture', 'design', 'structure', 'framework']):
                score += 2
        elif trigger_name == 'ui_testing':
            if any(pattern in file_patterns for pattern in ['html', 'css', 'ui', 'component']):
                score += 2
        elif trigger_name == 'deep_analysis':
            if any(word in task_description for word in ['analyze', 'investigate', 'research']):
                score += 2
        elif trigger_name == 'incident_response':
            if recent_errors and len(recent_errors) > 2:
                score += 3

        return score

    async def get_role_analytics(self) -> Dict[str, Any]:
        """Get analytics about role usage and transitions"""
        total_transitions = sum(self.transition_patterns.values())

        analytics = {
            'total_roles': len(self.roles),
            'total_transitions': total_transitions,
            'most_common_transitions': sorted(
                self.transition_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'role_complexity_distribution': {
                complexity: len([r for r in self.roles.values() if r.cognitive_complexity == complexity])
                for complexity in ['low', 'medium', 'high']
            },
            'escalation_frequency': dict(self.escalation_frequency),
            'role_tool_counts': {
                name: len(role.default_tools)
                for name, role in self.roles.items()
            }
        }

        return analytics

    async def optimize_role_for_adhd_user(self, role_name: str, user_preferences: Dict[str, Any]) -> Optional[Role]:
        """
        Create an ADHD-optimized version of a role based on user preferences.

        This allows customization while maintaining the core role structure.
        """
        base_role = self.roles.get(role_name)
        if not base_role:
            return None

        # Create customized copy
        optimized_role = Role(
            name=f"{role_name}_adhd_optimized",
            description=f"ADHD-optimized {base_role.description}",
            default_tools=base_role.default_tools.copy(),
            token_budget=base_role.token_budget,
            escalation_triggers=base_role.escalation_triggers.copy()
        )

        # Apply user preferences
        attention_span = user_preferences.get('attention_span', 'medium')  # short, medium, long
        cognitive_load_tolerance = user_preferences.get('cognitive_load_tolerance', 'medium')

        # Adjust based on attention span
        if attention_span == 'short':
            optimized_role.break_reminder_interval = 900   # 15 minutes
            optimized_role.typical_session_duration = 1800  # 30 minutes
        elif attention_span == 'long':
            optimized_role.break_reminder_interval = 2700  # 45 minutes
            optimized_role.typical_session_duration = 5400  # 90 minutes

        # Adjust based on cognitive load tolerance
        if cognitive_load_tolerance == 'low':
            # Reduce default tools for lower cognitive load
            optimized_role.default_tools = optimized_role.default_tools[:3]
            optimized_role.cognitive_complexity = 'low'
        elif cognitive_load_tolerance == 'high':
            # Can handle more tools
            optimized_role.cognitive_complexity = 'medium'

        return optimized_role

    def get_role_summary(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Get a comprehensive summary of a role"""
        role = self.roles.get(role_name)
        if not role:
            return None

        return {
            'name': role.name,
            'description': role.description,
            'default_tools': role.default_tools,
            'token_budget': role.token_budget,
            'cognitive_complexity': role.cognitive_complexity,
            'context_switching_cost': role.context_switching_cost,
            'focus_mode_recommended': role.focus_mode_recommended,
            'typical_session_duration_minutes': role.typical_session_duration // 60,
            'break_reminder_interval_minutes': role.break_reminder_interval // 60,
            'escalation_options': list(role.escalation_triggers.keys()),
            'workflow_transitions': role.workflow_transitions,
            'all_possible_tools': list(role.all_possible_tools),
            'complexity_score': role.complexity_score
        }