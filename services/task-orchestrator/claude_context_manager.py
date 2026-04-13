"""
Dynamic Claude.md Context Management System

Automatically updates Claude.md instructions based on current sprint context,
active tasks, and ADHD optimization patterns for seamless workflow automation.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContextMode(str, Enum):
    """Claude.md context modes."""
    SPRINT_PLANNING = "sprint_planning"
    ACTIVE_DEVELOPMENT = "active_development"
    CODE_REVIEW = "code_review"
    RETROSPECTIVE = "retrospective"
    MAINTENANCE = "maintenance"
    RESEARCH = "research"


class ADHDState(str, Enum):
    """ADHD state for context adaptation."""
    SCATTERED = "scattered"
    FOCUSED = "focused"
    HYPERFOCUS = "hyperfocus"
    LOW_ENERGY = "low_energy"
    BREAK_MODE = "break_mode"


@dataclass
class ClaudeContext:
    """Dynamic context for Claude.md."""
    # Sprint context
    active_sprint_id: Optional[str] = None
    sprint_name: Optional[str] = None
    sprint_mode: ContextMode = ContextMode.ACTIVE_DEVELOPMENT

    # Current work
    active_task_id: Optional[str] = None
    active_task_title: Optional[str] = None
    current_focus_area: Optional[str] = None
    priority_tasks: List[Dict[str, Any]] = None

    # ADHD state
    adhd_state: ADHDState = ADHDState.FOCUSED
    energy_level: str = "medium"
    recommended_task_duration: int = 25
    break_frequency: int = 25

    # System state
    available_agents: List[str] = None
    system_health: Dict[str, Any] = None
    recent_decisions: List[Dict[str, Any]] = None

    # Workflow automation
    automation_active: bool = True
    implicit_features: List[str] = None
    next_automated_actions: List[str] = None

    def __post_init__(self):
        if self.priority_tasks is None:
            self.priority_tasks = []
        if self.available_agents is None:
            self.available_agents = []
        if self.system_health is None:
            self.system_health = {}
        if self.recent_decisions is None:
            self.recent_decisions = []
        if self.implicit_features is None:
            self.implicit_features = []
        if self.next_automated_actions is None:
            self.next_automated_actions = []


class ClaudeContextManager:
    """
    Manages dynamic Claude.md context updates for seamless workflow automation.

    Features:
    - Real-time context updates based on sprint and task state
    - ADHD-adaptive instruction modification
    - Workflow automation guidance integration
    - Context preservation across sessions
    - Intelligent instruction prioritization
    """

    def __init__(
        self,
        workspace_path: Path,
        claude_md_path: Optional[Path] = None
    ):
        self.workspace_path = Path(workspace_path)
        self.claude_md_path = claude_md_path or (self.workspace_path / ".claude" / "CLAUDE.md")

        # Context state
        self.current_context = ClaudeContext()
        self.context_history: List[ClaudeContext] = []
        self.base_claude_md: Optional[str] = None

        # Template system
        self.context_templates: Dict[ContextMode, str] = {}
        self.adhd_adaptations: Dict[ADHDState, Dict[str, Any]] = {}

        # Update tracking
        self.last_update: Optional[datetime] = None
        self.update_frequency = 300  # 5 minutes
        self.pending_updates: Set[str] = set()

        # Background monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False

    async def initialize(self) -> None:
        """Initialize Claude.md context manager."""
        logger.info("📝 Initializing Claude.md Context Manager...")

        # Load base Claude.md content
        await self._load_base_claude_md()

        # Initialize context templates
        self._initialize_context_templates()

        # Initialize ADHD adaptations
        self._initialize_adhd_adaptations()

        # Start background monitoring
        await self._start_context_monitoring()

        self.running = True
        logger.info("✅ Claude.md Context Manager ready for dynamic updates!")

    async def _load_base_claude_md(self) -> None:
        """Load base Claude.md content as template."""
        try:
            if self.claude_md_path.exists():
                with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                    self.base_claude_md = f.read()

                logger.info(f"📄 Loaded base Claude.md from {self.claude_md_path}")
            else:
                logger.warning(f"Claude.md not found at {self.claude_md_path}")
                self.base_claude_md = self._get_default_claude_md()

        except Exception as e:
            logger.error(f"Failed to load Claude.md: {e}")
            self.base_claude_md = self._get_default_claude_md()

    def _initialize_context_templates(self) -> None:
        """Initialize context-specific templates."""
        self.context_templates = {
            ContextMode.SPRINT_PLANNING: """
