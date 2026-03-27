from argparse import Namespace
import json
from pathlib import Path
from types import SimpleNamespace

from src.dopemux_pr_merge_specialist.action_model import (
    dashboard_phase_for_snapshot,
    dashboard_tactic_for_snapshot,
)
from src.dopemux_pr_merge_specialist.conflict import apply_suggestion_to_file
from src.dopemux_pr_merge_specialist.dashboard import DopemuxDashboard, QueueState
from src.dopemux_pr_merge_specialist.metrics import MetricsEngine
from src.dopemux_pr_merge_specialist.queue_drain import _ignite_speculative_train
from src.dopemux_pr_merge_specialist.schema import (
    PRMergeReport,
    PRState,
    PRResult,
    PullRequestState,
    ReviewThread,
    ThreadComment,
)


def _pr_result(pr_id: int, *, lifecycle_state: str = "merge_ready") -> PRResult:
    pr = PullRequestState(
        pr_id=pr_id,
        title=f"PR {pr_id}",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref=f"feature-{pr_id}",
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="APPROVED",
        active_unresolved_threads=0,
    )
    return PRResult(
        run_id="run",
        pr_state=pr,
        lifecycle_state=lifecycle_state,
    )


def test_dashboard_render_passes_dashboard_console() -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    dashboard.state = QueueState(run_id="run", prs=[])

    captured = {}

    def fake_render(state, console=None):
        captured["state"] = state
        captured["console"] = console
        return "layout"

    dashboard.ux.render_dashboard_layout = fake_render  # type: ignore[method-assign]

    assert dashboard.render() == "layout"
    assert captured["state"] is dashboard.state
    assert captured["console"] is dashboard.console


def test_speculative_train_rebases_against_origin_main_and_continues(monkeypatch, tmp_path: Path) -> None:
    results = [_pr_result(101), _pr_result(102)]
    prepare_calls = []
    rebase_calls = []
    cleanup_calls = []

    def fake_prepare(repo_root, pr_id, active_run_id, commands_log, policy):
        prepare_calls.append(pr_id)
        return tmp_path / f"wt-{pr_id}", f"branch-{pr_id}", None

    def fake_rebase(*, worktree_path, onto_ref, commands_log, execute, policy):
        rebase_calls.append((worktree_path.name, onto_ref, execute))
        if worktree_path.name == "wt-101":
            return False, "conflict"
        return True, "ok"

    def fake_cleanup(repo_root, worktree_path, branch, commands_log, policy):
        cleanup_calls.append((worktree_path.name, branch))

    monkeypatch.setattr("src.dopemux_pr_merge_specialist.queue_drain.prepare_worktree", fake_prepare)
    monkeypatch.setattr("src.dopemux_pr_merge_specialist.queue_drain.attempt_speculative_rebase", fake_rebase)
    monkeypatch.setattr("src.dopemux_pr_merge_specialist.queue_drain.cleanup_worktree", fake_cleanup)

    merged_ids, queued_ids = _ignite_speculative_train(
        results=results,
        client=SimpleNamespace(repo=None),
        repo_root=tmp_path,
        active_run_id="run",
        commands_log=tmp_path / "commands.log",
        policy={},
        execute=False,
    )

    assert merged_ids == []
    assert queued_ids == [102]
    assert prepare_calls == [101, 102]
    assert rebase_calls == [
        ("wt-101", "origin/main", False),
        ("wt-102", "origin/main", False),
    ]
    assert cleanup_calls == [
        ("wt-101", "branch-101"),
        ("wt-102", "branch-102"),
    ]


def test_apply_suggestion_to_file_dry_run_returns_preview(tmp_path: Path) -> None:
    target = tmp_path / "demo.py"
    target.write_text("alpha\nbeta\n", encoding="utf-8")
    thread = ReviewThread(
        id="thread-1",
        is_resolved=False,
        is_outdated=False,
        viewer_can_resolve=True,
        path="demo.py",
        line=2,
        original_line=2,
        comments=[],
    )
    comment = ThreadComment(
        id="comment-1",
        author="reviewer",
        body="```suggestion\nbeta_updated\n```",
        created_at="2024-01-01T00:00:00Z",
        path="demo.py",
        line=2,
        original_line=2,
    )

    ok, reason, proposed_text = apply_suggestion_to_file(
        worktree_path=tmp_path,
        thread=thread,
        comment=comment,
        base_ref="main",
        policy={},
        dry_run=True,
    )

    assert ok is True
    assert "Applied suggestion" in reason
    assert proposed_text == "alpha\nbeta_updated\n"
    assert target.read_text(encoding="utf-8") == "alpha\nbeta\n"


def test_dashboard_tactic_distinguishes_validation_ci_and_threads() -> None:
    base_snapshot = {
        "allowed_actions": ["APPLY_FIX"],
        "ci_status": "SUCCESS",
        "unresolved_threads": 0,
        "validation_report": {"status": "not_executed"},
        "blockers": [],
    }

    validation_failed = dict(
        base_snapshot,
        validation_report={"status": "failed"},
        blockers=[{"type": "validation_failed"}],
    )
    ci_failed = dict(
        base_snapshot,
        ci_status="FAILURE",
        blockers=[{"type": "required_check_failed"}],
    )
    thread_blocked = dict(
        base_snapshot,
        unresolved_threads=2,
        blockers=[{"type": "active_thread"}],
    )

    assert dashboard_tactic_for_snapshot(validation_failed) == "F"
    assert dashboard_phase_for_snapshot(validation_failed) == "Validation Remediation"
    assert dashboard_tactic_for_snapshot(ci_failed) == "C"
    assert dashboard_phase_for_snapshot(ci_failed) == "CI Remediation"
    assert dashboard_tactic_for_snapshot(thread_blocked) == "T"
    assert dashboard_phase_for_snapshot(thread_blocked) == "Thread Review"


