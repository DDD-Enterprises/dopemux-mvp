---
id: CCAR-002R
title: CCAR-002 PR 1176 Portability Repair and Canonical Audit Return
type: explanation
owner: '@hu3mann'
author: Grok 4.5
date: '2026-08-02'
last_review: '2026-08-02'
next_review: '2026-08-31'
prelude: Narrow R1 portability/determinism repair plus R2 signed exact-head audit
  return for PR 1176 after CCAR-002 implementation-claimed but release-evidence-blocked.
---
# Task Packet: CCAR-002R · PR #1176 · Portability Repair + Canonical Audit Return

════════════════════════════════════════════════════════════

## Packet Identity

| Field | Value |
|---|---|
| Packet | `CCAR-002R` |
| Parent | `CCAR-002` |
| Series | `CCAR-SERIES-001` |
| Repository | `DDD-Enterprises/dopemux-mvp` |
| Existing PR | `#1176` |
| Existing branch | `feat/CCAR-002-normalized-agent-persona-catalog` |
| Required starting PR head | `a22699fc9834c77017ac88e482a6c94fdd319bda` |
| Decision-era head (superseded) | `1cd032213614dc1fc2506c9f78a7003cee012346` |
| Current live blocker | `PR Steward / final readiness = failure` (or Steward skipped after audit fail) |
| Failed trusted embedded-audit run (decision evidence) | `30664700480` (head `1cd032…`) |
| Later failed embedded-audit (post main-merge) | observe live; do not treat as pass |
| Risk | Medium — proof/authority-boundary + determinism contract |
| Status | `READY_FOR_R1_PORTABILITY_THEN_R2_PROOF` |

The exact starting SHA is intentional. This is a narrow repair against an existing PR, not a greenfield implementation packet.

**Head drift note (authoring time 2026-08-02):** Supervisor decision text pinned `1cd032…`. Live PR head is later merge-from-main `a22699…` of which `1cd032…` is an ancestor. This packet pins **live** head `a22699…`. If remote head is no longer exactly that SHA, **stop** and issue a refreshed packet. Do not invent a new starting SHA.

────────────────────────────────────────────────────────────

## Decision (inherited supervisor ruling)

```text
CONFLICTING → CCAR_002_NOT_COMPLETE
PR_1176_RELEASE_EVIDENCE_BLOCKED
CCAR_003_NOT_AUTHORIZED
MERGE_NOT_AUTHORIZED
```

Implementation may be substantially complete, but required audit and exact-head gates did **not** pass.

### Observed blocking evidence

* PR #1176 open; live head at packet authoring = `a22699fc9834c77017ac88e482a6c94fdd319bda`.
* Normal CI largely green; trusted embedded audit **failure**; Steward not READY.
* Trusted CI artifact failures (run `30664700480` on `1cd032…`):
  * PAL/Claude audit route: `Credit balance is too low`.
  * Local signed attestation: `signature_invalid: incorrect signature`.
* Canonical proof still audits `9221dd49b09628d8fd43a9fa7f01def89112beda`, not live head.
* Live head after implementation is not a proof-only return above an audited repair head (docs frontmatter + later main merge).
* `proof/CCAR-002/PROOF.json = SKIPPED` is honest **implementation-time** evidence and is **not** the primary failure.
* Generated catalog contains absolute path:

```text
/Users/hue/code/dopemux-mvp-worktrees/CCAR-002/proof/CCAR-002/SOURCE_MANIFEST.json
```

That violates CCAR-002 requirements: repo-relative paths, no private absolute path, deterministic output across worktrees. Auditor labeled low severity; under active packet rules this is **blocking**, with hard-coded `.parent.parent.parent` discovery.

### Classification tokens (pre-repair)

```text
CCAR_002_IMPLEMENTATION_CLAIMED
CCAR_002_PORTABILITY_REPAIR_REQUIRED
CCAR_002_AUDIT_RETURN_INVALID
PR_1176_NOT_READY
```

