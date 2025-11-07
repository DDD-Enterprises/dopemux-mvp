"""Comparison framework for running A/B tests between vanilla and genetic agents."""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ...core.config import AgentConfig
from ...vanilla.vanilla_agent import VanillaAgent
from ...genetic.genetic_agent import GeneticAgent


@dataclass
class ComparisonResult:
    """Result of comparing two agents on a test case."""

    test_case: str
    vanilla_result: Optional[Dict[str, Any]]
    genetic_result: Optional[Dict[str, Any]]
    vanilla_duration: float
    genetic_duration: float
    winner: str  # "vanilla", "genetic", or "tie"
    vanilla_tokens: int = 0
    genetic_tokens: int = 0

    @property
    def vanilla_success(self) -> bool:
        return self.vanilla_result.get("success", False) if self.vanilla_result else False

    @property
    def genetic_success(self) -> bool:
        return self.genetic_result.get("success", False) if self.genetic_result else False

    @property
    def both_success(self) -> bool:
        return self.vanilla_success and self.genetic_success

    @property
    def improvement_ratio(self) -> float:
        """How much better genetic is (negative = worse, positive = better)."""
        if not self.vanilla_success and not self.genetic_success:
            return 0.0
        if self.vanilla_success and not self.genetic_success:
            return -1.0
        if not self.vanilla_success and self.genetic_success:
            return 1.0
        # Both success - compare efficiency
        vanilla_efficiency = 1.0 / (self.vanilla_duration + 0.1)  # Avoid division by zero
        genetic_efficiency = 1.0 / (self.genetic_duration + 0.1)
        return (genetic_efficiency - vanilla_efficiency) / vanilla_efficiency