def test_metrics_log_event_accepts_dashboard_report_shape(tmp_path: Path) -> None:
    engine = MetricsEngine(tmp_path)
    pr = PullRequestState(
        pr_id=7,
        title="PR 7",
        author="tester",
        state="OPEN",
        base_ref="main",
        head_ref="feature-7",
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="APPROVED",
        unresolved_threads=2,
        lifecycle_state=PRState.QUEUED_FOR_MERGE,
    )
    report = PRMergeReport(
        pr_id="7",
        status="queued_for_merge",
        initial_state=pr,
        telemetry={"run_id": "run-7"},
    )

    engine.log_event(report=report, resolved_threads=3)

    ledger = next(tmp_path.glob("events-*.jsonl"))
    event = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert event["run_id"] == "run-7"
    assert event["is_in_queue"] is True
    assert event["unresolved_threads"] == 2
    assert event["resolved_threads_in_session"] == 3


def test_dashboard_decode_input_choice_maps_exit_keys_to_quit(monkeypatch) -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))

    assert dashboard._decode_input_choice("\x03") == "Q"
    assert dashboard._decode_input_choice("\x04") == "Q"
    assert dashboard._decode_input_choice("q") == "Q"

    dashboard._input_fd = 1
    monkeypatch.setattr(
        "src.dopemux_pr_merge_specialist.dashboard.select.select",
        lambda *_args, **_kwargs: ([], [], []),
    )
    assert dashboard._decode_input_choice("\x1b") == "Q"


def test_choose_autopilot_strategy_prefers_simple_for_small_independent_queue() -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    strategy, reason = dashboard._choose_autopilot_strategy(
        [
            {"pr_id": 1, "head_ref": "feature-1", "base_ref": "main"},
            {"pr_id": 2, "head_ref": "feature-2", "base_ref": "main"},
        ]
    )

    assert strategy == "simple"
    assert "small independent queue" in reason


def test_choose_autopilot_strategy_prefers_hybrid_for_stack() -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    strategy, reason = dashboard._choose_autopilot_strategy(
        [
            {"pr_id": 1, "head_ref": "feature-1", "base_ref": "main"},
            {"pr_id": 2, "head_ref": "feature-2", "base_ref": "feature-1"},
        ]
    )

    assert strategy == "hybrid"
    assert "stacked or larger queue" in reason


def test_autopilot_reassess_advances_after_stalled_pr(monkeypatch) -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    dashboard.state = QueueState(
        run_id="run",
        prs=[
            {"pr_id": 101, "lifecycle_state": "apply_ready", "allowed_actions": ["APPLY_FIX"], "validation_report": {"status": "not_executed"}, "ci_status": "SUCCESS", "unresolved_threads": 0, "blockers": []},
            {"pr_id": 102, "lifecycle_state": "merge_ready", "allowed_actions": ["MERGE"], "validation_report": {"status": "passed"}, "ci_status": "SUCCESS", "unresolved_threads": 0, "blockers": []},
        ],
        autopilot_strategy="hybrid",
    )

    def fake_refresh_queue_state(*, strategy_override=None, prefer_top=False):
        assert strategy_override == "hybrid"
        assert prefer_top is True
        return True

    monkeypatch.setattr(dashboard, "_refresh_queue_state", fake_refresh_queue_state)
    dashboard.state.last_action_result = "apply_ready"

    dashboard._reassess_autopilot_after_action(
        target_pr_id="101",
        initial_state="apply_ready",
        initial_tactic="P",
    )

    assert dashboard.state.active_index == 1
    assert "stalled" in dashboard.state.status_message


def test_select_advanced_strategy_prefers_patch_isolation_for_failed_ci() -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    strategy_id, rationale, steps = dashboard._select_advanced_strategy(
        {
            "pr_id": 201,
            "ci_status": "FAILURE",
            "validation_report": {"status": "passed"},
            "blockers": [{"type": "required_check_failed"}],
            "mergeable": "MERGEABLE",
            "merge_state_status": "CLEAN",
            "unresolved_threads": 0,
        }
    )

    assert strategy_id == "PATCH_ISOLATION_PLAN"
    assert "Broken validation or CI" in rationale
    assert steps[0] in {"F", "C"}


def test_select_advanced_strategy_prefers_ours_then_port_for_threads() -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    strategy_id, rationale, steps = dashboard._select_advanced_strategy(
        {
            "pr_id": 202,
            "ci_status": "SUCCESS",
            "validation_report": {"status": "not_executed"},
            "blockers": [{"type": "active_thread"}],
            "mergeable": "MERGEABLE",
            "merge_state_status": "CLEAN",
            "unresolved_threads": 2,
        }
    )

    assert strategy_id == "OURS_THEN_PORT_SELECTIVE"
    assert "Reviewer deltas" in rationale
    assert steps[0] == "T"


def test_autopilot_tactic_prefers_strategy_order_over_generic_choice() -> None:
    dashboard = DopemuxDashboard(manager=object(), args=Namespace(out_dir="reports"))
    snapshot = {
        "allowed_actions": ["APPLY_FIX"],
        "ci_status": "FAILURE",
        "validation_report": {"status": "failed"},
        "unresolved_threads": 2,
        "blockers": [
            {"type": "validation_failed"},
            {"type": "required_check_failed"},
            {"type": "active_thread"},
        ],
        "advanced_strategy_id": "PATCH_ISOLATION_PLAN",
        "advanced_strategy_steps": ["F", "C", "T", "V", "I"],
    }

    assert dashboard._autopilot_tactic_for_snapshot(snapshot) == "F"