────────────────────────────────────────────────────────────

## Objective

1. **R1** — Fix catalog portability/determinism so builder emits stable repo-relative paths and identical output from differently located worktrees; regenerate catalog + implementation evidence; preserve all agent/persona **source** files byte-for-byte.
2. **R2** — Fresh AGY audit against exact R1; finalize, sign, and verify canonical proof-only commit; require local acceptance + trusted embedded audit success + PR Steward READY.

No force push, history rewrite, merge, or CCAR-003 execution.

────────────────────────────────────────────────────────────

## Authority

### Execution authority

1. Explicit operator instruction / supervisor decision
2. This active packet
3. Parent `CCAR-002` invariants that remain applicable
4. Current `RULES.md`, `AGENTS.md`, proof and audit contracts
5. Tool defaults

### Truth authority

1. Live PR head, Git history, current checks, workflow logs, runtime scripts, schema validation
2. Trusted `main` audit acceptance scripts and allowed-signers file
3. Current proof and embedded-audit contracts
4. Packet claims
5. Inference

Local `PASS`, local `READY`, PR description, or handoff summary cannot override failed live status on the candidate head.

────────────────────────────────────────────────────────────

## Scope

### IN — R1 (portability + determinism)

* Add `task-packets/CCAR-002R.md` and `task-packets/CCAR-002R.json` to the existing PR branch.
* Replace absolute `meta.source_manifest` with stable **repo-relative** path (expected: `proof/CCAR-002/SOURCE_MANIFEST.json`).
* Replace fixed `Path(__file__).resolve().parent.parent.parent` discovery with explicit and/or validated repository-root resolution (e.g. `git rev-parse --show-toplevel`, marker walk for `.dopetaskroot` / `pyproject.toml`, optional CLI override). Fail closed if root cannot be validated.
* Add a test that generates the catalog from **two differently located worktrees** (or equivalent dual-root layout) and requires **byte-identical** catalog output after the documented timestamp normalization (same rule as builder `--check` for `generated_at`, or frozen `SOURCE_DATE_EPOCH` / fixed clock if introduced for determinism).
* Assert `meta.source_manifest` is repo-relative and contains **no** absolute path / home directory / private machine path.
* Regenerate `config/commandcode/normalized_agent_persona_catalog.yaml` and relevant `proof/CCAR-002/**` implementation evidence as needed.
* Preserve all source agent/persona files **byte-for-byte** (no edits under `.claude/agents/**`, `.claude/personas/**`, `.github/agents/**`, `src/dopemux/personas/**` source surfaces).

### IN — R2 (canonical audit return)

* Fresh **AGY** independent audit against **exact R1** (not R2, not pre-R1 head).
* Finalize `proof/pr_merge/embedded-audit/pr-1176/PROOF.json` completely **before** signing.
* Sign the exact final bytes (`scripts/audit/sign_local_audit_proof.sh 1176` or equivalent allowed path).
* Verify signature locally against trusted `main` allowed-signers.
* Fetch sufficient ancestry; require `local_audit_acceptance accepted=true` for prospective R2 head.
* Commit **only** `proof/pr_merge/embedded-audit/pr-1176/**` as R2.
* Push R2 (normal push), observe trusted embedded audit success and PR Steward READY.
* Update PR body to distinguish implementation claim from live release readiness.

### OUT

* Force push, rebase of pushed history, amend of any pushed commit, squash, history rewrite.
* Merge of PR #1176.
* CCAR-003 planning or implementation.
* Workflow / schema / allowed-signers / audit-script infrastructure fixes (unless a tiny allowlisted doc-only fix is separately authorized — default **no**).
* Source agent/persona content changes.
* Runtime activation of catalog (agents, skills, hooks, MCP, DCP, Universal Router, role routing).
* Claiming Claude-family audit ran if credits remain exhausted — use authorized AGY Gemini route only; record route honestly.
* Treating auditor “low severity” on absolute path as non-blocking.
* Treating `proof/CCAR-002/PROOF.json` SKIPPED as the primary failure to “fix” into PASS without R2 gates.

