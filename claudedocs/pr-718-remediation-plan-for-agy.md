# PR #718 Remediation Plan — for agy

**Target PR**: [#718 — DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED](https://github.com/DDD-Enterprises/dopemux-mvp/pull/718)
**Current HEAD**: `c9f66d2ab` on branch `claude/upbeat-thompson-35f2e8`
**Base**: `main`
**Verdict from review**: REQUEST_CHANGES
**Plan author**: claude (review session 2026-05-27)
**Plan readership**: agy (Antigravity) or any cold-start agent
**Authority order**: latest user → `AGENTS.md` → runtime code → schemas → tests → docs

---

## How to read this plan

You have no memory of the prior review. This document is self-contained. Every change includes:
1. Exact file path + line range
2. Concrete code or diff
3. Verification commands with expected outputs
4. Per-TP proof bundle requirements following the existing `proof/TP-DMX-*/PROOF.json` + `AUDITOR_REPORT.md` pattern (see `proof/TP-DMX-AUDIT-PROOF-004/PROOF.json` for shape)

**Truth Order**: when these instructions conflict with runtime code or schemas you find, runtime/schema wins. Mark unresolved authority as `UNKNOWN` and stop.

**Validation reporting**: every claim must be bucketed as PASS / FAIL / NOT_RUN. Never collapse NOT_RUN into PASS.

**Posture**: this PR is strictly **read-only**. Do not import `tools.pr_merge`. Do not introduce `pull_request_target`. Do not touch CODEOWNERS or branch protection. All artifacts must carry `mutation_performed: false`.

---

## Critical path (do in order)

```
Phase 1 (CI unblock, ~10 min)         → unblocks all other phases
  ├─ TP-DMX-CI-UNBLOCK-013-A: relocate artifacts/
  └─ TP-DMX-CI-UNBLOCK-013-B: relocate template MD
Phase 2 (correctness, ~45 min)        → unblocks merge
  └─ TP-DMX-AUDIT-NORMALIZE-014: F1 fix + regression test
Phase 3 (governance, ~60 min)         → unblocks merge
  └─ TP-DMX-VALIDATOR-SCOPE-015: F2 scoping
Phase 4 (recommended, ~30 min)        → strongly recommended in-PR
  └─ TP-DMX-BRIDGE-SYMMETRY-016: F5 fail-closed unknown blockers
Phase 5 (polish, ~30 min)             → can defer if blocked
  ├─ TP-DMX-SCHEMA-PROJECTION-017: F4 helper + docs
  ├─ TP-DMX-CHECK-STATUS-DOCS-018: F6 docstring
  └─ TP-DMX-AUDIT-FALLBACK-019: F7 default path
```

Phases 1–3 must land before merge. Phase 4 strongly recommended. Phase 5 acceptable as follow-up.

---

## Pre-flight (run once before starting)

```bash
# Verify worktree state
git rev-parse --show-toplevel              # → /Users/hue/code/dopemux-mvp
git branch --show-current                  # → claude/upbeat-thompson-35f2e8 (or your worktree branch)
git rev-parse HEAD                         # → c9f66d2ab (or later if you've started)
git status --short                         # → clean (or expected dirty)

# Verify python env
python3 --version                          # → 3.11+
python3 -c "import jsonschema; print(jsonschema.__version__)"  # → installed

# Capture baseline before changes
python3 scripts/audit/validate_audit_proof.py --all proof/ ; echo "exit=$?"
# Expected: 15/51 PASS, 36/51 FAIL, exit=1

# Run new test suites baseline
python3 -m pytest tests/pr_steward/ tests/pr_action_bridge/ tests/audit/ tests/copilot_repair/ tests/ci/ -q
# Expected: 342 passed (per PR body)
```

If any pre-flight returns differently, **stop and report**. Do not proceed on stale assumptions.

---

# Phase 1: CI unblock

## TP-DMX-CI-UNBLOCK-013-A: relocate `artifacts/` directory

**Why**: CI `root-hygiene` check rejects new top-level `artifacts/` directory. Per CI log:
```
root-hygiene: FAILED
   reason: top-level directory 'artifacts' is not allowlisted
```

**Diagnostic**: find the rule that defines the allowlist (so you can either move the file or extend the allowlist — moving is preferred).

```bash
# Find the root-hygiene check definition
grep -rn "root-hygiene\|allowlisted\|top-level directory" --include='*.py' --include='*.yml' --include='*.yaml' --include='*.sh' .github/ scripts/ tools/ pre-commit-hooks/ 2>/dev/null | head -20

# Find the file that's offending
ls -la artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json
```

**Decision**: choose ONE based on what the diagnostic reveals:

- **Option A (preferred)**: move `artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json` to a location already under an allowlisted root. Candidates in this PR's domain: `proof/TP-DMX-PR-FIXTURES-011/load_plan.json` or `docs/ops/load-plans/load_plan-DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED.json`.
- **Option B (only if A is infeasible)**: extend the root-hygiene allowlist to include `artifacts/`. Requires governance review — flag as `UNKNOWN` and ask before doing this.

**Implementation (Option A)**:
```bash
# Pick destination based on grep results
mkdir -p docs/ops/load-plans
git mv artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json \
       docs/ops/load-plans/load_plan-DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED.json

# Remove empty parent directories if nothing else lives there
rmdir artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED 2>/dev/null || true
rmdir artifacts/task-orchestrator 2>/dev/null || true
rmdir artifacts 2>/dev/null || true

# Grep for any string references to the old path and update them
grep -rln "artifacts/task-orchestrator/DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED/load_plan.json" \
  --include='*.py' --include='*.md' --include='*.json' --include='*.yml' --include='*.yaml' .
```

**Verification**:
```bash
# Confirm root-hygiene now passes locally (if such a script exists)
ls -la artifacts/ 2>&1  # → No such file or directory (expected after rmdir)

# If a local root-hygiene runner exists, invoke it
.github/scripts/check-root-hygiene.sh 2>/dev/null || \
  scripts/check_root_hygiene.py 2>/dev/null || \
  echo "NOT_RUN: no local root-hygiene runner found; rely on CI re-run"
```

**Proof bundle**: `proof/TP-DMX-CI-UNBLOCK-013-A/PROOF.json` + `AUDITOR_REPORT.md` per existing TP shape.

---

## TP-DMX-CI-UNBLOCK-013-B: relocate `templates/copilot/PR_REPAIR_PACKET.md`

**Why**: docs `checks` workflow rejects the file location. Per CI log:
```
Enforce markdown file locations for changed files..........................................Failed
❌ templates/copilot/PR_REPAIR_PACKET.md
```

**Diagnostic**: find the markdown-location enforcement rule.

```bash
grep -rn "Enforce markdown file locations\|markdown_locations\|md.*location" \
  --include='*.py' --include='*.yml' --include='*.yaml' --include='*.toml' .github/ scripts/ pre-commit-hooks/ .pre-commit-config.yaml 2>/dev/null | head -20

# Find what allowlisted markdown locations exist
grep -rE "allowed.*\.md|\.md.*allowed|markdown.*allow" --include='*.py' --include='*.yaml' --include='*.yml' --include='*.toml' . 2>/dev/null | head -10
```

**Decision**: move the template to a markdown-allowlisted location. Likely candidates:
- `docs/templates/copilot/PR_REPAIR_PACKET.md` (under `docs/` which is almost certainly allowlisted)
- `docs/ops/copilot-repair-templates/PR_REPAIR_PACKET.md`

**Implementation**:
```bash
# Pick destination based on the diagnostic
mkdir -p docs/templates/copilot
git mv templates/copilot/PR_REPAIR_PACKET.md docs/templates/copilot/PR_REPAIR_PACKET.md

# Clean up empty dirs
rmdir templates/copilot 2>/dev/null || true
rmdir templates 2>/dev/null || true

# Update all references — these are critical because the Copilot scaffold reads this template
grep -rln "templates/copilot/PR_REPAIR_PACKET.md" --include='*.py' --include='*.md' --include='*.json' .
# For each match, update the path
```

**Critical**: the Copilot repair scaffold (`scripts/audit/build_evidence_bundle.py` or similar — find it) likely reads this template path. After moving, run:

```bash
grep -rn "PR_REPAIR_PACKET\|REPAIR_PACKET\.md" --include='*.py' tools/ scripts/ tests/ | head -10
# Update any hard-coded paths
```

**Verification**:
```bash
# Run the markdown-location check locally if available
pre-commit run --all-files --hook-stage manual 2>&1 | grep -E "markdown|location" || \
  echo "NOT_RUN: no local markdown-location hook; rely on CI re-run"

# Confirm Copilot tests still pass after path move
python3 -m pytest tests/copilot_repair/ -q
# Expected: all passing
```

**Proof bundle**: `proof/TP-DMX-CI-UNBLOCK-013-B/PROOF.json` + `AUDITOR_REPORT.md`.

---

# Phase 2: correctness fix (the most important change)

## TP-DMX-AUDIT-NORMALIZE-014: normalize `_embedded_audit()` status + regression test

**Why** (this is F1 from the review, originally raised as Codex P2 against `d84d34df7`, still open at HEAD `c9f66d2ab` after two commits):

`tools/pr_steward/classifier.py:579-588` preserves the raw status string verbatim. The caller at line 128-134 detects unknown status and adds the `EMBEDDED_AUDIT_UNKNOWN` blocker, but the raw value still flows into `MERGE_READINESS.json` (line 212) and `PR_STATE_SNAPSHOT.json` (line 192). Both schemas constrain `embedded_audit.status` to the enum `["PASS","PASS_WITH_RISKS","FAIL","NEEDS_SUPERVISOR","SKIPPED"]` at:
- `schemas/pr_steward/merge_readiness.schema.json`
- `schemas/pr_steward/pr_state_snapshot.schema.json`

Result: when upstream emits a non-canonical value (e.g. `"NOT_RUN"`), the steward ships **schema-invalid JSON exactly when fail-closed reporting is needed**.

The 4 new fixture test files in this PR (~670 LOC) have **zero coverage** for the unknown-status path. Verified with:
```bash
grep -E "NOT_RUN|EMBEDDED_AUDIT_UNKNOWN|status.*UNKNOWN|status.*INVALID" \
  tests/pr_steward/test_classifier_proof_status.py \
  tests/pr_steward/test_classifier_mixed_sha.py \
  tests/pr_steward/test_classifier_readiness_harden.py \
  tests/pr_steward/test_intake.py
# yields zero matches
```

### Code change

**File**: `tools/pr_steward/classifier.py`

**Current code** (lines 579-588):
```python
def _embedded_audit(harvest: dict[str, Any]) -> dict[str, str]:
    raw = harvest.get("embedded_audit") or {}
    return {
        "status": str(raw.get("status") or "SKIPPED"),
        "report_path": str(
            raw.get("report_path") or "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md"
        ),
    }
```

**Replacement**:
```python
def _embedded_audit(harvest: dict[str, Any]) -> dict[str, str]:
    """Project the harvest's embedded_audit into the schema-valid summary shape.

    The merge_readiness and pr_state_snapshot schemas constrain
    embedded_audit.status to a 5-value enum. Any upstream status outside
    that enum is normalized to "SKIPPED" here so downstream artifacts
    remain schema-valid even when fail-closed reporting is in play. The
    caller (build_artifacts) separately adds the EMBEDDED_AUDIT_UNKNOWN
    blocker when the raw value is non-canonical, so the unknown state
    remains observable to operators.
    """
    raw = harvest.get("embedded_audit") or {}
    raw_status = str(raw.get("status") or "").upper()
    if raw_status in PASSING_AUDITS | BLOCKING_AUDITS:
        normalized = raw_status
    else:
        normalized = "SKIPPED"
    return {
        "status": normalized,
        "report_path": str(raw.get("report_path") or ""),
    }
```

Notes:
- **Uppercase normalization** (`.upper()`) is intentional — matches what `PASSING_AUDITS` and `BLOCKING_AUDITS` use, and tolerates upstream tools that emit `"pass"` or `"Fail"`.
- **Empty-string default for `report_path`** (was hard-coded to `proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md`) — this fixes F7 in the same commit. Empty string is allowed by the schema (no `minLength` constraint at the merge_readiness layer); if the schema in fact requires non-empty, use `"<no audit run>"` instead. **Verify by reading** `schemas/pr_steward/merge_readiness.schema.json` `properties.embedded_audit.properties.report_path` before committing.

### Caller — leave unchanged

The caller at lines 128-134 is correct:
```python
embedded_audit = _embedded_audit(harvest)
audit_status = embedded_audit["status"]
if audit_status in BLOCKING_AUDITS:
    _append_once(blockers, f"EMBEDDED_AUDIT_{audit_status}")
elif audit_status not in PASSING_AUDITS:
    _append_once(blockers, "EMBEDDED_AUDIT_UNKNOWN")
    _append_once(unknowns, f"Unknown embedded audit status: {audit_status}")
```

But there's a subtle interaction: after the fix, `audit_status` will always be in `PASSING_AUDITS | BLOCKING_AUDITS`, so the `elif` branch becomes unreachable. **Keep it** as defensive code — `_embedded_audit()` is a helper that other code paths may eventually call without going through `_normalize` semantics. Add a comment:

```python
elif audit_status not in PASSING_AUDITS:
    # Defensive: _embedded_audit() normalizes unknown status to "SKIPPED"
    # so this branch is currently unreachable. Retained for forward
    # compatibility if the helper is ever bypassed.
    _append_once(blockers, "EMBEDDED_AUDIT_UNKNOWN")
    _append_once(unknowns, f"Unknown embedded audit status: {audit_status}")
```

**However**: with this normalization, the `EMBEDDED_AUDIT_UNKNOWN` blocker would never fire — defeating fail-closed reporting. To preserve the blocker signal, capture the raw value before normalization and pass it through to the caller:

**Alternative caller-aware approach** (preferred): change `_embedded_audit()` to return a richer dict including a `_raw_status` field used only for blocker classification, then strip it before serializing.

```python
def _embedded_audit(harvest: dict[str, Any]) -> dict[str, str]:
    raw = harvest.get("embedded_audit") or {}
    raw_status = str(raw.get("status") or "").upper()
    if raw_status in PASSING_AUDITS | BLOCKING_AUDITS:
        normalized = raw_status
        was_unknown = False
    else:
        normalized = "SKIPPED"
        was_unknown = bool(raw_status)  # only "unknown" if upstream supplied a non-empty bad value
    return {
        "status": normalized,
        "report_path": str(raw.get("report_path") or ""),
        # `_raw_status` is internal; the caller uses it to add the
        # EMBEDDED_AUDIT_UNKNOWN blocker, then strips it before serializing.
        "_raw_status": raw_status if was_unknown else "",
    }
```

Then in the caller (around line 128):
```python
embedded_audit = _embedded_audit(harvest)
raw_status = embedded_audit.pop("_raw_status", "")
audit_status = embedded_audit["status"]
if audit_status in BLOCKING_AUDITS:
    _append_once(blockers, f"EMBEDDED_AUDIT_{audit_status}")
if raw_status:
    _append_once(blockers, "EMBEDDED_AUDIT_UNKNOWN")
    _append_once(unknowns, f"Unknown embedded audit status: {raw_status}")
```

This keeps both invariants:
1. Emitted `embedded_audit.status` is always in the schema enum.
2. `EMBEDDED_AUDIT_UNKNOWN` blocker still fires on non-canonical upstream input.

Pick whichever approach (simple-with-dead-branch vs richer-helper) matches the codebase style — `grep -n "_raw_" tools/pr_steward/` to see if there's precedent.

### Regression test

**File**: `tests/pr_steward/test_classifier_embedded_audit_normalization.py` (new)

```python
"""Regression tests for _embedded_audit() schema normalization.

Asserts that:
1. Unknown status values are normalized to "SKIPPED" so artifacts
   remain schema-valid.
2. The EMBEDDED_AUDIT_UNKNOWN blocker still fires when upstream
   supplies a non-canonical status.
3. The emitted MERGE_READINESS.json validates against
   schemas/pr_steward/merge_readiness.schema.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.pr_steward.classifier import build_artifacts


_REPO_ROOT = Path(__file__).resolve().parents[2]
_MERGE_READINESS_SCHEMA = (
    _REPO_ROOT / "schemas" / "pr_steward" / "merge_readiness.schema.json"
)
_PR_STATE_SNAPSHOT_SCHEMA = (
    _REPO_ROOT / "schemas" / "pr_steward" / "pr_state_snapshot.schema.json"
)


def _minimal_harvest(audit_status: str | None) -> dict:
    """Minimal harvest payload sufficient for build_artifacts() to run.

    Only the embedded_audit.status is parametrized; everything else is
    fixed so the test asserts on the audit normalization specifically.
    """
    return {
        "harvest_complete": True,
        "pr": {
            "number": 718,
            "url": "https://github.com/DDD-Enterprises/dopemux-mvp/pull/718",
            "state": "OPEN",
            "draft": False,
            "author": {"login": "test-author", "authorAssociation": "OWNER"},
            "baseRefName": "main",
            "headRefName": "test-branch",
            "headRefOid": "deadbeef",
        },
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [],
        "changed_files": [],
        "commits": [],
        "embedded_audit": (
            {"status": audit_status, "report_path": "proof/test/AUDITOR_REPORT.md"}
            if audit_status is not None
            else {}
        ),
        "proof": {
            "proof_path": "proof/test/PROOF.json",
            "proof_head_sha": "deadbeef",
            "matches_pr_head": True,
        },
    }


@pytest.fixture(scope="module")
def merge_readiness_schema():
    return json.loads(_MERGE_READINESS_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pr_state_snapshot_schema():
    return json.loads(_PR_STATE_SNAPSHOT_SCHEMA.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "raw_status,expected_normalized",
    [
        ("PASS", "PASS"),
        ("PASS_WITH_RISKS", "PASS_WITH_RISKS"),
        ("FAIL", "FAIL"),
        ("NEEDS_SUPERVISOR", "NEEDS_SUPERVISOR"),
        ("SKIPPED", "SKIPPED"),
        ("NOT_RUN", "SKIPPED"),       # Codex P2 case: non-canonical → SKIPPED
        ("UNKNOWN", "SKIPPED"),
        ("pass", "PASS"),              # case insensitive
        ("Fail", "FAIL"),
        ("", "SKIPPED"),
        (None, "SKIPPED"),
    ],
)
def test_embedded_audit_status_normalization(
    raw_status, expected_normalized, merge_readiness_schema, pr_state_snapshot_schema
):
    """Emitted embedded_audit.status is always in the schema enum."""
    harvest = _minimal_harvest(raw_status)
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )

    merge_readiness = artifacts["MERGE_READINESS.json"]
    snapshot = artifacts["PR_STATE_SNAPSHOT.json"]

    assert merge_readiness["embedded_audit"]["status"] == expected_normalized
    assert snapshot["embedded_audit"]["status"] == expected_normalized

    # Schema-validate both artifacts — this is the F1 regression assertion.
    jsonschema.Draft7Validator(merge_readiness_schema).validate(merge_readiness)
    jsonschema.Draft7Validator(pr_state_snapshot_schema).validate(snapshot)


@pytest.mark.parametrize("non_canonical_status", ["NOT_RUN", "UNKNOWN", "weird"])
def test_unknown_status_adds_embedded_audit_unknown_blocker(non_canonical_status):
    """Fail-closed: non-canonical upstream status still adds EMBEDDED_AUDIT_UNKNOWN blocker."""
    harvest = _minimal_harvest(non_canonical_status)
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )
    merge_readiness = artifacts["MERGE_READINESS.json"]
    assert "EMBEDDED_AUDIT_UNKNOWN" in merge_readiness["blockers"], (
        f"Blocker missing for raw status {non_canonical_status!r}; "
        f"got blockers={merge_readiness['blockers']!r}"
    )


def test_canonical_status_does_not_add_unknown_blocker():
    """Canonical status (PASS) must NOT trigger EMBEDDED_AUDIT_UNKNOWN."""
    harvest = _minimal_harvest("PASS")
    artifacts = build_artifacts(
        harvest,
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=718,
        strict=False,
        allow_closed=False,
    )
    merge_readiness = artifacts["MERGE_READINESS.json"]
    assert "EMBEDDED_AUDIT_UNKNOWN" not in merge_readiness["blockers"]
```

### Verification

```bash
# 1. Run the new regression test in isolation
python3 -m pytest tests/pr_steward/test_classifier_embedded_audit_normalization.py -v
# Expected: 14 tests PASS (11 parametrized + 3 specific)

# 2. Run the full PR Steward test suite — no regressions
python3 -m pytest tests/pr_steward/ -v
# Expected: prior tests still pass + the new file passes

# 3. Run the full new-test suite from this PR
python3 -m pytest tests/copilot_repair/ tests/pr_action_bridge/ tests/audit/ tests/ci/ tests/pr_steward/ -q
# Expected: 342 + 14 = 356 passed (or close — adjust if other tests had to change)

# 4. Spot-check: emit an artifact with NOT_RUN status and validate
python3 -c "
from tools.pr_steward.classifier import build_artifacts
import json, jsonschema
from pathlib import Path

harvest = {
    'harvest_complete': True,
    'pr': {
        'number': 718, 'url': 'https://x/y/pull/718', 'state': 'OPEN', 'draft': False,
        'author': {'login': 'x', 'authorAssociation': 'OWNER'},
        'baseRefName': 'main', 'headRefName': 'b', 'headRefOid': 'a',
    },
    'reviews': [], 'review_comments': [], 'review_threads': [],
    'issue_comments': [], 'checks': [], 'changed_files': [], 'commits': [],
    'embedded_audit': {'status': 'NOT_RUN', 'report_path': 'p.md'},
    'proof': {'proof_path': 'p.json', 'proof_head_sha': 'a', 'matches_pr_head': True},
}
arts = build_artifacts(harvest, repo='x/y', pr_number=718, strict=False, allow_closed=False)
mr = arts['MERGE_READINESS.json']
print('status:', mr['embedded_audit']['status'])
print('EMBEDDED_AUDIT_UNKNOWN in blockers:', 'EMBEDDED_AUDIT_UNKNOWN' in mr['blockers'])
schema = json.loads(Path('schemas/pr_steward/merge_readiness.schema.json').read_text())
jsonschema.Draft7Validator(schema).validate(mr)
print('schema validation: PASS')
"
# Expected output:
#   status: SKIPPED
#   EMBEDDED_AUDIT_UNKNOWN in blockers: True
#   schema validation: PASS
```

**Proof bundle**: `proof/TP-DMX-AUDIT-NORMALIZE-014/PROOF.json` + `AUDITOR_REPORT.md`. Include the spot-check above in `commands[]` with its exit code and output.

---

# Phase 3: validator scoping (governance)

## TP-DMX-VALIDATOR-SCOPE-015: bound `validate_audit_proof.py` enforcement

**Why** (F2): empirical run of `python3 scripts/audit/validate_audit_proof.py --all proof/` at HEAD yields:

```
Result: 15/51 PASS, 36/51 FAIL
```

The 36 failing bundles live in `proof/codex-refresh/`, `proof/fast-dev-os/`, `proof/orchestrator/`, `proof/repo-truth-extractor/`, `proof/rte-cost-profile-redesign/`, `proof/rte-ux/` — all pre-existing, all missing top-level `embedded_audit`. The PR body documents only 2 of these. If `--all proof/` is wired into CI as a required check, it will reject 70.6% of any change touching `proof/`.

### Decision required (pick one before implementing)

**Option A** — backfill all 36 bundles with a minimal `embedded_audit: {"status": "SKIPPED", ...}` block. Most thorough. Largest diff. ~36 files.

**Option B** — add a `proof/.validator_scope.json` allowlist that bounds enforcement. Recommended for time-bounded work.

**Option C** — add a `--canonical-only` CLI flag plus a per-bundle `proof/<TP-ID>/.canonical` sentinel file or `embedded_audit_required: true` field in PROOF.json. Lets each TP opt in.

**Recommended**: **Option B** (allowlist), because it (a) preserves the validator's strictness for future bundles, (b) makes the in-scope set explicit and reviewable in one file, (c) is the smallest diff that materially resolves F2.

### Option B implementation

**New file**: `proof/.validator_scope.json`

```json
{
  "schema_version": "1.0.0",
  "purpose": "Bounds the scope of scripts/audit/validate_audit_proof.py --all enforcement. Only proof bundles whose TP ID matches one of `include_patterns` are validated; bundles matching `exclude_patterns` are explicitly grandfathered with the documented reason. Out-of-pattern bundles are skipped with a warning.",
  "include_patterns": [
    "proof/TP-DMX-*/PROOF.json"
  ],
  "exclude_patterns": [
    {
      "pattern": "proof/codex-refresh/**/PROOF.json",
      "reason": "Pre-existing bundles missing embedded_audit; grandfathered pending TP-DMX-LEGACY-BACKFILL-NNN"
    },
    {
      "pattern": "proof/fast-dev-os/**/PROOF.json",
      "reason": "Pre-existing bundles missing embedded_audit; grandfathered pending TP-DMX-LEGACY-BACKFILL-NNN"
    },
    {
      "pattern": "proof/orchestrator/**/PROOF.json",
      "reason": "Pre-existing bundles missing embedded_audit; grandfathered pending TP-DMX-LEGACY-BACKFILL-NNN"
    },
    {
      "pattern": "proof/repo-truth-extractor/**/PROOF.json",
      "reason": "Pre-existing bundles missing embedded_audit; grandfathered pending TP-DMX-LEGACY-BACKFILL-NNN"
    },
    {
      "pattern": "proof/rte-cost-profile-redesign/**/PROOF.json",
      "reason": "Pre-existing bundles missing embedded_audit; grandfathered pending TP-DMX-LEGACY-BACKFILL-NNN"
    },
    {
      "pattern": "proof/rte-ux/**/PROOF.json",
      "reason": "Pre-existing bundles missing embedded_audit; grandfathered pending TP-DMX-LEGACY-BACKFILL-NNN"
    }
  ],
  "default_when_unmatched": "skip_with_warning"
}
```

**Modify** `scripts/audit/validate_audit_proof.py`:

Locate `collect_proof_paths()` and `main()`. Add scope filtering between path collection and validation:

```python
# After line ~70 in validate_audit_proof.py
DEFAULT_SCOPE_PATH = _REPO_ROOT / "proof" / ".validator_scope.json"


def load_scope(scope_path: Path) -> dict | None:
    """Load the validator scope manifest; None if missing (= unbounded)."""
    if not scope_path.exists():
        return None
    return json.loads(scope_path.read_text(encoding="utf-8"))


def apply_scope(
    paths: list[Path], scope: dict, repo_root: Path
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Filter paths by scope manifest.

    Returns (in_scope_paths, [(skipped_path, reason)...]).
    """
    import fnmatch

    include_patterns = scope.get("include_patterns", [])
    exclude_records = scope.get("exclude_patterns", [])
    default = scope.get("default_when_unmatched", "skip_with_warning")

    in_scope: list[Path] = []
    skipped: list[tuple[Path, str]] = []

    for p in paths:
        try:
            rel = p.resolve().relative_to(repo_root).as_posix()
        except ValueError:
            rel = p.as_posix()

        # First check excludes
        excluded_reason = None
        for record in exclude_records:
            if fnmatch.fnmatchcase(rel, record["pattern"]):
                excluded_reason = record["reason"]
                break
        if excluded_reason:
            skipped.append((p, f"excluded: {excluded_reason}"))
            continue

        # Then check includes
        matched_include = any(
            fnmatch.fnmatchcase(rel, pat) for pat in include_patterns
        )
        if matched_include:
            in_scope.append(p)
        elif default == "skip_with_warning":
            skipped.append((p, "not in include_patterns"))
        else:
            in_scope.append(p)  # default = enforce

    return in_scope, skipped
```

And in `main()`, after `collect_proof_paths()` and before the validation loop:

```python
# Apply scope manifest if present
scope = load_scope(DEFAULT_SCOPE_PATH)
if scope is not None and args.scan_root is not None:
    # Scope only applies to --all recursive scans, not explicit single-file args
    proof_paths, skipped = apply_scope(proof_paths, scope, _REPO_ROOT)
    for path, reason in skipped:
        rel = _rel_path(path)
        if not args.quiet:
            print(f"SKIP  {rel}  ({reason})")
```

**Critical**: scope only applies to `--all DIR` mode. Explicit single-file arguments must always validate (the CLI is also used to validate specific bundles).

### Add tests

**File**: `tests/audit/test_validator_scope.py` (new)

```python
"""Tests for proof/.validator_scope.json scope filtering."""
import json
from pathlib import Path

import pytest

from scripts.audit.validate_audit_proof import apply_scope, load_scope


def test_scope_excludes_match_winners(tmp_path):
    repo_root = tmp_path
    scope = {
        "include_patterns": ["proof/TP-DMX-*/PROOF.json"],
        "exclude_patterns": [
            {"pattern": "proof/legacy/**/PROOF.json", "reason": "grandfathered"}
        ],
        "default_when_unmatched": "skip_with_warning",
    }
    paths = [
        repo_root / "proof" / "TP-DMX-FOO-001" / "PROOF.json",
        repo_root / "proof" / "legacy" / "TP-OLD-001" / "PROOF.json",
        repo_root / "proof" / "outside-includes" / "PROOF.json",
    ]
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}")

    in_scope, skipped = apply_scope(paths, scope, repo_root)
    in_scope_names = [p.name for p in in_scope]
    skipped_paths = [str(p[0]).split("/")[-2] for p in skipped]

    assert "PROOF.json" in in_scope_names
    assert any(rec[0].name == "PROOF.json" for rec in skipped if "legacy" in str(rec[0]))


def test_scope_missing_returns_none(tmp_path):
    scope = load_scope(tmp_path / "absent.json")
    assert scope is None


# Additional tests: pattern syntax, default_when_unmatched=enforce, etc.
```

### Documentation update

**Update** `docs/ops/embedded-audit-proof.md`:

Add a section "Validator scope" explaining:
- The manifest at `proof/.validator_scope.json` bounds `--all` enforcement.
- Explicit single-file arguments always validate (no scope filtering).
- New TPs land under `proof/TP-DMX-*/PROOF.json` automatically in scope.
- Legacy bundles are grandfathered with documented reasons.
- A future `TP-DMX-LEGACY-BACKFILL-NNN` will retire the exclude list incrementally.

### Update PR body

After this TP lands, edit the PR description to remove the misleading "documented residual risk" framing about only 2 bundles. Replace with:

> ### Validator scope
>
> The PROOF.json embedded_audit validator (TP-004) is scoped via `proof/.validator_scope.json`. At HEAD, the in-scope corpus is 15 bundles (12 of which were authored by this series). 36 pre-existing bundles under `proof/codex-refresh/`, `proof/fast-dev-os/`, `proof/orchestrator/`, `proof/repo-truth-extractor/`, `proof/rte-cost-profile-redesign/`, `proof/rte-ux/` are grandfathered with the reason documented inline in the manifest, pending a future `TP-DMX-LEGACY-BACKFILL` series.

### Verification

```bash
# 1. With the new scope manifest, --all should pass on the in-scope corpus
python3 scripts/audit/validate_audit_proof.py --all proof/ ; echo "exit=$?"
# Expected: 15/15 PASS (or however many TP-DMX-* bundles), exit=0
# Skipped bundles should print "SKIP path (excluded: ...)" lines

# 2. Without --all, explicit single-file validation still works on legacy bundles
python3 scripts/audit/validate_audit_proof.py proof/codex-refresh/TP-DMX-CODEX-REFRESH-003-PROOF-PACKET-TEMPLATES/PROOF.json ; echo "exit=$?"
# Expected: FAIL (validator does NOT silently pass legacy bundles when targeted directly), exit=1

# 3. The new scope test passes
python3 -m pytest tests/audit/test_validator_scope.py -v
# Expected: all PASS

# 4. Full audit suite still passes
python3 -m pytest tests/audit/ -q
# Expected: 38 + N new tests passing
```

**Proof bundle**: `proof/TP-DMX-VALIDATOR-SCOPE-015/PROOF.json` + `AUDITOR_REPORT.md`. Include the before/after `--all proof/` output in `commands[]`.

---

# Phase 4: recommended (strong but not blocking)

## TP-DMX-BRIDGE-SYMMETRY-016: fail-closed unknown blockers in Action Bridge

**Why** (F5): `tools/pr_action_bridge/compiler.py:162-165` silently drops unknown blockers:

```python
if mapping is None:
    # Unknown blocker: silently skipped for forward compatibility.
    # Callers that need all blockers should inspect merge_readiness directly.
    continue
```

But the **same file** at line 218 explicitly fail-closes unknown roles to supervisor:

```python
# Unknown role: fail closed to supervisor so the action is never silently dropped.
by_role["supervisor"].append(action)
```

The asymmetry is the bug. Apply the same posture to unknown blockers.

### Code change

**File**: `tools/pr_action_bridge/compiler.py`

Replace lines 162-165 with:

```python
if mapping is None:
    # Fail-closed: unknown blocker becomes a supervisor action so a
    # future operator never relies on ACTION_PLAN.json alone and
    # misses a blocker that wasn't yet in the registry.
    action_num += 1
    actions.append(
        {
            "id": f"action-{action_num:04d}",
            "category": "unknown-blocker",
            "target_role": "supervisor",
            "source_blocker": blocker,
            "source_item_id": None,
            "rationale": (
                f"Blocker {blocker!r} is not in the action-bridge registry. "
                "Supervisor must classify and either map the blocker or "
                "document it as non-blocking. ACTION_PLAN.json never silently "
                "drops blockers."
            ),
        }
    )
    continue
```

Also extend `_build_rationale()` to include the new category for documentation completeness (optional, since the inline rationale above takes precedence).

### Test addition

**File**: `tests/pr_action_bridge/test_compiler.py` (extend existing)

```python
def test_unknown_blocker_emits_supervisor_action():
    """F5 regression: unknown blockers fail-closed to supervisor, not silently dropped."""
    merge_readiness = {
        "schema_version": "1.1.0",
        "generated_at": "2026-05-27T08:30:00Z",
        "pr": {
            "number": 999,
            "url": "https://github.com/x/y/pull/999",
            "base_ref": "main",
            "head_ref": "b",
            "head_sha": "deadbeef",
            "changed_files": [],
            "commits": [],
        },
        "readiness": "BLOCKED",
        "risk_tier": "MEDIUM",
        "blockers": ["TOTALLY_NEW_BLOCKER_THAT_DOES_NOT_EXIST_YET"],
        "unknowns": [],
        "mutation_performed": False,
    }
    action_plan, _ = compile_action_plan(
        merge_readiness,
        review_ledger={"items": []},
        thread_dispositions={"threads": []},
        ci_triage={"checks": []},
    )
    assert len(action_plan["actions"]) == 1
    action = action_plan["actions"][0]
    assert action["category"] == "unknown-blocker"
    assert action["target_role"] == "supervisor"
    assert action["source_blocker"] == "TOTALLY_NEW_BLOCKER_THAT_DOES_NOT_EXIST_YET"
```

### Verification

```bash
python3 -m pytest tests/pr_action_bridge/ -v
# Expected: all prior tests + new test PASS
```

**Proof bundle**: `proof/TP-DMX-BRIDGE-SYMMETRY-016/PROOF.json` + `AUDITOR_REPORT.md`.

---

# Phase 5: polish (acceptable as follow-up)

## TP-DMX-SCHEMA-PROJECTION-017: F4 projection helper + docs

The two `embedded_audit` schemas (11-field proof bundle vs 2-field merge_readiness summary) are intentional dual shapes (per gpt-5.1-codex analysis), but undocumented. Add:

1. A `tools/pr_steward/embedded_audit_projection.py` module with a single function:

```python
def project_to_summary(proof_embedded_audit: dict) -> dict:
    """Project the 11-field proof-bundle embedded_audit shape down to
    the 2-field merge_readiness summary shape.

    Used by the steward when consuming a fresh proof bundle and
    deriving the summary fields embedded into MERGE_READINESS.json.
    """
    return {
        "status": proof_embedded_audit.get("status", "SKIPPED"),
        "report_path": proof_embedded_audit.get("report_path", ""),
    }
```

2. `docs/ops/embedded-audit-shapes.md` documenting the two schemas, when to use which, and the projection.

3. Tests asserting that a valid 11-field proof bundle projects to a valid 2-field summary.

## TP-DMX-CHECK-STATUS-DOCS-018: F6 docstring

Add docstring to `_normalize_status()` at `tools/pr_steward/classifier.py:692-704` explaining the GitHub Checks API split between lifecycle status (`completed`, `queued`, `in_progress`, ...) and outcome conclusion (`success`, `failure`, ...), and why `success`/`failure`/`completed` all normalize to `"completed"`.

## TP-DMX-AUDIT-FALLBACK-019: F7 default path

Already folded into TP-014 (replaced hard-coded `proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md` with `""`). If for any reason TP-014's change is rolled back, restore this as a standalone TP.

---

# Per-TP proof bundle requirements

Every TP must produce `proof/<TP-ID>/PROOF.json` and `proof/<TP-ID>/AUDITOR_REPORT.md` following the existing shape (see `proof/TP-DMX-AUDIT-PROOF-004/PROOF.json` for reference). Required fields per the schema at `schemas/proof/embedded_audit.schema.json`:

```json
{
  "schema_version": "1.0.0",
  "tp_id": "TP-DMX-...",
  "series_id": "DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED",
  "repo": "DDD-Enterprises/dopemux-mvp",
  "branch": "claude/upbeat-thompson-35f2e8",
  "base_branch": "main",
  "head_before": "<SHA-before-TP>",
  "head_after": "<SHA-after-TP>",
  "mutation_performed": false,
  "github_mutation_performed": false,
  "secret_values_recorded": false,
  "operator_authorization_used": [],
  "forbidden_surfaces_touched": false,
  "files_changed": ["..."],
  "commands": [
    {"cmd": "...", "exit_code": 0, "result": "..."}
  ],
  "validation": {"status": "PASS", "details": [...]},
  "embedded_audit": {
    "required": true,
    "status": "PASS",
    "auditor_tool": "agy",
    "auditor_model": "<model>",
    "invocation": "...",
    "exit_code": 0,
    "report_path": "proof/<TP-ID>/AUDITOR_REPORT.md",
    "findings": [],
    "fixes_applied": [],
    "remaining_risks": [],
    "skip_reason": null
  }
}
```

Use the validator on your own proof:

```bash
python3 scripts/audit/validate_audit_proof.py proof/<TP-ID>/PROOF.json
# Must exit 0
```

---

# Commit and PR hygiene

- **Commit per TP**, not bulk. Each commit message: `feat|fix|refactor(<scope>): <verb noun>` then `\n\nTP: <TP-ID>` and `Co-Authored-By: <model>`.
- **Push after each phase** if working on a single branch, so reviewers can see incremental progress.
- **Do not amend** prior commits. If a hook fails, fix and add a new commit.
- **Never** add `--no-verify` to any git command.
- **Update PR body** after Phase 3 with the validator-scope language (above) and the corrected residual-risk counts.

---

# Final verification before requesting re-review

Run this complete checklist before posting "ready for re-review":

```bash
# 1. All CI checks pass locally where runnable
pre-commit run --all-files 2>&1 | tail -20

# 2. Full test suite green
python3 -m pytest tests/ -q
# Expected: all PASS (or pre-existing skips/xfails only)

# 3. Validator on in-scope corpus is clean
python3 scripts/audit/validate_audit_proof.py --all proof/ ; echo "exit=$?"
# Expected: exit=0 with all TP-DMX-* bundles PASS, legacy bundles SKIPPED

# 4. F1 regression test specifically passes
python3 -m pytest tests/pr_steward/test_classifier_embedded_audit_normalization.py -v
# Expected: all PASS

# 5. Spot-check Phase 2: emit artifact with NOT_RUN and validate
python3 -c "<the spot-check from Phase 2>"
# Expected: status=SKIPPED, blocker present, schema PASS

# 6. All proof bundles for new TPs are themselves valid
for tp in TP-DMX-CI-UNBLOCK-013-A TP-DMX-CI-UNBLOCK-013-B TP-DMX-AUDIT-NORMALIZE-014 \
          TP-DMX-VALIDATOR-SCOPE-015 TP-DMX-BRIDGE-SYMMETRY-016; do
    python3 scripts/audit/validate_audit_proof.py proof/$tp/PROOF.json
done
# Expected: all PASS

# 7. Posture verification — no mutation surfaces introduced
grep -r "pr_merge\|pull_request_target" --include='*.py' --include='*.yml' --include='*.yaml' \
  $(git diff --name-only main..HEAD)
# Expected: empty output

# 8. Push branch
git status --short                # → clean (or only intended changes)
git log --oneline main..HEAD      # → readable, per-TP commits
git push origin claude/upbeat-thompson-35f2e8
gh pr view 718 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion=="FAILURE")'
# Expected: empty (no failing checks) after CI re-runs
```

---

# Required final response structure (per AGENTS.md)

When you're done, your final response must contain:

- **Change Summary** — what changed across all phases, in plain terms
- **Authority Used** — Task Packet IDs, runtime code references, schemas, tests
- **Analysis Performed** — what you inspected, conclusions reached
- **Validation Performed** — PASS / FAIL / NOT_RUN bucketed
- **Remaining Uncertainty / Risk** — what you don't know
- **Files Touched** — exact paths
- **Git State** — branch, status, commit SHAs
- **Rollback Plan** — concrete commands to undo
- **Requested Next Step** — what to do next

Plus a proof bundle for each TP. No proof = incomplete.

---

# Out of scope for this remediation

- Backfilling the 34 legacy proof bundles (separate `TP-DMX-LEGACY-BACKFILL-NNN` series)
- Extending the steward to consume the 11-field proof shape directly (separate refactor)
- Branch-protection truth verification (separate TP, requires admin `gh api` access)
- Any GitHub mutation (creating issues, posting comments, merging) — this remains read-only

If you discover something that requires scope beyond this plan, **stop, document as `UNKNOWN`, and ask the operator** before proceeding.
