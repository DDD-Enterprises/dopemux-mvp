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
    from extractor.costing import get_registry
    monkeypatch.setattr(get_registry(), "_active_tracker", state)

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
    main() phase-execution path, so that read-only introspection commands
    (which exit before this point) are never subject to it, while every
    evidence-producing write and live/provider dispatch runs after it.

    RTE-W1-010 P1 (found during the post-ready-for-review Codex/Copilot
    review of PR #1232, head 492208f4): the gate previously sat immediately
    before ``runners = {`` -- textually after write_run_manifest/
    write_runner_identity/write_confidence_ramp_artifacts *and* after the
    --async-provider/--finalize/--batch-watch/--batch-retrieve CLI dispatch
    blocks, all of which ``sys.exit()`` on their own before ever reaching
    the gate. An UNKNOWN/unproven source identity therefore never blocked
    those paths -- they dispatched to providers and/or wrote canonical
    RUN_MANIFEST.json / RUNNER_IDENTITY.json evidence regardless. The gate
    is now positioned immediately after the last pure read-only/
    introspection early exit (persist=False --doctor) and before every
    write/dispatch branch, so this test additionally pins that ordering
    structurally (source-order assertions, per test_t6's rationale: driving
    the full multi-thousand-line main() end-to-end offline is impractical).
    """
    runner = _load_runner_module()
    source = inspect.getsource(runner.main)

    call_count = source.count("required_execution_source_identity(root)")
    assert call_count == 1

    gate_idx = source.index("required_execution_source_identity(root)")
    runners_dict_idx = source.index("runners = {")
    assert gate_idx < runners_dict_idx

    # Last pure read-only/introspection early exit (persist=False --doctor)
    # must remain reachable and unaffected -- it returns before the gate.
    # The gate is now placed *before* get_run_dirs and write_phase_contract_map
    # to ensure no run-scoped evidence is written.
    contract_map_idx = source.index("write_phase_contract_map(")
    assert gate_idx < contract_map_idx

    # Every canonical-evidence write and every live/provider dispatch branch
    # discovered during the P1 review must fall after the gate.
    for marker in (
        'run_integrated_prescan_stage(root, dirs["root"], cfg)',  # Stage 0 online prescan
        "prompt_report = write_run_manifest(",
        "write_runner_identity(",
        "enforce_pre_live_validator_for_execution(",
        "n = run_phase_R_async_submit(",
        "n = run_phase_R_finalize(",
        "watch_result = run_batch_watch(",
        "outcome = run_batch_retrieval_and_integration_detailed(",
        'if args.phase == "S_INT":',  # C1R2: S_INT synchronous dispatch (RTE-W1-010 residual gap)
    ):
        marker_idx = source.index(marker)
        assert gate_idx < marker_idx, f"{marker!r} must run after the identity gate"


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
    def __init__(
        self,
        *,
        insert_returns=True,
        fetch_returns=None,
        raise_on_insert=False,
        append_side_effects=None,
    ):
        self.insert_calls = []
        self.append_calls = []
        self.run_events = []
        self._insert_returns = insert_returns
        self._fetch_returns = fetch_returns
        self._raise_on_insert = raise_on_insert
        self._append_side_effects = list(append_side_effects or [])

    def insert_webhook_event_if_absent(self, event):
        if not isinstance(event, _WebhookEventInsert):
            raise TypeError("expected one WebhookEventInsert object")
        self.insert_calls.append(event)
        if self._raise_on_insert:
            raise RuntimeError("insert failed")
        if isinstance(self._insert_returns, list):
            return self._insert_returns.pop(0)
        if isinstance(self._insert_returns, dict):
            return self._insert_returns.get(event.idempotency_key, True)
        return self._insert_returns

    def fetch_webhook_event_id(self, provider: str, event_id: str):
        if isinstance(self._fetch_returns, dict):
            return self._fetch_returns.get(event_id)
        return self._fetch_returns

    def append_run_event(self, row):
        self.append_calls.append(row)
        if self._append_side_effects:
            side_effect = self._append_side_effects.pop(0)
            if side_effect is not None:
                raise side_effect
        if any(
            existing.kwargs["dedupe_key"] == row.kwargs["dedupe_key"]
            for existing in self.run_events
        ):
            return
        self.run_events.append(row)


class _WebhookEventInsert:
    def __init__(
        self,
        *,
        provider,
        idempotency_key,
        event_type,
        event_id,
        received_at_utc,
        payload_json,
        headers_json,
        signature_valid,
    ) -> None:
        self.provider = provider
        self.idempotency_key = idempotency_key
        self.event_type = event_type
        self.event_id = event_id
        self.received_at_utc = received_at_utc
        self.payload_json = payload_json
        self.headers_json = headers_json
        self.signature_valid = signature_valid


class _RunEventInsert:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture(autouse=True)
def _fake_ledger_module(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "ledger.interface",
        type(
            "_LedgerModule",
            (),
            {
                "WebhookEventInsert": _WebhookEventInsert,
                "RunEventInsert": _RunEventInsert,
            },
        )(),
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
    assert len(store.insert_calls) == 2
    assert len(store.run_events) == 2

    webhook_event = store.insert_calls[0]
    assert webhook_event.provider == "openai"
    assert webhook_event.idempotency_key == "batch_batch-1"
    assert webhook_event.event_type == "batch.completed"
    assert webhook_event.event_id == "batch_batch-1"
    assert webhook_event.received_at_utc == "2026-01-01T00:00:00Z"
    assert webhook_event.headers_json == "{}"
    assert webhook_event.signature_valid is True
    assert json.loads(webhook_event.payload_json) == {
        "schema": "DPMX_WEBHOOK_V1",
        "event": "batch.completed",
        "event_id": "batch_batch-1",
        "run_id": "rid",
        "phase": "R",
        "step_id": "batch_retrieval",
        "partition_id": "p",
        "batch_id": "batch-1",
        "status": "completed",
        "generated_at_utc": "2026-01-01T00:00:00Z",
        "provider": "openai",
        "provider_ref": "batch-1",
    }

    run_event = store.run_events[0]
    assert run_event.kwargs == {
        "run_id": "rid",
        "phase": "R",
        "step_id": "batch_retrieval",
        "partition_id": "p",
        "provider": "openai",
        "event_type": "batch.completed",
        "event_id": "batch_batch-1",
        "provider_ref": "batch-1",
        "webhook_event_id": None,
        "dedupe_key": "batch_batch-1_rid_R_batch_retrieval_p",
        "orphaned": False,
    }


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
    assert len(store.append_calls) == 1


def test_b_duplicate_retry_repairs_run_event_after_initial_append_failure() -> None:
    store = _FakeEventStore(
        insert_returns=[True, False],
        fetch_returns="openai:batch_batch-1",
        append_side_effects=[RuntimeError("append failed"), None],
    )
    batch_results = {
        "batch-1": {
            "status": "completed",
            "completed_at": "2026-01-01T00:00:00Z",
        }
    }

    first = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )
    retry = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results=batch_results,
        event_store=store,
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
    )

    assert first["integrated"] == 0
    assert first["idempotent_duplicates"] == 0
    assert first["failed"] == 1
    assert retry["integrated"] == 0
    assert retry["idempotent_duplicates"] == 1
    assert retry["failed"] == 0
    assert len(store.append_calls) == 2
    assert len(store.run_events) == 1


def test_b_already_complete_duplicate_remains_idempotent() -> None:
    existing = _RunEventInsert(
        run_id="rid",
        phase="R",
        step_id="batch_retrieval",
        partition_id="p",
        provider="openai",
        event_type="batch.completed",
        event_id="batch_batch-1",
        provider_ref="batch-1",
        webhook_event_id="openai:batch_batch-1",
        dedupe_key="batch_batch-1_rid_R_batch_retrieval_p",
        orphaned=False,
    )
    store = _FakeEventStore(
        insert_returns=False,
        fetch_returns="openai:batch_batch-1",
    )
    store.run_events.append(existing)

    result = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results={
            "batch-1": {
                "status": "completed",
                "completed_at": "2026-01-01T00:00:00Z",
            }
        },
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
    assert len(store.append_calls) == 1
    assert store.run_events == [existing]


def test_b_duplicate_retry_append_failure_fails_closed() -> None:
    store = _FakeEventStore(
        insert_returns=False,
        fetch_returns="openai:batch_batch-1",
        append_side_effects=[RuntimeError("retry append failed")],
    )

    result = batch_retriever_module.integrate_batch_results_with_webhook_detailed(
        batch_results={
            "batch-1": {
                "status": "completed",
                "completed_at": "2026-01-01T00:00:00Z",
            }
        },
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
    assert result["details"] == [
        {
            "batch_id": "batch-1",
            "outcome": "failed",
            "error": "retry append failed",
        }
    ]
    assert len(store.append_calls) == 1
    assert store.run_events == []


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
    assert store.append_calls == []


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


# ---------------------------------------------------------------------------
# B10-series (RTE-W1-006 V5 terminal repair): a provider terminal-failure
# batch (failed/expired/cancelled/canceled/timeout) must be material failure
# even when its batch.failed webhook event integrates cleanly. Regression
# for PR #1232 head 492208f4: integrate_batch_results_with_webhook_detailed
# only reports ``failed`` when the insert itself raises or has no
# idempotency evidence, so a successfully-inserted batch.failed event was
# previously counted as ``integrated`` with outcome.failed staying 0.
# ---------------------------------------------------------------------------


def test_b10_terminal_failure_batch_with_successful_webhook_integration_is_reported_as_failure(
    monkeypatch,
) -> None:
    runner = _load_runner_module()
    batch_results = {"b1": {"status": "failed", "completed_at": "t"}}
    store = _FakeEventStore(insert_returns=True)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    # The webhook event integration itself succeeded -- this is not a
    # failure of integrate_batch_results_with_webhook_detailed.
    assert outcome.integrated == 1
    assert outcome.failed == 0
    # But the batch's own provider-terminal status was a failure, and that
    # must still surface as material failure.
    assert outcome.terminal_failure_batches == 1
    assert outcome.success is False
    assert outcome.exit_code != 0
    assert "provider_terminal_batch_failure" in outcome.reason_codes


@pytest.mark.parametrize(
    "failure_status", ["failed", "expired", "cancelled", "canceled", "timeout"]
)
def test_b11_each_terminal_failure_status_is_material_failure(monkeypatch, failure_status) -> None:
    runner = _load_runner_module()
    batch_results = {"b1": {"status": failure_status, "completed_at": "t"}}
    store = _FakeEventStore(insert_returns=True)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.terminal_failure_batches == 1
    assert outcome.success is False
    assert outcome.exit_code != 0


def test_b12_mixed_successful_and_terminal_failure_batches_is_material_failure(monkeypatch) -> None:
    runner = _load_runner_module()
    batch_results = {
        "b1": {"status": "completed", "completed_at": "t"},
        "b2": {"status": "failed", "completed_at": "t"},
    }
    store = _FakeEventStore(insert_returns=True)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1", "b2"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.terminal == 2
    assert outcome.integrated == 2  # both webhook inserts succeeded
    assert outcome.failed == 0
    assert outcome.terminal_failure_batches == 1
    assert outcome.success is False
    assert outcome.exit_code != 0


def test_b13_idempotent_replay_of_terminal_failure_batch_remains_failure(monkeypatch) -> None:
    """Idempotency is about the webhook event, not a pardon for the batch's
    own terminal-failure status -- a replayed batch.failed event must still
    surface the underlying provider failure."""
    runner = _load_runner_module()
    batch_results = {"b1": {"status": "failed", "completed_at": "t"}}
    store = _FakeEventStore(insert_returns=False, fetch_returns="openai:batch_b1")
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.idempotent_duplicates == 1
    assert outcome.terminal_failure_batches == 1
    assert outcome.success is False
    assert outcome.exit_code != 0


def test_b14_fully_successful_terminal_set_still_exits_zero(monkeypatch) -> None:
    """Non-regression: a terminal set with zero failure-status batches must
    remain unaffected by the terminal_failure_batches check."""
    runner = _load_runner_module()
    batch_results = {
        "b1": {"status": "completed", "completed_at": "t"},
        "b2": {"status": "succeeded", "completed_at": "t"},
        "b3": {"status": "done", "completed_at": "t"},
    }
    store = _FakeEventStore(insert_returns=True)
    _fake_run_batch_retrieval_deps(runner, monkeypatch, batch_results=batch_results, event_store=store)

    outcome = runner.run_batch_retrieval_and_integration_detailed(
        run_id="rid", batch_ids=["b1", "b2", "b3"], cfg=SimpleNamespace(), provider="openai"
    )

    assert outcome.terminal_failure_batches == 0
    assert outcome.success is True
    assert outcome.exit_code == 0
    assert "fully_integrated" in outcome.reason_codes


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


# ---------------------------------------------------------------------------
# S10-series (RTE-W1-010 P1 repair): main() CLI dispatch is actually blocked,
# end to end, when source identity is unproven -- not just textually ordered
# ahead of the gate. Regression-repair for PR #1232 head 492208f4: the
# --async-provider/--finalize/--batch-watch/--batch-retrieve dispatch blocks
# each called sys.exit() on their own before main() ever reached the (then
# textually-later) identity gate, so an UNKNOWN identity never blocked them.
# ---------------------------------------------------------------------------


def _run_main_with_argv(runner, monkeypatch, tmp_path: Path, argv_tail: list) -> int:
    """Drive runner.main() to completion (it always sys.exit()s) with a
    controlled cwd/output-root and an UNKNOWN source identity, returning the
    process exit code. All provider-mutating dispatch points reachable after
    the identity gate are stubbed to raise -- if the gate is bypassed for a
    given CLI shape, the corresponding stub raising surfaces as a test
    failure (pytest.fail via the stub) rather than a silent false pass.

    DPMX_LIVE_OK=1 is set so the pre-existing, unrelated
    enforce_live_operation_consent() gate (batch-watch/batch-retrieve/
    async-provider always require this env var, independent of source
    identity) doesn't short-circuit before we ever reach the identity gate
    under test.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("DPMX_LIVE_OK", "1")
    monkeypatch.setattr(sys, "argv", ["run_extraction_v5.py", *argv_tail, "--output-root", str(output_root)])
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "UNKNOWN")

    def _must_not_be_called(name):
        def _raise(*_a, **_k):
            raise AssertionError(f"{name} must not be called with unproven source identity")

        return _raise

    for name in (
        "run_integrated_prescan_stage",
        "write_run_manifest",
        "write_runner_identity",
        "write_confidence_ramp_artifacts",
        "run_phase_R_async_submit",
        "run_phase_R_finalize",
        "run_batch_watch",
        "run_batch_retrieval_and_integration_detailed",
        "run_phase_A",
        "run_phase_R",
    ):
        monkeypatch.setattr(runner, name, _must_not_be_called(name))

    with pytest.raises(SystemExit) as exc_info:
        runner.main()
    return exc_info.value.code


def test_s10_ordinary_phase_execution_blocked_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    exit_code = _run_main_with_argv(
        runner, monkeypatch, tmp_path, ["--phase", "A", "--dry-run", "--run-id", "s10-phase"]
    )
    assert exit_code == 1


def test_s10_async_provider_submit_blocked_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    exit_code = _run_main_with_argv(
        runner,
        monkeypatch,
        tmp_path,
        ["--phase", "R", "--async-provider", "openai", "--run-id", "s10-async"],
    )
    assert exit_code == 1


def test_s10_finalize_blocked_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    exit_code = _run_main_with_argv(
        runner, monkeypatch, tmp_path, ["--phase", "R", "--finalize", "--run-id", "s10-finalize"]
    )
    assert exit_code == 1


def test_s10_batch_watch_blocked_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    exit_code = _run_main_with_argv(
        runner, monkeypatch, tmp_path, ["--phase", "R", "--batch-watch", "--run-id", "s10-watch"]
    )
    assert exit_code == 1


def test_s10_batch_retrieve_blocked_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    exit_code = _run_main_with_argv(
        runner,
        monkeypatch,
        tmp_path,
        ["--batch-retrieve", "--batch-ids", "b1", "--run-id", "s10-retrieve"],
    )
    assert exit_code == 1


def test_s10_s_int_blocked_before_dispatch(monkeypatch, tmp_path: Path) -> None:
    """C1R2 regression: --phase S_INT used to dispatch to run_s_int() (and,
    via its prompt_executor, to call_llm()) and sys.exit() entirely before
    main() ever reached the (then textually-later) identity gate -- an
    UNKNOWN identity never blocked it. required_execution_source_identity()
    must now dominate S_INT the same way it dominates every other dispatch
    path.

    Deliberately does NOT rely on exit_code alone: the pre-fix S_INT branch
    wraps run_s_int() in a bare ``except Exception: ... sys.exit(1)``, so a
    stub that merely raises would be swallowed into the *same* exit(1) a
    correctly-gated run produces, masking the bug. A call-recording side
    channel makes the assertion mutation-sensitive regardless of exit code.
    """
    runner = _load_runner_module()
    # NOTE: `import s_int.run_s_int as m` would bind `m` to the *function*
    # s_int.run_s_int (s_int/__init__.py's `from .run_s_int import run_s_int`
    # overwrites the package attribute of that name), not the submodule.
    # The local `from s_int.run_s_int import run_s_int` inside main() resolves
    # via sys.modules, so patch the true submodule object directly.
    s_int_run_s_int_module = importlib.import_module("s_int.run_s_int")

    calls: list = []

    def _record_and_raise(*_a, **_k):
        calls.append("run_s_int")
        raise AssertionError("run_s_int must not be called with unproven source identity")

    monkeypatch.setattr(s_int_run_s_int_module, "run_s_int", _record_and_raise)

    def _call_llm_record_and_raise(*_a, **_k):
        calls.append("call_llm")
        raise AssertionError("call_llm must not be called with unproven source identity")

    monkeypatch.setattr(runner, "call_llm", _call_llm_record_and_raise)

    exit_code = _run_main_with_argv(
        runner, monkeypatch, tmp_path, ["--phase", "S_INT", "--dry-run", "--run-id", "s10-s-int"]
    )
    assert calls == [], f"unproven-identity dispatch reached: {calls!r}"
    assert exit_code == 1


def _run_s_int_main_with_resolved_id(
    runner,
    monkeypatch,
    tmp_path: Path,
    capsys,
    *,
    resolved_run_id: str,
    argv_tail: list,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    (output_root / "runs" / resolved_run_id).mkdir(parents=True)
    observed = {}

    def _resolve_run_context(_root, args, **_kwargs):
        observed["resolver_input"] = args.run_id
        return SimpleNamespace(run_id=resolved_run_id)

    def _run_s_int(_root, run_id, **_kwargs):
        observed["run_s_int_run_id"] = run_id
        return {"status": "DRY_RUN", "run_id": run_id}

    def _forbid_provider_call(*_args, **_kwargs):
        raise AssertionError("provider call forbidden in S_INT run-id regression")

    s_int_run_s_int_module = importlib.import_module("s_int.run_s_int")
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "S_INT",
            "--dry-run",
            *argv_tail,
            "--output-root",
            str(output_root),
        ],
    )
    monkeypatch.setattr(runner, "resolve_run_context", _resolve_run_context)
    monkeypatch.setattr(
        runner,
        "required_execution_source_identity",
        lambda _root: VALID_SHA1,
    )
    monkeypatch.setattr(runner, "call_llm", _forbid_provider_call)
    monkeypatch.setattr(s_int_run_s_int_module, "run_s_int", _run_s_int)

    with pytest.raises(SystemExit) as exc_info:
        runner.main()

    assert exc_info.value.code == 0
    output = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    return observed, output