────────────────────────────────────────────────────────────

## Invariants

1. Starting PR head must be exactly `a22699fc9834c77017ac88e482a6c94fdd319bda`. Stop if different.
2. Worktree clean before R1 content is committed (except intentional staged R1 files).
3. R1 changes only the R1 allowlist (below).
4. All agent/persona **source** files remain byte-identical across R1 and R2.
5. Catalog `meta.source_manifest` is repo-relative; no absolute/private paths in generated catalog YAML.
6. Builder repo-root resolution is explicit or validated; no sole reliance on fixed three-level `.parent` depth.
7. Dual-worktree (or dual-root) catalog generation produces byte-identical output under the packet’s timestamp rule.
8. Existing CCAR-002 product invariants preserved: 9 base agents; persona coverage; no model IDs in catalog/schema; persona authority booleans false; no unauthorized route activation; schema `additionalProperties=false`; builder `--check` passes.
9. Fresh independent audit is bound to **exact R1**, not R2 and not any prior head.
10. `PROOF.json.head_sha` equals **R1** exactly (not R2).
11. `PROOF.json.pr_number` = `1176`; `repo` = `DDD-Enterprises/dopemux-mvp`.
12. `PROOF.json` contains passing `embedded_audit.status`: `PASS` or non-blocking `PASS_WITH_RISKS` **after** portability findings are fixed or reclassified only if no longer present.
13. Signature is detached OpenSSH over exact committed proof bytes in namespace `dopemux-embedded-audit`; verification uses trusted `main` `config/audit/embedded-audit-allowed-signers`.
14. R2 changes only `proof/pr_merge/embedded-audit/pr-1176/**` relative to R1.
15. No tracked file changes after R2.
16. `local_audit_acceptance` returns `accepted=true` for prospective R2 before push.
17. Live CI success and PR Steward READY outrank local claims.
18. No merge; no force push; no CCAR-003.

If an invariant appears impossible, stop and report.

────────────────────────────────────────────────────────────

## Allowed Files

### R1 allowlist

```text
task-packets/CCAR-002R.md
task-packets/CCAR-002R.json
scripts/commandcode_router/build_normalized_catalog.py
tests/commandcode_router/test_normalized_catalog.py
config/commandcode/normalized_agent_persona_catalog.yaml
proof/CCAR-002/**
```

Optional only if schema string constraints must mention relative-path shape (prefer not):

```text
schemas/commandcode/normalized_agent_persona_catalog.schema.json
```

Use schema edit only when required for a relative-path pattern / description that cannot be enforced by tests alone. Default: **no schema change**.

### R2 allowlist

```text
proof/pr_merge/embedded-audit/pr-1176/**
```

No other tracked file may change on R2.

GitHub metadata mutations limited to: PR #1176 body update; workflow/status observation. No merge, close, force-push, or opportunistic infra edits.

────────────────────────────────────────────────────────────

## Commit Topology

```text
a22699fc9834c77017ac88e482a6c94fdd319bda   required starting live head
    |
    v
R1  fix(commandcode): portable deterministic catalog paths + CCAR-002R
    |  portability + determinism + packet + regenerated catalog/evidence
    |  fresh AGY audit targets this SHA
    v
R2  proof(audit): signed local embedded-audit attestation for PR 1176
       changes only proof/pr_merge/embedded-audit/pr-1176/**
       PROOF.json.head_sha == R1
       final PR head == R2
```

Do **not** set `PROOF.json.head_sha == R2`.

Historical proof commits already on the branch (`eb26a718…`, `54331335…`, `24a48389…`, `72a6bd8b…`, etc.) remain history. R2 **overwrites** the canonical `proof/pr_merge/embedded-audit/pr-1176/**` contents with a correct exact-head package; do not delete history via rewrite.

