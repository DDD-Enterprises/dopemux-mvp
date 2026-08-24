"""Read-only snapshot behaviour: the six questions, determinism, containment."""

from __future__ import annotations

import inspect

import pytest

from dopemux.governed_delivery import models as m
from dopemux.governed_delivery import snapshot as s

PACKET = "TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001"
IDENTITY = m.Identity(
    project_id="dopemux-mvp",
    repository_id="DDD-Enterprises/dopemux-mvp",
    packet_id=PACKET,
)
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


def ledger(*gates, required=None):
    """A ledger holding exactly the supplied gates.

    ``required`` defaults to the classes actually supplied, which makes this
    helper useful for testing one gate's behaviour in isolation. Completeness is
    exercised separately by :func:`complete_ledger` and by TestRequiredGates.
    """
    supplied = list(gates)
    return m.GateLedger(
        ledger_id="ledger-1",
        identity=IDENTITY,
        subject_digest_or_head="abc",
        gates=supplied,
        required_gate_classes=(
            tuple(dict.fromkeys(g.gate_class for g in supplied))
            if required is None
            else tuple(required)
        ),
    )


def complete_ledger(*overrides):
    """Every required gate class present and SATISFIED, save the overrides.

    GOV-AUD-003: READY and phase advancement now require a complete ledger, so a
    test that means "everything is fine except X" has to say so explicitly.
    """
    replaced = {g.gate_class: g for g in overrides}
    gates = [replaced.get(name, gate(name)) for name in m.GATE_CLASSES]
    return m.GateLedger(
        ledger_id="ledger-complete",
        identity=IDENTITY,
        subject_digest_or_head="abc",
        gates=gates,
    )


