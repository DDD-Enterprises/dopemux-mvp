# PR Steward Security/Release Approval Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed, exact-head-bound security/release approval gate to the live CI-wired PR Steward path (`tools/pr_steward/` → `.github/workflows/pr-steward.yml`) without weakening any existing rule.

**Architecture:** A new pure module (`tools/pr_steward/security_release_gate.py`) computes whether a PR touches security/release-sensitive paths (reusing `dopemux.dcp.red_lane_rules.FORBIDDEN_PATHS` plus a small PR-Steward-local supplement, each finding tagged with a category), and validates an approval contract (GitHub PR review from a config-listed trusted approver, exact-head-bound) mirroring the existing `independent_audit_errors` binding pattern in `scripts/audit/run_embedded_audit.py`. The collector is extended to harvest reviews with their bound commit SHA via GraphQL (same pattern as the existing `reviewThreads` query). The classifier consumes both signals and adds `SECURITY_RELEASE_APPROVAL_*` blockers that map to `NEEDS_SUPERVISOR`, never overriding other blockers. The schema gains new required fields. `known_reviewers.json` gains a new, initially-empty `trusted_security_release_approvers` list — the identity roster is an **operator decision**, not authored by this plan.

**Tech Stack:** Python 3.12, `gh` CLI (GraphQL + REST), pytest, JSON Schema draft-07 (`schemas/pr_steward/`).

## Global Constraints

- Do not modify `src/dopemux/pcp/pr_steward.py` or `schemas/project_control_plane/merge_readiness.schema.json` (generic PCP-Core — reuse semantics only, per packet Scope OUT).
- Do not modify `src/dopemux/dcp/red_lane_rules.py` or `red_lane_scanner.py` — import `FORBIDDEN_PATHS` read-only.
- Do not expand `.github/workflows/pr-steward.yml` permissions beyond the current `contents: read, pull-requests: read, checks: read, statuses: write, actions: read, issues: read`.
- Do not seed `trusted_security_release_approvers` with any names — ship it empty; fail closed (`NEEDS_SUPERVISOR`) whenever `security_release_required=True` and the list is empty.
- Every new blocker is additive: a PR that doesn't touch a security-sensitive path must see byte-identical readiness/blocker behavior to today.
- `bool()` coercion, not `is True` identity, for every truthy check (locks the fail-open-fix pattern already established in `tools/pr_steward/classifier.py:251` and `src/dopemux/pcp/pr_steward.py:251`).

## Required pre-implementation trace (already performed — recorded here for the proof bundle)

| Question | Canonical source found | Notes |
|---|---|---|
| red-lane classification | `src/dopemux/dcp/routing_classifier.py::_derive_red_lane_state` (touches_security/touches_auth/touches_secrets/touches_destructive_path vocabulary); `src/dopemux/dcp/red_lane_rules.py::FORBIDDEN_PATHS` (concrete path globs) | Reused: import `FORBIDDEN_PATHS` directly; reuse the `touches_*` vocabulary as category names. |
| security-sensitive file classification (general, path→category) | **Not found** as an automated classifier. `red_lane_rules.FORBIDDEN_PATHS` is DCP-Core self-protection ("DCP Core must never touch"), not a general "PR needs security approval" signal — confirmed via `advisor()` review; its own list includes `.github/workflows/.*` which this very packet edits. | New, minimal, path-glob module built in this plan (Task 2), documented as PR-Steward-local, reusing `FORBIDDEN_PATHS` as its base set rather than duplicating it. |
| release-sensitive file classification | Not found. `schemas/dcp/dcp_red_lane_taxonomy.instance.json` lane `DCP-RED-PROOF-CONTRACT-SCHEMA-MUTATION` names the category but has no path list. | New glob added for `schemas/**/*.schema.json` and `contracts/**`, citing that lane ID in a comment. |
| trusted security/release approvers | **Not found** — `tools/pr_steward/known_reviewers.json` has general reviewer trust, not a security-approver class. | New empty config field, mechanism-only per Scope OUT — operator populates identities. |
| approval identity / head binding | `scripts/audit/run_embedded_audit.py::independent_audit_errors` (expected_pr/expected_head_sha/expected_repo binding pattern already shared by the embedded-audit workflow gate and the PR Steward collector). | Mirrored, not reinvented, in Task 3's `evaluate_security_release_approval`. |

`BLOCKED_CANONICAL_RED_LANE_SOURCE_UNKNOWN` is **not** triggered — red-lane classification exists. The two genuinely-missing pieces (file-sensitivity glob, approver roster) are explicitly in Scope IN (packet items 1–2, 4) and are built fresh, grounded in existing vocabulary/patterns rather than invented from nothing.

---

## Task 1: Worktree setup

**Files:** none (environment only)

- [ ] **Step 1: Create the worktree**

```bash
cd /Users/hue/code/dopemux-mvp
git fetch origin main
export PACKET_ID="TP-DMX-PR-STEWARD-SECURITY-APPROVAL-PARITY-001"
export BASE_SHA="$(git rev-parse origin/main)"
export WORKTREE="/Users/hue/code/.worktrees/${PACKET_ID}"
export BRANCH="feat/pr-steward-security-approval-parity"
git worktree add -b "${BRANCH}" "${WORKTREE}" "${BASE_SHA}"
cd "${WORKTREE}"
```

- [ ] **Step 2: Record starting state**

```bash
git status --porcelain=v1 --branch
git rev-parse HEAD
git config --get remote.origin.url
```

Expected: clean tree, HEAD == `$BASE_SHA`.

---

## Task 2: Security/release-sensitive path classifier

**Files:**
- Create: `tools/pr_steward/security_release_gate.py`
- Test: `tests/pr_steward/test_security_release_gate.py`

**Interfaces:**
- Produces: `classify_security_release_paths(changed_files: list[str]) -> SecurityReleaseClassification` where `SecurityReleaseClassification` is a `dataclass(frozen=True)` with fields `required: bool`, `categories: tuple[str, ...]`, `matched_paths: tuple[tuple[str, str], ...]` (path, category pairs).

- [ ] **Step 1: Write the failing test**

