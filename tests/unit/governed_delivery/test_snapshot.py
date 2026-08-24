"""Read-only snapshot behaviour: the six questions, determinism, containment."""

from __future__ import annotations

import inspect

import pytest

from dopemux.governed_delivery import models as m
from dopemux.governed_delivery import snapshot as s

IDENTITY = m.Identity(project_id="dopemux-mvp", repository_id="DDD-Enterprises/dopemux-mvp")
NOW = "2026-08-24T00:00:00Z"
EARLIER = "2026-08-23T00:00:00Z"


def reference(**overrides):
    kwargs = dict(
        evidence_id="ev-1",
        evidence_class="VALIDATION_RECEIPT",
        owner_system="PROOF_TOOLING",
        producer_identity="tool",
        canonical_location="proof/TP-X/VALIDATION.json",
        digest_or_signature="sha256:abc",
        identity=IDENTITY,
        observed_at=EARLIER,
        freshness_state=m.FreshnessState.CURRENT,
    )
    kwargs.update(overrides)
    return m.EvidenceReference(**kwargs)


def gate(gate_class="AUDIT", state=m.GateState.SATISFIED, gate_id=None):
    return m.GateEntry(
        gate_id=gate_id or gate_class.lower(),
        gate_class=gate_class,
        state=state,
        policy_owner="governance",
        policy_version="v1",
        subject_digest_or_head="abc",
        producer_identity="tool",
        observed_at=NOW,
        reason=f"{gate_class} is {state.value}",
    )


def ledger(*gates):
    return m.GateLedger(
        ledger_id="ledger-1",
        identity=IDENTITY,
        subject_digest_or_head="abc",
        gates=list(gates),
    )


def source(**overrides):
    kwargs = dict(
        identity=IDENTITY,
        work_item_id="TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001",
        as_of=NOW,
        subject=m.Subject(base_sha="base", head_sha="head"),
        packet_ref="TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001",
    )
    kwargs.update(overrides)
    return s.SnapshotInput(**kwargs)


class TestSixQuestions:
    def test_snapshot_answers_all_six_questions(self):
        answers = s.build_snapshot(source())["answers"]
        assert set(answers) == {
            "WHERE_IS_THIS_WORK",
            "WHAT_GATES_ARE_SATISFIED",
            "WHAT_BLOCKS_IT",
            "WHAT_EVIDENCE_IS_CURRENT",
            "WHO_ACTS_NEXT",
            "WHAT_ACTION_IS_LEGAL",
        }

    def test_satisfied_gates_are_listed(self):
        answers = s.build_snapshot(
            source(gate_ledger=ledger(gate("IDENTITY"), gate("AUDIT")))
        )["answers"]
        assert set(answers["WHAT_GATES_ARE_SATISFIED"]) == {"identity", "audit"}

    def test_who_acts_next_is_an_actor_class(self):
        answers = s.build_snapshot(source())["answers"]
        assert isinstance(answers["WHO_ACTS_NEXT"], str)

    def test_legal_action_is_never_dispatchable(self):
        answers = s.build_snapshot(source())["answers"]
        assert answers["WHAT_ACTION_IS_LEGAL"]["dispatch_eligible"] is False


class TestBlockerPreservation:
    def test_root_blockers_preserved_individually(self):
        snap = s.build_snapshot(
            source(
                gate_ledger=ledger(
                    gate("AUDIT", m.GateState.UNSATISFIED, "audit"),
                    gate("CI", m.GateState.BLOCKED, "ci"),
                )
            )
        )
        ids = {b["blocker_id"] for b in snap["answers"]["WHAT_BLOCKS_IT"]}
        assert ids == {"gate:audit", "gate:ci"}

    def test_unknown_gate_is_preserved_as_a_blocker(self):
        snap = s.build_snapshot(
            source(gate_ledger=ledger(gate("AUDIT", m.GateState.UNKNOWN, "audit")))
        )
        assert snap["answers"]["WHAT_BLOCKS_IT"]

    def test_conflicting_gate_is_preserved_as_a_blocker(self):
        snap = s.build_snapshot(
            source(gate_ledger=ledger(gate("AUDIT", m.GateState.CONFLICTING, "audit")))
        )
        assert snap["answers"]["WHAT_BLOCKS_IT"]

    def test_stale_evidence_becomes_a_blocker(self):
        snap = s.build_snapshot(
            source(evidence_refs=[reference(freshness_state=m.FreshnessState.STALE)])
        )
        classes = {b["normalized_class"] for b in snap["answers"]["WHAT_BLOCKS_IT"]}
        assert "STALE_OR_MISMATCHED_EVIDENCE" in classes

    def test_expired_evidence_becomes_a_blocker(self):
        snap = s.build_snapshot(source(evidence_refs=[reference(valid_until=EARLIER)]))
        assert snap["answers"]["WHAT_BLOCKS_IT"]

    def test_failed_audit_becomes_a_blocking_finding(self):
        snap = s.build_snapshot(source(audit_acceptable=False))
        classes = {b["normalized_class"] for b in snap["answers"]["WHAT_BLOCKS_IT"]}
        assert "BLOCKING_FINDING" in classes