def source(**overrides):
    kwargs = dict(
        identity=IDENTITY,
        work_item_id=PACKET,
        as_of=NOW,
        subject=m.Subject(base_sha="base", head_sha="head"),
        packet_ref=PACKET,
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
                gate_ledger=complete_ledger(
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
            source(
                gate_ledger=complete_ledger(),
                evidence_refs=[reference(freshness_state=m.FreshnessState.STALE)],
            )
        )
        blockers = {b["blocker_id"]: b for b in snap["answers"]["WHAT_BLOCKS_IT"]}
        assert blockers["evidence:ev-1"]["normalized_class"] == "STALE_OR_MISMATCHED_EVIDENCE"

    def test_expired_evidence_becomes_a_blocker(self):
        snap = s.build_snapshot(
            source(gate_ledger=complete_ledger(), evidence_refs=[reference(valid_until=EARLIER)])
        )
        assert "evidence:ev-1" in {b["blocker_id"] for b in snap["answers"]["WHAT_BLOCKS_IT"]}

    def test_failed_audit_becomes_a_blocking_finding(self):
        snap = s.build_snapshot(source(audit_acceptable=False))
        classes = {b["normalized_class"] for b in snap["answers"]["WHAT_BLOCKS_IT"]}
        assert "BLOCKING_FINDING" in classes


class TestPosture:
    def test_stale_evidence_prevents_ready(self):
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                gate_ledger=complete_ledger(),
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

    def test_ready_requires_a_complete_ledger_clean_evidence_and_accepted_audit(self):
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                gate_ledger=complete_ledger(),
                evidence_refs=[reference()],
            )
        )
        assert projection.posture is m.Posture.READY

    def test_partial_ledger_cannot_reach_ready(self):
        """GOV-AUD-003: AUDIT + VALIDATION alone used to be enough for READY.

        Every other required gate is simply absent, which the previous reducer
        read as "no problem" rather than "no evidence".
        """
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                gate_ledger=m.GateLedger(
                    ledger_id="partial",
                    identity=IDENTITY,
                    subject_digest_or_head="abc",
                    gates=[gate("AUDIT"), gate("VALIDATION")],
                ),
                evidence_refs=[reference()],
            )
        )
        assert projection.posture is m.Posture.BLOCKED

    def test_no_ledger_at_all_cannot_reach_ready(self):
        projection = s.build_projection(source(audit_acceptable=True))
        assert projection.posture is m.Posture.BLOCKED

    def test_a_gate_marked_not_applicable_satisfies_the_requirement(self):
        """Policy opts out explicitly with NOT_APPLICABLE, never by omission."""
        projection = s.build_projection(
            source(
                audit_acceptable=True,
                gate_ledger=complete_ledger(
                    gate("ACTIVATION", m.GateState.NOT_APPLICABLE, "activation")
                ),
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
    def _phase(self, *gates, required=None):
        return s.build_projection(
            source(gate_ledger=ledger(*gates, required=required))
        ).phase

    def test_phase_advances_through_a_satisfied_prefix(self):
        assert self._phase(gate("IDENTITY")) is m.Phase.REQUEST
        assert self._phase(gate("IDENTITY"), gate("AUTHORITY")) is m.Phase.AUTHORITY
        assert (
            self._phase(
                gate("IDENTITY"),
                gate("AUTHORITY"),
                gate("PACKET"),
                gate("SCOPE"),
                gate("VALIDATION"),
            )
            is m.Phase.VERIFY
        )

    def test_phase_stops_at_the_first_unsatisfied_required_gate(self):
        """GOV-AUD-003: a late gate must not claim a phase whose prerequisites are unproven."""
        phase = self._phase(
            gate("IDENTITY"),
            gate("SCOPE", m.GateState.UNSATISFIED, "scope"),
            gate("AUDIT"),
            required=("IDENTITY", "SCOPE", "AUDIT"),
        )
        assert phase is m.Phase.REQUEST

    def test_a_missing_required_gate_halts_advancement(self):
        phase = s.build_projection(
            source(
                gate_ledger=m.GateLedger(
                    ledger_id="partial",
                    identity=IDENTITY,
                    subject_digest_or_head="abc",
                    gates=[gate("VALIDATION"), gate("AUDIT")],
                )
            )
        ).phase
        assert phase is m.Phase.REQUEST

    def test_a_complete_satisfied_ledger_reaches_the_last_phase(self):
        assert s.build_projection(source(gate_ledger=complete_ledger())).phase is m.Phase.ACTIVATE

    def test_not_required_class_is_skipped_without_advancing(self):
        phase = self._phase(
            gate("IDENTITY"), gate("AUTHORITY"), required=("IDENTITY", "AUTHORITY")
        )
        assert phase is m.Phase.AUTHORITY

    def test_a_present_but_failed_gate_halts_even_when_policy_does_not_require_it(self):
        """"Not required" excuses an absence, never a visible failure.

        Found by adversarial probing during repair cycle 1: a gate present with
        UNSATISFIED state but outside the required set was being stepped over,
        letting a later gate claim a phase whose prerequisite demonstrably did
        not hold — the same defect class as GOV-AUD-003 one level down.
        """
        phase = self._phase(
            gate("IDENTITY"),
            gate("SCOPE", m.GateState.UNSATISFIED, "scope"),
            gate("AUDIT"),
            required=("IDENTITY", "AUDIT"),
        )
        assert phase is m.Phase.REQUEST

    @pytest.mark.parametrize(
        "state",
        [
            m.GateState.UNSATISFIED,
            m.GateState.BLOCKED,
            m.GateState.STALE,
            m.GateState.UNKNOWN,
            m.GateState.CONFLICTING,
            m.GateState.PENDING,
        ],
    )
    def test_every_non_satisfied_present_state_halts_advancement(self, state):
        phase = self._phase(
            gate("IDENTITY"),
            gate("SCOPE", state, "scope"),
            gate("AUDIT"),
            required=("IDENTITY", "AUDIT"),
        )
        assert phase is m.Phase.REQUEST

    def test_not_applicable_is_the_only_state_that_may_be_stepped_over(self):
        phase = self._phase(
            gate("IDENTITY"),
            gate("AUTHORITY"),
            gate("PACKET"),
            gate("SCOPE", m.GateState.NOT_APPLICABLE, "scope"),
            gate("VALIDATION"),
            required=("IDENTITY", "AUTHORITY", "PACKET", "SCOPE", "VALIDATION"),
        )
        assert phase is m.Phase.VERIFY

    def test_terminal_overrides(self):
        assert s.build_projection(source(terminal=True)).phase is m.Phase.TERMINAL

    def test_no_ledger_is_request_phase(self):
        assert s.build_projection(source()).phase is m.Phase.REQUEST


class TestRequiredGates:
    def test_missing_required_classes_are_reported(self):
        snap = s.build_snapshot(
            source(
                gate_ledger=m.GateLedger(
                    ledger_id="partial",
                    identity=IDENTITY,
                    subject_digest_or_head="abc",
                    gates=[gate("AUDIT")],
                )
            )
        )
        missing = set(snap["missing_required_gate_classes"])
        assert "AUDIT" not in missing
        assert {"IDENTITY", "SCOPE", "CI", "MERGE_AUTHORITY"} <= missing

    def test_missing_gate_materializes_as_unknown_not_as_silence(self):
        blockers = s.collect_blockers(
            source(
                gate_ledger=m.GateLedger(
                    ledger_id="partial",
                    identity=IDENTITY,
                    subject_digest_or_head="abc",
                    gates=[gate("AUDIT")],
                )
            )
        )
        synthesized = [b for b in blockers if b.blocker_id.startswith("gate:missing:")]
        assert synthesized
        assert all(
            b.normalized_class is m.NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE
            for b in synthesized
        )
        assert all("required evidence is missing" in b.statement for b in synthesized)

    def test_policy_may_narrow_the_required_set(self):
        narrowed = m.GateLedger(
            ledger_id="narrow",
            identity=IDENTITY,
            subject_digest_or_head="abc",
            gates=[gate("AUDIT"), gate("VALIDATION")],
            required_gate_classes=("AUDIT", "VALIDATION"),
        )
        assert narrowed.missing_required_classes() == []
        projection = s.build_projection(source(audit_acceptable=True, gate_ledger=narrowed))
        assert projection.posture is m.Posture.READY

    def test_unknown_required_gate_class_is_denied(self):
        with pytest.raises(m.Denial):
            m.GateLedger(
                ledger_id="bad",
                identity=IDENTITY,
                subject_digest_or_head="abc",
                required_gate_classes=("NOT_A_GATE",),
            )

    def test_a_blocking_duplicate_is_not_masked_by_a_satisfied_one(self):
        led = ledger(
            gate("AUDIT", m.GateState.SATISFIED, "audit-ok"),
            gate("AUDIT", m.GateState.UNSATISFIED, "audit-bad"),
        )
        assert led.states_by_class()["AUDIT"] is m.GateState.UNSATISFIED


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
        for shape in s._GIT_READ_SHAPES:
            assert not (set(shape) & write_verbs)

    def test_parameterized_positions_reject_non_sha_arguments(self):
        from pathlib import Path

        for injected in ("--upload-pack=touch /tmp/x", "HEAD", "main", "../etc", ""):
            with pytest.raises(m.Denial):
                s.run_git_read(Path("."), ["diff", "--name-only", injected, "a" * 40])

    def test_snapshot_module_opens_no_network_client(self):
        text = inspect.getsource(s)
        for forbidden in ("requests", "urllib", "httpx", "socket", "aiohttp"):
            assert forbidden not in text

    def test_snapshot_module_writes_no_files(self):
        text = inspect.getsource(s)
        for forbidden in ("open(", "write_text", "mkdir", "unlink", "rmtree"):
            assert forbidden not in text