```python
# tests/pr_steward/test_security_release_gate.py
from __future__ import annotations

from tools.pr_steward.security_release_gate import classify_security_release_paths


def test_ordinary_files_are_not_required():
    result = classify_security_release_paths(["src/foo.py", "docs/readme.md"])
    assert result.required is False
    assert result.categories == ()
    assert result.matched_paths == ()


def test_workflow_file_is_required_ci_workflow():
    result = classify_security_release_paths([".github/workflows/pr-steward.yml"])
    assert result.required is True
    assert "ci_workflow" in result.categories
    assert (".github/workflows/pr-steward.yml", "ci_workflow") in result.matched_paths


def test_codeowners_is_required():
    result = classify_security_release_paths(["CODEOWNERS"])
    assert result.required is True
    assert "codeowners" in result.categories


def test_nested_codeowners_is_required():
    result = classify_security_release_paths([".github/CODEOWNERS"])
    assert result.required is True
    assert "codeowners" in result.categories


def test_schema_file_is_required_schema_contract():
    result = classify_security_release_paths(["schemas/pr_steward/merge_readiness.schema.json"])
    assert result.required is True
    assert "schema_contract" in result.categories


def test_secrets_like_path_is_required():
    result = classify_security_release_paths(["config/secrets/prod.env"])
    assert result.required is True
    assert "secrets" in result.categories


def test_dcp_forbidden_path_is_required_dcp_boundary():
    result = classify_security_release_paths(
        ["services/task-orchestrator/src/index.ts"]
    )
    assert result.required is True
    assert "dcp_boundary" in result.categories


def test_multiple_categories_all_recorded():
    result = classify_security_release_paths(
        [".github/workflows/pr-steward.yml", "CODEOWNERS", "src/foo.py"]
    )
    assert result.required is True
    assert set(result.categories) == {"ci_workflow", "codeowners"}
    assert len(result.matched_paths) == 2


def test_empty_changed_files_not_required():
    result = classify_security_release_paths([])
    assert result.required is False


def test_result_is_frozen():
    result = classify_security_release_paths([])
    import dataclasses

    with_replace = dataclasses.replace(result, required=True)
    assert with_replace.required is True
    assert result.required is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pr_steward/test_security_release_gate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.pr_steward.security_release_gate'`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/pr_steward/security_release_gate.py