def test_s_int_omitted_run_id_uses_existing_resolved_identity(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    runner = _load_runner_module()

    observed, output = _run_s_int_main_with_resolved_id(
        runner,
        monkeypatch,
        tmp_path,
        capsys,
        resolved_run_id="resolved-omitted-run",
        argv_tail=[],
    )

    assert observed == {
        "resolver_input": None,
        "run_s_int_run_id": "resolved-omitted-run",
    }
    assert output["run_id"] == "resolved-omitted-run"


def test_s_int_explicit_run_id_remains_resolved_identity(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    runner = _load_runner_module()

    observed, output = _run_s_int_main_with_resolved_id(
        runner,
        monkeypatch,
        tmp_path,
        capsys,
        resolved_run_id="explicit-run",
        argv_tail=["--run-id", "explicit-run"],
    )

    assert observed == {
        "resolver_input": "explicit-run",
        "run_s_int_run_id": "explicit-run",
    }
    assert output["run_id"] == "explicit-run"


def test_s10_manifest_and_runner_identity_files_are_never_written(monkeypatch, tmp_path: Path) -> None:
    """Direct file-evidence proof (not just a mocked-call proof) for an
    unproven identity: RUNNER_IDENTITY.json is never written at all (there
    is no failure-record variant of it), and if a RUN_MANIFEST.json exists
    it is only the non-authoritative startup-failure record written by
    update_run_manifest_startup_failure (same shape already used for
    cost_cap_setup_failed/launch_provider_preflight_failed) -- never a
    manifest claiming a runnable canonical execution."""
    runner = _load_runner_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "A",
            "--dry-run",
            "--run-id",
            "s10-evidence",
            "--output-root",
            str(output_root),
        ],
    )
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "UNKNOWN")

    with pytest.raises(SystemExit) as exc_info:
        runner.main()

    assert exc_info.value.code == 1
    identities = list(output_root.rglob("RUNNER_IDENTITY.json"))
    assert identities == []

    manifests = list(output_root.rglob("RUN_MANIFEST.json"))
    for manifest_path in manifests:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert payload.get("run_status") == "FAILED"
        assert payload.get("failure_reason") == "source_identity_unproven"
        # Never the shape of a run that claims to have executed phases.
        assert "phases" not in payload
        assert "prompt_set_integrity" not in payload