class ComparisonRunner:
    """Runs A/B tests comparing vanilla and genetic agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.vanilla_agent = VanillaAgent(config)
        self.genetic_agent = GeneticAgent(config)
        self.results: List[ComparisonResult] = []

    async def run_comparison(self, test_cases: List[Dict[str, Any]]) -> List[ComparisonResult]:
        """Run comparison tests on multiple test cases."""
        results = []

        for test_case in test_cases:
            result = await self._compare_agents(test_case)
            results.append(result)
            self.results.append(result)

            # Log to ConPort
            await self._log_comparison_result(result)

        return results

    async def _compare_agents(self, test_case: Dict[str, Any]) -> ComparisonResult:
        """Compare vanilla and genetic agents on a single test case."""
        test_name = test_case.get("name", f"test_{len(self.results)}")

        # Run vanilla agent
        vanilla_start = time.time()
        try:
            vanilla_result = await self.vanilla_agent.process_task(test_case)
        except Exception as e:
            vanilla_result = {"success": False, "error": str(e)}
        vanilla_duration = time.time() - vanilla_start

        # Run genetic agent
        genetic_start = time.time()
        try:
            genetic_result = await self.genetic_agent.process_task(test_case)
        except Exception as e:
            genetic_result = {"success": False, "error": str(e)}
        genetic_duration = time.time() - genetic_start

        # Determine winner
        winner = self._determine_winner(vanilla_result, genetic_result, vanilla_duration, genetic_duration)

        return ComparisonResult(
            test_case=test_name,
            vanilla_result=vanilla_result,
            genetic_result=genetic_result,
            vanilla_duration=vanilla_duration,
            genetic_duration=genetic_duration,
            winner=winner
        )

    def _determine_winner(self, vanilla_result: Dict, genetic_result: Dict,
                          vanilla_time: float, genetic_time: float) -> str:
        """Determine which agent performed better."""
        vanilla_success = vanilla_result.get("success", False)
        genetic_success = genetic_result.get("success", False)

        # Success is primary criteria
        if vanilla_success and not genetic_success:
            return "vanilla"
        if genetic_success and not vanilla_success:
            return "genetic"
        if not vanilla_success and not genetic_success:
            return "tie"  # Both failed

        # Both succeeded - compare efficiency (lower time = better)
        time_ratio = vanilla_time / genetic_time if genetic_time > 0 else float('inf')
        if time_ratio > 1.2:  # Vanilla >20% slower
            return "genetic"
        if time_ratio < 0.8:  # Vanilla >20% faster
            return "vanilla"
        return "tie"

    async def _log_comparison_result(self, result: ComparisonResult):
        """Log comparison result to ConPort."""
        try:
            from ...shared.mcp.conport_client import ConPortClient
            import os

            config = self.config
            client = ConPortClient(config.conport_url, config)

            async with client:
                await client.log_decision(
                    summary=f"Agent Comparison: {result.test_case}",
                    rationale=f"Vanilla: {'Success' if result.vanilla_success else 'Failed'} "
                             f"({result.vanilla_duration:.2f}s), "
                             f"Genetic: {'Success' if result.genetic_success else 'Failed'} "
                             f"({result.genetic_duration:.2f}s), "
                             f"Winner: {result.winner}",
                    tags=["agent_comparison", "performance_test", result.winner]
                )
        except Exception as e:
            print(f"Failed to log comparison result: {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive comparison report."""
        if not self.results:
            return {"error": "No comparison results available"}

        total_tests = len(self.results)
        vanilla_wins = sum(1 for r in self.results if r.winner == "vanilla")
        genetic_wins = sum(1 for r in self.results if r.winner == "genetic")
        ties = sum(1 for r in self.results if r.winner == "tie")

        vanilla_success_rate = sum(1 for r in self.results if r.vanilla_success) / total_tests
        genetic_success_rate = sum(1 for r in self.results if r.genetic_success) / total_tests

        avg_vanilla_time = sum(r.vanilla_duration for r in self.results) / total_tests
        avg_genetic_time = sum(r.genetic_duration for r in self.results) / total_tests

        improvement_ratios = [r.improvement_ratio for r in self.results if r.improvement_ratio != 0]
        avg_improvement = sum(improvement_ratios) / len(improvement_ratios) if improvement_ratios else 0

        return {
            "summary": {
                "total_tests": total_tests,
                "vanilla_wins": vanilla_wins,
                "genetic_wins": genetic_wins,
                "ties": ties,
                "vanilla_success_rate": vanilla_success_rate,
                "genetic_success_rate": genetic_success_rate,
                "avg_vanilla_time": avg_vanilla_time,
                "avg_genetic_time": avg_genetic_time,
                "avg_improvement_ratio": avg_improvement
            },
            "recommendations": self._generate_recommendations(
                vanilla_success_rate, genetic_success_rate, avg_improvement
            ),
            "details": [
                {
                    "test_case": r.test_case,
                    "vanilla_success": r.vanilla_success,
                    "genetic_success": r.genetic_success,
                    "vanilla_time": r.vanilla_duration,
                    "genetic_time": r.genetic_duration,
                    "winner": r.winner,
                    "improvement_ratio": r.improvement_ratio
                }
                for r in self.results
            ]
        }

    def _generate_recommendations(self, vanilla_rate: float, genetic_rate: float,
                                 avg_improvement: float) -> List[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []

        if genetic_rate > vanilla_rate + 0.1:  # 10% better success
            recommendations.append("Genetic agent shows significantly better success rate - consider making it default for complex bugs")
        elif vanilla_rate > genetic_rate + 0.1:
            recommendations.append("Vanilla agent performs better overall - focus optimization efforts there")

        if avg_improvement > 0.2:  # 20% efficiency improvement
            recommendations.append("Genetic agent shows efficiency gains - optimize GP operators for speed")
        elif avg_improvement < -0.2:
            recommendations.append("Genetic agent is slower - investigate performance bottlenecks in GP operations")

        if genetic_rate < 0.7:  # Below target
            recommendations.append("Genetic success rate below target - review GP operator effectiveness and fitness functions")

        return recommendations if recommendations else ["Both agents performing adequately - monitor for optimization opportunities"]