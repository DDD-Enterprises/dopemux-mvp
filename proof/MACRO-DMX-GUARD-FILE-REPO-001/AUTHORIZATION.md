# MACRO-DMX-GUARD-FILE-REPO-001 — Operator authorization record

**When**: 2026-11-13, in the supervisor session.
**Asked**: "Authorize Task 0, and also publish its PR?"
**Operator's answer**: "Authorize and publish"
**Recorded as**: `AUTHORIZE_MACRO_DMX_GUARD_FILE_REPO_001_EXECUTION=YES` and `AUTHORIZE_MACRO_DMX_GUARD_FILE_REPO_001_PUBLISH=YES`

The operator answered with a button. The same turn named both lines and what each covers (`package/ISSUANCE.md`), so this record treats the answer as both gates. If the operator reads it differently, they can say so and the macro stops.

## What it covers

- Execution: the worktree `.worktrees/guard-file-repo-root` on new branch `fix/guard-file-repo-root` from main `264c97b23`; the import commit; G01 with one local commit.
- Publish (G02 only): push `fix/guard-file-repo-root` without force, open one PR to main as a draft, mark it ready once CI is green, reply on and resolve review threads.

## What it does not cover

The audit route, signing, the solo-owner release phrase, the merge, any force-push or rebase.

## Subject

| Item | SHA-256 or commit |
|---|---|
| Base | `264c97b23ec1b3e007e62079d4f6d2632ad71775` (origin/main re-checked at authorization: unchanged) |
| Import commit | `e5e49af09c3b5b02f53782c15a582dfbcdf28944` |
| `package/MACRO_PACKET.json` | `73247c2489570bc65efcb693974bd388937850bcf33c4b326bc53f59a67b2f90` |
| `package/WORKSTREAMS/G01/TASK_PACKET.json` | `992d2a1be965d900f441a14bc101984274070e98e9be808b456a69af79f0b51d` |
| `package/WORKSTREAMS/G02/TASK_PACKET.json` | `0eac3339de1b2bb4e0f1da10a242e882c120dc8e5643c57851cf587f32b96003` |

Authority NONE. This record constrains execution. It grants nothing beyond the operator's words above.
