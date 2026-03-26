from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from dopemux_pr_merge_specialist.dashboard import DopemuxDashboard, QueueState
from dopemux_pr_merge_specialist.queue_drain import _ignite_speculative_train
from dopemux_pr_merge_specialist.schema import PullRequestState, PRResult


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

    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.queue_drain.prepare_worktree", fake_prepare
    )
    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.queue_drain.attempt_speculative_rebase",
        fake_rebase,
    )
    monkeypatch.setattr(
        "dopemux_pr_merge_specialist.queue_drain.cleanup_worktree", fake_cleanup
    )

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
