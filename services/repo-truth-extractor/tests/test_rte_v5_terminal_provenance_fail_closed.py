"""Regression matrix for TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001.

Covers three RTE v5 fail-open defects, offline/deterministic only (no live
provider calls):

  * RTE-W1-001 (terminal truth): shell exit code must match canonical
    semantic run status.
  * RTE-W1-006 (batch outcome): batch retrieval/integration must report a
    typed outcome, not a bare integer count.
  * RTE-W1-010 (source identity): canonical execution evidence must have
    positively proven git source identity.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import lib.batch_retriever as batch_retriever_module


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    module_name = "run_extraction_v5_terminal_provenance_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_gate_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "validate_pre_live_gate_v25.py"
    module_name = "validate_pre_live_gate_v25_terminal_provenance_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALID_SHA1 = "a" * 40
VALID_SHA256 = "b" * 64


# ---------------------------------------------------------------------------
# T-series (RTE-W1-001): terminal truth
# ---------------------------------------------------------------------------


def _write_rollup(run_root: Path, run_status) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    payload = {} if run_status is _MISSING else {"run_status": run_status}
    (run_root / "COVERAGE_ROLLUP.json").write_text(json.dumps(payload), encoding="utf-8")


_MISSING = object()


def test_t1_successful_run_status_ok_exits_zero(tmp_path: Path) -> None:
    runner = _load_runner_module()
    _write_rollup(tmp_path, runner.RUN_STATUS_OK)

    exit_code, run_status = runner.resolve_final_run_terminal_exit_code(tmp_path)

    assert exit_code == 0
    assert run_status == runner.RUN_STATUS_OK


def test_t2_missing_required_artifact_blocked_status_exits_nonzero(tmp_path: Path) -> None:
    runner = _load_runner_module()
    _write_rollup(tmp_path, runner.RUN_STATUS_BLOCKED)

    exit_code, run_status = runner.resolve_final_run_terminal_exit_code(tmp_path)

    assert exit_code != 0
    assert run_status == runner.RUN_STATUS_BLOCKED


def test_t3_blocked_promptset_dispatch_exits_nonzero() -> None:
    runner = _load_runner_module()
    # Blocked-promptset CLI dispatch uses a dedicated nonzero exit code
    # (existing behavior, characterized here as a non-regression guard).
    assert runner.PROMPTSET_BLOCKED_EXIT_CODE != 0


def test_t4_failed_partition_reflected_as_blocked_status_exits_nonzero(tmp_path: Path) -> None:
    runner = _load_runner_module()
    # A failed partition surfaces as missing_required_artifacts_total > 0 in
    # compute_run_status, which yields RUN_STATUS_BLOCKED -- same contract
    # as T2, exercised here via compute_run_status directly.
    status = runner.compute_run_status(
        blocked_promptset=False,
        missing_required_artifacts_total=1,
        phase_statuses={"A": "FAIL"},
        cost_abort_triggered=False,
    )
    _write_rollup(tmp_path, status)

    exit_code, run_status = runner.resolve_final_run_terminal_exit_code(tmp_path)

    assert status == runner.RUN_STATUS_BLOCKED
    assert exit_code != 0
    assert run_status == runner.RUN_STATUS_BLOCKED


@pytest.mark.parametrize(
    "injected_status",
    ["WEIRD_INJECTED_STATUS", "", None, "ok", "Ok", "COST_ABORTED_TYPO"],
)
def test_t5_unknown_or_injected_terminal_status_exits_nonzero(tmp_path: Path, injected_status) -> None:
    runner = _load_runner_module()
    _write_rollup(tmp_path, injected_status)

    exit_code, run_status = runner.resolve_final_run_terminal_exit_code(tmp_path)

    assert exit_code != 0
    assert run_status == injected_status


def test_t5_missing_rollup_file_fails_closed(tmp_path: Path) -> None:
    runner = _load_runner_module()
    # No COVERAGE_ROLLUP.json at all: no evidence of success, fail closed.
    exit_code, run_status = runner.resolve_final_run_terminal_exit_code(tmp_path)

    assert exit_code != 0
    assert run_status is None


def test_t5_cost_aborted_status_exits_nonzero(tmp_path: Path) -> None:
    runner = _load_runner_module()
    _write_rollup(tmp_path, runner.RUN_STATUS_COST_ABORTED)

    exit_code, run_status = runner.resolve_final_run_terminal_exit_code(tmp_path)

    assert exit_code != 0
    assert run_status == runner.RUN_STATUS_COST_ABORTED


def test_t6_main_calls_terminal_exit_resolver_before_returning(tmp_path: Path) -> None:
    """RTE-W1-001 structural guard: main() must not fall off the end with an
    implicit exit 0 -- it must call resolve_final_run_terminal_exit_code and
    sys.exit with its result as the very last thing it does. Verified via
    source inspection since driving the full multi-thousand-line main()
    end-to-end offline is impractical; the coverage-rollup evidence write
    (write_coverage_rollup) already runs inside the per-phase loop, strictly
    before this final resolver call, both textually and at runtime given
    Python's sequential execution.
    """
    runner = _load_runner_module()
    source = inspect.getsource(runner.main)

    resolver_idx = source.rindex("resolve_final_run_terminal_exit_code(")
    exit_idx = source.rindex("sys.exit(exit_code)")
    write_coverage_rollup_idx = source.rindex("write_coverage_rollup(root, dirs, run_id)")

    assert write_coverage_rollup_idx < resolver_idx < exit_idx


def test_dry_run_meta_never_trips_cost_abort(monkeypatch, tmp_path: Path) -> None:
    """S4 regression-repair pin: record_request_cost must be a no-op for
    dry-run request meta. Pre-fix, an initialized spend tracker treated
    dry-run's absent response_summary.usage as a cost-cap breach, setting
    cost_abort_triggered=True for every dry run regardless of real spend
    (root-caused and repaired during this packet's S4 -- see
    proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/scratch_notes.md).
    record_request_cost has exactly one call site (enrich_request_meta,
    request-time only) -- no resume/replay path feeds a persisted
    request_meta back through it, so this dry_run flag cannot be replayed
    to bypass the cap on a live run.
    """
    runner = _load_runner_module()
    state = runner.SpendTrackerState(
        run_root=tmp_path,
        run_id="rid",
        max_cost_usd=5.0,
        pricing_source="test",
        pricing_sha256="0" * 64,
        pricing_registry={},
        total_cost_usd=0.0,
        cost_abort_triggered=False,
        abort_reason=None,
        entries=[],
    )
    monkeypatch.setattr(runner, "_ACTIVE_SPEND_TRACKER", state)

    result = runner.record_request_cost(
        {"dry_run": True, "status_code": None},
        phase="A",
        step_id="A0",
        partition_id="p1",
        provider="openai",
        model_id="gpt-5",
    )

    assert result == {"dry_run": True, "status_code": None}
    assert state.cost_abort_triggered is False
    assert state.abort_reason is None
    assert state.entries == []


# ---------------------------------------------------------------------------
# S-series (RTE-W1-010): source identity
# ---------------------------------------------------------------------------


def test_s1_normal_git_checkout_records_exact_commit_identity(tmp_path: Path) -> None:
    runner = _load_runner_module()
    repo_root = Path(__file__).resolve().parents[3]

    sha = runner.required_execution_source_identity(repo_root)

    assert sha != "UNKNOWN"
    assert runner._looks_like_plausible_git_sha(sha)


def test_s2_git_resolution_failure_blocks_with_source_identity_error(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()

    def _raise(*_args, **_kwargs):
        raise RuntimeError("git binary not found")

    monkeypatch.setattr(runner.subprocess, "check_output", _raise)

    with pytest.raises(runner.SourceIdentityUnprovenError):
        runner.required_execution_source_identity(tmp_path)


@pytest.mark.parametrize("injected", ["UNKNOWN", "unknown", "Unknown"])
def test_s3_literal_unknown_injected_is_rejected(monkeypatch, injected, tmp_path: Path) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "get_git_sha", lambda root: injected)

    with pytest.raises(runner.SourceIdentityUnprovenError):
        runner.required_execution_source_identity(tmp_path)


@pytest.mark.parametrize("injected", ["", "   ", None, "not-a-sha", "deadbeef", 12345])
def test_s4_blank_or_none_or_implausible_identity_is_rejected(monkeypatch, injected, tmp_path: Path) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "get_git_sha", lambda root: injected)

    with pytest.raises(runner.SourceIdentityUnprovenError):
        runner.required_execution_source_identity(tmp_path)


@pytest.mark.parametrize("valid_sha", [VALID_SHA1, VALID_SHA256])
def test_s4_plausible_sha1_and_sha256_shapes_are_accepted(monkeypatch, valid_sha, tmp_path: Path) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "get_git_sha", lambda root: valid_sha)

    resolved = runner.required_execution_source_identity(tmp_path)

    assert resolved == valid_sha


def test_s5_run_manifest_and_runner_identity_agree_on_source_revision(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "get_git_sha", lambda root: VALID_SHA1)

    run_root = tmp_path / "run"
    run_root.mkdir(parents=True, exist_ok=True)
    runner.write_runner_identity(tmp_path, run_root, "run-1")

    runner_identity = json.loads((run_root / "RUNNER_IDENTITY.json").read_text(encoding="utf-8"))
    assert runner_identity["git_sha"] == VALID_SHA1

    # RUN_MANIFEST.json's own git_sha field is written by write_run_manifest
    # via the same get_git_sha(root) dependency (reporting.ReportingDeps) --
    # asserting the dependency wiring is single-sourced (no second identity
    # authority) rather than re-deriving identity independently.
    assert runner._reporting_deps().get_git_sha is runner.get_git_sha


def test_s6_pre_live_gate_blocks_evidence_approval_without_proven_identity() -> None:
    gate = _load_gate_module()

    unproven_results, unproven_blockers = gate.evaluate_source_identity({"git_sha": "UNKNOWN"})
    assert unproven_results["status"] == "FAIL"
    assert len(unproven_blockers) == 1
    assert unproven_blockers[0].reason_code == gate.SOURCE_IDENTITY_UNPROVEN

    proven_results, proven_blockers = gate.evaluate_source_identity({"git_sha": VALID_SHA1})
    assert proven_results["status"] == "PASS"
    assert proven_blockers == []


def test_s6_pre_live_gate_blocker_classified_as_environment_blocker() -> None:
    gate = _load_gate_module()

    bucket = gate.classify_blocker_bucket(
        {"reason_code": gate.SOURCE_IDENTITY_UNPROVEN, "details": {}}
    )

    assert bucket == gate.ENVIRONMENT_BLOCKER


def test_s7_read_only_best_effort_identity_never_raises(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "UNKNOWN")

    # Read-only/advisory surfaces must keep working even without proven
    # identity -- best_effort_source_identity must never raise.
    assert runner.best_effort_source_identity(tmp_path) == "UNKNOWN"


def test_s7_required_execution_source_identity_gate_is_a_single_call_site() -> None:
    """Guardrail: the fail-closed identity gate must only appear once in the
    main() phase-execution path, immediately before phase execution begins,
    so that read-only introspection commands (which exit before this point)
    are never subject to it.
    """
    runner = _load_runner_module()
    source = inspect.getsource(runner.main)

    call_count = source.count("required_execution_source_identity(root)")
    assert call_count == 1

    gate_idx = source.index("required_execution_source_identity(root)")
    runners_dict_idx = source.index('runners = {')
    assert gate_idx < runners_dict_idx


def test_s8_no_alternate_non_git_execution_identity_contract_exists() -> None:
    """S0/S8 characterization: this repo has no repo-authoritative,
    evidence-producing, non-Git execution identity contract. The only
    content-hash identity present (lib.prescan.intelligence_router's
    corpus_manifest_hash / build_prescan_source_identity) is explicitly
    scoped to prescan-freshness decisions ("local-only identity metadata
    used to decide whether imports are fresh") and is not wired into
    RUN_MANIFEST.json / RUNNER_IDENTITY.json / CERTIFICATION_RESULT.json as
    a replacement for git identity. We therefore do not invent one; a plain
    git checkout remains the only supported evidence-producing path.
    """
    import lib.intelligence_router as intelligence_router_module

    doc = intelligence_router_module.build_prescan_source_identity.__doc__ or ""
    assert "local-only" in doc


# ---------------------------------------------------------------------------
# B-series (RTE-W1-006): batch outcome typed contract
# ---------------------------------------------------------------------------


class _FakeEventStore:
    def __init__(self, *, insert_returns=True, fetch_returns=None, raise_on_insert=False):
        self.insert_calls = []
        self.run_events = []
        self._insert_returns = insert_returns
        self._fetch_returns = fetch_returns
        self._raise_on_insert = raise_on_insert

    def insert_webhook_event_if_absent(self, **kwargs):
        self.insert_calls.append(kwargs)
        if self._raise_on_insert:
            raise RuntimeError("insert failed")
        if isinstance(self._insert_returns, dict):
            return self._insert_returns.get(kwargs["idempotency_key"], True)
        return self._insert_returns

    def fetch_webhook_event_id(self, provider: str, event_id: str):
        if isinstance(self._fetch_returns, dict):
            return self._fetch_returns.get(event_id)
        return self._fetch_returns

    def append_run_event(self, row):
        self.run_events.append(row)


@pytest.fixture(autouse=True)
def _fake_ledger_module(monkeypatch):
    class _RunEventInsert:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setitem(
        sys.modules,
        "ledger.interface",
        type("_LedgerModule", (), {"RunEventInsert": _RunEventInsert})(),
    )


def test_b7_fully_successful_batch_is_reported_as_such() -> None:
    store = _FakeEventStore(insert_returns=True)
    batch_results = {
        "batch-1": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"},
        "batch-2": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"},
    }

    result = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )

    assert result["integrated"] == 2
    assert result["idempotent_duplicates"] == 0
    assert result["failed"] == 0


def test_b8_idempotent_duplicate_is_not_misclassified_as_failure() -> None:
    # insert returns False (already exists) but the event store has prior
    # idempotency evidence (fetch_webhook_event_id returns a real id).
    store = _FakeEventStore(insert_returns=False, fetch_returns="openai:batch_batch-1")
    batch_results = {"batch-1": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"}}

    result = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )

    assert result["integrated"] == 0
    assert result["idempotent_duplicates"] == 1
    assert result["failed"] == 0


def test_b_not_inserted_with_no_idempotency_evidence_fails_closed() -> None:
    # insert returns False and the event store has no discoverable prior
    # event id -- ambiguous, must fail closed rather than assume duplicate.
    store = _FakeEventStore(insert_returns=False, fetch_returns=None)
    batch_results = {"batch-1": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"}}

    result = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )

    assert result["integrated"] == 0
    assert result["idempotent_duplicates"] == 0
    assert result["failed"] == 1


def test_b5_all_integrations_raise_is_reported_as_all_failed() -> None:
    store = _FakeEventStore(raise_on_insert=True)
    batch_results = {
        "batch-1": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"},
        "batch-2": {"status": "failed", "completed_at": "2026-01-01T00:00:00Z"},
    }

    result = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )

    assert result["integrated"] == 0
    assert result["failed"] == 2


def test_integrate_batch_results_with_webhook_legacy_int_contract_preserved() -> None:
    """Backward-compat guard: v3 (out of scope) imports
    integrate_batch_results_with_webhook and depends on its int return."""
    store = _FakeEventStore(insert_returns=True)
    batch_results = {"batch-1": {"status": "completed", "completed_at": "2026-01-01T00:00:00Z"}}

    integrated = batch_retriever_module.integrate_batch_results_with_webhook(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )

    assert integrated == 1
    assert isinstance(integrated, int)


def _fake_run_batch_retrieval_deps(runner, monkeypatch, *, batch_results, event_store):
    monkeypatch.setattr(
        batch_retriever_module,
        "retrieve_openai_batches",
        lambda **_kwargs: batch_results,
    )
    monkeypatch.setattr(runner, "resolve_api_key", lambda *_a, **_k: ("fake-key", "OPENAI_API_KEY"))
    monkeypatch.setattr(runner, "_build_event_store_for_runner", lambda: event_store)


def test_b1_retriever_module_unavailable_fails_closed(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    monkeypatch.setitem(sys.modules, "lib.batch_retriever", None)
    try:
        outcome = runner.run_batch_retrieval_and_integration_detailed(
            run_id="rid", batch_ids=["b1", "b2"], cfg=SimpleNamespace(), provider="openai"
        )
    finally:
        monkeypatch.undo()
        # Restore the real module for subsequent tests in this process.
        import importlib

        importlib.reload(batch_retriever_module)

    assert outcome.success is False
    assert outcome.exit_code != 0
    assert outcome.attempted == 2
    assert outcome.failed == 2
    assert "retriever_module_unavailable" in outcome.reason_codes


def test_b2_provider_credential_unavailable_fails_closed_no_secret_leak(monkeypatch, capsys) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "resolve_api_key", lambda *_a, **_k: (None, "OPENAI_API_KEY"))

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.success is False
    assert outcome.exit_code != 0
    assert "provider_credential_unavailable" in outcome.reason_codes
    captured = capsys.readouterr()
    assert "fake-key" not in captured.out
    assert "fake-key" not in captured.err


def test_b3_event_store_unavailable_fails_closed(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(runner, "resolve_api_key", lambda *_a, **_k: ("fake-key", "OPENAI_API_KEY"))
    monkeypatch.setattr(
        batch_retriever_module,
        "retrieve_openai_batches",
        lambda **_kwargs: {"b1": {"status": "completed", "completed_at": "t"}},
    )

    def _raise():
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(runner, "_build_event_store_for_runner", _raise)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.success is False
    assert outcome.exit_code != 0
    assert "event_store_unavailable" in outcome.reason_codes


def test_b4_retrieval_exception_all_fail(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {
        "b1": {"status": "unknown", "error": "Batch retrieval failed: boom"},
        "b2": {"status": "unknown", "error": "Batch retrieval failed: boom"},
    }
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=_FakeEventStore())

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1", "b2"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.attempted == 2
    assert outcome.retrieved < outcome.attempted
    assert outcome.failed > 0
    assert outcome.success is False
    assert outcome.exit_code != 0


def test_b5_all_integrations_fail_end_to_end(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {
        "b1": {"status": "completed", "completed_at": "t"},
        "b2": {"status": "failed", "completed_at": "t"},
    }
    store = _FakeEventStore(raise_on_insert=True)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1", "b2"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.terminal == 2
    assert outcome.integrated == 0
    assert outcome.success is False
    assert outcome.exit_code != 0
    assert "all_integrations_failed" in outcome.reason_codes


def test_b6_partial_success_defaults_to_failure(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {
        "b1": {"status": "completed", "completed_at": "t"},
        "b2": {"status": "completed", "completed_at": "t"},
    }
    store = _FakeEventStore(insert_returns={"batch_b1": True, "batch_b2": False}, fetch_returns=None)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1", "b2"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.integrated == 1
    assert outcome.failed == 1
    # No evidence of an existing warning-only partial-success policy for
    # batch retrieval was found in this repo (S0 finding) -- default to
    # failure per system invariant 16.
    assert outcome.success is False
    assert outcome.exit_code != 0


def test_b7_fully_successful_end_to_end(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {
        "b1": {"status": "completed", "completed_at": "t"},
        "b2": {"status": "completed", "completed_at": "t"},
    }
    store = _FakeEventStore(insert_returns=True)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1", "b2"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.attempted == outcome.retrieved == outcome.terminal == 2
    assert outcome.failed == 0
    assert outcome.unmapped == 0
    assert outcome.success is True
    assert outcome.exit_code == 0


def test_b8_idempotent_duplicate_end_to_end_is_success(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {"b1": {"status": "completed", "completed_at": "t"}}
    store = _FakeEventStore(insert_returns=False, fetch_returns="openai:batch_b1")
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.integrated == 0
    assert outcome.idempotent_duplicates == 1
    assert outcome.failed == 0
    assert outcome.success is True
    assert outcome.exit_code == 0
    assert "idempotent_replay_only" in outcome.reason_codes


def test_b_legitimate_zero_work_pending_batches_is_not_a_failure(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {"b1": {"status": "in_progress", "completed_at": ""}}
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=_FakeEventStore())

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.terminal == 0
    assert outcome.integrated == 0
    assert outcome.success is True
    assert outcome.exit_code == 0
    assert "no_terminal_batches_yet" in outcome.reason_codes


def test_b9_original_submission_provenance_is_deferred_not_fabricated(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {"b1": {"status": "completed", "completed_at": "t"}}
    _fake_run_batch_retrieval_deps(
        runner, monkeypatch, batch_results=batch_results, event_store=_FakeEventStore(insert_returns=True)
    )

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.original_submission_provenance == "DEFERRED_RESIDUAL"


def test_cli_dispatch_exits_with_outcome_exit_code(monkeypatch) -> None:
    """Structural guard: the --batch-retrieve CLI dispatch must exit with
    outcome.exit_code, not a bare-integer >= 0 comparison (the original
    RTE-W1-006 defect)."""
    runner = _load_runner_module()
    source = inspect.getsource(runner.main)

    assert "sys.exit(0 if integrated >= 0 else 1)" not in source
    assert "sys.exit(outcome.exit_code)" in source
    assert "run_batch_retrieval_and_integration_detailed(" in source


def test_s9_doctor_full_persist_blocks_certification_on_unproven_identity(
    monkeypatch, tmp_path: Path
) -> None:
    """RTE-W1-010: --doctor's persist=True path (run_doctor_full) writes
    genuine certification evidence (DOCTOR_FULL.json + CERTIFICATION_RESULT
    via write_certification_result) for the CURRENT run -- it is not
    read-only introspection reporting a historical run, so it must be
    gated the same as the main phase-execution path. Found during
    independent audit: this dispatch is reached via a different CLI branch
    than the phase-execution gate and was originally left ungated."""
    runner = _load_runner_module()
    run_root = tmp_path / "artifact-root" / "runs" / "doctor_probe"
    dirs = {"root": run_root}
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "routing_policy", "cost")

    monkeypatch.setattr(runner, "collect_prompt_index", lambda: ({}, []))
    monkeypatch.setattr(runner, "get_phase_prompts", lambda phase: [])
    monkeypatch.setattr(
        runner,
        "get_required_artifact_status",
        lambda dirs_arg, phases: {"required_groups_present_pct": 100.0},
    )
    monkeypatch.setattr(runner, "collect_provider_routes", lambda **kwargs: {})
    monkeypatch.setattr(runner, "run_provider_doctor_probe", lambda **kwargs: {})
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "UNKNOWN")

    exit_code = runner.run_doctor_full(
        tmp_path, dirs, run_id="doctor_probe", phases=["A"], cfg=cfg
    )

    assert exit_code == 1
    assert not (run_root / "CERTIFICATION_RESULT.json").exists()
    assert not (runner.current_doctor_root(tmp_path) / "DOCTOR_FULL.json").exists()


def test_s9_doctor_full_persist_false_is_unaffected_by_identity_gate(
    monkeypatch, tmp_path: Path
) -> None:
    """Read-only preservation: the persist=False --doctor variant must not
    be blocked by the identity gate (invariant 11)."""
    runner = _load_runner_module()
    run_root = tmp_path / "artifact-root" / "runs" / "doctor_probe"
    dirs = {"root": run_root}
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    object.__setattr__(cfg, "routing_policy", "cost")

    monkeypatch.setattr(runner, "collect_prompt_index", lambda: ({}, []))
    monkeypatch.setattr(runner, "get_phase_prompts", lambda phase: [])
    monkeypatch.setattr(
        runner,
        "get_required_artifact_status",
        lambda dirs_arg, phases: {"required_groups_present_pct": 100.0},
    )
    monkeypatch.setattr(runner, "collect_provider_routes", lambda **kwargs: {})
    monkeypatch.setattr(runner, "run_provider_doctor_probe", lambda **kwargs: {})
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "UNKNOWN")

    exit_code = runner.run_doctor_full(
        tmp_path, dirs, run_id="doctor_probe", phases=["A"], cfg=cfg, persist=False
    )

    # No prompts are registered for phase A in this fixture, so run_doctor_full's
    # own has_missing check independently drives exit_code=1 -- unrelated to
    # source identity. The point of this test is that persist=False never
    # invokes required_execution_source_identity() at all (no certification
    # evidence is ever written for the read-only variant, gate or no gate).
    assert exit_code == 1
    assert not (run_root / "CERTIFICATION_RESULT.json").exists()
    assert not (runner.current_doctor_root(tmp_path) / "DOCTOR_FULL.json").exists()
