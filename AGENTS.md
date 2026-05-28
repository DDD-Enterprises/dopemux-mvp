# AGENTS.md

## 1. Purpose

This is durable operator-control guidance for Codex and agent-style work in this repository. Act from repo truth, preserve architecture boundaries, execute scoped repo-changing work end-to-end, and never hide `UNKNOWN`.

Repo truth beats docs. Here, repo truth means observed runtime and source truth: runtime code,
config, compose wiring, tests, and active entrypoints. Active Task Packets control the
current execution slice, allowlists, validation obligations, and stop conditions; they do
not make unsupported runtime behavior claims true.

## 2. Truth Order

When sources conflict, use this order:

1. Active Task Packet for the current work slice, for execution control, allowlists, validation obligations, and repo-changing scope.
2. Runtime code, config, compose wiring, tests, and active entrypoints, for behavior claims and implemented system truth.
3. `TRUTH_*.md` if present, otherwise the tracked `docs/03-reference/truth/*` equivalents.
4. `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, and `SYSTEM_*.md` if present, plus tracked equivalents under `docs/03-reference/`.
5. Historical, generated, advisory, exploratory, uploaded, assembled, external, or design docs.

Never let extracted artifacts outrank the runtime they describe. Mark absent or unresolved authority as `UNKNOWN`.
Never let a Task Packet authorize a runtime claim that code, config, tests, compose wiring,
or active entrypoints do not support.

## 3. Default Behavior

- Simple questions: answer directly, cite the evidence used, and do not create process artifacts.
- Non-trivial design, implementation, or repo-changing work: Do not stop at a standalone Task Packet. Create the Task Packet, validate it, execute the scoped work end-to-end, and close with proof.
- Ambiguous work: choose the smallest safe slice that preserves authority boundaries instead of inventing scope.
- Ask only when work is unsafe, impossible, blocked by missing credentials/secrets, or missing a decision that cannot be inferred safely from repo truth.

## 4. Codex End-to-End Default

For implementation or repo-changing work, ChatGPT/Codex must execute this lifecycle by default:

1. Preflight repo identity, remote, branch, status, and markers from the primary checkout.
2. Read required authority files and call out missing authority as `UNKNOWN`.
3. Create a fresh dedicated worktree from the verified base branch.
4. Verify the worktree root, remote, branch, markers, clean status, and that execution is not in the primary checkout.
5. Create a Task Packet before implementation.
6. Validate the Task Packet against `dopetask-canonical-spec.json` when the schema is present; otherwise perform and report a manual schema check.
7. Implement only files in the TP allowlist, in commit-sized slices.
8. After each meaningful slice, run the smallest relevant validation and inspect the diff before continuing.
9. Run codereview before precommit.
10. Run targeted tests, lint, or type checks where relevant; always run `git diff --check`.
11. Run repo pre-commit hooks if configured and safe.
12. Commit only allowed files, push the branch, and open a PR with `gh pr create` when authenticated.
13. Emit proof and remove the dedicated worktree after PR creation when safe.

Do not emit standalone Task Packets as the final deliverable unless the user explicitly asks for only a packet.

## 5. Task Packet Rules

Task Packets must conform to `dopetask-canonical-spec.json` when that schema is available.

Required root fields:
- `id`
- `project`
- `target`
- `repo_binding`
- `series`
- `commit`
- `pr`
- `steps`

Rules:
- Use no undeclared fields.
- Every step must include `id`, `task`, and non-empty `validation`.
- Packets must be repo-bound, series-bound, commit-sized, and verifiable.
- If `execution.agent = "gemini"`, then `pal_chain.enabled = true`.
- Codex minimum chain: `analyze -> planner -> codereview -> precommit`.
- Risky or architecture-sensitive chain: `analyze -> thinkdeep -> challenge -> planner -> challenge -> implement -> codereview -> precommit -> challenge`.

## 6. Architecture Boundaries

- `dopemux`: operator control, CLI, startup, routing, MCP/service coordination.
- `dopetask`: external execution runtime through `scripts/dopetask`; `scripts/taskx` is a compatibility shim.
- PM metadata: Leantime.
- Workflow transitions: task-orchestrator.
- Decisions, progress, and structured context: ConPort.
- Historical receipts and chronicle: dope-memory.
- Code and docs retrieval: dope-context.
- dopecon-bridge routes, proxies, and transports events only; it is not canonical task, workflow, decision, progress, PM, chronicle, or retrieval authority.
- ADHD Engine supports operator state, cognitive-state, recommendations, and hooks only.
- Repo Truth Extractor audits and extracts repo truth only; its outputs are evidence artifacts, not runtime truth.

Agents do not own PM truth. Repo-wide agent runtime authority remains `UNKNOWN` across `services/agents`, `src/dopemux/agent_orchestrator.py`, and `services/task-orchestrator/task_orchestrator/agents` unless a specific runtime path is verified.

## 7. RTE Safety Invariants

For Repo Truth Extractor work, agents must preserve the merged authority-order model and these safety rules:

- Runtime/source truth governs behavior claims. Do not claim RTE behavior unless code, config, tests, compose wiring, active entrypoints, or representative artifacts support it. Task Packets scope execution; they do not authorize unsupported runtime claims.
- Missing source, missing artifacts, missing provider evidence, and absent audit bundles remain `UNKNOWN`. Do not convert `UNKNOWN` into recommendations, findings, implementation claims, or proof.
- Generated audit packs, valuation matrices, Deep Research baselines, extracted truth packs, and external docs are advisory unless runtime/source truth supports them.
- Do not run provider calls, live extraction, live preflight, network/provider validation, or account-specific checks without explicit Task Packet authorization and direct evidence.
- Treat `DPMX_LIVE_OK` and pre-live validation as live-execution boundaries. Do not bypass consent gates or turn blocked runs into permissive behavior.
- Do not include secrets, local credentials, raw tokens, private keys, `.env` values, unredacted provider metadata, or sensitive provider output samples in proof or output.
- Repo Truth Extractor is extraction/audit runtime only. It is not PM authority, memory authority, retrieval authority, provider authority, or replacement source truth.
- Keep follow-on RTE UX packets separated: CLI tone cleanup, validator error-shape cleanup, run-help progressive disclosure, accepted-later work, and deferred items are separate work.

## 8. Local Instruction Surfaces

- `AGENTS.md` is the durable repo guidance for Codex and agent-style repo work.
- `config/instructions/agents.instructions.md` is observed as GitHub Copilot custom-agent file authoring guidance with `applyTo: '**/*.agent.md'`; this file is not proven to govern Codex runtime behavior.
- `.github/copilot-instructions.md` is Copilot-specific guidance and should not be treated as Codex runtime authority without separate evidence.
- `.claude/personas/*.agent.md` files are persona or agent definitions, not proof of a single repo-wide agent runtime authority.

## 9. Proof and Finality

Never say complete or done without evidence. Final confidence must be `VERIFIED`.

Proof for repo-changing work must include:
- TP path and ID
- worktree path
- branch
- repo identity result
- slices completed
- files changed
- validations with exit codes
- codereview status
- precommit status
- commit SHA
- PR URL or exact blocker
- residual risks
- `UNKNOWN`s
- cleanup status

No proof means incomplete.

## 10. Known Dangers

- `dopecon-bridge` exposes broad surfaces that can look authoritative, but it is only bridge/proxy/event transport.
- Task-orchestrator runtime authority is conflicted across `app/main.py`, `task_orchestrator/app.py`, and Docker wiring.
- Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`.
- Agent responsibilities are duplicated across multiple families, and agent authority is `UNKNOWN`.
- `scripts/dopetask` is the observed runtime, but operator naming still drifts through TaskX language.
- MCP and proxy config surfaces are inconsistent in places, including stale port assumptions and missing launch targets.

## 11. Claude-Code Doctrine Alignment

This file is the Codex-facing authority. The Claude-Code-facing companion is `.claude/claude.md`, which embeds a brief governance section and links to the full canonical module at `.claude/modules/shared/governance-principles.md`.

The canonical module elaborates the same Truth Order (§2), proof-and-finality regime (§9), and architecture-boundary discipline (§6) for Claude-Code sessions. It additionally covers:

- inspect-before-edit, minimal correct change, deterministic-systems-first
- canonical writer rules and contract-sensitive surfaces specific to this repo
- validation policy with explicit `PASS / FAIL / NOT_RUN` buckets
- confidence states and communication style
- required final response structure for every substantial response

PAL workflow chain rules remain owned by §5 of this file. The canonical module references §5 — it does not duplicate the chains. If chain rules change, update §5 only; the module link will continue to resolve.

When updating doctrine, keep these three files in sync:

- `AGENTS.md` (this file) — Codex authority, Task Packet rules, PAL chains, proof bundle requirements
- `.claude/claude.md` — Claude-Code-facing summary + non-negotiables checklist
- `.claude/modules/shared/governance-principles.md` — full canonical doctrine, referenced by both

## 12. Orchestrator Operations

Task-orchestrator is the canonical workflow authority per §6 and [`docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`](docs/90-adr/adr-task-orchestrator-as-workflow-authority.md) (accepted). Codex agents drive it through the same MCP surface as Claude Code: 14 tools exposed via the stdio wrapper at `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`.

**Single source of operational truth**: [`docs/03-reference/orchestrator-note-filling-protocol.md`](docs/03-reference/orchestrator-note-filling-protocol.md). This document is the cross-agent protocol — Codex, Claude Code, Copilot, and persona surfaces all inherit from it. Read it before invoking orchestrator MCP tools.

**Codex floor** (what every Codex session must know without reading further docs):

1. The 14 orchestrator MCP tools: `manage_items`, `query_items`, `manage_notes`, `query_notes`, `manage_dependencies`, `query_dependencies`, `advance_item`, `claim_item`, `get_next_status`, `get_next_item`, `get_blocked_items`, `complete_tree`, `create_work_tree`, `get_context`.
2. Every repo-changing TP follows §4 (Codex E2E Default) AND attaches PAL chain artifacts as orchestrator notes per §5.
3. The PAL chain stages (`analyze`, `planner`, `codereview`, `precommit`) map to note keys of the same name. Upsert via `manage_notes(operation="upsert")` as each stage produces output.
4. **The complete-gate is mechanical**: `advance_item(trigger="complete")` on a `type="task-packet"` (or any change-producing schema) FAILS without a `proof-bundle` note filled in the review phase. Per §9 — no proof means incomplete.
5. Set `type` on items at creation (e.g. `type: "task-packet"`) for schema activation. Tag-only items fall through to the `default` schema (proof-bundle gate only).
6. Use the standard note-filling loop: `get_context` → read `guidancePointer` → invoke `skillPointer`'s tool if set → `manage_notes(upsert)` → repeat until `gateStatus.canAdvance: true` → `advance_item`. Full protocol in the reference doc above.

**Authority caveats**:

- Schema config lives at [`.taskorchestrator/config.yaml`](.taskorchestrator/config.yaml). This is a contract-sensitive surface per §6 — Codex must not edit it without explicit Task Packet authorization and a linked ADR.
- The orchestrator MCP wrapper is external (lives outside this repo in `/Users/hue/plugins/dopemux-mission-control/`). Snapshots of the wrapper are committed to [`scripts/external-references/`](scripts/external-references/) for traceability per §6 + §10. Editing the wrapper is not authorized by the repo-bound `AGENTS.md`; treat external-plugin changes as out-of-scope unless the active Task Packet explicitly says otherwise.
- Multi-spawn safety: the wrapper enforces one container per workspace (`--name task-orchestrator-<workspace_id>`). Opening a second Codex (or Claude Code) session on the same project disconnects the first session's MCP. Acceptable for single-operator-per-project use; documented at [`scripts/external-references/README.md`](scripts/external-references/README.md).

**Discovery sequence for a fresh Codex session**:

```
1. get_context()                                    # health-check: what's active, blocked, stalled?
2. get_next_item(includeAncestors=true, limit=3)    # what should I work on?
3. get_context(itemId=<chosen>)                     # full state: schema, gate, missing notes, guidance
4. (work according to the protocol document)
```

Standalone Task Packet emission is not the final deliverable per §3 — Codex must execute work end-to-end through this orchestrator surface and emit the proof bundle (§9) on completion.
