"""Fail-closed lane classification tests for validate_change_contract.py.

Covers three audited defects:
  F1 — L3 secret / CI-action / auth-code paths missed by the path rules.
  F2 — L0 proof rules broader than the proof-only closure allowlist and
       traversal segments accepted by the packet segment.
  F3 — max_lane() ranking unknown tokens / empty input as a low lane.

Pure functions only; no network, no git fixtures.
"""
from __future__ import annotations

import pytest

from scripts.governance.validate_change_contract import (
    _PROOF_ONLY_ALLOWED,
    classify_path,
    evaluate,
    max_lane,
)

# --- F1 -----------------------------------------------------------------------

F1_L3_PATHS = [
    ".env.production",
    ".env.local",
    "config/secrets.yaml",
    "config/credentials.json",
    ".github/actions/setup/action.yml",
    "src/x/authentication.py",
    "src/authz/policy.py",
    "src/x/auth_handler.py",
    "src/authn/__init__.py",
    "src/oauth/client.py",
]


@pytest.mark.parametrize("path", F1_L3_PATHS)
def test_f1_secret_ci_action_and_auth_paths_are_l3(path: str) -> None:
    assert classify_path(path) == "L3"


@pytest.mark.parametrize(
    "path",
    [
        "src/x/author.py",  # 'auth' prefix inside a longer word is not auth code
        "src/x/authors.md",
        "docs/environment.md",
        # token inside a longer directory name is not an auth component
        "audit_inputs/DR-FLEET-PLAN-AUTH-2026-07-13/00-control/RUN-CONTROL.md",
    ],
)
def test_f1_auth_rule_does_not_match_unrelated_words(path: str) -> None:
    assert classify_path(path) != "L3"


# --- F2 -----------------------------------------------------------------------

CRITICAL_PROOF_ONLY_DELTA = [
    "proof/TP-DMX-PR1447-L3-AUDIT-002/PROOF.json",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/AUDITOR_REPORT.md",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/AUDITOR_VERDICT.json",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/AUDIT_INPUT.md",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/AUDIT_INVOCATION.txt",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/AUDIT_OUTPUT_RAW.json",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/CI_EVIDENCE.json",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/DIFF_NAME_STATUS.txt",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/HEAD.txt",
    "proof/TP-DMX-PR1447-L3-AUDIT-002/review_bundle/INSTRUCTION_LIKE.json",
    "proof/pr_merge/embedded-audit/pr-1447/PROOF.json",
    "proof/pr_merge/embedded-audit/pr-1447/PROOF.json.sig",
]


@pytest.mark.parametrize(
    "path",
    [
        "proof/pr_merge/embedded-audit/pr-12/post_checkout.sh",
        "proof/pr_merge/embedded-audit/pr-12/hook.py",
        "proof/pr_merge/embedded-audit/pr-12/review_bundle/evil.bin",
        "proof/../AGENTS.md",
        "proof/./PROOF.json",
        "proof/pkg/../../AGENTS.md",
        "proof//PROOF.json",
        "proof/pkg/generators/gen_proof.py",
        "task-packets/../AGENTS.md",
    ],
)
def test_f2_non_artifact_or_traversal_proof_paths_are_not_l0(path: str) -> None:
    assert classify_path(path) != "L0"


@pytest.mark.parametrize(
    "path",
    [
        "proof/../PROOF.json",
        "proof/./PROOF.json",
        "proof/../pkg/PROOF.json",
        "proof/pr_merge/embedded-audit/pr-12/../PROOF.json",
    ],
)
def test_f2_proof_only_allowlist_rejects_traversal(path: str) -> None:
    assert _PROOF_ONLY_ALLOWED.match(path) is None


@pytest.mark.parametrize("path", CRITICAL_PROOF_ONLY_DELTA)
def test_f2_critical_pr1447_delta_stays_l0(path: str) -> None:
    assert classify_path(path) == "L0"
    assert _PROOF_ONLY_ALLOWED.match(path) is not None


def test_f2_critical_pr1447_delta_max_lane_is_l0() -> None:
    assert max_lane(classify_path(p) for p in CRITICAL_PROOF_ONLY_DELTA) == "L0"


# --- F3 -----------------------------------------------------------------------


def test_f3_unknown_token_fails_closed() -> None:
    with pytest.raises(ValueError):
        max_lane(["RED"])


def test_f3_unknown_token_cannot_rank_below_known_lanes() -> None:
    # Either raises (preferred) or escalates; it must never resolve to L1.
    try:
        lane = max_lane(["bogus", "L1"])
    except ValueError:
        return
    assert lane != "L1"
    assert lane in {"L2", "L3"}


def test_f3_normal_cases_unchanged() -> None:
    assert max_lane(["L0", "L2"]) == "L2"
    assert max_lane(["L1", "L3", "L2"]) == "L3"
    assert max_lane(["L0"]) == "L0"


def test_f3_empty_change_set_does_not_evaluate_to_l0(tmp_path) -> None:
    # `max_lane([]) == "L0"` is pinned by tests/governance/test_validate_change_contract.py
    # (test_max_lane) and is out of this packet's edit scope, so the fail-closed
    # treatment of an empty change set lives in the caller: evaluate().
    result = evaluate(paths=[], cwd=tmp_path, file_text={})
    assert result.max_lane != "L0"
    assert result.model_audit_required is True
