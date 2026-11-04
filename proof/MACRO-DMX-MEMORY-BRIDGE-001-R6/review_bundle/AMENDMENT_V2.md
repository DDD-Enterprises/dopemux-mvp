# Amendment v1 → v2 - MACRO-DMX-MEMORY-BRIDGE-001-R6

Coordinator: Claude Code desktop, `claude-opus-5-5`, effort `xhigh` (`$CLAUDE_EFFORT`; it was `high` at issuance). Recorded 2026-11-01. Authority: NONE.

## Operator instructions since the R6 authorization (typed in this session's chat, not relayed)

The two R6 lines in `AUTHORIZATION_RECORD.md` stay in force unchanged.

1. `#1482 is merged` and later `It's merged now`. The coordinator checked GitHub both times: PR #1482 was OPEN (BLOCKED, head `b275543fe`, no `mergedAt`, no merge-queue entry) and `origin/main` was still `97b6d5040`. The W02 gate stayed closed.
2. `Yes, message it`: the coordinator asked the Route Ledger session to finish #1482's signing path. It answered that no audit of `b275543fe` exists yet, so there is nothing to sign.
3. `mmaarrkk. rreeaaddyy`, read as "mark ready". The coordinator ran `gh pr ready 1483` on 2026-11-01. The R6 packet lists `mark_ready` under `global_forbidden_actions`. The action was taken on the operator's direct instruction, which outranks the packet; it is recorded here as a deviation from the issued packet, and v2 keeps `mark_ready` forbidden from here on. Side effects of the ready transition: a Codex review (stopped on the account's usage limit, no findings), a `recheck` run (RECHECK_BLOCKED, same cause as the audit check), and the Copilot review below.
4. `Yes, amend R6`: the answer to the question "Should I fold the fixes into R6 so the one R6 audit covers them?". This is the authority for v2.

## What the Copilot review found (review 5725954984 on `bff3fd46e`, rechecked at `4f66e7ea6`)

| ID | Comment | Finding | Source evidence | Holds at `4f66e7ea6` |
|---|---|---|---|---|
| C1 | 4434064547 | Without `.dopemux` the docs say rows stay "in memory only"; in fact `persistOnce` writes them with `$.store.set` and `ensureLoaded` reads them back. | `register.tsx:517`, `:553-574`; `$.store` is a per-plugin JSON file in the user's Claude Code config directory kept across sessions (`proof/MACRO-DMX-MEMORY-BRIDGE-001/review_bundle/W01_FINDINGS.md:36`) | yes (how-to; the README names `$.store` but not that it is on disk) |
| C2 | 4434064563 | "Never creates `.dopemux`" holds only for the outbox writer; replay runs without it and `capture emit` creates the ledger's parent directory. | `register.tsx` `replayTick` (no `.dopemux` check); `src/dopemux/memory/capture_client.py:525-526` (`ledger_path.parent.mkdir(parents=True, exist_ok=True)`), `:261-265` (default ledger path) | yes |
| C3 | 4434064569 | The README verification query selects `event_id`, a column `raw_activity_events` does not have; the sent id is stored in `id`. | `services/working-memory-assistant/chronicle/schema.sql:5-20`; INSERT at `capture_client.py:541-548` | yes |
| C4 | 4434064579 | R2 `RETURN-01.md:29` says "No cap was hit", but the 6 h cap from authorization to a frozen head was exceeded. | R2 `MACRO_PACKET.json` `base_policy`; R2 bindings and `git log` (see `ERRATUM_R2_WALL_CAP.md`) | yes (a record error, no code) |

## Changes v1 → v2

| | v1 (issued) | v2 (executed) |
|---|---|---|
| Workstreams | W01 (test fix, done at `4f66e7ea6`), W02 (base update, after #1482) | W01 unchanged; **W03** new: C1-C3 in `plugins/dopemux-memory-bridge/README.md` and `docs/02-how-to/memory-bridge.md`, C4 as `review_bundle/ERRATUM_R2_WALL_CAP.md`; W02 now depends on W01 and W03 |
| W02 start head | `c1256c0600` | the W03 commit |
| Join J01 | W01, W02 | W01, W03, W02; adds "C1-C3 corrected and the C4 erratum recorded" |
| Final audit prompt | one line per earlier finding | the same, plus C1-C4 |
| Stop on a `register.tsx` change | W01 | W01 and W03 |
| Team-lead binding | effort `high` | effort `xhigh` (re-observed); gate refs list the R6 lines and instruction 4 |

Unchanged: allowances (no new child dispatch; subagent tokens stay within 400,000), the audit route line and its one attempt, the W02 gate on #1482, and every R2 and R5 record (C4 is corrected by an erratum, not by editing R2).

Route for W03: the coordinator itself, no child. Cost basis: three short doc corrections whose source evidence the coordinator had already read for this check; a child would have to re-read the same files. Requested and observed model `claude-opus-5-5` (response-claimed), effort `xhigh`; provider-attested identity UNKNOWN.

Residual (out of scope, code): the status label still reads `📮 memory-only`; renaming it would change `register.tsx`. The docs now say what it means.

Still excluded: push, PR update, signing, attestation, merge, a second audit, any advisor call.

## Package hashes

| Member | v1 (issued) | v2 (executed) |
|---|---|---|
| `MACRO_PACKET.json` | `8e07297c2501b6e58dca3b05274873641833c753af5fbd8228a6f7e99cd339db` | `1473d2e070ec3528af446c43b0507b997e9986f96ebd40f60799afc57aee9a42` |
| `EXECUTION_BINDING.json` | `891e05e8fd9fd2266f3666668b50afa30e44ba897a2debc42cfcb4687f196d06` | `b7e66055530c7f47c21ad3f781df089e60b8b985ddf790f94a008d5f465e26c5` |
| `W01 TASK_PACKET.json` | `6b0aec4d28a09a74fc591aeb1c6597f62c0347898dbd0651a5f26e59f29e141b` | unchanged |
| `W02 TASK_PACKET.json` | `ba0dce253a5e554c0184fef3d270f8dc28d31cdd8238db5467d35b77cb6ed747` | `946b18acb803358ea3121d31ac94260143c5961ded69888b730aed541f049e2f` |
| `W03 TASK_PACKET.json` | (none) | `2d80d222ee126c3fe7bc6d8458545077b67048760d27256dc49256aece159d9a` |

v1 is kept as `ISSUED_V1_*.json`; the generator is `AMENDMENT_V2_GENERATOR.txt`. v2 validation: `ct validate-macro` STATIC_VALID; `ct validate-binding` PASS (team lead and W01); `task_packet.v2` schema PASS ×3; pins MATCH.
