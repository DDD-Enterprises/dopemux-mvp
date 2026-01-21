"""Memory adapter for ConPort logging of GP attempts and failure signals."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .conport_client import ConPortClient


class MemoryAdapter:
    """Adapter for logging genetic agent attempts and learning to ConPort."""

    def __init__(self, conport_client: ConPortClient, workspace_id: str):

import logging

logger = logging.getLogger(__name__)

        self.conport_client = conport_client
        self.workspace_id = workspace_id
        self.session_start_time = datetime.now()

    async def log_attempt(self, attempt_number: int, operator: str, fitness_score: float,
                         context: Dict[str, Any], success: bool = False) -> None:
        """Log a GP attempt with metadata for learning."""

        # Structure the progress entry for ConPort
        progress_data = {
            "status": "completed" if success else "in_progress",
            "description": f"GP Attempt {attempt_number}: {operator} (fitness: {fitness_score:.3f})",
            "parent_id": None,  # Could link to parent repair task
            "linked_item_type": "decision",
            "linked_item_id": "385"  # Link to the GP research decision
        }

        # Log to ConPort progress tracking
        try:
            async with self.conport_client:
                result = await self.conport_client.log_progress(
                    workspace_id=self.workspace_id,
                    **progress_data
                )
                logger.info(f"Logged GP attempt {attempt_number} to ConPort: {result.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to log GP attempt to ConPort: {e}")

        # Log operator success patterns for learning
        if success:
            await self._log_operator_success(operator, fitness_score, context)

    async def log_failure_signals(self, failure_signals: List[str], context: Dict[str, Any]) -> None:
        """Log failure patterns for future GP learning."""

        # Create a custom data entry for failure patterns
        failure_data = {
            "category": "gp_failure_patterns",
            "key": f"failure_{datetime.now().isoformat()}",
            "value": {
                "signals": failure_signals,
                "context": {
                    "file_path": context.get("file_path", ""),
                    "line_number": context.get("line", 0),
                    "complexity_score": context.get("complexity", {}).get("score", 0.5),
                    "similar_patterns_count": len(context.get("similar_patterns", {}).get("results", []))
                },
                "timestamp": datetime.now().isoformat()
            }
        }

        try:
            async with self.conport_client:
                result = await self.conport_client.log_custom_data(
                    workspace_id=self.workspace_id,
                    **failure_data
                )
                logger.error(f"Logged failure signals to ConPort: {result.get('key', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to log failure signals to ConPort: {e}")

    async def _log_operator_success(self, operator: str, fitness_score: float,
                                   context: Dict[str, Any]) -> None:
        """Log successful operator patterns for future selection bias."""

        success_data = {
            "category": "gp_operator_success",
            "key": f"success_{operator}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": {
                "operator": operator,
                "fitness_score": fitness_score,
                "context_complexity": context.get("complexity", {}).get("score", 0.5),
                "lines_of_code": len(context.get("description", "").split()),
                "timestamp": datetime.now().isoformat()
            }
        }

        try:
            async with self.conport_client:
                result = await self.conport_client.log_custom_data(
                    workspace_id=self.workspace_id,
                    **success_data
                )
                logger.info(f"Logged operator success to ConPort: {result.get('key', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to log operator success to ConPort: {e}")

    async def get_operator_history(self, operator: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Retrieve historical performance of a specific operator."""

        try:
            async with self.conport_client:
                # Search for operator success patterns
                results = await self.conport_client.search_custom_data_value_fts(
                    workspace_id=self.workspace_id,
                    query_term=f"operator.*{operator}",
                    category_filter="gp_operator_success",
                    limit=50
                )

                # Filter by time if needed
                return [item["value"] for item in results.get("results", [])]
        except Exception as e:
            logger.error(f"Failed to retrieve operator history: {e}")
            return []

    async def get_operator_success_patterns(self, limit: int = 10) -> Dict[str, Dict[str, Any]]:
        """Retrieve successful operator patterns for GP learning."""

        try:
            async with self.conport_client:
                results = await self.conport_client.get_custom_data(
                    workspace_id=self.workspace_id,
                    category="gp_operator_success"
                )

                # Aggregate success patterns by operator
                operator_stats = {}
                for key, data in results.get("gp_operator_success", {}).items():
                    operator = data.get("operator", "unknown")
                    fitness = data.get("fitness_score", 0.0)
                    complexity = data.get("context_complexity", 0.5)

                    if operator not in operator_stats:
                        operator_stats[operator] = {
                            "operator": operator,
                            "total_uses": 0,
                            "total_fitness": 0.0,
                            "avg_fitness": 0.0,
                            "success_rate": 0.0,
                            "complexity_matches": [],
                            "recent_uses": []
                        }

                    operator_stats[operator]["total_uses"] += 1
                    operator_stats[operator]["total_fitness"] += fitness
                    operator_stats[operator]["complexity_matches"].append(complexity)
                    operator_stats[operator]["recent_uses"].append(data)

                # Calculate averages and sort by success rate
                for op_data in operator_stats.values():
                    op_data["avg_fitness"] = op_data["total_fitness"] / op_data["total_uses"]
                    op_data["success_rate"] = len([f for f in op_data["recent_uses"] if f.get("fitness_score", 0) > 0.7]) / op_data["total_uses"]
                    op_data["recent_uses"] = op_data["recent_uses"][-5:]  # Keep only last 5 uses

                # Sort by average fitness and return top operators
                sorted_ops = sorted(
                    operator_stats.values(),
                    key=lambda x: x["avg_fitness"],
                    reverse=True
                )
                return {op["operator"]: op for op in sorted_ops[:limit]}

        except Exception as e:
            logger.error(f"Failed to retrieve operator success patterns: {e}")
            return {}

    async def recommend_operator(self, context_complexity: float, recent_failures: List[str] = None) -> str:
        """Recommend best operator based on historical success patterns."""

        try:
            success_patterns = await self.get_operator_success_patterns()

            if not success_patterns:
                return "ast_safe_mutation"  # Default fallback

            # Score operators based on context
            scored_ops = []
            for op_name, op_data in success_patterns.items():
                score = op_data["avg_fitness"]  # Base score from historical performance

                # Bonus for complexity matching
                avg_complexity = sum(op_data["complexity_matches"]) / len(op_data["complexity_matches"]) if op_data["complexity_matches"] else 0.5
                complexity_match = 1.0 - abs(avg_complexity - context_complexity)
                score += complexity_match * 0.2

                # Penalty for recent failures (if applicable)
                if recent_failures and op_name in recent_failures:
                    score -= 0.3

                scored_ops.append((op_name, score))

            # Return highest scoring operator
            best_op = max(scored_ops, key=lambda x: x[1])
            return best_op[0]

        except Exception as e:
            logger.error(f"Failed to recommend operator: {e}")
            return "ast_safe_mutation"

    async def get_failure_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent failure patterns for GP learning."""

        try:
            async with self.conport_client:
                results = await self.conport_client.get_custom_data(
                    workspace_id=self.workspace_id,
                    category="gp_failure_patterns"
                )

                # Sort by timestamp and return most recent
                patterns = results.get("gp_failure_patterns", {}).values()
                sorted_patterns = sorted(
                    patterns,
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )
                return sorted_patterns[:limit]
        except Exception as e:
            logger.error(f"Failed to retrieve failure patterns: {e}")
            return []

    async def log_session_summary(self, total_attempts: int, successful_repairs: int,
                                average_fitness: float, operators_used: Dict[str, int]) -> None:
        """Log comprehensive session summary for analysis."""

        session_duration = (datetime.now() - self.session_start_time).total_seconds()

        summary_data = {
            "category": "gp_session_summary",
            "key": f"session_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}",
            "value": {
                "duration_seconds": session_duration,
                "total_attempts": total_attempts,
                "successful_repairs": successful_repairs,
                "success_rate": successful_repairs / max(total_attempts, 1),
                "average_fitness": average_fitness,
                "operators_used": operators_used,
                "timestamp": datetime.now().isoformat()
            }
        }

        try:
            async with self.conport_client:
                result = await self.conport_client.log_custom_data(
                    workspace_id=self.workspace_id,
                    **summary_data
                )
                logger.info(f"Logged session summary to ConPort: {result.get('key', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to log session summary to ConPort: {e}")