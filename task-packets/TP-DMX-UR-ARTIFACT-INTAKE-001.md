---
id: TP-DMX-UR-ARTIFACT-INTAKE-001
title: Universal Router Architecture and Audit Evidence Intake
type: explanation
owner: '@hu3mann'
author: 'GPT-5.6 Pro'
date: '2026-07-13'
last_review: '2026-07-13'
next_review: '2026-10-11'
prelude: Binding packet for preserving UR-ARCH-001 and UR-AUDIT-001R3 evidence without runtime changes.
---
# Task Packet: TP-DMX-UR-ARTIFACT-INTAKE-001

## Packet identity

| Field | Value |
|---|---|
| Packet | `TP-DMX-UR-ARTIFACT-INTAKE-001` |
| Series | `UR-ROUTER-GOV-001` |
| Base | `main@45b5ee3f320e777111a6f00227072efeb725996b` |
| Branch | `codex/ur-artifact-intake-001` |
| Risk | Low, provenance-sensitive |
| Status | `READY_FOR_EXECUTION` only while `origin/main` equals the pinned SHA |

## Objective

Copy and verify the accepted UR-ARCH-001 architecture, UR-AUDIT-001R3 audit, and supervisor adjudication from `~/Downloads` or this kit into traceable repository evidence paths. Do not change runtime behavior and do not delete the source files before merge.

## Why this is separate from UR-TP-001

Evidence intake and production contract code have different authority, review, rollback, and retention semantics. Combining them would create a bloated commit where a schema repair could rewrite the evidence spine. That would be stupid, so this packet stays documentation/evidence-only.

## Scope

### IN

- Exact archives and extracted contents under `audit_inputs/universal_router/`.
- Thin, normalized architecture/audit pointer pages under canonical docs roots.
- Registration of this packet and `UR-TP-001`.
- Artifact manifest, checksums, proof, embedded audit, and PR Steward evidence.

### OUT

- Runtime or service code.
- Schemas, policy, provider/runner configuration, routing behavior, or task execution.
- Rewriting architecture or audit claims.
- Deleting or modifying Downloads sources.
- Unrelated docs cleanup.

## Source identities

| Source | Required SHA-256 |
|---|---|
| `UR-ARCH-001_DELIVERABLES.zip` | `9b78e2bd3a6311615e80194398cf07e996f59c952ba9d0280c140d5d39d5e090` |
| `UR-ARCH-001-OPUS-AUDIT-R3.zip` | `b44e892f4ef6fbf0b0235f28f6245143ae04caa1b9a562fad2b64995a923d372` |
| `UR-AUDIT-001R3_SUPERVISOR_ADJUDICATION.md` | `a0176778170edd800e40b7be56ca51100cb1a2ec93326d5fa17de6110cc03e2a` |
| `UR-AUDIT-001R3_SUPERVISOR_ADJUDICATION.json` | `68236db5f904ab5b6942fbb8a55334e717a3e3d67e69fed2e8c682e849cdb4b3` |

## Destination map

```text
audit_inputs/universal_router/UR-ARCH-001/ORIGINAL/
audit_inputs/universal_router/UR-ARCH-001/DELIVERABLES/
audit_inputs/universal_router/UR-AUDIT-001R3/ORIGINAL/
audit_inputs/universal_router/UR-AUDIT-001R3/DELIVERABLES/
audit_inputs/universal_router/UR-AUDIT-001R3/SUPERVISOR/
audit_inputs/universal_router/ARTIFACT_MANIFEST.json
docs/94-architecture/universal-router/ur-arch-001.md
docs/05-audit-reports/universal-router/ur-audit-001r3.md
task-packets/TP-DMX-UR-ARTIFACT-INTAKE-001.json
task-packets/TP-DMX-UR-ARTIFACT-INTAKE-001.md
task-packets/UR-TP-001.json
task-packets/UR-TP-001.md
task-packets/INDEX.md
proof/TP-DMX-UR-ARTIFACT-INTAKE-001/
```

## Invariants

1. Current runtime, config, tests, active entrypoints, and tracked authority outrank imported artifacts.
2. Original archives and extracted files remain byte-identical.
3. The source files remain in Downloads until the intake PR is merged and destination hashes are rechecked.
4. Only the JSON packet allowlist may change.
5. Any hash, inventory, base-SHA, branch, worktree, or destination collision fails closed.

## Exact worktree setup

```bash
cd /Users/hue/code/dopemux-mvp
git fetch origin
test "$(git rev-parse origin/main)" = "45b5ee3f320e777111a6f00227072efeb725996b"
git worktree add -b codex/ur-artifact-intake-001 \
  /Users/hue/code/dopemux-mvp-wt-ur-artifact-intake-001 \
  origin/main
cd /Users/hue/code/dopemux-mvp-wt-ur-artifact-intake-001
```

## Staging commands

First run the no-write check:

```bash
STAGE_UR_DRY_RUN=1 \
  /path/to/UR-TP-001_AND_ARTIFACT_INTAKE_KIT/scripts/stage_ur_artifacts.sh \
  "$PWD" "$HOME/Downloads"
```

Then stage the files into the worktree:

```bash
/path/to/UR-TP-001_AND_ARTIFACT_INTAKE_KIT/scripts/stage_ur_artifacts.sh \
  "$PWD" "$HOME/Downloads"
```

The script copies and verifies. It does not run `git add`, commit, push, open a PR, or delete Downloads.

## Required validation

Execute every `commit.verify` command in the JSON packet, then capture:

```bash
git status --short --branch
git diff --check
git diff --stat
git diff --no-ext-diff
```

## Embedded audit

This governance/evidence packet requires embedded audit under `docs/ops/embedded-audit.md`. `SKIPPED`, `FAIL`, `NEEDS_SUPERVISOR`, malformed proof, stale proof, or head mismatch blocks readiness.

## PR Steward

Use the current canonical operator surface:

```bash
python -m dopemux.cli pr-steward intake \
  --repo DDD-Enterprises/dopemux-mvp \
  --pr "$PR_NUMBER" \
  --out proof/TP-DMX-UR-ARTIFACT-INTAKE-001/pr-steward \
  --strict \
  --proof-path proof/TP-DMX-UR-ARTIFACT-INTAKE-001/PROOF.json \
  --format json
```

`MERGE_READINESS.json` must report `READY` at the current PR head.

## Proof minimums

- Git root, origin, branch, worktree list, base SHA, head SHA.
- Status before and after.
- Source and destination checksums.
- Full destination inventory and artifact manifest.
- Task-packet validation outputs and exit codes.
- Diff stat and full diff.
- Embedded-audit proof/report.
- PR Steward artifacts and current `MERGE_READINESS.json`.

## Rollback

Revert the unmerged commit or close the PR. Preserve source downloads and governance evidence. Do not rewrite shared history.

## Stop conditions

- `origin/main` is not `45b5ee3f320e777111a6f00227072efeb725996b`.
- Wrong repo, primary checkout, dirty baseline, or wrong branch.
- Any source hash or archive inventory mismatch.
- Existing destination content would be overwritten.
- A path outside the allowlist is required.
- Embedded audit or PR Steward blocks.
