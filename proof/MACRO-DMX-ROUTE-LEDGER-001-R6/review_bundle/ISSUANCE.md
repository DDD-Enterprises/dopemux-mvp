# MACRO-DMX-ROUTE-LEDGER-001-R6 — Issuance Record (final audit of the repaired Route Ledger, two routes)

**Issued**: 2026-10-31 by the Control Tower supervisor session for this worktree, drafted on the supervisor's brief by a delegated drafting agent (Claude Code, `claude-sonnet-5-5` per its system prompt; observed identity needs a runtime receipt). The issuing binding records the supervisor route `claude-code-desktop`, `claude-opus-5-5`, `xhigh`.
**Status**: ISSUED, NOT EXECUTED. Authority NONE. Nothing in R6 was run, sent to an auditor, committed, signed, pushed or merged. The working package is untracked under `task-packets/`; the flat copy under `proof/MACRO-DMX-ROUTE-LEDGER-001-R6/review_bundle/` is untracked and is committed by the R6 team lead.
**Relation to earlier rounds**: R4 audited the merge head `989fe4651c050ec23619e5208da17d6152b477b0` on the same two routes; R5 changed the audited code, so the R4 audits and the unsigned R4 proof do not cover this subject. R1 to R5 packages and bundles are preserved unchanged.

## Why a new revision

R4 returned an unsigned proof with 11 findings in union, none BLOCKING. The operator then chose to repair first and R5 changed the audited code: the repair commit `26414fef53df4970e39269a3ba9ed93afd6b8f32` (ten findings) and three later changes that followed review feedback, each with an additive successor note in `proof/MACRO-DMX-ROUTE-LEDGER-001-R5/review_bundle/`:

| Commit | Change | Note |
|---|---|---|
| `13ceb5020` | test-only (CodeQL `js/incomplete-sanitization`) | `SUCCESSOR_NOTE_CODEQL.md` |
| `61c371f28` | Codex P2: `/clear` keeps unwritten receipts until they are on disk | `SUCCESSOR_NOTE_CODEX_CLEAR.md` |
| `3d2af4b20` | Codex P2 x2: a failed `fs.list` fails closed; segment size in UTF-8 bytes | `SUCCESSOR_NOTE_CODEX_LIST_BYTES.md` |

The implementer reports 104 plugin tests passing and `validate`, `tsc` and `diff --check` exiting 0 (claims; W01 re-runs every gate and records them in `GATES_PRE_AUDIT.txt`). Each later change is a semantic change after R5's own verification, so the subject for the final audit is the branch head after the last note: `b275543fe1011bf3a9351a10448c24d94f205370` (PR 1482; `origin/claude/route-ledger-001-8d8032` pointed at it when this package was drafted).

## The operator's route choice (recorded verbatim, 2026-10-31; the full sequence)

1. **Earlier typo and first question.** The operator's typo "grij akibe, go" had been read by the implementer session as "Grok alone". Asked **"Should #1482's R6 audit run on Grok alone (one attempt, no retries, no fallback)?"** the operator answered **"AGY (Gemini)"**.
2. **Implementer report.** The implementer session then reported that the operator had written **"11,,  bbootthh"** in Route Ledger's session, which it read as **"1, both"**.
3. **Second question and the answer that governs.** Asked **"For #1482's R6 audit you chose AGY here, but wrote what reads as '1, both' in Route Ledger's session. Which route should the packet seal?"** the operator answered **"Both: Grok + AGY"**.

Answer 3 GOVERNS. R6 seals BOTH routes in the R4 shape: `grok-cli` `grok-4.5` as PRIMARY and `agy` `gemini-4-argon-high` as CORROBORATING, one attempt each, zero retries, no fallback and no promotion of one route to replace the other. Answers 1 and 2 are kept for history and are superseded. The earlier decision to give the auditors the previous findings as untrusted claims still applies.

## The subject