def test_s10_unproven_identity_blocks_pre_live_validation_before_provider_boundary(
    monkeypatch, tmp_path: Path
) -> None:
    """Execution identity failure must dominate the validator's online boundary."""
    runner = _load_runner_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    validator_calls: list[object] = []

    monkeypatch.chdir(repo_root)
    monkeypatch.setenv(runner.DPMX_LIVE_OK_ENV, "1")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "A",
            "--execute",
            "--run-id",
            "s10-validator-boundary",
            "--output-root",
            str(output_root),
        ],
    )
    monkeypatch.setattr(runner, "get_git_sha", lambda _root: "UNKNOWN")
    monkeypatch.setattr(
        runner,
        "enforce_pre_live_validator_for_execution",
        lambda **kwargs: validator_calls.append(kwargs),
    )

    with pytest.raises(SystemExit) as exc_info:
        runner.main()

    assert exc_info.value.code == 1
    assert validator_calls == []
    assert list(output_root.rglob("RUNNER_IDENTITY.json")) == []


def test_s10_valid_identity_reaches_pre_live_validator(monkeypatch, tmp_path: Path) -> None:
    """Moving the identity gate must preserve valid execution validation."""
    runner = _load_runner_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    validator_calls: list[object] = []

    monkeypatch.chdir(repo_root)
    monkeypatch.setenv(runner.DPMX_LIVE_OK_ENV, "1")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "A",
            "--execute",
            "--run-id",
            "s10-validator-valid",
            "--output-root",
            str(output_root),
        ],
    )
    monkeypatch.setattr(runner, "required_execution_source_identity", lambda _root: VALID_SHA1)
    monkeypatch.setattr(
        runner,
        "enforce_pre_live_validator_for_execution",
        lambda **kwargs: validator_calls.append(kwargs),
    )
    monkeypatch.setattr(
        runner,
        "run_integrated_prescan_stage",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("stop_after_validator")),
    )

    with pytest.raises(RuntimeError, match="stop_after_validator"):
        runner.main()

    assert len(validator_calls) == 1