────────────────────────────────────────────────────────────

## Forbidden Files and Actions

Do not modify:

```text
.claude/agents/**
.claude/personas/**
.github/agents/**
src/dopemux/personas/**
src/dopemux/roles/**
.github/workflows/**
scripts/audit/**
config/audit/**
.commandcode/**
.mcp.json
AGENTS.md
RULES.md
```

(Exception: reading any of the above is allowed.)

Do not:

* force push or rewrite pushed commits;
* add or change signers;
* expose private signing keys;
* claim Claude-route success when credits blocked;
* start CCAR-003;
* merge PR #1176;
* invent a third repair commit after R2 for “one more doc tweak” without a new packet.

────────────────────────────────────────────────────────────

## Plan

### R1-1. Exact-head preflight

```bash
set -euo pipefail
git fetch --prune origin
test "$(git rev-parse HEAD)" = "a22699fc9834c77017ac88e482a6c94fdd319bda" \
  || { echo "STOP: local HEAD drift"; git rev-parse HEAD; exit 2; }
REMOTE_HEAD="$(git ls-remote origin refs/heads/feat/CCAR-002-normalized-agent-persona-catalog | awk '{print $1}')"
test "$REMOTE_HEAD" = "a22699fc9834c77017ac88e482a6c94fdd319bda" \
  || { echo "STOP: remote head drift: $REMOTE_HEAD"; exit 2; }
test -z "$(git status --porcelain=v1)" || { echo "STOP: dirty worktree"; git status -sb; exit 2; }
gh pr view 1176 --json state,headRefOid,baseRefName,mergeable
```

If local worktree is still at `1cd032…`, hard-reset is **not** authorized on a dirty tree; prefer `git merge --ff-only origin/feat/CCAR-002-normalized-agent-persona-catalog` (or fresh worktree at exact head). No force push.

### R1-2. Portability repair

1. Resolve repo root via validated strategy (git toplevel + marker validation; optional `--repo-root`).
2. Emit `meta.source_manifest` as repo-relative path only.
3. Add dual-location determinism test.
4. Add assertion: catalog YAML has no absolute path prefixes (`/Users/`, `/home/`, etc.) in `source_manifest`.
5. Regenerate catalog; run focused tests; builder `--check`.
6. Refresh `proof/CCAR-002/**` implementation evidence honestly (audit remains SKIPPED or pending-R2 as appropriate for implementation packet proof — do not fake PASS).
7. Verify source agent/persona hashes still match `SOURCE_MANIFEST.json`.

### R1-3. Commit R1

Commit only R1 allowlist paths. Capture `R1=$(git rev-parse HEAD)`. Verify `git diff --name-only a22699… R1` ⊆ allowlist.

### R2-1. Fresh AGY audit against R1

* Capture review bundle for exact R1 + current PR base.
* Run AGY Gemini high-effort read-only audit (exact selector from `agy models`).
* Require PASS or non-blocking PASS_WITH_RISKS with portability findings **resolved** (no remaining absolute-path / depth-assumption blocking findings).
* If AGY unavailable, **stop** — do not re-use stale proof bytes or invent PASS.

### R2-2. Finalize, sign, verify, accept

1. Write complete `PROOF.json` with `head_sha=R1`, full embedded_audit, correct schema shape.
2. Sign exact final bytes; never edit after sign without re-sign.
3. Verify signature against trusted main allowed-signers.
4. Commit only `proof/pr_merge/embedded-audit/pr-1176/**` as R2.
5. Run:

```bash
python3 -m scripts.audit.local_audit_acceptance \
  --repo DDD-Enterprises/dopemux-mvp \
  --pr 1176 \
  --head-sha "$(git rev-parse HEAD)" \
  --allowed-signers config/audit/embedded-audit-allowed-signers \
  --schema schemas/proof/embedded_audit.schema.json
```

