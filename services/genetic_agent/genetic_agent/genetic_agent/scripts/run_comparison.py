#!/usr/bin/env python3
"""Script to run comparison tests between vanilla and genetic agents."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from genetic_agent.core.config import AgentConfig
from genetic_agent.tests.comparison.comparison_runner import ComparisonRunner


async def main():
    """Run comparison tests."""
    logger.info("🧪 Running Genetic Coding Agent Comparison Tests")

import logging

logger = logging.getLogger(__name__)

    logger.info("=" * 50)

    # Load configuration
    config = AgentConfig()

    # Initialize comparison runner
    runner = ComparisonRunner(config)

    # Define test cases
    test_cases = [
        {
            "name": "simple_null_check",
            "bug_description": "Add null check for user parameter to prevent null pointer exception",
            "file_path": "user.py",
            "line_number": 10
        },
        {
            "name": "boundary_check",
            "bug_description": "Add boundary check for array access to prevent index out of bounds",
            "file_path": "array_utils.py",
            "line_number": 25
        },
        {
            "name": "type_validation",
            "bug_description": "Add type validation for input parameter to prevent type errors",
            "file_path": "data_processor.py",
            "line_number": 15
        }
    ]

    logger.info(f"📋 Running {len(test_cases)} comparison tests...")
    logger.info()

    try:
        # Run comparisons
        results = await runner.run_comparison(test_cases)

        # Generate and display report
        report = runner.generate_report()

        logger.info("📊 COMPARISON RESULTS")
        logger.info("-" * 30)
        summary = report["summary"]
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Vanilla Wins: {summary['vanilla_wins']}")
        logger.info(f"Genetic Wins: {summary['genetic_wins']}")
        logger.info(f"Ties: {summary['ties']}")
        logger.info(".1%")
        logger.info(".1%")
        logger.info(".2f")
        logger.info(".2f")
        if summary['avg_improvement_ratio'] != 0:
            logger.info(".1%")

        logger.info()
        logger.info("🎯 RECOMMENDATIONS")
        logger.info("-" * 20)
        for rec in report["recommendations"]:
            logger.info(f"• {rec}")

        logger.info()
        logger.info("📋 DETAILED RESULTS")
        logger.info("-" * 20)
        for detail in report["details"]:
            status = "✅" if detail["genetic_success"] else "❌"
            print(f"{status} {detail['test_case']}: {detail['winner']} "
                  ".2f")

        # Save report to file
        report_file = Path(__file__).parent.parent / "comparison_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"\n💾 Report saved to: {report_file}")

    except Exception as e:
        logger.error(f"❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1

    logger.info("\n🎉 Comparison testing complete!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)