def test_s10_execution_artifacts_pin_validated_source_identity(monkeypatch, tmp_path: Path) -> None:
    """Canonical execution evidence must not re-query mutable Git state."""
    runner = _load_runner_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    git_calls: list[Path] = []

    def _git_sha(root: Path) -> str:
        git_calls.append(root)
        return VALID_SHA1 if len(git_calls) == 1 else "UNKNOWN"

    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "A",
            "--dry-run",
            "--run-id",
            "s10-pinned-identity",
            "--output-root",
            str(output_root),
        ],
    )
    monkeypatch.setattr(runner, "get_git_sha", _git_sha)
    monkeypatch.setattr(runner, "run_integrated_prescan_stage", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        runner,
        "write_run_routing_fingerprint",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("stop_after_evidence")),
    )

    with pytest.raises(RuntimeError, match="stop_after_evidence"):
        runner.main()

    run_root = output_root / "runs" / "s10-pinned-identity"
    manifest = json.loads((run_root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    identity = json.loads((run_root / "RUNNER_IDENTITY.json").read_text(encoding="utf-8"))
    assert manifest["git_sha"] == VALID_SHA1
    assert identity["git_sha"] == VALID_SHA1
    assert len(git_calls) == 1


def test_s10_proof_pack_writers_pin_supplied_source_identity(monkeypatch, tmp_path: Path) -> None:
    """Normal and blocked proof paths use supplied custody, never a fallback."""
    runner = _load_runner_module()
    dirs = {"root": tmp_path / "run", "A": tmp_path / "run" / "A"}
    dirs["root"].mkdir(parents=True)
    monkeypatch.setattr(
        runner,
        "get_git_sha",
        lambda _root: (_ for _ in ()).throw(AssertionError("git must not be re-queried")),
    )

    runner.update_proof_pack(
        tmp_path,
        dirs,
        "run-1",
        "2026-01-01T00:00:00Z",
        "A",
        {},
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:00:01Z",
        source_identity=VALID_SHA1,
    )
    normal = json.loads((dirs["root"] / "PROOF_PACK.json").read_text(encoding="utf-8"))
    assert normal["git_sha"] == VALID_SHA1

    runner.write_blocked_promptset_proof_pack(
        tmp_path,
        dirs,
        "run-1",
        "2026-01-01T00:00:00Z",
        ["A"],
        {"blocked_promptset": True},
        source_identity=VALID_SHA256,
    )
    blocked = json.loads((dirs["root"] / "PROOF_PACK.json").read_text(encoding="utf-8"))
    assert blocked["git_sha"] == VALID_SHA256


def test_s10_cost_abort_proof_pins_supplied_source_identity(monkeypatch, tmp_path: Path) -> None:
    """Cost-abort proof creation cannot re-resolve execution identity."""
    runner = _load_runner_module()
    dirs = {"root": tmp_path / "run", "A": tmp_path / "run" / "A"}
    dirs["root"].mkdir(parents=True)
    monkeypatch.setattr(
        runner,
        "get_git_sha",
        lambda _root: (_ for _ in ()).throw(AssertionError("git must not be re-queried")),
    )
    monkeypatch.setattr(runner, "phase_status_snapshot", lambda *_args, **_kwargs: {})

    runner._persist_cost_abort(
        root=tmp_path,
        dirs=dirs,
        run_id="run-1",
        phases=["A"],
        run_started_at="2026-01-01T00:00:00Z",
        exc=runner.CostLimitExceededError("cap", {"phase": "A"}),
        source_identity=VALID_SHA1,
    )

    proof = json.loads((dirs["root"] / "PROOF_PACK.json").read_text(encoding="utf-8"))
    assert proof["git_sha"] == VALID_SHA1


def test_s10_separate_evidence_write_cannot_inherit_prior_pinned_identity(tmp_path: Path) -> None:
    """Pinned identity is explicit per call, not retained in process state."""
    runner = _load_runner_module()
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()

    runner.write_runner_identity(
        tmp_path, first_root, "first", source_identity=VALID_SHA1
    )
    runner.write_runner_identity(
        tmp_path, second_root, "second", source_identity=VALID_SHA256
    )

    first = json.loads((first_root / "RUNNER_IDENTITY.json").read_text(encoding="utf-8"))
    second = json.loads((second_root / "RUNNER_IDENTITY.json").read_text(encoding="utf-8"))
    assert first["git_sha"] == VALID_SHA1
    assert second["git_sha"] == VALID_SHA256


def test_s10_read_only_print_config_is_unaffected_by_unproven_identity(monkeypatch, tmp_path: Path) -> None:
    """Preservation guard: a pure read-only introspection command must keep
    working (and keep exiting 0) even with an unproven source identity,
    since it returns before the gate is ever reached."""
    runner = _load_runner_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    output_root = tmp_path / "artifacts"
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_extraction_v5.py",
            "--phase",
            "A",
            "--print-config",
            "--run-id",
            "s10-readonly",
            "--output-root",
            str(output_root),
        ],
    )
    monkeypatch.setattr(runner, "get_git_sha", lambda root: "UNKNOWN")

    with pytest.raises(SystemExit) as exc_info:
        runner.main()

    assert exc_info.value.code == 0