class TestPosture:
    def test_stale_evidence_prevents_ready(self):
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                evidence_refs=[reference(freshness_state=m.FreshnessState.STALE)],
            )
        )
        assert projection.posture is not m.Posture.READY

    def test_unknown_gate_prevents_ready(self):
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                gate_ledger=ledger(gate("AUDIT", m.GateState.UNKNOWN, "audit")),
            )
        )
        assert projection.posture is not m.Posture.READY

    def test_unknown_audit_outcome_prevents_ready(self):
        projection = s.build_projection(source(audit_acceptable=None))
        assert projection.posture is not m.Posture.READY

    def test_ready_requires_clean_evidence_and_accepted_audit(self):
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                gate_ledger=ledger(gate("AUDIT"), gate("VALIDATION")),
                evidence_refs=[reference()],
            )
        )
        assert projection.posture is m.Posture.READY

    def test_blocked_outranks_decision_required(self):
        """Architecture section 02 orders blocking gate/blocker above human decision."""
        projection = s.build_projection(
            source(
                audit_acceptable=False,  # BLOCKING_FINDING
                gate_ledger=ledger(gate("AUTHORITY", m.GateState.UNSATISFIED, "authority")),
            )
        )
        assert projection.posture is m.Posture.BLOCKED

    def test_decision_required_when_only_a_judgment_blocker_exists(self):
        blockers = [
            m.Blocker("b", m.NormalizedFailureClass.AUTHORITY_OR_JUDGMENT_REQUIRED, "operator")
        ]
        assert s.derive_posture(source(), blockers) is m.Posture.DECISION_REQUIRED

    def test_terminal_is_terminal(self):
        assert s.build_projection(source(terminal=True)).posture is m.Posture.TERMINAL

    def test_ready_still_does_not_authorize_dispatch(self):
        projection = s.build_projection(
            source(audit_acceptable=True, gate_ledger=ledger(gate("AUDIT")))
        )
        assert projection.next_legal_action.dispatch_eligible is False


class TestPhase:
    def test_phase_advances_with_satisfied_gates(self):
        early = s.build_projection(source(gate_ledger=ledger(gate("IDENTITY"))))
        late = s.build_projection(
            source(gate_ledger=ledger(gate("IDENTITY"), gate("VALIDATION"), gate("AUDIT")))
        )
        assert early.phase is m.Phase.REQUEST
        assert late.phase is m.Phase.REVIEW

    def test_terminal_overrides(self):
        assert s.build_projection(source(terminal=True)).phase is m.Phase.TERMINAL

    def test_no_ledger_is_request_phase(self):
        assert s.build_projection(source()).phase is m.Phase.REQUEST


class TestNativeStatePreservation:
    def test_native_states_are_preserved_verbatim(self):
        projection = s.build_projection(
            source(
                native_state_refs=[
                    m.NativeStateRef("task-orchestrator", "implementation_in_progress"),
                    m.NativeStateRef("github", "OPEN_DRAFT"),
                ]
            )
        )
        states = {r.subsystem: r.native_state for r in projection.native_state_refs}
        assert states == {
            "task-orchestrator": "implementation_in_progress",
            "github": "OPEN_DRAFT",
        }

    def test_derived_phase_does_not_replace_native_state(self):
        projection = s.build_projection(
            source(native_state_refs=[m.NativeStateRef("task-orchestrator", "custom_state")])
        )
        assert projection.native_state_refs[0].native_state == "custom_state"
        assert projection.phase in set(m.Phase)


class TestDeterminism:
    def test_snapshot_is_repeatable(self):
        assert s.build_snapshot(source()) == s.build_snapshot(source())

    def test_projection_digest_is_stable(self):
        first = s.build_projection(source()).as_dict()["projection_digest"]
        second = s.build_projection(source()).as_dict()["projection_digest"]
        assert first == second

    def test_different_as_of_produces_a_different_projection(self):
        a = s.build_projection(source(as_of=NOW)).as_dict()["projection_digest"]
        b = s.build_projection(source(as_of=EARLIER)).as_dict()["projection_digest"]
        assert a != b


class TestReadOnlyContainment:
    def test_git_read_allowlist_rejects_write_verbs(self):
        from pathlib import Path

        for forbidden in (["commit"], ["push"], ["checkout", "main"], ["reset", "--hard"]):
            with pytest.raises(m.Denial):
                s.read_git_fact(Path("."), forbidden)

    def test_allowlist_contains_only_read_commands(self):
        write_verbs = {
            "commit", "push", "checkout", "reset", "merge", "rebase",
            "clean", "rm", "add", "fetch", "pull", "tag", "branch",
        }
        for command in s._ALLOWED_GIT_READS:
            assert not (set(command) & write_verbs)

    def test_snapshot_module_opens_no_network_client(self):
        text = inspect.getsource(s)
        for forbidden in ("requests", "urllib", "httpx", "socket", "aiohttp"):
            assert forbidden not in text

    def test_snapshot_module_writes_no_files(self):
        text = inspect.getsource(s)
        for forbidden in ("open(", "write_text", "mkdir", "unlink", "rmtree"):
            assert forbidden not in text
