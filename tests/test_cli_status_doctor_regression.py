"""Regression tests for two long-standing CLI runtime crashes.

Both bugs pre-date 2026-04 and made `dopemux doctor` and `dopemux status`
unusable:

* ``doctor`` -> ``styled_table`` received a single-element column tuple
  ``("Status",)`` and raised ``ValueError: not enough values to unpack``.
* ``status`` -> iterated ``get_progress()["tasks"]`` using keys
  (``completed``/``in_progress``/``name``) that the task dict never contains;
  the real shape exposes ``status`` (string) and ``description``.
"""

from unittest.mock import patch

from click.testing import CliRunner

from dopemux.cli import cli
from dopemux.ui.theme import styled_table


def test_styled_table_accepts_single_element_column_tuple():
    """A ``(name,)`` column (no kwargs) must not raise — root cause of `doctor`."""
    table = styled_table(
        "Diag",
        ("Check", {"style": "text"}),
        ("Status",),
    )
    headers = [col.header for col in table.columns]
    assert "Check" in headers
    assert "Status" in headers


def test_status_tasks_renders_real_task_shape():
    """`status --tasks` must render the actual get_progress() task shape.

    The real per-task dict exposes ``status`` (string) and ``description`` —
    not ``completed``/``in_progress``/``name``.
    """
    payload = {
        "total_tasks": 2,
        "completed_tasks": 1,
        "in_progress_tasks": 1,
        "overall_progress": 0.5,
        "current_task": None,
        "tasks": [
            {"id": "t1", "description": "Write docs", "status": "completed", "progress": 1.0},
            {"id": "t2", "description": "Fix the bug", "status": "in_progress", "progress": 0.4},
        ],
        "summary": {"total": 2, "completed": 1, "in_progress": 1},
    }
    runner = CliRunner()
    with patch(
        "dopemux.adhd.task_decomposer.TaskDecomposer.get_progress",
        return_value=payload,
    ):
        result = runner.invoke(cli, ["status", "--tasks"])

    assert result.exit_code == 0, (result.output, result.exception)
    assert "Write docs" in result.output
    assert "Fix the bug" in result.output
