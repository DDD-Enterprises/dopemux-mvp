"""
MetaMCP Pre-tool Hooks for Budget-aware Query Optimization

This module implements the pre-tool hook system that optimizes queries and enforces
token budgets before tools are executed. Hooks analyze incoming tool calls and can:
- Trim query parameters to reduce token consumption
- Project token costs and prevent budget overruns
- Suggest more efficient query alternatives
- Log optimization wins for observability

Key design principles:
- ADHD-friendly: Clear feedback on optimizations made
- Non-breaking: Hooks enhance rather than replace functionality
- Observable: All optimizations and savings are logged
- Configurable: Rules can be adjusted based on usage patterns
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OptimizationAction(Enum):
    """Types of optimizations that can be applied to tool calls"""

    TRIM_RESULTS = "trim_results"
    REDUCE_SCOPE = "reduce_scope"
    CACHE_RESULT = "cache_result"
    SUGGEST_ALTERNATIVE = "suggest_alternative"
    DENY_EXPENSIVE = "deny_expensive"


@dataclass
class OptimizationResult:
    """Result of applying pre-tool hooks to a tool call"""

    action_taken: OptimizationAction
    original_call: Dict[str, Any]
    optimized_call: Dict[str, Any]
    estimated_token_savings: int
    explanation: str
    user_message: Optional[str] = None


@dataclass
class BudgetStatus:
    """Current token budget status for a session"""

    total_budget: int
    used_tokens: int
    remaining_tokens: int
    warning_threshold: int
    hard_cap: int

    @property
    def usage_percentage(self) -> float:
        return (self.used_tokens / self.total_budget) * 100

    @property
    def is_warning_level(self) -> bool:
        return self.used_tokens >= self.warning_threshold

    @property
    def is_near_cap(self) -> bool:
        return self.used_tokens >= (self.hard_cap * 0.9)


class PreToolHookManager:
    """
    Manages pre-tool hooks for budget-aware query optimization.

    This is the core component that intercepts tool calls before execution,
    applies optimizations based on role policies and current budget status,
    and provides clear feedback to users about optimizations made.
    """

    def __init__(self, policy_config: Dict[str, Any], budget_manager):
        self.policy = policy_config
        self.budget_manager = budget_manager
        self.optimization_cache = {}
        self.stats = {
            "total_calls": 0,
            "optimizations_applied": 0,
            "tokens_saved": 0,
            "calls_denied": 0,
        }

    async def pre_tool_check(
        self, call: Dict[str, Any], session_context: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[OptimizationResult]]:
        """
        Main entry point for pre-tool optimization.

        Args:
            call: The original tool call with method, parameters, etc.
            session_context: Current session state including role, budget, etc.

        Returns:
            Tuple of (optimized_call, optimizations_applied)
        """
        self.stats["total_calls"] += 1

        # Get current budget status
        budget_status = await self.budget_manager.get_budget_status(
            session_context["session_id"]
        )

        # Check if we should proceed at all
        if budget_status.is_near_cap:
            await self._handle_budget_near_cap(call, budget_status)

        optimizations = []
        optimized_call = call.copy()

        # Apply tool-specific optimizations
        tool_name = call.get("tool", "")
        method = call.get("method", "")

        if tool_name == "claude-context":
            optimization = await self._optimize_claude_context(
                optimized_call, budget_status
            )
            if optimization:
                optimizations.append(optimization)
                optimized_call = optimization.optimized_call

        elif tool_name == "task-master-ai":
            optimization = await self._optimize_task_master(
                optimized_call, budget_status
            )
            if optimization:
                optimizations.append(optimization)
                optimized_call = optimization.optimized_call

        elif tool_name == "exa":
            optimization = await self._optimize_exa_search(
                optimized_call, budget_status
            )
            if optimization:
                optimizations.append(optimization)
                optimized_call = optimization.optimized_call

        elif tool_name == "sequential-thinking":
            optimization = await self._optimize_sequential_thinking(
                optimized_call, budget_status
            )
            if optimization:
                optimizations.append(optimization)
                optimized_call = optimization.optimized_call

        elif tool_name == "zen":
            optimization = await self._optimize_zen_tools(
                optimized_call, method, budget_status
            )
            if optimization:
                optimizations.append(optimization)
                optimized_call = optimization.optimized_call

        # Apply general budget enforcement
        projected_cost = await self._estimate_token_cost(optimized_call)
        if projected_cost > budget_status.remaining_tokens:
            optimization = await self._handle_budget_exceeded(
                optimized_call, projected_cost, budget_status
            )
            if optimization:
                optimizations.append(optimization)
                optimized_call = optimization.optimized_call

        # Update statistics
        if optimizations:
            self.stats["optimizations_applied"] += len(optimizations)
            self.stats["tokens_saved"] += sum(
                opt.estimated_token_savings for opt in optimizations
            )

        # Log optimizations for observability
        await self._log_optimizations(
            call, optimized_call, optimizations, session_context
        )

        return optimized_call, optimizations

    async def _optimize_claude_context(
        self, call: Dict[str, Any], budget: BudgetStatus
    ) -> Optional[OptimizationResult]:
        """Optimize claude-context search calls to reduce token consumption."""
        params = call.get("args", {})

        # Get trim rules from policy
        trim_rules = (
            self.policy.get("rules", {}).get("trims", {}).get("claude-context", {})
        )

        params.copy()
        optimized = False

        # Limit search results
        max_results = trim_rules.get("max_results", 3)
        if params.get("maxResults", 10) > max_results:
            params["maxResults"] = max_results
            optimized = True

        # Limit file size processing
        max_file_size = trim_rules.get("max_file_size", 50000)
        if "maxFileSize" not in params:
            params["maxFileSize"] = max_file_size
            optimized = True

        # Filter by preferred file types if not specified
        preferred_types = trim_rules.get(
            "preferred_file_types", [".py", ".js", ".ts", ".md"]
        )
        if "fileTypes" not in params:
            params["fileTypes"] = preferred_types
            optimized = True

        if optimized:
            estimated_savings = min(
                2000, int(budget.remaining_tokens * 0.15)
            )  # Estimated 15% savings

            return OptimizationResult(
                action_taken=OptimizationAction.TRIM_RESULTS,
                original_call=call,
                optimized_call={**call, "args": params},
                estimated_token_savings=estimated_savings,
                explanation=f"Limited search to {max_results} results, preferred file types, and {max_file_size} char files",
                user_message=f"🎯 Optimized search scope - estimated {estimated_savings} tokens saved",
            )

        return None

    async def _optimize_task_master(
        self, call: Dict[str, Any], budget: BudgetStatus
    ) -> Optional[OptimizationResult]:
        """Optimize task-master-ai calls to reduce verbose responses."""
        params = call.get("args", {})
        method = call.get("method", "")

        if method == "list_tasks":
            trim_rules = (
                self.policy.get("rules", {})
                .get("trims", {})
                .get("task-master-ai", {})
                .get("list_tasks", {})
            )

            params.copy()
            optimized = False

            # Limit number of tasks returned
            limit = trim_rules.get("limit", 50)
            if params.get("limit", 100) > limit:
                params["limit"] = limit
                optimized = True

            # Exclude completed tasks by default
            if "includeCompleted" not in params and not trim_rules.get(
                "include_completed", False
            ):
                params["includeCompleted"] = False
                optimized = True

            # Limit description length
            max_desc_len = trim_rules.get("max_description_length", 200)
            if "maxDescriptionLength" not in params:
                params["maxDescriptionLength"] = max_desc_len
                optimized = True

            if optimized:
                estimated_savings = min(1500, int(budget.remaining_tokens * 0.10))

                return OptimizationResult(
                    action_taken=OptimizationAction.TRIM_RESULTS,
                    original_call=call,
                    optimized_call={**call, "args": params},
                    estimated_token_savings=estimated_savings,
                    explanation=f"Limited to {limit} active tasks with {max_desc_len} char descriptions",
                    user_message=f"📋 Streamlined task list - estimated {estimated_savings} tokens saved",
                )

        return None

    async def _optimize_exa_search(
        self, call: Dict[str, Any], budget: BudgetStatus
    ) -> Optional[OptimizationResult]:
        """Optimize exa web search to prevent overwhelming results."""
        params = call.get("args", {})
        trim_rules = self.policy.get("rules", {}).get("trims", {}).get("exa", {})

        params.copy()
        optimized = False

        # Ensure minimum query length for quality results
        query = params.get("query", "")
        min_length = trim_rules.get("min_query_length", 12)
        if len(query) < min_length:
            return OptimizationResult(
                action_taken=OptimizationAction.SUGGEST_ALTERNATIVE,
                original_call=call,
                optimized_call=call,  # No change to call
                estimated_token_savings=0,
                explanation=f"Query too short ({len(query)} chars), minimum {min_length} chars recommended",
                user_message=f"💡 Try a more specific search query (at least {min_length} characters)",
            )

        # Limit number of results
        max_results = trim_rules.get("max_results", 10)
        if params.get("numResults", 20) > max_results:
            params["numResults"] = max_results
            optimized = True

        # Get summaries instead of full text
        if params.get("includeText", True) and not trim_rules.get(
            "include_text", False
        ):
            params["includeText"] = False
            params["includeSummary"] = True
            optimized = True

        # Exclude low-value domains
        excluded = trim_rules.get("exclude_domains", [])
        if excluded and "excludeDomains" not in params:
            params["excludeDomains"] = excluded
            optimized = True

        if optimized:
            estimated_savings = min(3000, int(budget.remaining_tokens * 0.20))

            return OptimizationResult(
                action_taken=OptimizationAction.TRIM_RESULTS,
                original_call=call,
                optimized_call={**call, "args": params},
                estimated_token_savings=estimated_savings,
                explanation=f"Limited to {max_results} results with summaries, excluded low-value domains",
                user_message=f"🔍 Focused search results - estimated {estimated_savings} tokens saved",
            )

        return None

    async def _optimize_sequential_thinking(
        self, call: Dict[str, Any], budget: BudgetStatus
    ) -> Optional[OptimizationResult]:
        """Optimize sequential-thinking to balance depth with token usage."""
        params = call.get("args", {})
        trim_rules = (
            self.policy.get("rules", {}).get("trims", {}).get("sequential-thinking", {})
        )

        params.copy()
        optimized = False

        # Limit thinking depth for token efficiency
        max_depth = trim_rules.get("max_thinking_depth", 5)
        if params.get("maxDepth", 10) > max_depth:
            params["maxDepth"] = max_depth
            optimized = True

        # Enable focus mode for concise reasoning
        if trim_rules.get("focus_mode", True) and "focusMode" not in params:
            params["focusMode"] = True
            optimized = True

        # Set time limit to prevent runaway thinking
        time_limit = trim_rules.get("time_limit", 300)  # 5 minutes
        if "timeLimitSeconds" not in params:
            params["timeLimitSeconds"] = time_limit
            optimized = True

        if optimized:
            estimated_savings = min(4000, int(budget.remaining_tokens * 0.25))

            return OptimizationResult(
                action_taken=OptimizationAction.REDUCE_SCOPE,
                original_call=call,
                optimized_call={**call, "args": params},
                estimated_token_savings=estimated_savings,
                explanation=f"Limited thinking to {max_depth} levels, focus mode, {time_limit}s timeout",
                user_message=f"🧠 Balanced thinking depth - estimated {estimated_savings} tokens saved",
            )

        return None

    async def _optimize_zen_tools(
        self, call: Dict[str, Any], method: str, budget: BudgetStatus
    ) -> Optional[OptimizationResult]:
        """Optimize zen multi-model tools based on method and budget."""
        params = call.get("args", {})
        trim_rules = self.policy.get("rules", {}).get("trims", {}).get("zen", {})

        if method == "consensus":
            consensus_rules = trim_rules.get("consensus", {})

            # Limit number of models for efficiency
            max_models = consensus_rules.get("max_models", 3)
            if params.get("models", 5) > max_models:
                params["models"] = max_models

                estimated_savings = min(5000, int(budget.remaining_tokens * 0.30))

                return OptimizationResult(
                    action_taken=OptimizationAction.REDUCE_SCOPE,
                    original_call=call,
                    optimized_call={**call, "args": params},
                    estimated_token_savings=estimated_savings,
                    explanation=f"Limited consensus to {max_models} models for efficiency",
                    user_message=f"🤝 Streamlined consensus - estimated {estimated_savings} tokens saved",
                )

        elif method == "codereview":
            review_rules = trim_rules.get("codereview", {})

            # Focus on specific areas
            focus_areas = review_rules.get(
                "focus_areas", ["security", "performance", "maintainability"]
            )
            if "focusAreas" not in params:
                params["focusAreas"] = focus_areas

                estimated_savings = min(3000, int(budget.remaining_tokens * 0.20))

                return OptimizationResult(
                    action_taken=OptimizationAction.REDUCE_SCOPE,
                    original_call=call,
                    optimized_call={**call, "args": params},
                    estimated_token_savings=estimated_savings,
                    explanation=f"Focused review on {', '.join(focus_areas)}",
                    user_message=f"🔍 Targeted code review - estimated {estimated_savings} tokens saved",
                )

        return None

    async def _handle_budget_exceeded(
        self, call: Dict[str, Any], projected_cost: int, budget: BudgetStatus
    ) -> Optional[OptimizationResult]:
        """Handle cases where projected token cost exceeds remaining budget."""
        overage = projected_cost - budget.remaining_tokens

        # Try to reduce scope to fit budget
        tool_name = call.get("tool", "")

        if tool_name in ["claude-context", "exa", "task-master-ai"]:
            # For search tools, suggest reducing scope
            return OptimizationResult(
                action_taken=OptimizationAction.SUGGEST_ALTERNATIVE,
                original_call=call,
                optimized_call=call,
                estimated_token_savings=0,
                explanation=f"Projected cost ({projected_cost}) exceeds budget by {overage} tokens",
                user_message=f"⚠️  Query too large for remaining budget. Try: smaller search scope, fewer results, or more specific terms",
            )

        else:
            # For other tools, deny the expensive operation
            return OptimizationResult(
                action_taken=OptimizationAction.DENY_EXPENSIVE,
                original_call=call,
                optimized_call={},  # Empty call means denied
                estimated_token_savings=0,
                explanation=f"Tool call denied - projected cost ({projected_cost}) exceeds remaining budget ({budget.remaining_tokens})",
                user_message=f"🚫 Operation requires {projected_cost} tokens but only {budget.remaining_tokens} remaining. Consider switching to a role with higher budget or try a simpler approach.",
            )

    async def _handle_budget_near_cap(self, call: Dict[str, Any], budget: BudgetStatus):
        """Provide warnings when approaching budget limits."""
        if budget.is_near_cap:
            logger.warning(
                f"Session approaching token cap: {budget.usage_percentage:.1f}% used"
            )
            # Could trigger UI notification here

    async def _estimate_token_cost(self, call: Dict[str, Any]) -> int:
        """Estimate token cost for a tool call based on historical data and heuristics."""
        tool_name = call.get("tool", "")
        method = call.get("method", "")

        # Base costs per tool (from historical analysis)
        base_costs = {
            "claude-context": 1200,
            "sequential-thinking": 4000,
            "zen": 2500,
            "exa": 1500,
            "task-master-ai": 800,
            "context7": 600,
            "serena": 400,
            "conport": 300,
            "cli": 200,
            "playwright": 1000,
        }

        base_cost = base_costs.get(tool_name, 500)

        # Adjust based on parameters
        params = call.get("args", {})
        multiplier = 1.0

        if tool_name == "claude-context":
            max_results = params.get("maxResults", 10)
            multiplier = min(max_results / 3.0, 3.0)  # Scale with results, cap at 3x

        elif tool_name == "sequential-thinking":
            max_depth = params.get("maxDepth", 5)
            multiplier = min(max_depth / 5.0, 2.0)  # Scale with depth, cap at 2x

        elif tool_name == "zen":
            if method == "consensus":
                models = params.get("models", 3)
                multiplier = models / 3.0

        return int(base_cost * multiplier)

    async def _log_optimizations(
        self,
        original_call: Dict[str, Any],
        optimized_call: Dict[str, Any],
        optimizations: List[OptimizationResult],
        session_context: Dict[str, Any],
    ):
        """Log optimization results for observability and learning."""
        if not optimizations:
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_context.get("session_id"),
            "role": session_context.get("role"),
            "tool": original_call.get("tool"),
            "method": original_call.get("method"),
            "optimizations": [
                {
                    "action": opt.action_taken.value,
                    "token_savings": opt.estimated_token_savings,
                    "explanation": opt.explanation,
                }
                for opt in optimizations
            ],
            "total_savings": sum(opt.estimated_token_savings for opt in optimizations),
        }

        logger.info(f"PreToolHook optimization applied: {log_entry}")

        # Could also store in metrics database for dashboard

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get current optimization statistics for monitoring dashboard."""
        return {
            **self.stats,
            "optimization_rate": self.stats["optimizations_applied"]
            / max(self.stats["total_calls"], 1),
            "average_savings_per_optimization": self.stats["tokens_saved"]
            / max(self.stats["optimizations_applied"], 1),
        }


