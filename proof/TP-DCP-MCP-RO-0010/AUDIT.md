# TP-DCP-MCP-RO-0010 Embedded Audit

**Verdict: PASS_WITH_RISKS** (all risks non-blocking; enumerated below).

Auditor: Claude Code Opus (independent of the Claude Sonnet subagent that
implemented the code). Codereview provider note: PAL external codereview was
attempted on `gpt-5-codex` (OpenAI **401 invalid key**) and `gemini-2.5-pro`
(Google **429 quota=0**) — both providers unavailable this session, so the
external-model codereview is recorded **NOT_RUN (infrastructure)**. The native
`advisor()` second-opinion was used as the governed fallback and validated the
four design questions below.

## Scope Check

Implementation commit `1f420929b` touches only allowlisted paths
(`services/dcp-readonly-facade/**`, `docs/03-reference/dcp/chatgpt-mcp-readonly/**`,
`task-packets/.../TP-DCP-MCP-RO-0010.*`, `proof/TP-DCP-MCP-RO-0010/**`) — verified
via `git show --name-only`. Audit-hardening changes (this reviewer) touch only
`registry_v2.py`, `resolver_core.py`, the duplicate fixture, its test, and
`REGISTRY_V2_CONTRACT.md`. The v1 `registry.py`/`resolver.py` are untouched
(evolved alongside, not replaced). No `src/**`, other `services/**`, `docker/**`,
`.env*`, or `.dopemux/**` were touched. The pre-existing dirty
`.claude/claude_config.json` (hook artifact, present before this session) was
deliberately excluded from all commits.

## Contract Fidelity (ADR-DCP-MCP-RO-0009) — verified by reading + tests

- Exactly the 9 ADR service families; the bare name `task-orchestrator` is in
  `FORBIDDEN_FAMILY_NAMES` and rejected at target level (fail-closed whole target).
- `FAMILY_POLICY_TABLE` encodes (resolution_class, chatgpt_posture) matching the
  ADR posture table; it carries no live/callable knowledge.
- `PRIMARY_CHECKOUT_ONLY` is the only accepted `binding_mode`; the resolver never
  enumerates sibling/newest worktrees.
- Capability separation: `capability.py` reports `configured` distinctly from
  `live` (always `"UNKNOWN"`) and `callable` (always `False`). Configured never
  implies callable.
- `target_id` is the only caller handle; block reasons are short and opaque (no
  absolute path / port / URL leakage — `validate_workspace`'s raw error is
  intentionally discarded).

## Purity / Determinism — verified

- `generation` is a `sha256` content hash (`_generation`), no timestamps/random.
- `_derive_roots` reads `.git` (dir vs gitfile) and `commondir` directly — **no
  `git` subprocess, no network, no sockets, no container inspection**. Purity scan
  of the three new modules returns no real I/O primitives (only the literal
  family name `docker_mcp_gateway`).
- Full facade suite passes with **no backend service running** (187 passed, 1
  pre-existing live-optional skip) — determinism demonstrated.

## Real-World Verification — VERIFIED vs REASONED (honest distinction)

- **VERIFIED (executed on genuine metadata):** `_derive_roots` run against *this
  actual linked worktree* returns `project_root=/Users/hue/code/dopemux-mvp`,
  `worktree_root=<this worktree>` — the highest-risk logic is correct against a
  real `.git` gitfile + `commondir`, not only fixtures.
- **REASONED (not executed):** submodule (`.git`→`modules/<n>`, no `commondir`)
  and symlinked-`.git` layouts. Both **fail closed** by construction (missing
  `commondir` → `(None, None)` → block); worst case is a false block, never a
  wrong-repo bind. Not exercised live — flagged as reasoned.

## Audit Hardenings Applied (post-implementation, this reviewer)

1. **Duplicate `target_id` now fails closed** (was keep-first + warn). A duplicate
   is an ambiguous exposure-consent binding; per ADR invariant "Ambiguity blocks"
   the id is now poisoned — the already-accepted entry is removed and no later
   entry can revive it, so the id resolves to nothing. Test + fixture + contract
   doc updated.
2. **Stray v1 `projects` key alongside v2 `targets`** now records a drift warning
   instead of silently ignoring the remnant.
3. Cosmetic: unused `_err` → `_` in the resolver (Pyright hint) with a clarifying
   comment on why `validate_workspace`'s error is discarded.

## Residual Risks (non-blocking)

- `project_root` derived here is trusted downstream. **0011 handoff:** the runtime
  join must re-validate per-service project identity and MUST NOT treat a
  `project_root` derived from a poisoned/crafted `.git` gitfile as authority (an
  attacker with write access to an approved workspace's `.git` could point
  `commondir` at another repo). Defense-in-depth belongs at the 0011/0012
  ownership-evidence layer.
- Submodule/symlinked-`.git` derivation is reasoned, not live-tested (fail-closed).
- Secret-scan matches exist repo-wide only in **pre-existing** redaction test
  fixtures and a runbook example; **zero** secrets in any 0010 new file.
- PAL external codereview NOT_RUN (provider outage); mitigated by Opus manual
  audit + `advisor()` second opinion.

## Result

The registry-v2 + pure-resolver-core slice is deterministic, fail-closed, and
faithful to ADR-DCP-MCP-RO-0009. No runtime, network, or backend code was
introduced. Acceptable to merge pending operator merge-cadence decision; runtime
join and live ownership remain out of scope (0011/0012).