"""Security/release-sensitive path classifier for the live PR Steward path.

This module answers one question: does a PR's changed-file set touch a path
category that requires an explicit security/release approval before READY?

It is deliberately distinct from ``dopemux.dcp.red_lane_scanner`` /
``red_lane_rules.FORBIDDEN_PATHS``, which encode "DCP Core must never touch
this" (a hard block for DCP Core specifically, not a general PR-approval
signal — see docs/superpowers/plans/2026-07-20-pr-steward-security-approval-parity.md
trace table). ``FORBIDDEN_PATHS`` is reused here, read-only, as one input
category (``dcp_boundary``) alongside PR-Steward-local categories for
surfaces DCP Core's list doesn't cover (CODEOWNERS, schema/contract files,
secrets-like paths). Matching a category here means "needs approval", not
"forbidden outright" — editing ``.github/workflows/pr-steward.yml`` (this
packet's own scope) correctly triggers ``ci_workflow``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS

_CI_WORKFLOW = re.compile(r"^\.github/workflows/.*$")
_CODEOWNERS = re.compile(r"^(\.github/)?CODEOWNERS$")
# DCP-RED-PROOF-CONTRACT-SCHEMA-MUTATION (schemas/dcp/dcp_red_lane_taxonomy.instance.json)
_SCHEMA_CONTRACT = re.compile(r"^(schemas|contracts)/.*\.(schema\.json|json|proto|graphql)$")
_SECRETS_LIKE = re.compile(
    r"(^|/)secrets?(/|$)|\.env(\.|$)", re.IGNORECASE
)

_LOCAL_CATEGORY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ci_workflow", _CI_WORKFLOW),
    ("codeowners", _CODEOWNERS),
    ("schema_contract", _SCHEMA_CONTRACT),
    ("secrets", _SECRETS_LIKE),
)


@dataclass(frozen=True)
class SecurityReleaseClassification:
    """Result of classifying a PR's changed files for security/release sensitivity."""

    required: bool
    categories: tuple[str, ...] = field(default_factory=tuple)
    matched_paths: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def classify_security_release_paths(
    changed_files: list[str],
) -> SecurityReleaseClassification:
    """Classify *changed_files* into security/release-sensitive categories.

    Pure function: no I/O, no filesystem access, no mutation of input.
    """
    matches: list[tuple[str, str]] = []
    for path in changed_files:
        for category, pattern in _LOCAL_CATEGORY_PATTERNS:
            if pattern.search(path):
                matches.append((path, category))
        for forbidden in FORBIDDEN_PATHS:
            if forbidden.match(path):
                matches.append((path, "dcp_boundary"))
                break

    categories = tuple(sorted({category for _, category in matches}))
    return SecurityReleaseClassification(
        required=bool(matches),
        categories=categories,
        matched_paths=tuple(matches),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_security_release_gate.py -v`
Expected: PASS (10 passed)

- [ ] **Step 5: Commit**

```bash
git add tools/pr_steward/security_release_gate.py tests/pr_steward/test_security_release_gate.py
git commit -m "feat(pr-steward): add security/release-sensitive path classifier"
```

---

## Task 3: Approval contract validator

**Files:**
- Create: `tools/pr_steward/security_release_approval.py`
- Test: `tests/pr_steward/test_security_release_approval.py`

**Interfaces:**
- Consumes: nothing from Task 2 (independent).
- Produces: `evaluate_security_release_approval(approval: dict | None, *, required: bool, expected_repo: str, expected_pr: int, expected_head_sha: str, trusted_approvers: list[str]) -> list[str]` — a list of blocker strings (empty means satisfied), used identically to `independent_audit_errors`.

- [ ] **Step 1: Write the failing test**

```python
# tests/pr_steward/test_security_release_approval.py
from __future__ import annotations

from tools.pr_steward.security_release_approval import evaluate_security_release_approval


HEAD = "a" * 40
REPO = "DDD-Enterprises/dopemux-mvp"
PR = 1234


def _approval(**overrides):
    base = {
        "state": "APPROVED",
        "repository": REPO,
        "pr_number": PR,
        "head_sha": HEAD,
        "approver": "trusted-approver",
        "approval_ref": "review-node-id-123",
        "approved_at": "2026-07-20T10:00:00Z",
    }
    base.update(overrides)
    return base


def test_not_required_returns_no_errors_even_without_approval():
    errors = evaluate_security_release_approval(
        None,
        required=False,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
    )
    assert errors == []


def test_required_with_no_approval_is_required_error():
    errors = evaluate_security_release_approval(
        None,
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert errors == ["SECURITY_RELEASE_APPROVAL_REQUIRED"]


def test_required_with_empty_trusted_approvers_is_approver_unknown():
    errors = evaluate_security_release_approval(
        _approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=[],
    )
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in errors


def test_valid_approval_at_exact_head_has_no_errors():
    errors = evaluate_security_release_approval(
        _approval(),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert errors == []


def test_wrong_repo_is_rejected():
    errors = evaluate_security_release_approval(
        _approval(repository="someone-else/other-repo"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_wrong_pr_is_rejected():
    errors = evaluate_security_release_approval(
        _approval(pr_number=9999),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_wrong_head_is_head_mismatch():
    errors = evaluate_security_release_approval(
        _approval(head_sha="b" * 40),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH" in errors


def test_future_dated_approval_is_stale():
    errors = evaluate_security_release_approval(
        _approval(approved_at="2099-01-01T00:00:00Z"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_STALE" in errors


def test_unparseable_timestamp_is_invalid():
    errors = evaluate_security_release_approval(
        _approval(approved_at="not-a-timestamp"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_non_approved_state_is_invalid():
    errors = evaluate_security_release_approval(
        _approval(state="CHANGES_REQUESTED"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_unknown_approver_is_approver_unknown():
    errors = evaluate_security_release_approval(
        _approval(approver="random-user"),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in errors


def test_empty_approval_ref_is_invalid():
    errors = evaluate_security_release_approval(
        _approval(approval_ref=""),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_non_boolean_truthy_state_does_not_bypass():
    # integer 1 / string "true" must not be treated as APPROVED via loose equality
    errors = evaluate_security_release_approval(
        _approval(state=1),
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert "SECURITY_RELEASE_APPROVAL_INVALID" in errors


def test_malformed_payload_is_invalid():
    errors = evaluate_security_release_approval(
        "not-a-dict",  # type: ignore[arg-type]
        required=True,
        expected_repo=REPO,
        expected_pr=PR,
        expected_head_sha=HEAD,
        trusted_approvers=["trusted-approver"],
    )
    assert errors == ["SECURITY_RELEASE_APPROVAL_INVALID"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pr_steward/test_security_release_approval.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# tools/pr_steward/security_release_approval.py
"""Exact-head-bound security/release approval contract validator.

Mirrors the (repo, PR, head_sha) binding pattern already established by
``scripts.audit.run_embedded_audit.independent_audit_errors`` — the shared
validator used by both the embedded-audit workflow hard gate and the PR
Steward collector's proof check. This module applies the same binding
discipline to a *reviewer approval* rather than an audit proof.

Approval never overrides another blocker; callers add these errors as
additional ``SECURITY_RELEASE_APPROVAL_*`` blockers alongside all existing
ones.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def evaluate_security_release_approval(
    approval: Mapping[str, Any] | None,
    *,
    required: bool,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    trusted_approvers: list[str],
) -> list[str]:
    """Return fail-closed blocker codes for a security/release approval claim.

    Returns an empty list only when *required* is falsy, or *approval* is a
    well-formed, current, exact-head-bound APPROVED review from a login in
    *trusted_approvers*.
    """
    if not bool(required):
        return []

    if approval is None:
        return ["SECURITY_RELEASE_APPROVAL_REQUIRED"]

    if not isinstance(approval, Mapping):
        return ["SECURITY_RELEASE_APPROVAL_INVALID"]

    errors: list[str] = []

    state = approval.get("state")
    if state != "APPROVED":
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    approval_ref = approval.get("approval_ref")
    if not isinstance(approval_ref, str) or not approval_ref:
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    repository = approval.get("repository")
    pr_number = approval.get("pr_number")
    if repository != expected_repo or pr_number != expected_pr:
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    head_sha = approval.get("head_sha")
    if isinstance(head_sha, str) and repository == expected_repo and pr_number == expected_pr:
        if head_sha != expected_head_sha:
            errors.append("SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH")
    elif not isinstance(head_sha, str):
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    approved_at = approval.get("approved_at")
    parsed_at = _parse_rfc3339(approved_at)
    if parsed_at is None:
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")
    elif parsed_at > datetime.now(timezone.utc):
        errors.append("SECURITY_RELEASE_APPROVAL_STALE")

    approver = approval.get("approver")
    if not trusted_approvers or approver not in trusted_approvers:
        errors.append("SECURITY_RELEASE_APPROVER_UNKNOWN")

    # De-duplicate while preserving first-seen order.
    seen: set[str] = set()
    ordered: list[str] = []
    for err in errors:
        if err not in seen:
            seen.add(err)
            ordered.append(err)
    return ordered


def _parse_rfc3339(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_security_release_approval.py -v`
Expected: PASS (14 passed)

- [ ] **Step 5: Commit**

```bash
git add tools/pr_steward/security_release_approval.py tests/pr_steward/test_security_release_approval.py
git commit -m "feat(pr-steward): add exact-head-bound security/release approval validator"
```

---

## Task 4: `known_reviewers.json` — trusted security/release approver roster

**Files:**
- Modify: `tools/pr_steward/known_reviewers.json`
- Modify: `tools/pr_steward/classifier.py` (add `load_trusted_security_approvers`)
- Test: `tests/pr_steward/test_trusted_security_approvers.py`

**Interfaces:**
- Produces: `load_trusted_security_approvers(path: Path) -> list[str]`

- [ ] **Step 1: Write the failing test**

```python
# tests/pr_steward/test_trusted_security_approvers.py
from __future__ import annotations

import json
from pathlib import Path

from tools.pr_steward.classifier import load_trusted_security_approvers


def test_missing_key_returns_empty_list(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(json.dumps({"known_reviewers": [], "trusted_author_associations": []}))
    assert load_trusted_security_approvers(path) == []


def test_populated_key_returns_list(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(
        json.dumps(
            {
                "known_reviewers": [],
                "trusted_author_associations": [],
                "trusted_security_release_approvers": ["alice", "bob"],
            }
        )
    )
    assert load_trusted_security_approvers(path) == ["alice", "bob"]


def test_repo_known_reviewers_file_has_empty_roster():
    """The shipped roster starts empty — approver identity is an operator decision."""
    from pathlib import Path as _P

    repo_path = _P(__file__).resolve().parents[2] / "tools" / "pr_steward" / "known_reviewers.json"
    assert load_trusted_security_approvers(repo_path) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pr_steward/test_trusted_security_approvers.py -v`
Expected: FAIL with `ImportError: cannot import name 'load_trusted_security_approvers'`

- [ ] **Step 3: Write minimal implementation**

In `tools/pr_steward/known_reviewers.json`, add the new key (empty — no identities seeded):

```json
{
  "known_reviewers": [
    "chatgpt-codex-connector",
    "copilot-pull-request-reviewer",
    "github-actions[bot]",
    "github-actions",
    "dependabot[bot]",
    "hu3mann"
  ],
  "trusted_author_associations": [
    "OWNER",
    "MEMBER",
    "COLLABORATOR"
  ],
  "trusted_security_release_approvers": []
}
```

In `tools/pr_steward/classifier.py`, add (near `load_known_reviewers`):

```python
def load_trusted_security_approvers(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [str(item) for item in payload.get("trusted_security_release_approvers", [])]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_trusted_security_approvers.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add tools/pr_steward/known_reviewers.json tools/pr_steward/classifier.py tests/pr_steward/test_trusted_security_approvers.py
git commit -m "feat(pr-steward): add empty trusted security/release approver roster"
```

---

## Task 5: Schema — add security/release approval fields and blockers

**Files:**
- Modify: `schemas/pr_steward/merge_readiness.schema.json`
- Test: `tests/pr_steward/test_schema_security_release.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: schema now requires `security_release` object on every `MERGE_READINESS.json`.

- [ ] **Step 1: Write the failing test**

```python
# tests/pr_steward/test_schema_security_release.py
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "pr_steward"
    / "merge_readiness.schema.json"
)


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_is_valid_draft7():
    Draft7Validator.check_schema(_schema())


def test_security_release_is_required_top_level_key():
    schema = _schema()
    assert "security_release" in schema["required"]


def test_security_release_object_shape():
    schema = _schema()
    props = schema["properties"]["security_release"]["properties"]
    for key in ("required", "approved", "categories", "approval"):
        assert key in props


def test_ready_requires_security_release_satisfied():
    """A hand-crafted READY payload with required=True, approved=False must fail schema."""
    schema = _schema()
    base = _minimal_valid_document()
    base["readiness"] = "READY"
    base["security_release"] = {
        "required": True,
        "approved": False,
        "categories": ["ci_workflow"],
        "approval": None,
    }
    base["blockers"] = []
    base["unknowns"] = []
    errors = list(Draft7Validator(schema).iter_errors(base))
    assert errors, "READY with required=True, approved=False must be schema-invalid"


def _minimal_valid_document() -> dict:
    return {
        "schema_version": "1.1.0",
        "generated_at": "2026-07-20T10:00:00Z",
        "pr": {
            "number": 1,
            "url": "https://example.invalid/pr/1",
            "base_ref": "main",
            "head_ref": "feature",
            "head_sha": "a" * 40,
            "changed_files": [],
            "commits": [],
        },
        "readiness": "NOT_READY",
        "risk_tier": "LOW",
        "review_item_ledger_path": "REVIEW_ITEM_LEDGER.json",
        "thread_dispositions_path": "THREAD_DISPOSITIONS.json",
        "ci_triage_path": "CI_TRIAGE.json",
        "embedded_audit": {"status": "SKIPPED", "report_path": ""},
        "proof": {
            "proof_path": "",
            "proof_head_sha": None,
            "matches_pr_head": False,
            "proof_freshness": {
                "status": "MISSING",
                "matches_pr_head": False,
                "reason": "",
                "proof_recorded_sha": None,
                "pr_head_sha": None,
                "self_reference_exception": None,
            },
        },
        "blockers": [],
        "unknowns": [],
        "mutation_performed": False,
        "security_release": {
            "required": False,
            "approved": False,
            "categories": [],
            "approval": None,
        },
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pr_steward/test_schema_security_release.py -v`
Expected: FAIL (`security_release` not in `required`; `KeyError` on `properties["security_release"]`)

- [ ] **Step 3: Write minimal implementation**

Edit `schemas/pr_steward/merge_readiness.schema.json`:

1. Add `"security_release"` to the top-level `"required"` array (after `"mutation_performed"`).
2. Add to `"properties"` (after `"mutation_performed"`):

```json
    "security_release": {
      "type": "object",
      "additionalProperties": false,
      "required": ["required", "approved", "categories", "approval"],
      "properties": {
        "required": { "type": "boolean" },
        "approved": { "type": "boolean" },
        "categories": {
          "type": "array",
          "items": { "type": "string" }
        },
        "approval": {
          "type": ["object", "null"],
          "additionalProperties": true
        }
      }
    },
```

3. Extend the existing `readiness == "READY"` conditional's `then` block (the single entry under `"allOf"`) to also require `security_release` to be satisfied — add this property alongside the existing `risk_tier`/`blockers`/`unknowns` requirements inside the same `"then".properties"` object:

```json
          "security_release": {
            "if": {
              "properties": { "required": { "const": true } },
              "required": ["required"]
            },
            "then": {
              "properties": { "approved": { "const": true } },
              "required": ["approved"]
            }
          }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_schema_security_release.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add schemas/pr_steward/merge_readiness.schema.json tests/pr_steward/test_schema_security_release.py
git commit -m "feat(pr-steward): schema — require security_release gate on every readiness signal"
```

---

## Task 6: Wire the gate into `classifier.build_artifacts`

**Files:**
- Modify: `tools/pr_steward/classifier.py`
- Test: `tests/pr_steward/test_classifier_security_release_gate.py`

**Interfaces:**
- Consumes: `classify_security_release_paths` (Task 2), `evaluate_security_release_approval` (Task 3), `load_trusted_security_approvers` (Task 4).
- Modifies: `build_artifacts(harvest, *, repo, pr_number, strict, allow_closed, generated_at=None, known_reviewers_path=None)` — harvest may now include `harvest["security_release_approval"]` (a dict or `None`, shaped as `{state, repository, pr_number, head_sha, approver, approval_ref, approved_at}`, populated by the collector in Task 7).

- [ ] **Step 1: Write the failing test**

```python
# tests/pr_steward/test_classifier_security_release_gate.py
from __future__ import annotations

from pathlib import Path

import pytest

from tools.pr_steward.classifier import build_artifacts

ROOT = Path(__file__).resolve().parents[2]
KNOWN_REVIEWERS_PATH = ROOT / "tools" / "pr_steward" / "known_reviewers.json"
TRUSTED_FIXTURE = ROOT / "tests" / "pr_steward" / "fixtures" / "known_reviewers_with_approver.json"

HEAD_SHA = "head000000000000000000000000000000000000"


def _base_harvest(changed_files=None, security_release_approval=None) -> dict:
    return {
        "harvest_complete": True,
        "harvest_errors": [],
        "pr": {
            "number": 704,
            "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/704",
            "state": "OPEN",
            "isDraft": False,
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": "APPROVED",
            "baseRefName": "main",
            "baseRefOid": "base000000000000000000000000000000000000",
            "headRefName": "codex/test",
            "headRefOid": HEAD_SHA,
            "author": {"login": "hu3mann"},
            "createdAt": "2026-05-26T01:00:00Z",
            "updatedAt": "2026-05-26T02:00:00Z",
        },
        "changed_files": [{"path": p, "additions": 1} for p in (changed_files or ["foo.py"])],
        "commits": [{"oid": HEAD_SHA, "messageHeadline": "test"}],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [
            {"name": "unit", "status": "COMPLETED", "conclusion": "success", "headSha": HEAD_SHA}
        ],
        "proof": {
            "proof_path": "proof/PROOF.json",
            "proof_head_sha": HEAD_SHA,
            "matches_pr_head": True,
        },
        "embedded_audit": {"status": "PASS", "report_path": "proof/AUDITOR_REPORT.md"},
        "security_release_approval": security_release_approval,
    }


@pytest.fixture(autouse=True, scope="module")
def _fixture_dir():
    TRUSTED_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    TRUSTED_FIXTURE.write_text(
        """{
  "known_reviewers": ["hu3mann"],
  "trusted_author_associations": ["OWNER"],
  "trusted_security_release_approvers": ["trusted-approver"]
}"""
    )
    yield
    TRUSTED_FIXTURE.unlink(missing_ok=True)


def _artifacts(harvest: dict, known_reviewers_path=KNOWN_REVIEWERS_PATH) -> dict:
    return build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=704,
        strict=True,
        allow_closed=False,
        known_reviewers_path=known_reviewers_path,
    )["MERGE_READINESS.json"]


def test_ordinary_pr_does_not_require_security_release():
    readiness = _artifacts(_base_harvest())
    assert readiness["security_release"]["required"] is False
    assert readiness["readiness"] == "READY"


def test_red_lane_pr_without_approval_cannot_be_ready():
    readiness = _artifacts(_base_harvest(changed_files=[".github/workflows/x.yml"]))
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is False
    assert readiness["readiness"] != "READY"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]


def test_red_lane_pr_with_valid_approval_is_ready():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "trusted-approver",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=TRUSTED_FIXTURE,
    )
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is True
    assert readiness["readiness"] == "READY"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" not in readiness["blockers"]


def test_approval_does_not_override_other_blockers():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "trusted-approver",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    harvest = _base_harvest(
        changed_files=[".github/workflows/x.yml"],
        security_release_approval=approval,
    )
    harvest["checks"] = [
        {"name": "unit", "status": "COMPLETED", "conclusion": "failure", "headSha": HEAD_SHA}
    ]
    readiness = _artifacts(harvest, known_reviewers_path=TRUSTED_FIXTURE)
    assert readiness["security_release"]["approved"] is True
    assert readiness["readiness"] != "READY"
    assert "FAILED_CHECK" in readiness["blockers"]


def test_new_commit_invalidates_earlier_approval():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": "stale0000000000000000000000000000000000",
        "approver": "trusted-approver",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=TRUSTED_FIXTURE,
    )
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH" in readiness["blockers"]


def test_unknown_approver_fails_closed():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "random-user",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=TRUSTED_FIXTURE,
    )
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in readiness["blockers"]


def test_empty_approver_roster_fails_closed_even_with_approval():
    approval = {
        "state": "APPROVED",
        "repository": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 704,
        "head_sha": HEAD_SHA,
        "approver": "hu3mann",
        "approval_ref": "review-1",
        "approved_at": "2026-05-26T01:30:00Z",
    }
    readiness = _artifacts(
        _base_harvest(
            changed_files=[".github/workflows/x.yml"],
            security_release_approval=approval,
        ),
        known_reviewers_path=KNOWN_REVIEWERS_PATH,  # shipped roster is empty
    )
    assert readiness["security_release"]["approved"] is False
    assert "SECURITY_RELEASE_APPROVER_UNKNOWN" in readiness["blockers"]


def test_readiness_maps_security_release_blockers_to_needs_supervisor():
    readiness = _artifacts(_base_harvest(changed_files=["CODEOWNERS"]))
    assert readiness["readiness"] == "NEEDS_SUPERVISOR"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pr_steward/test_classifier_security_release_gate.py -v`
Expected: FAIL — `readiness["security_release"]` raises `KeyError` (key doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

In `tools/pr_steward/classifier.py`, add imports near the top (after existing imports):

```python
from tools.pr_steward.security_release_gate import classify_security_release_paths
from tools.pr_steward.security_release_approval import evaluate_security_release_approval
```

Add a helper (near `load_known_reviewers`):

```python
def load_trusted_security_approvers(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [str(item) for item in payload.get("trusted_security_release_approvers", [])]
```

In `build_artifacts`, after `snapshot_changed_files = _changed_files(harvest.get("changed_files") or [])` (existing line), add:

```python
    changed_paths = [item["path"] for item in snapshot_changed_files if item.get("path")]
    security_classification = classify_security_release_paths(changed_paths)
    trusted_security_approvers = load_trusted_security_approvers(known_path)
    security_release_errors = evaluate_security_release_approval(
        harvest.get("security_release_approval"),
        required=security_classification.required,
        expected_repo=repo,
        expected_pr=pr_number,
        expected_head_sha=pr["head_sha"],
        trusted_approvers=trusted_security_approvers,
    )
    for err in security_release_errors:
        _append_once(blockers, err)
    security_release = {
        "required": security_classification.required,
        "approved": security_classification.required and not security_release_errors,
        "categories": list(security_classification.categories),
        "approval": harvest.get("security_release_approval"),
    }
```

(`known_path` is already bound earlier in the function from `known_reviewers_path or Path(__file__).with_name("known_reviewers.json")` — reuse it, do not re-derive.)

Add `"security_release": security_release,` to both the `merge_readiness` dict literal and — for completeness/inspectability — leave `snapshot` untouched (it is not schema-constrained the same way).

Update `_readiness(blockers)` — add the new blocker family to the `NEEDS_SUPERVISOR` branch's set:

```python
    if any(
        item.startswith("EMBEDDED_AUDIT_") or item.startswith("SECURITY_RELEASE_")
        for item in blocker_set
    ) or blocker_set & {
```

(This changes the existing `any(item.startswith("EMBEDDED_AUDIT_") ...)` guard to also match `SECURITY_RELEASE_*` — a one-line generalization, not a new branch.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_classifier_security_release_gate.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Run the full existing pr_steward suite to confirm no regression**

Run: `pytest tests/pr_steward -v`
Expected: all prior tests (readiness harden, proof status, mixed sha, embedded audit normalization, intake) still PASS, plus new ones.

- [ ] **Step 6: Commit**

```bash
git add tools/pr_steward/classifier.py tests/pr_steward/test_classifier_security_release_gate.py
git commit -m "feat(pr-steward): wire security/release approval gate into build_artifacts"
```

---

## Task 7: Collector — harvest reviews with head-bound approval evidence

**Files:**
- Modify: `tools/pr_steward/collector.py`
- Modify: `tools/pr_steward/intake.py`
- Test: `tests/pr_steward/test_collector_security_release_approval.py`

**Interfaces:**
- Consumes: `known_reviewers.json` trusted approver list is *not* consulted here — the collector only harvests raw evidence; Task 6's `evaluate_security_release_approval` does the trust check.
- Produces: `collect_from_github(...)` return dict gains key `"security_release_approval"` — the most recent `APPROVED` review (by `submittedAt`) whose bound `commit.oid` is present, or `None` if no approved review exists.

- [ ] **Step 1: Write the failing test**

```python
# tests/pr_steward/test_collector_security_release_approval.py
from __future__ import annotations

from tools.pr_steward.collector import _select_security_release_approval


def _review(**overrides):
    base = {
        "id": "R_1",
        "state": "APPROVED",
        "author": {"login": "trusted-approver"},
        "authorAssociation": "COLLABORATOR",
        "submittedAt": "2026-07-20T10:00:00Z",
        "commit": {"oid": "a" * 40},
    }
    base.update(overrides)
    return base


def test_no_reviews_returns_none():
    assert _select_security_release_approval([], repo="o/r", pr_number=1) is None


def test_single_approved_review_is_selected():
    result = _select_security_release_approval(
        [_review()], repo="owner/repo", pr_number=42
    )
    assert result is not None
    assert result["state"] == "APPROVED"
    assert result["approver"] == "trusted-approver"
    assert result["head_sha"] == "a" * 40
    assert result["approval_ref"] == "R_1"
    assert result["repository"] == "owner/repo"
    assert result["pr_number"] == 42
    assert result["approved_at"] == "2026-07-20T10:00:00Z"


def test_most_recent_approved_review_wins():
    older = _review(id="R_1", submittedAt="2026-07-20T09:00:00Z")
    newer = _review(id="R_2", submittedAt="2026-07-20T11:00:00Z")
    result = _select_security_release_approval([older, newer], repo="o/r", pr_number=1)
    assert result["approval_ref"] == "R_2"


def test_changes_requested_after_approval_is_not_selected_as_approved():
    approved = _review(id="R_1", state="APPROVED", submittedAt="2026-07-20T09:00:00Z")
    later_changes = _review(
        id="R_2", state="CHANGES_REQUESTED", author={"login": "trusted-approver"},
        submittedAt="2026-07-20T11:00:00Z",
    )
    result = _select_security_release_approval([approved, later_changes], repo="o/r", pr_number=1)
    assert result is None


def test_review_without_commit_oid_is_skipped():
    result = _select_security_release_approval(
        [_review(commit=None)], repo="o/r", pr_number=1
    )
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/pr_steward/test_collector_security_release_approval.py -v`
Expected: FAIL — `ImportError: cannot import name '_select_security_release_approval'`

- [ ] **Step 3: Write minimal implementation**

In `tools/pr_steward/collector.py`, extend the `_fetch_review_threads` GraphQL query to also fetch `reviews`. Add a new function alongside it (do not remove `_fetch_review_threads` — it stays independent):

```python
def _fetch_reviews_with_commit(
    *, repo: str, pr_number: int
) -> tuple[list[dict[str, Any]], list[str]]:
    owner, name = repo.split("/", 1)
    query = textwrap.dedent(
        """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              reviews(first: 100) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  state
                  submittedAt
                  author { login }
                  authorAssociation
                  commit { oid }
                }
              }
            }
          }
        }
        """
    ).strip()
    result = _run(
        [
            "gh", "api", "graphql",
            "-f", f"owner={owner}",
            "-f", f"repo={name}",
            "-F", f"number={pr_number}",
            "-f", f"query={query}",
        ]
    )
    if result.returncode != 0:
        return [], [f"gh api graphql reviews failed: {result.stderr.strip()}"]
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return [], [f"gh api graphql reviews returned invalid JSON: {exc}"]
    page = (
        payload.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviews", {})
    )
    errors: list[str] = []
    if page.get("pageInfo", {}).get("hasNextPage"):
        errors.append("reviews harvest exceeded first 100 reviews")
    return page.get("nodes") or [], errors


def _select_security_release_approval(
    reviews: list[dict[str, Any]], *, repo: str, pr_number: int
) -> dict[str, Any] | None:
    """Return the most recent APPROVED review with a bound commit, or None.

    Chronological order matters: a later CHANGES_REQUESTED from anyone must
    not be shadowed by an earlier APPROVED — GitHub's own reviewDecision
    semantics treat the latest state per-author as authoritative, but for
    this fail-closed gate we take the single most-recent APPROVED review
    with commit binding, full stop. If a subsequent review (any state, any
    author) is more recent than the latest APPROVED review, treat approval
    as absent — a fresh review event means the approval is not necessarily
    still current from the maintainers' perspective.
    """
    dated = [r for r in reviews if isinstance(r, dict) and r.get("submittedAt")]
    if not dated:
        return None
    dated.sort(key=lambda r: r["submittedAt"])
    most_recent = dated[-1]
    if most_recent.get("state") != "APPROVED":
        return None
    commit = most_recent.get("commit")
    if not isinstance(commit, dict) or not commit.get("oid"):
        return None
    author = most_recent.get("author") or {}
    login = author.get("login") if isinstance(author, dict) else None
    if not login:
        return None
    return {
        "state": "APPROVED",
        "repository": repo,
        "pr_number": pr_number,
        "head_sha": str(commit["oid"]),
        "approver": str(login),
        "approval_ref": str(most_recent.get("id") or ""),
        "approved_at": str(most_recent.get("submittedAt") or ""),
    }
```

Wire it into `collect_from_github`, right after the existing `threads, thread_errors = _fetch_review_threads(...)` call:

```python
    reviews_raw, review_errors = _fetch_reviews_with_commit(repo=repo, pr_number=pr_number)
    errors.extend(review_errors)
    security_release_approval = _select_security_release_approval(
        reviews_raw, repo=repo, pr_number=pr_number
    )
```

And add `"security_release_approval": security_release_approval,` to the dict returned by `normalize_gh_payload(...)` call at the bottom of `collect_from_github` — pass it through as a new parameter:

```python
    return normalize_gh_payload(
        pr_payload,
        review_threads=threads,
        harvest_errors=errors,
        proof_state=proof_state,
        security_release_approval=security_release_approval,
    )
```

Update `normalize_gh_payload`'s signature and return dict:

```python
def normalize_gh_payload(
    pr_payload: dict[str, Any],
    *,
    review_threads: list[dict[str, Any]],
    harvest_errors: list[str],
    proof_state: dict[str, Any] | None = None,
    security_release_approval: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review_comments = []
    for thread in review_threads:
        review_comments.extend(thread.get("comments") or [])

    proof = proof_state or _missing_proof_state(None)
    return {
        "harvest_complete": not harvest_errors,
        "harvest_errors": harvest_errors,
        "pr": pr_payload,
        "changed_files": pr_payload.get("files") or [],
        "commits": pr_payload.get("commits") or [],
        "reviews": pr_payload.get("reviews") or [],
        "review_comments": review_comments,
        "review_threads": review_threads,
        "issue_comments": pr_payload.get("comments") or [],
        "checks": pr_payload.get("statusCheckRollup") or [],
        "embedded_audit": proof["embedded_audit"],
        "proof": proof["proof"],
        "security_release_approval": security_release_approval,
    }
```

Also add `"security_release_approval": None,` to `_incomplete_harvest`'s returned dict (so a harvest failure still has a well-formed key — required=False PRs are unaffected; required=True PRs correctly fail closed with `SECURITY_RELEASE_APPROVAL_REQUIRED`).

`tools/pr_steward/intake.py` needs no change: `harvest` already flows opaquely from `collect_from_github`/`load_fixture` straight into `build_artifacts(harvest, ...)` (Task 6 reads `harvest.get("security_release_approval")`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_collector_security_release_approval.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add tools/pr_steward/collector.py tests/pr_steward/test_collector_security_release_approval.py
git commit -m "feat(pr-steward): harvest head-bound approved reviews for the security/release gate"
```

---

## Task 8: Fixture-mode intake end-to-end test

**Files:**
- Create: `tests/pr_steward/fixtures/security_release_red_lane/harvest.json`
- Test: `tests/pr_steward/test_intake_security_release_fixture.py`

- [ ] **Step 1: Write the fixture**

```json
{
  "harvest_complete": true,
  "harvest_errors": [],
  "pr": {
    "number": 9001,
    "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/9001",
    "state": "OPEN",
    "isDraft": false,
    "mergeable": "MERGEABLE",
    "mergeStateStatus": "CLEAN",
    "reviewDecision": "APPROVED",
    "baseRefName": "main",
    "baseRefOid": "base000000000000000000000000000000000000",
    "headRefName": "feat/x",
    "headRefOid": "fixturehead0000000000000000000000000000",
    "author": {"login": "hu3mann"},
    "createdAt": "2026-07-20T01:00:00Z",
    "updatedAt": "2026-07-20T02:00:00Z"
  },
  "changed_files": [{"path": ".github/workflows/example.yml", "additions": 3}],
  "commits": [{"oid": "fixturehead0000000000000000000000000000", "messageHeadline": "ci: tweak"}],
  "reviews": [],
  "review_comments": [],
  "review_threads": [],
  "issue_comments": [],
  "checks": [
    {"name": "unit", "status": "COMPLETED", "conclusion": "success", "headSha": "fixturehead0000000000000000000000000000"}
  ],
  "proof": {
    "proof_path": "proof/PROOF.json",
    "proof_head_sha": "fixturehead0000000000000000000000000000",
    "matches_pr_head": true
  },
  "embedded_audit": {"status": "PASS", "report_path": "proof/AUDITOR_REPORT.md"},
  "security_release_approval": null
}
```

- [ ] **Step 2: Write the test**

```python
# tests/pr_steward/test_intake_security_release_fixture.py
from __future__ import annotations

from pathlib import Path

from tools.pr_steward.classifier import build_artifacts
from tools.pr_steward.collector import load_fixture

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "security_release_red_lane"


def test_fixture_workflow_touch_without_approval_is_needs_supervisor():
    harvest = load_fixture(FIXTURE_DIR)
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=9001,
        strict=True,
        allow_closed=False,
    )
    readiness = artifacts["MERGE_READINESS.json"]
    assert readiness["security_release"]["required"] is True
    assert readiness["security_release"]["approved"] is False
    assert readiness["readiness"] == "NEEDS_SUPERVISOR"
    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/pr_steward/test_intake_security_release_fixture.py -v`
Expected: PASS (this exercises the real `--fixture-dir` code path used by `intake.main`)

- [ ] **Step 4: Commit**

```bash
git add tests/pr_steward/fixtures/security_release_red_lane tests/pr_steward/test_intake_security_release_fixture.py
git commit -m "test(pr-steward): fixture-mode end-to-end coverage for the security/release gate"
```

---

## Task 9: Full validation sweep

**Files:** none (validation only)

- [ ] **Step 1: Run the full focused suite**

```bash
python -m pytest -q tests/pr_steward
python -m pytest -q tests/project_control_plane/test_pr_steward.py
python -m pytest -q tests/pr_merge_specialist/test_steward_gate.py
python -m pytest -q tests/audit/test_exact_head_readiness.py
```

Expected: all PASS. The `project_control_plane`/`pr_merge_specialist`/`audit` suites must be byte-identical in behavior (this plan never touches those modules) — a failure there indicates an accidental cross-import, not an intended change.

- [ ] **Step 2: Schema and JSON validation**

```bash
python -m json.tool tools/pr_steward/known_reviewers.json >/dev/null
find schemas/pr_steward -type f -name '*.json' -print0 | xargs -0 -n1 python -m json.tool >/dev/null
```

- [ ] **Step 3: Diff hygiene**

```bash
git diff --check
git diff --stat
```

- [ ] **Step 4: Confirm scope allowlist**

```bash
git diff --name-only origin/main...HEAD
```

Expected: only files under `tools/pr_steward/`, `schemas/pr_steward/`, `tests/pr_steward/`, `tests/fixtures/pr_steward/` (if used), `tests/pr_merge_specialist/test_steward_gate.py` (read-only — should show no diff), and this plan doc. **No** changes to `.github/workflows/pr-steward.yml` are required by this plan (the existing exit-code-2-on-non-READY path already propagates the new gate) — if the diff shows workflow changes, stop and reconcile against Scope IN before proceeding.

- [ ] **Step 5: Full repo test run (broader safety net)**

```bash
python -m pytest -q tests/
```

Expected: PASS. `NOT_RUN` with reason if the full suite is too slow for this environment — record in the proof bundle either way.

---

## Task 10: Embedded audit and PR

**Files:** none (process only)

- [ ] **Step 1: Run embedded audit**

Per `AGENTS.md §5`/`GOVERNANCE_PRINCIPLES.md` PAL workflow rules (risky/architecture-sensitive chain): `analyze → thinkdeep → challenge → planner → challenge → implement → codereview → precommit → challenge`. This packet already ran `advisor()` in place of an initial `thinkdeep`/`challenge` pass during planning (recorded in the proof trace table above). Before commit, run:

```bash
# codereview + precommit via PAL (or equivalent configured embedded-audit route)
```

Record `auditor_tool`, `auditor_model`, `invocation`, `exit_code`, `auditor_verdict`, `auditor_findings`, `fixes_applied_from_audit`, `remaining_risks` in the proof bundle. `FAIL`, `NEEDS_SUPERVISOR`, or `SKIPPED` blocks completion per packet requirements.

- [ ] **Step 2: Open PR**

```bash
git push -u origin feat/pr-steward-security-approval-parity
gh pr create --title "feat(pr-steward): security/release approval parity gate" --body "$(cat <<'EOF'
## Summary
- Adds a fail-closed, exact-head-bound security/release approval gate to the live PR Steward path.
- Reuses dopemux.dcp.red_lane_rules.FORBIDDEN_PATHS + touches_* vocabulary for path sensitivity; mirrors independent_audit_errors for head-binding.
- Trusted-approver roster ships empty — operator decision, not authored here.
- Generic PCP-Core (src/dopemux/pcp/pr_steward.py) and its schema are untouched.

## Test plan
- [ ] tests/pr_steward (new + existing)
- [ ] tests/project_control_plane/test_pr_steward.py (regression — untouched module)
- [ ] tests/pr_merge_specialist/test_steward_gate.py (regression — untouched module)
- [ ] tests/audit/test_exact_head_readiness.py (regression — untouched module)
EOF
)"
```

- [ ] **Step 3: Run PR Steward against the final head**

```bash
python -m tools.pr_steward.intake --repo DDD-Enterprises/dopemux-mvp --pr <PR_NUMBER> --out proof/pr-steward-final --strict --format json --proof-path <PROOF_PATH>
```

Confirm `readiness == "READY"` with all review items classified, or record the exact blocker for follow-up.

---

## Self-review notes (writing-plans skill checklist — recorded, not re-run)

- **Spec coverage:** every packet Scope-IN item (1–7) maps to a task above; every acceptance criterion (1–10) is exercised by a test in Tasks 2–8; every required negative test in the packet's "Required tests" list is present (see Task 3/6 test files — `1`/`"true"` non-bool-truthy coverage is `test_non_boolean_truthy_state_does_not_bypass`, scope/repo/PR/head mismatch cases are `test_wrong_repo_is_rejected`/`test_wrong_pr_is_rejected`/`test_wrong_head_is_head_mismatch`, stale-approval is `test_future_dated_approval_is_stale`, new-commit-invalidates-approval is `test_new_commit_invalidates_earlier_approval`, unknown-red-lane-classification-fails-closed is structurally impossible here since `classify_security_release_paths` has no "unknown" state — it only returns `required: bool`, so absence of a match is definitionally "not required", which is the documented, correct fail-open-on-non-match / fail-closed-on-match design).
- **Placeholder scan:** none — every step has complete, runnable code.
- **Type consistency:** `SecurityReleaseClassification.required`/`.categories`/`.matched_paths` (Task 2) → consumed as-is in Task 6. `evaluate_security_release_approval` signature (Task 3) → called identically in Task 6. `_select_security_release_approval` return shape (Task 7) → matches the `approval` dict shape asserted in Task 3's tests and consumed by Task 6.