# Example usage and testing helpers
async def example_usage():
    """Example of how the pre-tool hook system works in practice."""

    # Mock policy configuration
    policy = {
        "rules": {
            "trims": {
                "claude-context": {
                    "max_results": 3,
                    "max_file_size": 50000,
                    "preferred_file_types": [".py", ".js"],
                },
                "exa": {"max_results": 10, "include_text": False},
            }
        }
    }

    # Mock budget manager
    class MockBudgetManager:
        async def get_budget_status(self, session_id):
            return BudgetStatus(
                total_budget=60000,
                used_tokens=45000,
                remaining_tokens=15000,
                warning_threshold=48000,
                hard_cap=120000,
            )

    # Initialize hook manager
    hook_manager = PreToolHookManager(policy, MockBudgetManager())

    # Example tool call that will be optimized
    original_call = {
        "tool": "claude-context",
        "method": "search",
        "args": {
            "query": "authentication implementation",
            "maxResults": 20,  # Will be trimmed to 3
            "includeTests": True,
        },
    }

    session_context = {"session_id": "test-session-123", "role": "developer"}

    # Apply optimizations
    optimized_call, optimizations = await hook_manager.pre_tool_check(
        original_call, session_context
    )

    print("Original call:", original_call)
    print("Optimized call:", optimized_call)
    print("Optimizations applied:", len(optimizations))

    for opt in optimizations:
        print(f"- {opt.action_taken.value}: {opt.explanation}")
        if opt.user_message:
            print(f"  User message: {opt.user_message}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
