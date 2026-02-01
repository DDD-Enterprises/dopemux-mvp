"""Unit tests for the comparison framework."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from genetic_agent.core.config import AgentConfig
from genetic_agent.tests.comparison.comparison_runner import ComparisonRunner, ComparisonResult


@pytest.fixture
def agent_config():
    """Fixture for agent configuration."""
    return AgentConfig()


@pytest.fixture
def comparison_runner(agent_config):
    """Fixture for comparison runner."""
    return ComparisonRunner(agent_config)


@pytest.mark.asyncio
async def test_comparison_result_properties():
    """Test ComparisonResult properties."""
    # Both success
    result = ComparisonResult(
        test_case="test1",
        vanilla_result={"success": True},
        genetic_result={"success": True},
        vanilla_duration=1.0,
        genetic_duration=2.0,
        winner="vanilla"
    )

    assert result.vanilla_success is True
    assert result.genetic_success is True
    assert result.both_success is True
    assert result.improvement_ratio < 0  # Vanilla faster

    # Vanilla fails, genetic succeeds
    result2 = ComparisonResult(
        test_case="test2",
        vanilla_result={"success": False},
        genetic_result={"success": True},
        vanilla_duration=1.0,
        genetic_duration=2.0,
        winner="genetic"
    )

    assert result2.improvement_ratio == 1.0


@pytest.mark.asyncio
async def test_comparison_runner_basic(comparison_runner):
    """Test basic comparison runner functionality."""
    test_cases = [
        {
            "name": "simple_null_check",
            "bug_description": "Add null check for user parameter",
            "file_path": "user.py",
            "line_number": 10
        }
    ]

    # Mock the agents to avoid actual processing
    with patch.object(comparison_runner.vanilla_agent, 'process_task', new_callable=AsyncMock) as mock_vanilla, \
         patch.object(comparison_runner.genetic_agent, 'process_task', new_callable=AsyncMock) as mock_genetic:

        mock_vanilla.return_value = {"success": True, "confidence": 0.8}
        mock_genetic.return_value = {"success": True, "confidence": 0.9}

        results = await comparison_runner.run_comparison(test_cases)

        assert len(results) == 1
        assert results[0].vanilla_success is True
        assert results[0].genetic_success is True
        assert results[0].winner in ["vanilla", "genetic", "tie"]

        # Verify agents were called
        mock_vanilla.assert_called_once()
        mock_genetic.assert_called_once()


def test_comparison_report_generation(comparison_runner):
    """Test report generation with sample results."""
    # Add some sample results
    comparison_runner.results = [
        ComparisonResult(
            test_case="test1",
            vanilla_result={"success": True},
            genetic_result={"success": True},
            vanilla_duration=1.0,
            genetic_duration=1.5,
            winner="vanilla"
        ),
        ComparisonResult(
            test_case="test2",
            vanilla_result={"success": False},
            genetic_result={"success": True},
            vanilla_duration=2.0,
            genetic_duration=3.0,
            winner="genetic"
        )
    ]

    report = comparison_runner.generate_report()

    assert "summary" in report
    assert "recommendations" in report
    assert "details" in report
    assert report["summary"]["total_tests"] == 2
    assert report["summary"]["genetic_wins"] == 1
    assert len(report["details"]) == 2