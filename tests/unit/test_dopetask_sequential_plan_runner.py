from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.dopemux_pr_merge_specialist.dopetask_packet_launcher import (
    DopetaskPacketLauncher,
    PacketLaunchTrace,
)
from src.dopemux_pr_merge_specialist.dopetask_sequential_plan_runner import (
    DopetaskSequentialPlanRunner,
    PlanPacket,
    PlanValidationError,
    SequentialPlan,
)


@pytest.fixture
def mock_launcher() -> MagicMock:
    return MagicMock(spec=DopetaskPacketLauncher)


@pytest.fixture
def runner(mock_launcher: MagicMock, tmp_path: Path) -> DopetaskSequentialPlanRunner:
    return DopetaskSequentialPlanRunner(mock_launcher, tmp_path)


def test_run_successful_chain(
    runner: DopetaskSequentialPlanRunner, mock_launcher: MagicMock, tmp_path: Path
) -> None:
    plan = SequentialPlan(
        plan_id="PLAN-1",
        packets=[
            PlanPacket(tp_id="TP-1"),
            PlanPacket(tp_id="TP-2", depends_on=["TP-1"]),
        ],
    )
    
    # Setup mock responses
    mock_launcher.launch.side_effect = [
        PacketLaunchTrace("TP-1", "lane", "run-1", "path/1", True, None, 1.0),
        PacketLaunchTrace("TP-2", "lane", "run-2", "path/2", True, None, 2.0),
    ]

    result = runner.run(plan, {})
    
    assert result.status == "SUCCESS"
    assert result.completed_count == 2
    assert len(result.traces) == 2
    assert (tmp_path / "SEQUENTIAL_PLAN_RESULT.json").exists()


def test_run_fail_stop(
    runner: DopetaskSequentialPlanRunner, mock_launcher: MagicMock
) -> None:
    plan = SequentialPlan(
        plan_id="PLAN-FAIL",
        packets=[
            PlanPacket(tp_id="TP-1"),
            PlanPacket(tp_id="TP-2", depends_on=["TP-1"]),
            PlanPacket(tp_id="TP-3", depends_on=["TP-2"]),
        ],
    )
    
    # TP-2 fails
    mock_launcher.launch.side_effect = [
        PacketLaunchTrace("TP-1", "lane", "run-1", "path/1", True, None, 1.0),
        PacketLaunchTrace("TP-2", "lane", "run-2", None, False, "Error!", 2.0),
    ]

    result = runner.run(plan, {})
    
    assert result.status == "FAILED"
    assert result.failure_point == "TP-2"
    assert result.completed_count == 1
    assert result.attempted_count == 2
    # TP-3 should never be called
    assert mock_launcher.launch.call_count == 2


def test_rejects_out_of_order_dependency(runner: DopetaskSequentialPlanRunner) -> None:
    plan = SequentialPlan(
        plan_id="PLAN-BAD",
        packets=[
            PlanPacket(tp_id="TP-2", depends_on=["TP-1"]),
            PlanPacket(tp_id="TP-1"),
        ],
    )
    with pytest.raises(PlanValidationError, match="depends on 'TP-1' which is not defined before it"):
        runner.run(plan, {})


def test_rejects_missing_dependency(runner: DopetaskSequentialPlanRunner) -> None:
    plan = SequentialPlan(
        plan_id="PLAN-MISSING",
        packets=[
            PlanPacket(tp_id="TP-1", depends_on=["GHOST"]),
        ],
    )
    with pytest.raises(PlanValidationError, match="depends on 'GHOST' which is not defined before it"):
        runner.run(plan, {})
