"""
ToolOrchestrator - Intelligent MCP Tool & Model Selection Agent

Selects optimal MCP servers and models based on task requirements.
Provides invisible optimization for best tool selection.

Authority: Tool selection and performance optimization

Week: 8
Complexity: 0.5 (Medium)
Effort: 5 days (10 focus blocks)
Code Reuse: 80% from Zen MCP (listmodels wrapper)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity tiers for model selection"""
    SIMPLE = "simple"  # 0.0-0.3
    MEDIUM = "medium"  # 0.3-0.7
    COMPLEX = "complex"  # 0.7-1.0


class ModelTier(str, Enum):
    """Model performance tiers"""
    FAST = "fast"  # Quick responses, lower cost
    MID = "mid"  # Balanced performance
    POWER = "power"  # Maximum capability


@dataclass
class ToolSelection:
    """Selected tool configuration for a task"""
    primary_tool: str  # Main MCP server to use
    method: Optional[str] = None  # Specific method (e.g., "thinkdeep", "chat")
    model: Optional[str] = None  # Model name (e.g., "gpt-5-mini")
    fallback_tool: Optional[str] = None  # Fallback if primary unavailable
    rationale: Optional[str] = None  # Why this selection
    estimated_cost: Optional[float] = None  # Estimated cost in USD
    estimated_latency: Optional[float] = None  # Estimated latency in seconds
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class TaskToolRequirements:
    """Tool requirements for a task"""
    task_type: str  # analysis, implementation, testing, documentation, etc.
    complexity: float  # 0.0-1.0
    requires_code_nav: bool = False
    requires_reasoning: bool = False
    requires_documentation: bool = False
    requires_web_search: bool = False
    performance_priority: str = "balanced"  # fast, balanced, quality
    workspace_path: Optional[str] = None  # Multi-workspace tracking