# Sprint Planning Mode - Automated PM Workflow

## 🎯 Current Sprint Context
- **Sprint**: {{sprint_name}} ({{sprint_id}})
- **Mode**: PLANNING
- **Tasks**: {{task_count}} total, {{complex_tasks}} complex
- **Focus**: Sprint setup and task decomposition

## 🤖 Automatic Workflows Active
- ✅ **Task Analysis**: Complexity scoring and ADHD decomposition
- ✅ **Agent Assignment**: Optimal AI agent routing for each task type
- ✅ **Progress Setup**: Automatic tracking across Leantime, ConPort, local systems
- ✅ **Break Planning**: 25-minute chunks with hyperfocus protection

## 📋 Priority Actions
{{#each priority_tasks}}
- **{{title}}** ({{complexity_label}}) - Estimated: {{estimated_minutes}}min
{{/each}}

## 🧠 ADHD Accommodations
- **Energy Matching**: Tasks automatically matched to current energy level
- **Cognitive Load**: {{cognitive_load_status}}
- **Break Frequency**: Every {{break_frequency}} minutes
- **Context Switching**: Minimized through intelligent batching
""",

            ContextMode.ACTIVE_DEVELOPMENT: """
# Active Development Mode - Seamless PM Automation

## 🎯 Current Work Context
- **Sprint**: {{sprint_name}} ({{sprint_id}})
- **Active Task**: {{active_task_title}}
- **Focus Area**: {{current_focus_area}}
- **Progress**: Auto-tracked via file changes and git commits

## 🤖 Implicit Automation Active
- ✅ **Progress Tracking**: File changes automatically update task progress in Leantime
- ✅ **Context Preservation**: Work context saved across interruptions
- ✅ **Break Management**: Gentle reminders every {{break_frequency}} minutes
- ✅ **Decision Linking**: Code changes linked to architectural decisions in ConPort

## 🧠 ADHD Status: {{adhd_state}}
- **Energy Level**: {{energy_level}}
- **Recommended Duration**: {{recommended_task_duration}} minutes
- **Focus Mode**: {{focus_mode_status}}

## ⚡ Next Actions (Auto-Prioritized)
{{#each next_automated_actions}}
- {{action}} ({{timing}})
{{/each}}
""",

            ContextMode.CODE_REVIEW: """
# Code Review Mode - Quality Automation

## 🎯 Review Context
- **Sprint**: {{sprint_name}}
- **Review Type**: {{review_type}}
- **Files Changed**: {{files_changed}}

## 🤖 Automated Quality Checks
- ✅ **Zen Code Review**: Multi-model analysis active
- ✅ **Pattern Validation**: ConPort pattern compliance checking
- ✅ **Progress Correlation**: Changes automatically linked to tasks
- ✅ **ADHD Feedback**: Gentle, constructive review comments

## 🧠 Review Accommodations
- **Complexity Chunking**: Large reviews broken into manageable pieces
- **Progress Indicators**: Clear completion status throughout review
- **Context Breadcrumbs**: Easy navigation back to implementation context
""",

            ContextMode.RETROSPECTIVE: """
# Retrospective Mode - Learning Automation

## 🎯 Sprint Retrospective: {{sprint_name}}
- **Completed Tasks**: {{completed_count}}
- **Duration**: {{sprint_duration}}
- **Automation Effectiveness**: {{automation_success_rate}}

## 🤖 Auto-Generated Insights
### What Went Well
{{#each positive_insights}}
- {{insight}} ({{confidence}})
{{/each}}

### ADHD Accommodations That Worked
{{#each adhd_insights}}
- {{accommodation}} - {{effectiveness}}
{{/each}}

### Workflow Optimizations for Next Sprint
{{#each workflow_improvements}}
- {{improvement}} ({{implementation_effort}})
{{/each}}

## 🧠 ADHD Pattern Analysis
- **Focus Duration**: {{average_focus_duration}} minutes
- **Context Switches**: {{context_switches}} ({{trend}})
- **Energy Utilization**: {{energy_efficiency}}
- **Break Compliance**: {{break_compliance_rate}}
"""
        }

    def _initialize_adhd_adaptations(self) -> None:
        """Initialize ADHD-specific adaptations."""
        self.adhd_adaptations = {
            ADHDState.SCATTERED: {
                "max_instructions": 5,
                "instruction_length": "short",
                "visual_indicators": "high",
                "chunk_size": "small",
                "encouragement_level": "high"
            },
            ADHDState.FOCUSED: {
                "max_instructions": 10,
                "instruction_length": "medium",
                "visual_indicators": "medium",
                "chunk_size": "medium",
                "encouragement_level": "medium"
            },
            ADHDState.HYPERFOCUS: {
                "max_instructions": 15,
                "instruction_length": "detailed",
                "visual_indicators": "minimal",
                "chunk_size": "large",
                "encouragement_level": "low",
                "protection_reminders": True
            },
            ADHDState.LOW_ENERGY: {
                "max_instructions": 3,
                "instruction_length": "minimal",
                "visual_indicators": "high",
                "chunk_size": "tiny",
                "encouragement_level": "very_high",
                "energy_boosting": True
            },
            ADHDState.BREAK_MODE: {
                "max_instructions": 1,
                "instruction_length": "minimal",
                "primary_message": "Take a break - you've earned it! 💙",
                "hide_complex_tasks": True
            }
        }

    async def _start_context_monitoring(self) -> None:
        """Start background context monitoring."""
        self.monitor_task = asyncio.create_task(self._context_monitor())

    async def _context_monitor(self) -> None:
        """Background monitor for context changes."""
        logger.info("👁️ Started Claude.md context monitoring")

        while self.running:
            try:
                # Check for context updates needed
                context_changed = await self._check_context_changes()

                if context_changed or self.pending_updates:
                    await self._update_claude_context()

                # Monitor every 2 minutes
                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Context monitoring error: {e}")
                await asyncio.sleep(300)

    # Core Context Management

    async def update_sprint_context(
        self,
        sprint_id: str,
        sprint_name: str,
        mode: ContextMode,
        task_data: List[Dict[str, Any]] = None
    ) -> None:
        """Update context for new sprint."""
        try:
            # Update context
            self.current_context.active_sprint_id = sprint_id
            self.current_context.sprint_name = sprint_name
            self.current_context.sprint_mode = mode

            if task_data:
                # Extract priority tasks (high priority, not blocked)
                priority_tasks = [
                    task for task in task_data
                    if task.get("priority", 5) <= 3 and task.get("status") != "blocked"
                ]
                self.current_context.priority_tasks = priority_tasks[:5]  # Top 5 for ADHD

            # Mark for update
            self.pending_updates.add("sprint_context")

            logger.info(f"🎯 Sprint context updated: {sprint_name} ({mode.value})")

        except Exception as e:
            logger.error(f"Sprint context update failed: {e}")

    async def update_active_task_context(
        self,
        task_id: str,
        task_title: str,
        focus_area: str = None
    ) -> None:
        """Update context for active task."""
        try:
            self.current_context.active_task_id = task_id
            self.current_context.active_task_title = task_title
            self.current_context.current_focus_area = focus_area or task_title

            # Mark for update
            self.pending_updates.add("active_task")

            logger.debug(f"📍 Active task context updated: {task_title}")

        except Exception as e:
            logger.error(f"Active task context update failed: {e}")

    async def update_adhd_state(
        self,
        adhd_state: ADHDState,
        energy_level: str,
        recommended_duration: int = 25
    ) -> None:
        """Update ADHD state for context adaptation."""
        try:
            previous_state = self.current_context.adhd_state

            self.current_context.adhd_state = adhd_state
            self.current_context.energy_level = energy_level
            self.current_context.recommended_task_duration = recommended_duration

            # Adjust break frequency based on state
            if adhd_state == ADHDState.HYPERFOCUS:
                self.current_context.break_frequency = 30  # Longer for hyperfocus
            elif adhd_state == ADHDState.LOW_ENERGY:
                self.current_context.break_frequency = 15  # More frequent breaks
            else:
                self.current_context.break_frequency = 25  # Standard Pomodoro

            # Mark for update if state changed significantly
            if previous_state != adhd_state:
                self.pending_updates.add("adhd_state")
                logger.info(f"🧠 ADHD state updated: {previous_state.value} → {adhd_state.value}")

        except Exception as e:
            logger.error(f"ADHD state update failed: {e}")

    async def update_automation_status(
        self,
        implicit_features: List[str],
        next_actions: List[str],
        system_health: Dict[str, Any]
    ) -> None:
        """Update automation and system status."""
        try:
            self.current_context.implicit_features = implicit_features
            self.current_context.next_automated_actions = next_actions
            self.current_context.system_health = system_health

            self.pending_updates.add("automation_status")

        except Exception as e:
            logger.error(f"Automation status update failed: {e}")

    # Claude.md Generation and Updates

    async def _update_claude_context(self) -> None:
        """Update Claude.md with current context."""
        try:
            if not self.pending_updates:
                return

            # Generate updated Claude.md content
            updated_content = await self._generate_dynamic_claude_md()

            # Write to file
            await self._write_claude_md(updated_content)

            # Clear pending updates
            self.pending_updates.clear()
            self.last_update = datetime.now(timezone.utc)

            logger.info("📝 Claude.md updated with current context")

        except Exception as e:
            logger.error(f"Claude.md update failed: {e}")

    async def _generate_dynamic_claude_md(self) -> str:
        """Generate dynamic Claude.md content based on current context."""
        try:
            # Start with base content
            if not self.base_claude_md:
                content = self._get_default_claude_md()
            else:
                content = self.base_claude_md

            # Find dynamic context insertion point
            context_marker = "# Dynamic Context - Auto-Generated"
            context_end_marker = "# End Dynamic Context"

            # Remove existing dynamic context
            if context_marker in content:
                start_pos = content.find(context_marker)
                end_pos = content.find(context_end_marker)

                if end_pos > start_pos:
                    end_pos += len(context_end_marker)
                    content = content[:start_pos] + content[end_pos:]

            # Generate new dynamic context
            dynamic_context = await self._generate_context_section()

            # Insert at the beginning for visibility
            insertion_point = content.find("\n## ")  # After main title
            if insertion_point > 0:
                content = (
                    content[:insertion_point] + "\n\n" +
                    dynamic_context + "\n" +
                    content[insertion_point:]
                )
            else:
                content = dynamic_context + "\n\n" + content

            return content

        except Exception as e:
            logger.error(f"Dynamic Claude.md generation failed: {e}")
            return self.base_claude_md or self._get_default_claude_md()

    async def _generate_context_section(self) -> str:
        """Generate dynamic context section based on current state."""
        try:
            context = self.current_context

            # Select appropriate template
            template = self.context_templates.get(
                context.sprint_mode,
                self.context_templates[ContextMode.ACTIVE_DEVELOPMENT]
            )

            # Apply ADHD adaptations
            adhd_config = self.adhd_adaptations.get(
                context.adhd_state,
                self.adhd_adaptations[ADHDState.FOCUSED]
            )

            # Template variables
            template_vars = {
                "sprint_name": context.sprint_name or "No active sprint",
                "sprint_id": context.active_sprint_id or "none",
                "active_task_title": context.active_task_title or "No active task",
                "current_focus_area": context.current_focus_area or "General development",
                "task_count": len(context.priority_tasks),
                "complex_tasks": len([t for t in context.priority_tasks if t.get("complexity_score", 0) > 0.7]),
                "adhd_state": context.adhd_state.value,
                "energy_level": context.energy_level,
                "break_frequency": context.break_frequency,
                "recommended_task_duration": context.recommended_task_duration,
                "cognitive_load_status": self._get_cognitive_load_status(),
                "focus_mode_status": self._get_focus_mode_status(),
                "automation_success_rate": self._get_automation_success_rate(),
                "priority_tasks": self._format_priority_tasks(context.priority_tasks),
                "next_automated_actions": self._format_next_actions(context.next_automated_actions),
                "implicit_features": ", ".join(context.implicit_features),
                "system_status": self._format_system_status(context.system_health)
            }

            # Apply template with variables
            rendered_content = self._render_template(template, template_vars)

            # Apply ADHD adaptations
            adapted_content = self._apply_adhd_adaptations(rendered_content, adhd_config)

            # Add timestamp and automation marker
            final_content = f"""# Dynamic Context - Auto-Generated
*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
*Automation: Task Orchestrator v2*

{adapted_content}

# End Dynamic Context"""

            return final_content

        except Exception as e:
            logger.error(f"Context section generation failed: {e}")
            return "# Dynamic Context - Error generating context"

    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables."""
        try:
            rendered = template

            # Simple variable substitution
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))

            # Handle conditional blocks
            rendered = self._process_conditional_blocks(rendered, variables)

            return rendered

        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template

    def _process_conditional_blocks(self, content: str, variables: Dict[str, Any]) -> str:
        """Process conditional template blocks."""
        try:
            # Handle {{#each array}} blocks
            each_pattern = r'\{\{#each (\w+)\}\}(.*?)\{\{/each\}\}'

            def replace_each(match):
                array_name = match.group(1)
                block_content = match.group(2)
                array_data = variables.get(array_name, [])

                if not array_data:
                    return ""

                result = []
                for item in array_data:
                    item_content = block_content
                    # Replace item properties
                    if isinstance(item, dict):
                        for key, value in item.items():
                            item_content = item_content.replace(f"{{{{{key}}}}}", str(value))
                    result.append(item_content)

                return "".join(result)

            content = re.sub(each_pattern, replace_each, content, flags=re.DOTALL)
            return content

        except Exception as e:
            logger.error(f"Conditional block processing failed: {e}")
            return content

    def _apply_adhd_adaptations(self, content: str, adhd_config: Dict[str, Any]) -> str:
        """Apply ADHD-specific adaptations to content."""
        try:
            adapted = content

            # Limit instruction count
            max_instructions = adhd_config.get("max_instructions", 10)
            lines = adapted.split('\n')
            instruction_lines = [line for line in lines if line.strip().startswith('-')]

            if len(instruction_lines) > max_instructions:
                # Keep most important instructions
                important_lines = instruction_lines[:max_instructions]
                adapted = '\n'.join([
                    line for line in lines
                    if not line.strip().startswith('-') or line in important_lines
                ])

            # Adjust instruction length
            instruction_length = adhd_config.get("instruction_length", "medium")
            if instruction_length == "short":
                # Truncate long instructions
                adapted = re.sub(r'- (.{50}).*', r'- \1...', adapted)
            elif instruction_length == "minimal":
                # Keep only essential words
                adapted = re.sub(r'- (.{20}).*', r'- \1...', adapted)

            # Add visual indicators
            visual_level = adhd_config.get("visual_indicators", "medium")
            if visual_level == "high":
                adapted = self._enhance_visual_indicators(adapted)

            # Add encouragement
            encouragement_level = adhd_config.get("encouragement_level", "medium")
            if encouragement_level in ["high", "very_high"]:
                adapted = self._add_encouragement(adapted, encouragement_level)

            # Add protection reminders for hyperfocus
            if adhd_config.get("protection_reminders"):
                adapted += "\n\n⚠️ **Hyperfocus Protection**: Remember to take breaks and stay hydrated!"

            return adapted

        except Exception as e:
            logger.error(f"ADHD adaptation failed: {e}")
            return content

    def _enhance_visual_indicators(self, content: str) -> str:
        """Enhance visual indicators for ADHD users."""
        # Add more emojis and visual breaks
        enhanced = content.replace("##", "## 🎯")
        enhanced = enhanced.replace("- ✅", "- ✅ 🟢")
        enhanced = enhanced.replace("**Active**", "**🔥 Active**")
        enhanced = enhanced.replace("**Complete**", "**✅ Complete**")

        return enhanced

    def _add_encouragement(self, content: str, level: str) -> str:
        """Add encouragement for ADHD users."""
        encouragements = {
            "high": [
                "🌟 You're doing great work!",
                "💪 Keep up the excellent progress!",
                "🎯 Focused and productive - nice job!"
            ],
            "very_high": [
                "🚀 Amazing progress - you should be proud!",
                "💙 Your ADHD brain is working beautifully!",
                "✨ Each small step is a victory - celebrate it!"
            ]
        }

        messages = encouragements.get(level, [])
        if messages:
            # Add random encouragement
            import random
            encouragement = random.choice(messages)
            content = f"*{encouragement}*\n\n" + content

        return content

    # Utility Methods

    async def _check_context_changes(self) -> bool:
        """Check if context has changed significantly."""
        try:
            # This would check various sources for context changes
            # For now, simulate periodic need for updates
            if not self.last_update:
                return True

            time_since_update = (datetime.now(timezone.utc) - self.last_update).total_seconds()
            return time_since_update > self.update_frequency

        except Exception:
            return False

    async def _write_claude_md(self, content: str) -> None:
        """Write updated content to Claude.md."""
        try:
            # Ensure directory exists
            self.claude_md_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(self.claude_md_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"📝 Updated {self.claude_md_path}")

        except Exception as e:
            logger.error(f"Failed to write Claude.md: {e}")

    def _get_default_claude_md(self) -> str:
        """Get default Claude.md content."""
        return """# Dynamic Dopemux Project Configuration

## 🚀 Task Orchestrator Integration

This project uses automated PM workflow orchestration with Leantime integration.

### Current Status
- **Automation**: Active
- **ADHD Optimization**: Enabled
- **Multi-System Sync**: Active

## 🤖 Available Systems
- **ConPort**: Decision and progress tracking
- **Serena**: Code intelligence and navigation
- **Leantime**: Team project management
- **Task Orchestrator**: Automated coordination

*This file is automatically updated based on current sprint and task context.*
"""

    # Placeholder utility methods
    def _get_cognitive_load_status(self) -> str:
        return "🟡 Moderate"

    def _get_focus_mode_status(self) -> str:
        return "Normal focus mode"

    def _get_automation_success_rate(self) -> str:
        return "95%"

    def _format_priority_tasks(self, tasks: List[Dict]) -> str:
        return "\n".join([f"- {task.get('title', 'Unknown')}" for task in tasks])

    def _format_next_actions(self, actions: List[str]) -> str:
        return "\n".join([f"- {action}" for action in actions])

    def _format_system_status(self, health: Dict[str, Any]) -> str:
        return health.get("overall_status", "Unknown")

    async def close(self) -> None:
        """Shutdown Claude.md context manager."""
        logger.info("🛑 Shutting down Claude.md Context Manager...")

        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("✅ Claude.md Context Manager shutdown complete")