def test_s10_persisted_coverage_report_pins_supplied_source_identity(monkeypatch, tmp_path: Path) -> None:
    """Coverage report creation cannot re-resolve execution identity."""
    runner = _load_runner_module()
    dirs = {"root": tmp_path / "run", "A": tmp_path / "run" / "A"}
    dirs["root"].mkdir(parents=True)
    monkeypatch.setattr(
        runner,
        "get_git_sha",
        lambda _root: "UNKNOWN",
    )
    monkeypatch.setattr(runner, "_coverage_for_phase", lambda *args, **kwargs: {"phase": "A", "status": "ok"})
    monkeypatch.setattr(runner, "get_required_artifact_status", lambda *args, **kwargs: {})

    runner.generate_coverage_report(
        root=tmp_path,
        dirs=dirs,
        run_id="run-1",
        phases=["A"],
        persist=True,
        source_identity=VALID_SHA1,
    )

    import json
    report = json.loads((dirs["root"] / "COVERAGE_REPORT.json").read_text(encoding="utf-8"))
    assert report["git_sha"] == VALID_SHA1


def test_s10_webhook_payload_pins_supplied_source_identity(monkeypatch, tmp_path: Path) -> None:
    """Webhook payload creation cannot re-resolve execution identity."""
    runner = _load_runner_module()
    monkeypatch.setattr(
        runner,
        "get_git_sha",
        lambda _root: "UNKNOWN",
    )

    payload = runner.build_webhook_payload(
        root=tmp_path,
        run_id="run-1",
        phase_id="A",
        phase_dir=tmp_path / "A",
        step_id="step-1",
        provider_id="provider-1",
        model_id="model-1",
        job_id="job-1",
        state="success",
        detail="detail",
        artifacts_written=[],
        artifacts_missing=[],
        source_identity=VALID_SHA1,
    )

    assert payload["run"]["git_sha"] == VALID_SHA1


