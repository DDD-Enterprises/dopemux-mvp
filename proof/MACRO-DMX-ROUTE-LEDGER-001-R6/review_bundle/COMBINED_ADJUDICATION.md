# Combined adjudication (MACRO-DMX-ROUTE-LEDGER-001-R6, W04)

Subject: `b275543fe1011bf3a9351a10448c24d94f205370` on `claude/route-ledger-001-8d8032` (PR 1482), a normal commit with one parent `3d2af4b209dfc1fb703f82658a0c3a35cd804814`; base `97b6d5040496e2271c41d24c339d039303bbe6b1`. Written after both custody commits existed (`ced97d784` Grok, `91bf32291` AGY). Authority NONE: readiness stays with PR Steward and the operator. Per-auditor detail: `GROK_ADJUDICATION.md`, `AGY_ADJUDICATION.md`.

## Verdict rule applied
- Grok (PRIMARY, `grok-cli` / `grok-4.5`, tool-less): `PASS_WITH_RISKS`, Q1-Q13 all PASS, 5 findings, none BLOCKING.
- AGY (CORROBORATING, `agy` / `gemini-4-argon-high`, request-review hardening): `PASS_WITH_RISKS`, Q1, Q2, Q4-Q13 PASS, **Q3 UNKNOWN**, 5 findings, none BLOCKING.
- Stricter outcome: both statuses are `PASS_WITH_RISKS`; AGY is not stricter at the status level and raised no BLOCKING finding, so the aggregate outcome is `PASS_WITH_RISKS` and `embedded_audit.verdict` is the primary's (Grok). The aggregate does not report the stronger of the two alone: AGY's Q3 is UNKNOWN.
- **Corroboration is PARTIAL, and that is the open point for the operator.** AGY's copy of the 194,244-byte prompt was cut by about 2.3-2.7 KB at the tail (inside `receipt.schema.json`, after about line 99 of 163), by AGY's side of the transport; the prompt we sent was intact and byte-equal to the committed one (`AGY_ADJUDICATION.md`, "Input integrity"). The schema tail it did not see (the end of `definitions.step_observed`, all of `definitions.advisor_call`) was seen and passed by the primary auditor. The packet allows one attempt per route and no retry, so no re-run was made. Whether partial corroboration is acceptable, or a further AGY run on a shorter prompt (a new package revision with new hashes and a new operator line) is wanted, is the operator's decision; this workstream does not make it.
- Neither auditor was shown the other's output. Both received the earlier audit's findings as untrusted claims (operator decision). Authority: the verdicts are claims by tool-less (Grok) and non-tool-less-but-gated (AGY) models; identity is a claim for both (`model_self_reported`: `grok-4` and `unknown`).

## Union of findings (maximum severity; every one OPEN, the operator decides what to accept)
The ids below are this round's. Grok's N1, N10, N14, N15, N16 keep their ids; AGY's own ids N2, N3, N4, N5 are renumbered N17, N18, N19, N20 so they do not collide with the R4 ids N2-N5 (different findings).