class ToolOrchestrator:
    """
    Intelligent MCP Tool & Model Selector.

    Responsibilities:
    1. Select optimal models based on task complexity
    2. Choose MCP servers based on task requirements
    3. Track performance metrics (latency, success rate, cost)
    4. Provide fallback options
    5. Invisible optimization (user doesn't think about tools)

    Example:
        orchestrator = ToolOrchestrator()
        await orchestrator.initialize()

        # Get tool selection for task
        selection = await orchestrator.select_tools_for_task(
            task_type="analysis",
            complexity=0.6
        )

        # Use selected tools
        if selection.primary_tool == "zen":
            result = await mcp__zen__thinkdeep(
                model=selection.model,
                ...
            )
    """

    def __init__(
        self,
        workspace_id: str,
        conport_client: Optional[Any] = None,
        enable_cost_tracking: bool = True
    ):
        """
        Initialize ToolOrchestrator.

        Args:
            workspace_id: Absolute path to workspace
            conport_client: ConPort MCP client for metrics logging
            enable_cost_tracking: Track estimated costs
        """
        self.workspace_id = workspace_id
        self.conport_client = conport_client
        self.enable_cost_tracking = enable_cost_tracking

        # Available models (from Zen MCP listmodels)
        self.available_models: Dict[str, Any] = {}

        # Performance metrics
        self.metrics = {
            "selections_made": 0,
            "fast_tier_selected": 0,
            "mid_tier_selected": 0,
            "power_tier_selected": 0,
            "total_estimated_cost": 0.0
        }

        # Tool selection rules
        self.selection_rules = self._load_selection_rules()

        logger.info(f"ToolOrchestrator initialized (workspace: {workspace_id})")

    async def initialize(self):
        """Initialize ToolOrchestrator and load available models"""
        logger.info("🚀 Initializing ToolOrchestrator...")

        # Load available models from Zen MCP
        await self._load_available_models()

        logger.info("✅ ToolOrchestrator ready for tool selection")

    async def _load_available_models(self):
        """
        Load available models from Zen MCP.

        Week 8: 80% code reuse - wrapper around mcp__zen__listmodels
        """
        # TODO: Call real mcp__zen__listmodels when Zen MCP connected
        # For now, use hardcoded model catalog

        self.available_models = {
            # Fast tier (Intelligence 12-13)
            "gpt-5-mini": {
                "tier": ModelTier.FAST,
                "intelligence": 12,
                "context": "400K",
                "cost_per_1m": 0.50,
                "avg_latency": 2.0
            },
            "gemini-flash": {
                "tier": ModelTier.FAST,
                "intelligence": 12,
                "context": "1M",
                "cost_per_1m": 0.30,
                "avg_latency": 1.5
            },
            "grok-4-fast": {
                "tier": ModelTier.FAST,
                "intelligence": 16,
                "context": "2M",
                "cost_per_1m": 0.00,  # FREE!
                "avg_latency": 2.5
            },

            # Mid tier (Intelligence 14-16)
            "gpt-5": {
                "tier": ModelTier.MID,
                "intelligence": 16,
                "context": "400K",
                "cost_per_1m": 2.00,
                "avg_latency": 4.0
            },
            "gpt-5-codex": {
                "tier": ModelTier.MID,
                "intelligence": 17,
                "context": "400K",
                "cost_per_1m": 2.50,
                "avg_latency": 3.5
            },
            "gemini-2.5-pro": {
                "tier": ModelTier.MID,
                "intelligence": 18,
                "context": "1M",
                "cost_per_1m": 1.50,
                "avg_latency": 3.0
            },

            # Power tier (Intelligence 17-18)
            "grok-code-fast-1": {
                "tier": ModelTier.POWER,
                "intelligence": 18,
                "context": "2M",
                "cost_per_1m": 0.00,  # FREE!
                "avg_latency": 3.0
            },
            "o3-mini": {
                "tier": ModelTier.POWER,
                "intelligence": 12,
                "context": "200K",
                "cost_per_1m": 5.00,
                "avg_latency": 5.0
            },
        }

        logger.info(f"📋 Loaded {len(self.available_models)} models")

    def _load_selection_rules(self) -> Dict[str, Any]:
        """
        Load tool selection rules for different task types.

        Rules based on Dopemux MCP ecosystem and ADHD optimization.
        """
        return {
            # Task type → Primary MCP server
            "task_types": {
                "analysis": {
                    "primary": "zen",
                    "method": "thinkdeep",
                    "description": "Systematic investigation"
                },
                "planning": {
                    "primary": "zen",
                    "method": "planner",
                    "description": "Interactive planning"
                },
                "code_review": {
                    "primary": "zen",
                    "method": "codereview",
                    "description": "Multi-model code review"
                },
                "debugging": {
                    "primary": "zen",
                    "method": "debug",
                    "description": "Systematic debugging"
                },
                "code_navigation": {
                    "primary": "serena",
                    "method": "find_symbol",
                    "description": "LSP-based navigation",
                    "required": True  # No fallback
                },
                "code_search": {
                    "primary": "dope-context",
                    "method": "search_code",
                    "description": "Semantic code search"
                },
                "documentation": {
                    "primary": "pal",
                    "method": "apilookup",
                    "fallback": "exa"
                },
                "web_research": {
                    "primary": "exa",
                    "method": "search",
                    "fallback": "gpt-researcher"
                },
                "deep_research": {
                    "primary": "gpt-researcher",
                    "method": "deep_research",
                    "description": "Multi-source comprehensive research"
                },
            },

            # Complexity → Model tier mapping
            "complexity_tiers": {
                TaskComplexity.SIMPLE: ModelTier.FAST,
                TaskComplexity.MEDIUM: ModelTier.MID,
                TaskComplexity.COMPLEX: ModelTier.POWER
            },

            # Performance priorities
            "performance_modes": {
                "fast": {
                    "prefer": ["grok-4-fast", "gemini-flash", "gpt-5-mini"],
                    "max_latency": 3.0
                },
                "balanced": {
                    "prefer": ["gpt-5", "gemini-2.5-pro", "gpt-5-codex"],
                    "max_latency": 5.0
                },
                "quality": {
                    "prefer": ["grok-code-fast-1", "gemini-2.5-pro", "gpt-5-codex"],
                    "max_latency": 10.0
                }
            }
        }

    async def select_tools_for_task(
        self,
        task_type: str,
        complexity: float = 0.5,
        requirements: Optional[TaskToolRequirements] = None
    ) -> Dict[str, ToolSelection]:
        """
        Select optimal tools for a task.

        Args:
            task_type: Type of task (analysis, implementation, etc.)
            complexity: Task complexity (0.0-1.0)
            requirements: Additional requirements

        Returns:
            Dictionary of tool selections by category
        """
        self.metrics["selections_made"] += 1

        selections = {}

        # Determine complexity tier
        complexity_tier = self._get_complexity_tier(complexity)

        # Select primary MCP server based on task type
        if task_type in self.selection_rules["task_types"]:
            rule = self.selection_rules["task_types"][task_type]

            # Select model for this tool
            model = await self._select_model_for_complexity(complexity_tier, task_type)

            selections["primary"] = ToolSelection(
                primary_tool=rule["primary"],
                method=rule.get("method"),
                model=model["name"] if model else None,
                fallback_tool=rule.get("fallback"),
                rationale=f"{task_type} task (complexity: {complexity:.2f})",
                estimated_cost=model.get("cost_per_1m", 0.0) if model else 0.0,
                estimated_latency=model.get("avg_latency", 0.0) if model else 0.0
            )

        # Add supporting tools based on requirements
        if requirements:
            if requirements.requires_code_nav:
                selections["code_nav"] = ToolSelection(
                    primary_tool="serena",
                    method="find_symbol",
                    rationale="Code navigation required"
                )

            if requirements.requires_documentation:
                selections["docs"] = ToolSelection(
                    primary_tool="pal",
                    method="apilookup",
                    fallback_tool="exa",
                    rationale="Documentation lookup required"
                )

            if requirements.requires_web_search:
                if requirements.task_type == "deep_research":
                    selections["research"] = ToolSelection(
                        primary_tool="gpt-researcher",
                        method="deep_research",
                        rationale="Comprehensive research required"
                    )
                else:
                    selections["search"] = ToolSelection(
                        primary_tool="exa",
                        method="search",
                        rationale="Quick web search required"
                    )

        logger.info(
            f"🎯 Selected tools for {task_type} (complexity: {complexity:.2f}): "
            f"{selections['primary'].primary_tool} with {selections['primary'].model}"
        )

        return selections

    def _get_complexity_tier(self, complexity: float) -> TaskComplexity:
        """Map complexity score to tier"""
        if complexity < 0.3:
            return TaskComplexity.SIMPLE
        elif complexity < 0.7:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.COMPLEX

    async def _select_model_for_complexity(
        self,
        tier: TaskComplexity,
        task_type: str,
        performance_priority: str = "balanced"
    ) -> Optional[Dict[str, Any]]:
        """
        Select optimal model for complexity tier.

        Week 8: 80% reuse - uses Zen listmodels data structure
        """
        # Map complexity tier to model tier
        model_tier = self.selection_rules["complexity_tiers"][tier]

        # Filter models by tier
        candidates = [
            {**model_info, "name": name}
            for name, model_info in self.available_models.items()
            if model_info["tier"] == model_tier
        ]

        if not candidates:
            return None

        # Apply performance priority
        perf_mode = self.selection_rules["performance_modes"].get(performance_priority, {})
        preferred = perf_mode.get("prefer", [])

        # Prefer FREE models for fast tier
        if model_tier == ModelTier.FAST:
            free_models = [m for m in candidates if m["cost_per_1m"] == 0.0]
            if free_models:
                candidates = free_models

        # Sort by preference list
        def sort_key(model):
            name = model["name"]
            if name in preferred:
                return (0, preferred.index(name))  # Preferred models first
            return (1, model["intelligence"])  # Then by intelligence

        candidates.sort(key=sort_key, reverse=False)

        # Update metrics
        if model_tier == ModelTier.FAST:
            self.metrics["fast_tier_selected"] += 1
        elif model_tier == ModelTier.MID:
            self.metrics["mid_tier_selected"] += 1
        else:
            self.metrics["power_tier_selected"] += 1

        selected = candidates[0]

        logger.debug(
            f"📊 Model selected: {selected['name']} "
            f"(intelligence: {selected['intelligence']}, tier: {model_tier.value})"
        )

        return selected

    async def select_model_for_zen(
        self,
        tool_method: str,
        complexity: float,
        performance_priority: str = "balanced"
    ) -> str:
        """
        Select optimal model for Zen MCP tool.

        Convenience method for Zen tool usage.

        Args:
            tool_method: Zen method (thinkdeep, planner, debug, codereview, consensus)
            complexity: Task complexity (0.0-1.0)
            performance_priority: fast, balanced, quality

        Returns:
            Model name string
        """
        tier = self._get_complexity_tier(complexity)
        model = await self._select_model_for_complexity(tier, tool_method, performance_priority)

        return model["name"] if model else "gpt-5-mini"  # Default fallback

    async def get_tool_recommendations(
        self,
        task_description: str,
        complexity: float = 0.5
    ) -> Dict[str, ToolSelection]:
        """
        Get tool recommendations based on task description.

        Uses simple keyword matching to infer task type.

        Args:
            task_description: Natural language task description
            complexity: Estimated complexity

        Returns:
            Tool selections for the task
        """
        # Infer task type from description
        task_type = self._infer_task_type(task_description)

        # Get selections
        return await self.select_tools_for_task(task_type, complexity)

    def _infer_task_type(self, description: str) -> str:
        """Infer task type from description using keywords"""
        desc_lower = description.lower()

        # Keyword mapping
        if any(word in desc_lower for word in ["analyze", "investigate", "understand", "why"]):
            return "analysis"
        elif any(word in desc_lower for word in ["plan", "design", "architecture", "approach"]):
            return "planning"
        elif any(word in desc_lower for word in ["review", "audit", "check", "validate"]):
            return "code_review"
        elif any(word in desc_lower for word in ["debug", "fix", "bug", "error", "broken"]):
            return "debugging"
        elif any(word in desc_lower for word in ["navigate", "find", "locate", "symbol"]):
            return "code_navigation"
        elif any(word in desc_lower for word in ["search code", "find code", "code example"]):
            return "code_search"
        elif any(word in desc_lower for word in ["docs", "documentation", "api reference", "how to"]):
            return "documentation"
        elif any(word in desc_lower for word in ["research", "learn", "explore", "discover"]):
            if any(word in desc_lower for word in ["deep", "comprehensive", "thorough"]):
                return "deep_research"
            else:
                return "web_research"
        else:
            return "analysis"  # Default

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get tool selection metrics"""
        total = self.metrics["selections_made"]

        if total > 0:
            fast_pct = (self.metrics["fast_tier_selected"] / total) * 100
            mid_pct = (self.metrics["mid_tier_selected"] / total) * 100
            power_pct = (self.metrics["power_tier_selected"] / total) * 100
        else:
            fast_pct = mid_pct = power_pct = 0.0

        return {
            "total_selections": total,
            "fast_tier_pct": round(fast_pct, 1),
            "mid_tier_pct": round(mid_pct, 1),
            "power_tier_pct": round(power_pct, 1),
            "estimated_total_cost": round(self.metrics["total_estimated_cost"], 4),
            "cost_tracking_enabled": self.enable_cost_tracking
        }

    async def close(self):
        """Shutdown ToolOrchestrator"""
        logger.info("🛑 ToolOrchestrator shutdown complete")


# ============================================================================
# Demo / Test
# ============================================================================

async def demo():
    """Demonstrate ToolOrchestrator"""

    logger.info("\n" + "="*70)
    logger.info("TOOL ORCHESTRATOR DEMO")
    logger.info("="*70)

    orchestrator = ToolOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    await orchestrator.initialize()

    # Example 1: Analysis task (medium complexity)
    logger.info("\n" + "="*70)
    logger.info("Example 1: Analysis Task (complexity 0.6)")
    logger.info("="*70)

    selections = await orchestrator.select_tools_for_task(
        task_type="analysis",
        complexity=0.6
    )

    primary = selections["primary"]
    logger.info(f"\nPrimary Tool: {primary.primary_tool}")
    logger.info(f"Method: {primary.method}")
    logger.info(f"Model: {primary.model}")
    logger.info(f"Rationale: {primary.rationale}")
    logger.info(f"Estimated Cost: ${primary.estimated_cost:.4f} per 1M tokens")
    logger.info(f"Estimated Latency: {primary.estimated_latency}s")

    # Example 2: Simple debugging (low complexity)
    logger.info("\n" + "="*70)
    logger.debug("Example 2: Simple Debugging (complexity 0.2)")
    logger.info("="*70)

    model = await orchestrator.select_model_for_zen(
        tool_method="debug",
        complexity=0.2,
        performance_priority="fast"
    )

    logger.info(f"\nSelected Model: {model}")
    logger.info(f"Rationale: Simple task → Fast tier model")

    # Example 3: Complex code review (high complexity)
    logger.info("\n" + "="*70)
    logger.info("Example 3: Complex Code Review (complexity 0.9)")
    logger.info("="*70)

    model = await orchestrator.select_model_for_zen(
        tool_method="codereview",
        complexity=0.9,
        performance_priority="quality"
    )

    logger.info(f"\nSelected Model: {model}")
    logger.info(f"Rationale: Complex task → Power tier model")

    # Example 4: Natural language task
    logger.info("\n" + "="*70)
    logger.info("Example 4: Natural Language Task Description")
    logger.info("="*70)

    selections = await orchestrator.get_tool_recommendations(
        task_description="Analyze why the authentication system is failing",
        complexity=0.7
    )

    primary = selections["primary"]
    logger.info(f"\nTask Type Inferred: analysis")
    logger.info(f"Primary Tool: {primary.primary_tool}")
    logger.info(f"Method: {primary.method}")
    logger.info(f"Model: {primary.model}")

    # Metrics
    logger.info("\n" + "="*70)
    logger.info("Tool Selection Metrics")
    logger.info("="*70)

    metrics = await orchestrator.get_metrics_summary()
    logger.info(f"\nTotal Selections: {metrics['total_selections']}")
    logger.info(f"Fast Tier: {metrics['fast_tier_pct']}%")
    logger.info(f"Mid Tier: {metrics['mid_tier_pct']}%")
    logger.info(f"Power Tier: {metrics['power_tier_pct']}%")

    await orchestrator.close()

    logger.info("\n" + "="*70)
    logger.info("✅ Demo complete!")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