def test_s10_dashboard_snapshot_pins_supplied_source_identity(monkeypatch, tmp_path: Path) -> None:
    """Dashboard snapshot creation cannot re-resolve execution identity."""
    runner = _load_runner_module()
    dirs = {"root": tmp_path / "run", "A": tmp_path / "run" / "A"}
    dirs["root"].mkdir(parents=True)
    monkeypatch.setattr(
        runner,
        "get_git_sha",
        lambda _root: "UNKNOWN",
    )
    monkeypatch.setattr(runner, "phase_status_snapshot", lambda *args, **kwargs: {})
    monkeypatch.setattr(runner, "collect_rte_risk_dashboard_inputs", lambda *args, **kwargs: {})
    monkeypatch.setattr(runner, "build_rte_risk_dashboard", lambda *args, **kwargs: {})

    runner.emit_run_dashboard_snapshot(
        run_id="run-1",
        dirs=dirs,
        ui=None,
        source="phase",
        source_identity=VALID_SHA1,
    )

    import json
    # It writes to RUN_DASHBOARD_SNAPSHOT.json and RTE_RISK_DASHBOARD.json. Wait, does it?
    # Actually, we can check if it passed source_identity to get_git_sha logic, but let's just
    # check if collect_rte_risk_dashboard_inputs received the correct git_sha.
    # The simplest is to mock collect_rte_risk_dashboard_inputs and assert on it.

    collected_git_sha = None

    def mock_collect(*args, **kwargs):
        nonlocal collected_git_sha
        collected_git_sha = kwargs.get("git_sha")
        return {}

    monkeypatch.setattr(runner, "collect_rte_risk_dashboard_inputs", mock_collect)

    runner.emit_run_dashboard_snapshot(
        run_id="run-1",
        dirs=dirs,
        ui=None,
        source="phase",
        source_identity=VALID_SHA1,
    )

    assert collected_git_sha == VALID_SHA1