| Id | Max severity | Grok | AGY | Adjudication | Title |
|---|---|---|---|---|---|
| N1 | HIGH | HIGH | HIGH | CONFIRMED (live gap); AGY's `stat` semantics doubt not supported by the local declaration, live UNVERIFIABLE | The frozen head has not run in a real Claude Code session; the host's `$.fs.stat` symlink semantics are mock-tested only. |
| N17 | LOW | - | LOW (AGY N2) | CONFIRMED | `/route-ledger receipts` typed right after `/clear`, before the next hook, prints `receipt file: none` and `receiptsEnabled false` (the command handlers do not re-init the ledger). |
| N18 | LOW | - | LOW (AGY N3) | CONFIRMED (mechanism); impact bounded | The first unpinned Agent call after a start or `/clear` adds its tool_use id to the toast-once set before `initSession` replaces the set, so that one in-memory entry is lost (the toast was already shown). |
| N19 | LOW | - | LOW (AGY N4) | CONFIRMED; by design, disclosed | A segment holding an Agent request whose `agent.spawn` never completes or is denied is never evicted from memory. |
| N10 | INFO | INFO | - | CONFIRMED | The plugin API is early access; coexistence with another plugin's status line is unverified. |
| N14 | INFO | INFO | - | CONFIRMED; by design, disclosed | An explicit absolute `receiptDir` is allowed (subject to the link and directory checks). |
| N15 | INFO | INFO | - | CONFIRMED; disclosed | The 15-mutation sanity check was not re-run after `13ceb5020`, `61c371f28`, `3d2af4b20`. |
| N16 | INFO | INFO | - | CONFIRMED; disclosed | markdownlint NOT_RUN. |
| N20 | INFO | - | INFO (AGY N5) | CONFIRMED (as to what AGY received) | AGY's copy of the prompt was truncated at the tail (`<truncated 2662 bytes>` after about line 99 of `receipt.schema.json`); our prompt was intact. |

Totals (union): 9 findings: 1 HIGH, 3 LOW, 5 INFO; none BLOCKING.

## Disagreements
- Q3: Grok PASS, AGY UNKNOWN (input truncated on AGY's side). No other question differs.
- Findings raised by one auditor only: N17, N18, N19, N20 (AGY); N10, N14, N15, N16 (Grok). Both raised N1 at HIGH.
- Identity: Grok's answer says `grok-4`, the CLI was run with `-m grok-4.5` and every init event shows `grok-4.5` (R4 saw `grok-4.7`): UNRESOLVED. AGY's answer says `unknown`. Provider attestation UNKNOWN for both.

## How the R4 findings fared
Neither auditor re-raised any of the R4 findings that the claims file lists as repaired or changed (N2-N5, N8, N9, N11-N13, O1-O5). Both answered Q12 PASS and cited the code and the pinning tests for each repair item and for the three later fixes. N1 (no live session) and N10 (API early access, status-line coexistence) are the carried findings, not repaired in code. The new findings (N17, N18, N19) are LOW, bounded, and the first and third are described in the docs or the R5 notes.

## Operator steps per finding
- **N1** (HIGH): the live check on the frozen head: `claude --plugin-dir plugins/dopemux-route-ledger --setting-sources user` with `.control-tower/state` present; one pinned advisor-calling child, one clean pinned child, one unpinned Agent call (an 8 s toast), `/route-ledger`, `/route-ledger receipts`, a `/clear` (note whether the session id changes), and, with a symlinked relative `receiptDir`, whether receipts turn off.
- **N17** (LOW): accept, or make the command handlers call `ensureReady`.
- **N18** (LOW): accept, or add the id to `s.toasted` only after `ensureReady`.
- **N19** (LOW): accept (disclosed), or expire unjoined requests when `agent.spawn` is denied.
- **N10, N14, N15, N16** (INFO): accept as disclosed; N10 is cleared by the live check with dopemux-pulse enabled.
- **N20** (INFO) and the partial corroboration: decide whether to accept the AGY leg as partial corroboration, or ask for a new AGY run on a shorter prompt (new package revision, new operator line). Any code change to N17-N19 would be a semantic change that invalidates both audits and needs a new audit.

## What the audits do not cover
- Neither auditor ran the code or the tests: both judged the diff text. Both asked for the live session, the declaration file, the mutation re-run and markdownlint, all NOT_RUN.
- AGY cannot be made tool-less (60 built-in tools in the init event); its containment rests on the session-only settings and the stream gate, and the stream shows only `user_input` and `agent_response` steps (evidence, not proof). Exact-model evidence for the schema-required `gemini-3.1-pro-high` is unavailable: the proof records `auditor_tool: agy`, `auditor_model: gemini`, and PR Steward may not treat that as READY.
- The three Codex review threads (4425125083, 4425202528, 4425202538) are answered in code and replied to but unresolved on GitHub; resolving them is the operator's.