| Item | Value |
|---|---|
| Frozen subject | **`b275543fe1011bf3a9351a10448c24d94f205370`** on `claude/route-ledger-001-8d8032` (PR 1482), one parent `3d2af4b209dfc1fb703f82658a0c3a35cd804814` |
| Diff base | `97b6d5040496e2271c41d24c339d039303bbe6b1` (origin/main; unchanged since R4, re-checked by W01 with a fresh fetch) |
| Earlier audited head (R4 subject) | `989fe4651c050ec23619e5208da17d6152b477b0` (ancestor of the subject) |
| Content paths | the same seven as R4: the plugin manifest, `hooks/hooks.json`, `hooks/register.tsx`, `hooks/register.test.ts`, `receipt.schema.json`, the plugin README and `docs/02-how-to/route-ledger.md`; the drafter's filtered `git diff --name-only` found no other path |
| Cumulative diff (base..subject, seven paths) | 165525 bytes, sha256 `90b53907b50f690f9b551b8795251167dcdcffaaa057358b253141aad606ab71` (drafter-measured, read-only); embedded in the prompt |
| Delta since the R4 audit | 102347 bytes, sha256 `4ea3c97a9040bd7908d06bf51a02f24752605e9e863151b3db9c2612bed3c862`; six of the seven files change (`hooks.json` does not); kept as the committed artifact `FROZEN_DELTA_SINCE_R4_AUDIT.diff`, **not embedded** |
| Commits | 25 in base..subject, 9 touch the seven files; 13 since the R4 subject, 4 touch them |
| Unrelated local edit | ` M .codex/config.toml`: never committed, never audited |

## Prompt size (supervisor decision, 2026-10-31)

The first draft forecast a prompt far over R4's 160,000-byte limit because the cumulative diff alone is 165525 bytes. Decision: **drop the full DELTA diff section** (the cumulative diff already contains every delta hunk) and replace it with a **DELTA SUMMARY** that W01 generates deterministically (`git log --oneline 989fe4651..b275543fe` restricted to the seven paths, plus `git diff --stat` over the same range); **the limit is 200,000 bytes.** Forecast (an estimate): template head 14,815 bytes (about 17-18 KB after the rewrites) + summary about 1.2 KB + claims section about 5-6 KB + 165525 bytes of diff = **about 191 KB** (range roughly 187-195 KB), under the limit by 5 to 13 KB. If the measured prompt still exceeds 200,000 bytes, W01 STOPs with NEEDS_SUPERVISOR and trims nothing.

## Workstreams and TP_ROUTE (serial; one mutating writer; max_mutating_workstreams 1)