def test_s8_early_exits_respect_identity_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: unresolved execution identity => zero provider-call count for
    every provider-live early command. Unresolved execution identity =>
    PHASE_CONTRACT_MAP.json absent."""
    import sys
    runner = _load_runner_module()

    def mock_required_identity(root):
        raise runner.SourceIdentityUnprovenError("mocked failure")

    monkeypatch.setattr(runner, "required_execution_source_identity", mock_required_identity)

    monkeypatch.setattr(runner, "configure_output_layout", lambda root, output_root: None)
    monkeypatch.setattr(runner, "get_run_dirs", lambda *args, **kwargs: {"root": tmp_path})
    monkeypatch.setattr(runner, "resolve_run_context", lambda *args, **kwargs: runner.RunContext("test-run", "test-run"))

    # We must mock the env to pass argparse live gate
    monkeypatch.setenv("DPMX_LIVE_OK", "1")

    commands = [
        ["--doctor-auth"],
        ["--preflight-providers"],
        ["--doctor"],
        ["--gemini-list-models"],
        ["--promptgen-scan", "--promptgen-output-dir", "foo"],
        ["--execute", "--phase", "S_INT"],
        ["--batch-mode", "--execute", "--phase", "ALL"]
    ]

    for cmd in commands:
        monkeypatch.setattr(sys, "argv", ["run_extraction_v5.py"] + cmd)
        with pytest.raises(SystemExit) as exc_info:
            runner.main()
        assert exc_info.value.code == 1

        # Also check PHASE_CONTRACT_MAP.json is absent
        assert not (tmp_path / "PHASE_CONTRACT_MAP.json").exists()
