# MACRO-DMX-ROUTE-LEDGER-001-R4 — Issuance Record (retarget of the final audit round)

**Issued**: 2026-10-30 by the Control Tower supervisor session for this worktree (Claude Code desktop, `claude-sonnet-5-5` per the session's system prompt; observed identity needs a runtime receipt), started by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`.
**Status**: ISSUED, NOT EXECUTED. Authority NONE. Nothing in R4 was run, sent to an auditor, signed, pushed or merged. The package is untracked under `task-packets/`.
**Supersedes R3** (`../MACRO-DMX-ROUTE-LEDGER-001-R3/`, preserved unchanged, 12 hashes re-verified). R1 and R2 are also preserved unchanged.

## Why a new revision

The operator was asked "Which way should the merge train go?" and answered, verbatim, **"Run it in order"** (PR 1482 first, then 1483, 1485, 1484), relayed by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`. The relaying session read that as including a retarget of this audit: `main` requires up-to-date branches and a signed proof binds to the audited head, so an audit of `4fcdc9761` alone is stale before it finishes (merging `main` afterwards fails proof-only closure with `proof_only_escaped_path` and forces another audit). The subject therefore had to include current `main` as a merge commit, not a rebase. The relay authorizes nothing the packet gates on a literal operator line, so **R4 needs its own gate line** (below).

## What happened to R3 (facts)

| Step | Result |
|---|---|
| R3 gate line | typed verbatim by the operator 2026-10-30; covers R3 (subject `4fcdc9761`) only |
| W01 inputs | done by a Sonnet child (0 advisor blocks, 0 Agent calls, 35 tool uses, 131,633 tokens, 2.9 min active), verified, corrected by the coordinator, committed `c02748b05` |
| W02 Grok (grok-cli 1.0.70, grok-4.5, tool-less) | ran ONCE on `4fcdc9761`: exit 0, `init.tools == []`, 0 tool_use, 124 s, USD 0.0555 (probes 0.0283). Custody `4b8838cf3`. **The verdict is UNREAD** and unused |
| W03 AGY (agy 1.4.11, gemini-4-argon-high) | probes clean; the one real attempt was stopped by the coordinator at 09:34:56Z on the retarget (`error: interrupted`), no verdict. Custody `ad8a141c6` |
| Retarget | the operator's relayed decision above |

R3's spend is **sunk cost, not R4 budget**: Grok USD 0.0839, about 26k AGY probe tokens, the stopped AGY run unmeasured.

## The new subject (done by the coordinator on the relayed decision; local, unpushed)

| Item | Value |
|---|---|
| Frozen subject (merge head) | **`989fe4651c050ec23619e5208da17d6152b477b0`** on `claude/route-ledger-001-8d8032` |
| Parents | `ad8a141c6a88ce05f865fb7d26d84ce0beeb4137` (the R3 custody head, which contains the repair commit `4fcdc9761`) and `97b6d5040496e2271c41d24c339d039303bbe6b1` (`origin/main`, PR 1472 merged 2026-10-30T08:59:28Z) |
| How | the app's `sync_with_base_branch` tool: a true two-parent merge commit, no rebase, nothing pushed; PR 1482 reported `BEHIND` before and the branch is 0 behind main now |
| The seven audited content paths | **byte-identical to `4fcdc9761`** (`git diff` empty); `main` changed 96 files since the branch base and none of the seven |
| Diffs against the new base | cumulative (`git diff 97b6d5040 989fe4651 -- <7 paths>`) and delta since the R2 audit are **byte-identical** to R3's frozen diffs, so the audit prompt body stays valid |
| Gates on the merge head (run by the coordinator) | plugin tests 55 of 55 PASS; `claude plugin validate` PASS with warnings; in-tree `tsc` exit 0; change contract PASS, lane L2, `proof_only=False` (77 paths) |
| Unrelated local edit | `.codex/config.toml` (an env-injection block of workspace ports and IDs) blocked the merge tool; it was backed up byte for byte (sha256 `8f7860cf...`), reverted for the merge, and restored exactly (hash re-checked). Never committed |
| Rollback of the merge | reset the local branch to `ad8a141c6` (the first parent); PR 1482 on the remote is untouched at `b0b802617` |

## Workstreams and TP_ROUTE (serial; one writer per workstream)

| WS | What | Executor | TP_ROUTE (runner, model, effort) | Fallback |
|---|---|---|---|---|
| W01 | Verify the pin, run the deterministic gates, byte-exact diffs (cmp to R3), derive the prompt from R3's corrected prompt by exact single-occurrence substitution, scan, hash, commit | coordinator script, **no model dispatch** | `claude-code-desktop`, `claude-sonnet-5-5`, `high` | none |
| W02 | PRIMARY audit: sealed dir, 2 probes (`init.tools == []`), 1 attempt, verdict-blind custody commit | coordinator shell | `grok-cli`, `grok-4.5`, `high` | none |
| W03 | CORROBORATING audit: model list check, 2 probes, sealed run with **session-only request-review hardening**, 1 attempt, verdict-blind custody commit | coordinator shell | `agy`, `gemini-4-argon-high`, `high` | none |
| W04 | Read both verdicts, adjudicate every finding against source, stricter-outcome rule, unsigned `PROOF.json`, `AUDITOR_REPORT.md`, ledger, flattened package | coordinator | `claude-code-desktop`, `claude-sonnet-5-5`, `high` | none |

The operator confirmed both coordinator readings from R3 in this session: Argon tier `gemini-4-argon-high` and **Grok primary** (its verdict becomes `embedded_audit`), AGY corroborating. Verdict rule, failure semantics and allowances are the R3 ones with these changes:

## What changed from R3

1. **Subject**: the merge head above instead of `4fcdc9761`; diff base `97b6d5040` instead of `93050d135` (same bytes).
2. **W01 is no longer a child dispatch.** R3's child authored the prompt; R4 only substitutes the head, counts and a merge disclosure, which a script does exactly. That is the cheapest adequate route and makes macro child dispatches 0 (the substitution list is in W01's invariants; any anchor that does not match exactly once is a STOP).
3. **AGY hardening is now explicit in the packet** (it was a coordinator refinement in R3): your SAVED agy settings are `toolPermission=always-proceed` and `allowNonWorkspaceAccess=true` with an allow list including `git commit` and `gh`; agy exposes 60 built-in tools and 11 global MCP servers and cannot be made tool-less. Every AGY run uses `--settings '{"toolPermission":"request-review","allowNonWorkspaceAccess":false,"permissions":{"allow":[]}}'` (session-only, never saved), `env -i HOME PATH` and a sealed cwd; the init event must report `permission_mode = request-review` or the run stops before sending the audit prompt. The packet forbids `agy mcp disable` and any edit to agy or gemini settings: your global configuration is not touched.
4. **Main-moved guard**: a fresh `git fetch origin main` that shows anything other than `97b6d5040` stops the macro (the subject would need another retarget).
5. **Allowances** reset for R4 (child dispatches 0; same audit caps: 1 attempt per route, probes <= 3 Grok / <= 2 AGY, wall <= 20 / 30 min, Grok cost <= USD 0.30). Two final audits remain the operator-ratified exception, **re-ratified by the R4 gate line**.

## What the operator still has to provide

1. **The R4 gate line** (verbatim, below). The R3 line does not cover a new subject, the merge, or the AGY hardening.
2. **Your acceptance of the local merge commit `989fe4651c`** that I made on the relayed decision (local, unpushed, rollback above). If you would rather it not exist, say so before the gate and I re-pin.
3. **The AGY residual**: the R4 AGY token accepts that agy runs with 60 tools and 11 global MCP servers present, contained by session-only `request-review`, the sealed cwd and the stream gate (only `user_input` and `agent_response` steps are admissible).
4. **R3's unread Grok verdict**: default is that it stays unread and unused; tell me if you want it read as information after the R4 adjudication.
5. After the audits (operator-owned, unchanged): attest independence, sign (I can draft a dry-run `sign-route-ledger-r4.sh` modelled on `sign-pulse-r2.sh`, never run by me), push, and the draft-to-ready and merge decisions. PR 1482 stays at `b0b802617` on the remote until you push.

## Operator gate (execution starts only after you type this verbatim in chat)

```
AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R4_EXECUTION=YES AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R4_AUDIT_ROUTE_GROK_CLI_GROK_4_5=YES AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R4_AUDIT_ROUTE_AGY_GEMINI_4_ARGON_HIGH=YES
```

The R1, R2 and R3 lines do not authorize R4. The line authorizes exactly the hashed routes in this package: subject `989fe4651c050ec23619e5208da17d6152b477b0`, one attempt per route, zero retries, no fallback.

## Open risks (unchanged unless noted)

| Risk | State |
|---|---|
| AGY exact-model evidence | UNAVAILABLE for `gemini-3.1-pro-high`; Argon is a stated operator-approved route; recorded as `auditor_tool: agy`, `auditor_model: gemini`; the steward may not treat it as READY |
| AGY containment | relies on session-only request-review plus the stream gate, not on removing tools (see change 3); the model's own tool list is a claim |
| Route availability | quota and auth of both routes UNKNOWN at issuance (Grok and AGY both answered today; AGY returned 429 on 2026-10-21) |
| CLI drift | grok 1.0.70 and agy 1.4.11 today; both versions are recorded at run time (agy updated itself between two checks today) |
| Independence | prior findings are given as claims, so neither audit is blind (operator decision) |
| Merge in the subject | the audit judges the seven files only; main's 96 files are outside the change set and the prompt says so |
| Not run | a live session on the repaired code, the `markdownlint` hook (Node env cannot install on this host; CI covers it), DCP and Task Orchestrator |
| Untracked `plugins/dopemux-route-ledger/tsconfig.json` | engine-laid, extends a gitignored file: never committed |

## Package members

The macro pins the coordinator binding, each TASK_PACKET and (through `base_policy`) `ALLOWANCES.json`. Child bindings are listed for the record and are not pinned.

| Member | SHA-256 | Pinned by macro |
|---|---|---|
| `MACRO_PACKET.json` | `8099340c653faed72e0e96632234748dbf392f910740c1125916a6413c62af10` | n/a (the subject) |
| `EXECUTION_BINDING.json` (coordinator) | `cfaf3ca97494fb7820337464fe8c639729e53c8c0f980e335467730bfc2694c5` | yes |
| `ALLOWANCES.json` | `8935893413be3a0a11b5c49eb5f0957d26150acd8dec0abb291623e5efb4d8d5` | yes (base_policy text) |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `79ae04f581b0b0ba49fb2b0b4d75cdac2854c08673137a46ae0637299a7c99d8` | yes |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `73bc83866f261f20a4fa37b9d5bdb23d060db692cad395150c9b6f6818bdb2dc` | yes |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `d64f671e97789b527d6475c5d1371ba29f05e89bc2265a75c5c458661732372c` | yes |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `ebebcef29b9af7a35032bb3f6b89552a0ff012f73ab22c460fa744c9d556b909` | yes |
| `WORKSTREAMS/W01/EXECUTION_BINDING.json` | `628f357b128b91672a72bf8ede9cc1a6facfd174a74c5e7714b9902f6f7c6e9b` | no |
| `WORKSTREAMS/W02/EXECUTION_BINDING.json` | `fa042a81a76a48a3bfb7ecedd2b779b9d945783395eafd9dc54af44f16c4b924` | no |
| `WORKSTREAMS/W03/EXECUTION_BINDING.json` | `1d02859db5785eefaafdd8236ef433290e2d831cca9bdac0097432624b9053f5` | no |
| `WORKSTREAMS/W04/EXECUTION_BINDING.json` | `9d9194b58818425fdd8ba693dcbb4c04f9b8ca54e062b698be39aab0f108c4f4` | no |

This file is not referenced by the macro and is not part of the pinned subject.

## Validation of this package

| Check | Result |
|---|---|
| `ct validate-macro` | PASS: `STATIC_VALID`, 0 errors |
| `task_packet.v2` schema (local registry), W01-W04 | PASS x4 |
| `ct bind-record` then `ct validate-binding`, coordinator and W01-W04 | PASS x5 (authority NONE) |
| Every own-identity field (macro id, workstream ids, audit group, write surfaces) | R4 (checked with jq); R3 mentions are only references to R3's files and gate line |
| R1, R2, R3 packages re-hashed | identical (R3: 12 of 12) |
| Any R4 workstream, auditor run, send, commit, push | NOT_RUN |
| DCP route, Task Orchestrator state | NOT_RUN |

## Execution outline (after the gate)

1. W01 (coordinator): fresh fetch, pin and parents check, deterministic gates, diffs cmp-equal to R3, derive the prompt by exact substitution, scan, hash, write `SUPERSEDED_R3_NOTE.md`, commit.
2. W02 (Grok, primary): probes, one attempt, custody commit. W03 (AGY, corroborating, hardened): version and model checks, probes, one attempt, custody commit. No verdict read yet.
3. W04: read both, adjudicate every finding against source, stricter-outcome rule, unsigned proof, validation with explicit heads (only `proof_only_missing_signature` may remain), commit, STOP and report.
4. The operator tail is unchanged: attest, sign, push, ready, merge are yours.