| WS | What | TP_ROUTE (runner, model, effort) | Fallback |
|---|---|---|---|
| W01 | pin check; re-run every gate; byte-exact diffs; deterministic DELTA SUMMARY; REBUILD the prompt builder as a committed script (`build_audit_prompt.py`; R4's was a lost scratch script); derive the prompt from R4's template by anchored substitutions; size, pattern and verdict-text scans; commit | `claude-code-desktop`, `claude-sonnet-5-5`, `high` (the R6 team lead session; deterministic script, no model dispatch) | none |
| W02 | PRIMARY audit: `grok models` must list `grok-4.5`; sealed dir; tool-less recipe (`GROK_DISALLOWED`, no-skills system prompt); two probes with `init.tools == []`; one attempt; verdict-blind custody commit | `grok-cli`, `grok-4.5`, `high` | none |
| W03 | CORROBORATING audit: `agy models` must list `gemini-4-argon-high`; sealed cwd; `env -i HOME PATH`; session-only request-review `--settings`; two probes, mechanical gate, one attempt (`--print-timeout 15m`); verdict-blind custody commit | `agy`, `gemini-4-argon-high`, `high` | none |
| W04 | read both verdicts; adjudicate every finding against source; stricter-outcome rule; unsigned `PROOF.json`, `AUDITOR_REPORT.md`, allowance ledger; verify the flattened package | `claude-code-desktop`, `claude-sonnet-5-5`, `high` | none |

Joins: `J01-INPUTS` (W01), `J02-CUSTODY` (W02, W03), `J03-FREEZE` (all four). Cost-first basis: deterministic local tools for everything mechanical; the cheapest adequate qualified model for the judgment steps; the audits run on the two different-family routes the operator chose. Cost figures are UNKNOWN (no current price evidence). Advisor calls: 0 for every child and the coordinator. Intermediate model audits: 0.

**Grok model id re-check (done at issuance).** R4 ran `-m grok-4.5` (every init event showed `grok-4.5`) and the recorded contained-audit recipe also names `grok-4.5`; they agree. W02 must STOP, with nothing sent, if `grok` cannot select that exact model (`grok models` under `env -i HOME PATH` must list it); no substitution.

## What changed from R4

1. **Subject** moved from the merge head `989fe4651c050ec23619e5208da17d6152b477b0` to `b275543fe1011bf3a9351a10448c24d94f205370`; the delta artifact is `FROZEN_DELTA_SINCE_R4_AUDIT.diff`.
2. **No full delta in the prompt**: a deterministic DELTA SUMMARY replaces it; the prompt limit is 200,000 bytes (R4: 160,000).
3. **The diffs are no longer byte-identical to R3/R4**, so the cmp-to-R3 check is replaced by a double generation, cmp, and a size/hash match against the drafter-measured values.
4. **The prompt builder is a committed script** with a size check before writing, a `--check` mode, and a verdict-text scan (no earlier verdict, auditor name or route may appear in the prompt).
5. **The claims and disclosures are rebuilt** for the repaired code: D6 fails closed on a symlinked state directory; a receipt directory that exists but cannot be listed now turns receipts off; D9 records no description by default; the `/clear` session-id behaviour (D8) is UNKNOWN on the host; the 15-mutation check was not re-run after R5 (its harness is gone); no live-session check (N1); markdownlint NOT_RUN.
6. **Timeouts**: the AGY real-run `--print-timeout` is 15m (R4: 10m; the recorded R4 run took 300 s). The Grok caps (R4 passed no Grok timeout flag) are scaled the same way, x1.5: run <= 15 min, probes plus run <= 30 min; the macro active cap becomes 45 min. This scaling is a drafter judgment.
7. **Allowances** are R4's for both legs, PROPOSED; advisor calls 0 (R4 allowed one coordinator call); final audits 2 (the operator-ratified exception, re-ratified by the two route tokens).

## Operator gate (execution starts only after you type this verbatim in chat; ALL THREE tokens are required)

```
AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R6_EXECUTION=YES AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R6_AUDIT_ROUTE_GROK_CLI_GROK_4_5=YES AUTHORIZE_MACRO_DMX_ROUTE_LEDGER_001_R6_AUDIT_ROUTE_AGY_GEMINI_4_ARGON_HIGH=YES
```

The R1 to R5 lines do not authorize R6. The tokens authorize exactly the routes in this package: subject `b275543fe1011bf3a9351a10448c24d94f205370`, one attempt per route, zero retries, no fallback.

**Residual exposure you accept with the Grok token.** The tool-less recipe exposes no tool (`init.tools == []` is the gate), but the Grok CLI still injects home-level instruction, skill and MCP-server NAMES from `~/.grok/config.toml` (no secret values; R4 saw 156 slash-command names, 143 skill names and 7 MCP server names). The audit prompt (the diff of the seven files) is sent to xAI. Your saved Grok configuration (always-approve, five global MCP servers) is NOT changed.

**Residual exposure you accept with the AGY token.** `agy` cannot be made tool-less: its init event lists 60 built-in tools (including `run_command`, `call_mcp_tool`, `write_to_file`, `search_web`) and 11 global MCP servers are enabled. Containment rests on session-only `--settings` (`toolPermission=request-review`, `allowNonWorkspaceAccess=false`, `permissions.allow=[]`), `env -i HOME PATH`, a sealed cwd and the mechanical stream gate (only `user_input` and `agent_response` steps are admissible); absence of a tool step in the stream is evidence, not proof that no capability was available. The audit prompt is kept in agy's conversation history under `~/.gemini/antigravity-cli`. Your SAVED agy settings are `always-proceed` with `allowNonWorkspaceAccess=true` and an allow list that includes `git commit` and `gh`; they are NOT changed (no `agy mcp disable`, no settings edit).

## Open risks

| Risk | State |
|---|---|
| Prompt size | forecast about 191 KB against 200,000 (see above); a measured overrun is a W01 STOP with NEEDS_SUPERVISOR. Grok and AGY both accept the larger prompt only if their context allows it: UNKNOWN until the probes and the run (R4's prompt was 136,451 bytes). |
| AGY exact-model evidence | UNAVAILABLE for the schema-required `gemini-3.1-pro-high` (no longer listed). The proof records `auditor_tool: agy`, `auditor_model: gemini` plus the invocation; **PR Steward may not treat that as READY.** |
| AGY containment | see the residual exposure above. |
| Route availability | Grok and AGY quota and auth are UNKNOWN until the run (both answered on 2026-10-30; AGY returned a 429 on 2026-10-21). A failure ends that leg with NEEDS_SUPERVISOR; no retry, no fallback, no promotion of the other route. |
| CLI drift | grok 1.0.70 and agy 1.4.11 at R4; both update; versions are recorded before each run. R4's `GROK_DISALLOWED.txt` is the 38-id list; the recorded recipe for a newer CLI lists 45 ids, so the one re-probe rule may add ids. |
| Independence | the earlier findings are given as claims (operator decision), so neither audit is blind to R4. |
| Disclosed implementer limitations | D6, the listing failure, D9, D8, the un-rerun mutation check, no live session (N1), markdownlint NOT_RUN: given to the auditors as limitations and carried into the proof's remaining risks. |
| Not run | a live Claude Code session on the repaired head (N1, the operator's step), the `markdownlint` hook, DCP and Task Orchestrator. |
| Open review threads | three Codex threads (4425125083, 4425202528, 4425202538) are answered in code and replied to but unresolved; resolving them is the operator's, not this packet's. |
| Untracked `plugins/dopemux-route-ledger/tsconfig.json` | engine-laid, extends a gitignored file: never committed. |

## Package members

The macro pins the issuing binding, each TASK_PACKET and (through `base_policy`) `ALLOWANCES.json`. Child bindings are listed for the record and are not pinned.

| Member | SHA-256 | Pinned by macro |
|---|---|---|
| `MACRO_PACKET.json` | `e117ff2985f033ece119f4c0402eee53cc2bfc447876b7c3357974b59d118840` | n/a (the subject) |
| `EXECUTION_BINDING.json` (issuing) | `54c2a8491cebfdaa4eab56bfe4bb8205772848b22f45da23eaced6b465f430bf` | yes |
| `ALLOWANCES.json` | `2749fa37c8425cea7085b96db97c181c90f4a1133829e7960dc492ba71adb20c` | yes (base_policy text) |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `f4a95887760db417bfcee34eeb09f1cc799cc4a4f137a18f5dd9382ebcb2f39a` | yes |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `32cd675557a3c2a0e782315ce86753b3ff99c25619d3fea9fc68673b50fb6284` | yes |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `e53d56e130cfce629976a90be997a2d8ca22ecee07558d79573bd2c5ff08854d` | yes |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `abe9b3de789e8f26ab8073cc70a9e73328fc6a1223cbd48efab32f3cd251db76` | yes |
| `WORKSTREAMS/W01/EXECUTION_BINDING.json` | `b4569ecabc46133fb3d9dbe20a2fcf8e19031b205ede98d4781128951d781d81` | no |
| `WORKSTREAMS/W02/EXECUTION_BINDING.json` | `bbeca351061df1ec5ef80d62bd8fda1b080b17f2612c4af634bf55f62a8dc84b` | no |
| `WORKSTREAMS/W03/EXECUTION_BINDING.json` | `3728fea76e6a70a9febae9004966b54b1bd2921b8bd4f72bf8b5b035119243b0` | no |
| `WORKSTREAMS/W04/EXECUTION_BINDING.json` | `5a6fa98cda025e20b3bfb8e49337f2a30df75e304e653227bc48927e31b67acd` | no |

This file is not referenced by the macro and is not part of the pinned subject. The flat copy carries the same members under `W0N_TASK_PACKET.json` / `W0N_EXECUTION_BINDING.json` names plus `SHA256SUMS_PACKAGE.txt`.

## Validation of this package

| Check | Result |
|---|---|
| `ct validate-macro` | PASS: `STATIC_VALID`, 0 errors |
| `task_packet.v2` schema (local registry), W01 to W04 | PASS x4 (a negative control with `risk_lane` removed FAILS, as it should) |
| `ct bind-record` then `ct validate-binding`, issuing and W01 to W04 | PASS x5 (authority NONE) |
| Macro pins (binding, four task packets, `ALLOWANCES.json` in `base_policy`) | MATCH |
| `shasum -c SHA256SUMS_PACKAGE.txt`; secret scan with word boundaries; `git status` | run after this file was written; results are in the drafter's return |
| Any R6 workstream, auditor run, send, commit, push | NOT_RUN |
| DCP route, Task Orchestrator state | NOT_RUN |

The recorded bindings live in this worktree's gitignored `.control-tower/state/bindings/` only.

## Execution outline (after all three tokens)

1. W01: pin check, gates, diffs, delta summary, builder, prompt, scans, commit. A prompt over 200,000 bytes stops here with NEEDS_SUPERVISOR.
2. W02 (Grok, primary): `grok models`, probes, one attempt, custody commit. W03 (AGY, corroborating, hardened): `agy models`, probes, one attempt, custody commit. No verdict is read until BOTH custody commits exist.
3. W04: read both, adjudicate every finding against source, stricter-outcome rule, unsigned proof, validation with explicit heads (only `proof_only_missing_signature` may remain), commit, STOP and report.
4. The operator tail is unchanged and yours: attest independence, sign, push, readiness, merge, the N1 live check, and the three Codex threads.