Expect `accepted=true`. Fetch sufficient ancestry if evaluator requires it.

### R2-3. Push and live gates

* Normal push of R1+R2 (if R1 not yet pushed, push both once after local acceptance on R2).
* Observe trusted embedded-audit success (no `signature_invalid`; no skipped Steward due to audit fail).
* Observe PR Steward / final readiness **READY**.
* If Claude credit route still fails but local-signed path is the accepted CI path, ensure proof provenance records local attestation honestly per contract.
* Do not merge.

────────────────────────────────────────────────────────────

## Validation Gates

### R1 gates

| Gate | Expect |
|---|---|
| Packet JSON schema / dopetask validate | exit 0 |
| `meta.source_manifest` repo-relative | exact relative path; no `/Users/` etc. |
| Dual-worktree catalog identity | byte-identical under timestamp rule |
| Builder `--check` | exit 0 |
| Focused `tests/commandcode_router/test_normalized_catalog.py` | exit 0 |
| Source agent/persona SHA-256 | match manifest |
| R1 path allowlist | exact |
| `git diff --check` | clean |

### R2 gates

| Gate | Expect |
|---|---|
| AGY audit bound to R1 | recorded tool/model/invocation/exit/findings |
| `PROOF.json.head_sha` | equals R1 |
| Signature verify | valid vs trusted main signers |
| `local_audit_acceptance` | `accepted=true` |
| R2 path set | only `proof/pr_merge/embedded-audit/pr-1176/**` |
| Trusted embedded audit | success on final head |
| PR Steward final readiness | READY |
| PR merge state | open, unmerged |

────────────────────────────────────────────────────────────

## Success Criteria

1. Catalog portable and dual-worktree deterministic.
2. No absolute private path in generated catalog meta.
3. Fresh signed proof on exact R1; final head is proof-only R2.
4. Local acceptance true; trusted embedded audit success; Steward READY.
5. PR #1176 still open; no merge; CCAR-003 not started.

### Success tokens (only after live gates)

```text
CCAR_002R_R1_PORTABILITY_PASS
CCAR_002R_R2_AUDIT_RETURN_PASS
PR_1176_READY
CCAR_002_RELEASE_EVIDENCE_UNBLOCKED
```

Until then retain:

```text
CCAR_002_NOT_COMPLETE
PR_1176_NOT_READY
```

────────────────────────────────────────────────────────────

## Residual Risks / UNKNOWN

* Claude-family credit balance may remain exhausted; AGY Gemini is the authorized audit route for R2.
* Signature failure root cause on prior attestation may be incomplete PROOF finalization before sign, wrong namespace, or wrong bytes; R2 must re-finalize then sign once.
* Post-authoring head drift (further merges to branch) voids this packet’s starting SHA pin.
* Whether schema needs a relative-path pattern remains UNKNOWN until R1 implementation chooses enforcement site (test-only vs schema).
* Model-family independence of auditor vs implementer remains UNKNOWN if not proven; record as remaining risk in proof if applicable.

────────────────────────────────────────────────────────────

## Stop Conditions

Stop and report if:

* head is not exactly the pinned SHA;
* source agent/persona bytes change;
* dual-worktree determinism fails after repair attempt;
* AGY audit unavailable or non-passing;
* signature verification fails;
* local acceptance false;
* live embedded audit or Steward not READY after honest R2;
* any force-push or merge pressure appears.

────────────────────────────────────────────────────────────

## Handoff Template (after R2 live gates)

```text
packet: CCAR-002R
pr: 1176
start_head: a22699fc9834c77017ac88e482a6c94fdd319bda
R1: <sha>
R2: <sha>
audit_tool/model: agy / <selector>
local_acceptance: true
trusted_embedded_audit: success
pr_steward: READY
merge: NOT_DONE
ccar_003: NOT_AUTHORIZED
```
