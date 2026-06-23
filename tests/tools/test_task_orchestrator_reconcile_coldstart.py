from __future__ import annotations

"""Tests for the coldstart render_markdown function and CLI.

All tests run offline — they load the committed COLDSTART_RECONCILIATION.json
fixture or inline data. No live database access required.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_JSON = (
    ROOT
    / "audit_inputs"
    / "task-orchestrator-canon"
    / "to-all-dbs-20260622T192814Z"
    / "COLDSTART_RECONCILIATION.json"
)
GENERATED_MD = (
    ROOT
    / "docs"
    / "05-audit-reports"
    / "task-orchestrator"
    / "coldstart-reconciliation-20260622.md"
)


def _load_fixture() -> dict:
    return json.loads(FIXTURE_JSON.read_text(encoding="utf-8"))


def _render(coldstart: dict | None = None) -> str:
    # Import here so tests get a fresh import each time
    # (avoids sys.modules caching issues when running in isolation)
    import importlib

    mod = importlib.import_module("tools.task_orchestrator_reconcile.coldstart")
    data = coldstart if coldstart is not None else _load_fixture()
    return mod.render_markdown(data)


def _run_cli(from_json: str, emit_md: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.task_orchestrator_reconcile.coldstart",
            "--from-json",
            from_json,
            "--emit-md",
            emit_md,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


# --- (a) Render determinism ---------------------------------------------------


def test_render_is_deterministic():
    """Calling render_markdown twice on the same input must produce identical output."""
    data = _load_fixture()
    first = _render(data)
    second = _render(data)
    assert first == second, "render_markdown is not deterministic"


# --- (b) CLI byte-identical on re-run ----------------------------------------


def test_cli_byte_identical_on_rerun(tmp_path: Path):
    """Running the CLI twice must produce byte-identical output files."""
    out1 = tmp_path / "run1.md"
    out2 = tmp_path / "run2.md"

    r1 = _run_cli(str(FIXTURE_JSON), str(out1))
    assert r1.returncode == 0, f"CLI run 1 failed: {r1.stderr}"

    r2 = _run_cli(str(FIXTURE_JSON), str(out2))
    assert r2.returncode == 0, f"CLI run 2 failed: {r2.stderr}"

    assert out1.read_bytes() == out2.read_bytes(), (
        "CLI output differs between runs — not byte-stable"
    )


# --- (c) Items 100/101/109 render with accepted_do_not_rerun -----------------


def test_items_100_101_109_render_accepted_do_not_rerun():
    """TP-100, TP-101, and TP-109 must appear with decision=accepted_do_not_rerun."""
    md = _render()
    expected_titles = [
        "TP-DMX-COLDSTART-L0-DEP-AUDIT-100",
        "TP-DMX-COLDSTART-SALVAGE-COLDSTART-LIB-101",
        "TP-DMX-COLDSTART-ORCH-HTTP-CUTOVER-109",
    ]
    for title in expected_titles:
        assert title in md, f"title not found in rendered output: {title}"
    # All three must appear alongside accepted_do_not_rerun
    assert md.count("accepted_do_not_rerun") >= 3, (
        "expected at least 3 occurrences of accepted_do_not_rerun "
        f"(one per repo_pr_proof_observed item), got: {md.count('accepted_do_not_rerun')}"
    )


# --- (d) Item 102 renders as keep_blocked_until_repo_packet_allowlist_exists --


def test_item_102_renders_keep_blocked():
    """TP-DMX-COLDSTART-INIT-UNIFY-102 must appear with the correct blocked decision."""
    md = _render()
    assert "TP-DMX-COLDSTART-INIT-UNIFY-102" in md
    assert "keep_blocked_until_repo_packet_allowlist_exists" in md


# --- (e) OP-DMX-COLDSTART-PYPI-NAME-000 appears -----------------------------


def test_operator_gate_item_appears():
    """OP-DMX-COLDSTART-PYPI-NAME-000 must appear in the rendered Markdown."""
    md = _render()
    assert "OP-DMX-COLDSTART-PYPI-NAME-000" in md


# --- (f) valid_as_of_utc banner is present -----------------------------------


def test_valid_as_of_utc_banner_present():
    """The point-in-time valid_as_of_utc value must appear verbatim in the output."""
    data = _load_fixture()
    expected = data["point_in_time"]["valid_as_of_utc"]
    md = _render(data)
    assert expected in md, (
        f"valid_as_of_utc '{expected}' not found in rendered Markdown"
    )
