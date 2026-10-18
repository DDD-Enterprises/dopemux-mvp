# MACRO-DMX-CMD-REPAIR-001 — Aggregate Return 02 (supersedes RETURN-01's blocker)

**Status**: `PARTIAL_BLOCKED`. All five workstreams are implemented, committed and locally validated. The head is frozen. The single final independent audit was NOT run: the audit route is blocked (below).
**Authority**: NONE. This aggregate mints no PASS/READY/DONE.
**Recorded**: 2026-10-16 ~20:45Z, coordinator turns on `claude-sonnet-5-5` (the operator selected it in the model menu after RETURN-01).

## Frozen subject

- **Branch / worktree**: `fix/cmd-repair-001` at `.worktrees/cmd-repair-001`.
- **Head**: `70eb50363f2cb1ff59758a9321faf9d033684b40`.
- **Base**: `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (fresh `origin/main` at start).
- **Size**: 5 commits, 48 files, +368/−104. The diff's sha256 is `3ed3a84060ece85437cc68f99c46dc9378c473c77b18d237cab046ea62a253cc`.
- **Not pushed**: no PR, no merge.
- **Not in the branch**: the issuance package (`proof/MACRO-DMX-CMD-REPAIR-001/review_bundle/`) is still untracked in the main checkout.

| Commit | WS | Files | Model (requested → observed) | Advisor |
|---|---|---|---|---|
| `55e4f6cad` | W01 ConPort/FTS names | 18 | haiku-5-5 → haiku-5-5 | 0 |
| `b0c505489` | W03 dead targets | 5 | sonnet-5-5 → sonnet-5-5 | 0 |
| `08130eb5c` | W02 model pins | 26 | haiku-5-5 → haiku-5-5 | 0 |
| `9c93afbb7` | W04 drift-gate test | 1 | sonnet-5-5 → sonnet-5-5 | 0 |
| `70eb50363` | W05 fleet snapshot (AMENDMENT-01) | 1 | sonnet-5-5 → sonnet-5-5 | 0 |

- **Observed model** is the `message.model` in each child transcript. Effort is `runner-default` and observed UNKNOWN.
- **Coordinator turns**: Opus 5.5 from start through the W04 return, Sonnet 5.5 from W05 on. The override was unrealized until the operator switched.
- **W05 amendment**: authorized in chat. Its packet sha256 is `e7886743058c07625cafec13d97b08f69b335a23789fd0cc8d71e4151f87caca`, at `AMENDMENT-01/WORKSTREAMS/W05/TASK_PACKET.json`. The six pinned members are unchanged.
- **Forbidden git**: none mutating.

## Validation on the frozen head

| Check | Result |
|---|---|
| Dead-name gates (`conport_[a-z]`, `_fts\b`, dead targets), stale-pin gate | PASS |
| `pytest tests/arch -q` | PASS: 195 passed (W04's 11 tests included) |
| W04 base-tree negative control | PASS as a control: violation counts 25 / 0 / 26 / 3 for checks 1 / 2 / 3 / 4 |
| `validate_change_contract.py --base origin/main --head HEAD` | PASS, exit 0; all 50 paths L2, no L3 |
| Per-workstream commit vs. allowlist | PASS: W01 18/18, W03 5/5, W02 26/26, W04 1/1, W05 1/1 |
| `git diff --check` | PASS |
| `pre-commit run --from-ref origin/main --to-ref HEAD` | PASS (hooks with matching files: preflight, deprecated-memory-backend, md-location, docs-filename audit, root-hygiene) |
| black / flake8 on the new test | PASS / PASS |
| black / flake8 on `fleet_catalog.py` | not clean at base (142 E501 before and after); no new finding in the edited block |
| Full `make test` | NOT_RUN |
| Live ConPort runtime qualification | NOT_RUN (July 2026-07-16 capture is historical; server source agrees) |
| **Final independent audit** | **NOT_RUN (route blocked)** |
| §9 proof bundle | NOT_RUN (no audit) |
| `ct return-pack` | NOT_RUN |

Pre-existing note: Pyright flags lines 856 and 1353 of `fleet_catalog.py`. They are outside the edited block.

## Audit route blocker (precise)

- **Requirement**: `docs/ops/embedded-audit.md` Tier 1 route 1 is AGY with Sonnet or the exact model `gemini-3.1-pro-high`. The proof must record `auditor_tool: agy` and `auditor_model: gemini-3.1-pro-high` (schema enum), and the model must be proven by list or help evidence. The doc says: "Do not infer a model from branding. If model or invocation cannot be proven, use the next route or record SKIPPED."
- **Observed**: `agy` 1.3.6 at `/Users/hue/.local/bin/agy`. `agy models` lists Gemini 4 Argon (low/medium/high), Gemini 3.8 Flash, Claude Opus 5.5, Claude Sonnet 5.5 and GPT-OSS 120B. **`gemini-3.1-pro-high` is not available.**
- **Why not other routes**:
  - **AGY + Sonnet 5.5** is the same family as the implementers, so it fails the packet's `auditor_independence: DIFFERENT_FAMILY` and the launch file's "different-family".
  - **Claude Code CLI Sonnet/Opus** (routes 2–3) fail for the same reason.
  - **Gemini 4 Argon via AGY** is not an enum-valid `auditor_model`. Only the generic `gemini` is allowed, which the docs call not a substitute for exact-model evidence.
  - **Gemini CLI / PAL clink / Copilot** need a credential or fallback the packet doesn't grant. The packet allows no fallback, and a packet-specific fallback auditor needs a recorded supervisor approval.
- **Not attempted**: no auditor call of any kind, no probe, and no data left the machine.

## Decision needed (operator)

Pick one:
1. **Approve a packet-specific fallback**: `agy --model gemini-4-argon-high --print …`.
   - **Why it fits**: Google family, so different from Claude. Same already-authorized AGY tool.
   - **Input**: the frozen diff only (42 KB, scanned: no secrets) plus the audit contract; no repo mount.
   - **Proof**: recorded as `auditor_tool: agy` with `auditor_model: gemini`, flagged "exact-model evidence unavailable, operator-approved fallback". Expect the verdict to be advisory for PR Steward because the model enum isn't the exact one.
2. **Wait** for `gemini-3.1-pro-high` to return to AGY, or choose another route.
3. **Stop here**: keep the branch with the audit NOT_RUN.

## Remaining work after a route is chosen

Audit → proof bundle (`proof/MACRO-DMX-CMD-REPAIR-001/`) → copy the issuance package into the branch → final return. Push, PR and merge stay operator gates.

## Residual uncertainty

- **Live ConPort**: whether the running server on :3005 still matches the July capture (NOT_RUN).
- **W01 semantics**: `update_context` patch-versus-replace is UNKNOWN. Custom-data search now goes through `get_custom_data`, with recall unverified live.
- **Docs mismatch**: `docs/02-how-to/mcp-integration-guide.md:165-167` still describes the old snapshot. It is out of every allowlist; a follow-up item.
- **Out of scope** (from the issuance record): duplicate-command consolidation, plugin packaging, the `/dx:plan-enter|plan-exit` port, pal naming, `.claude/claude.md` references, and `ccr_model_tracker.sh`.

## Closure

- **Children**: all 5 completed. No running processes and no `agy` run.
- **Custody**: the worktree and branch are retained, with a clean tree and no stash entries.
- **Main checkout**: untouched, still dirty with another actor's edits. Checkpoint `01a13db3` and audit `01a14638-0128` files untouched.
- **Quota**: weekly usage was 99% at the last read (resets 2026-10-16T22:59:59Z); extra usage OFF.

## Rollback

```bash
git worktree remove .worktrees/cmd-repair-001
git branch -D fix/cmd-repair-001
```

Branch deletion is an operator-only gate. Alternatively, revert any single commit above.
