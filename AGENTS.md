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
- Stage-based dev-workflow model routing: see config/ai/model-routing.policy.yaml §AUTHORITY for scope and relationship to PAL chain, LiteLLM proxy, and RTE extraction routing.

## 6. Architecture Boundaries

**Memory Trinity (accepted ADR law, 2026-06-19):** ConPort, dope-memory, and dope-context are distinct canonical planes. Cross-plane projection is allowed; cross-plane canonical overwrite is forbidden. See `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md` and `.claude/modules/shared/memory-trinity-routing.md`.

- `dopemux`: operator control, CLI, startup, routing, MCP/service coordination.
- `dopetask`: external execution runtime through `scripts/dopetask`; `scripts/taskx` is a compatibility shim.
- PM metadata: Leantime.
- Workflow transitions: task-orchestrator.
- Decisions, progress, and structured context: **ConPort** (Memory Trinity plane 1).
- Historical receipts and chronicle: **dope-memory** (Memory Trinity plane 2).
- Code and docs retrieval: **dope-context** (Memory Trinity plane 3; read-only retrieval, never canonical writer).
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

### 9.1 Embedded Audit

Governance, process, schema, prompt, proof, and authority-boundary packets require an embedded audit before final readiness — see `docs/ops/embedded-audit.md`. `SKIPPED`, `FAIL`, `NEEDS_SUPERVISOR`, malformed/stale proof, or head mismatch blocks readiness.

- Claude Code CLI (Sonnet, then Opus) is a valid Tier-1 auditor route; Codex is forbidden as a formal auditor.
- A Claude Code session may run the audit locally against the diff and author the proof — see the runbook's "Local Claude Code / CLI route (pre-PR)". Precedent: `proof/TP-DCP-MCP-RO-0008`.
- Proof: `proof/<PACKET_ID>/PROOF.json` (`embedded_audit` per `schemas/proof/embedded_audit.schema.json`) + `AUDITOR_REPORT.md` + `review_bundle/`; validate with `scripts/audit/validate_audit_proof.py`.
- A pre-PR local audit leaves the PR-scoped `pr-steward gate --audit-proof` `NOT_RUN` (1-hour TTL + PR-head match); regenerate and re-pin the proof to the PR head before the FINALIZATION gate.

## 10. Known Dangers

- `dopecon-bridge` exposes broad surfaces that can look authoritative, but it is only bridge/proxy/event transport.
- Task-orchestrator runtime authority is conflicted across `app/main.py`, `task_orchestrator/app.py`, and Docker wiring.
- Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`.
- Agent responsibilities are duplicated across multiple families, and agent authority is `UNKNOWN`.
- `scripts/dopetask` is the observed runtime, but operator naming still drifts through TaskX language.
- MCP and proxy config surfaces are inconsistent in places, including stale port assumptions and missing launch targets.

## 10. Claude-Code Doctrine Alignment

This file is the Codex-facing authority. The Claude-Code-facing companion is `.claude/claude.md`, which embeds a brief governance section and links to the full canonical module at `.claude/modules/shared/governance-principles.md`.

The canonical module elaborates the same Truth Order (§2), proof-and-finality regime (§8), and architecture-boundary discipline (§6) for Claude-Code sessions. It additionally covers:

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

## 11. OpenCode Auto-Load Behavior (2026-06)

OpenCode does **not** behave like Claude Code regarding instruction files.

**What OpenCode automatically reads:**
- `AGENTS.md` in the project root
- `~/.config/opencode/AGENTS.md` (global)
- Files listed in the `"instructions"` array inside `opencode.json` or `opencode.jsonc`

**What OpenCode does NOT automatically read:**
- `CLAUDE.md` (unless explicitly listed in `"instructions"`)
- Arbitrary files under `~/.claude/` (e.g. `~/.claude/PAL_OPENCODE_GUIDE.md`)
- `CLAUDE.local.md` or similar Claude-specific files

**Rule for this repo:**
- All OpenCode-specific guidance (including PAL tool usage rules) must be placed in one of:
  - `AGENTS.md`
  - A file referenced via `"instructions"` in `opencode.jsonc`
- Never rely on `~/.claude/*.md` files being loaded by OpenCode.

## 12. MCP Setup, Transport, and Debug Rules

### 12.1 Canonical Transport Architecture

Do not change transport types without reading the server source.  The mapping is:

| Server | `type` in .mcp.json | Protocol | Endpoint |
|---|---|---|---|
| `conport` | `sse` | Server-Sent Events | `GET /sse` |
| `dope-memory` | `http` | Streamable HTTP (FastMCP `http_app()`) | `POST /mcp` |
| `task-orchestrator` | `http` | Streamable HTTP (Ktor) | `POST /mcp` |
| `pal`, `serena`, `dope-context` | `http` | Streamable HTTP | `POST /mcp` |
| `desktop-commander` | `sse` | Server-Sent Events | `GET /sse` |

**Critical invariant**: A `406 Not Acceptable: Client must accept text/event-stream`
response to a `GET /mcp` is **correct server behaviour** for a Streamable HTTP
endpoint.  It is NOT evidence that the server is SSE.  The fix is to use `POST`
with a JSON-RPC body — not to change `"type"` to `"sse"`.

### 12.2 Port Allocation Invariants

`dopemux mcp init` computes per-worktree port offsets via:
```
port = default_port_base + sha1(workspace_path)[:4] % 100
```

**Invariants enforced by `_allocate_ports`** (as of 2026-07-06):
- `wrapper-singleton` services (`management_model: wrapper-singleton`, e.g.
  `task-orchestrator`) always use `default_port_base` directly — **no hash offset**.
- All singleton catalog ports are pre-seeded in the collision map so a per-worktree
  hash cannot silently land on a singleton-reserved port.
- Collision detection raises an error before writing any config.

### 12.3 Setting Up MCP in a New Repo

```bash
cd ~/code/target-repo    # must be a git repo
dopemux mcp init         # generates .mcp.json + .envrc.dopemux-mcp
source .envrc.dopemux-mcp
dopemux mcp doctor       # verify env vars + port reachability
```

For full guidance including manual (non-dopemux) setup and vanilla Claude Code:
→ `docs/02-how-to/mcp-setup-other-repos.md`

### 12.4 MCP Debug Sequence

When MCP servers fail to connect, follow this sequence in order:

1. **Source the envrc**: `source .envrc.dopemux-mcp` — unset vars fall back to
   catalog defaults which may not match running containers.

2. **Run doctor**: `dopemux mcp doctor` — checks env vars and port reachability.

3. **Probe with correct transport**:
   ```bash
   # Streamable HTTP (dope-memory, task-orchestrator, pal, serena):
   curl -X POST http://localhost:$DOPE_MEMORY_PORT/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'

   # SSE (conport):
   curl -N -s http://localhost:$CONPORT_MCP_PORT/sse -H "Accept: text/event-stream"
   ```

4. **Tail container logs** during connection attempt:
   ```bash
   docker logs -f dopemux-dope-memory-1 2>&1 | grep -i "mcp\|error"
   docker logs -f dopemux-task-orchestrator 2>&1 | grep -i "mcp\|error"
   ```

5. **Run health report**: `./mcp_server_health_report.sh`

6. **Check for port collisions**: If `dopemux mcp init` raises a collision error,
   adjust `default_port_base` in `mcp_catalog.yaml` to create more spacing, or
   use a workspace path with a different hash.

**Reference docs**:
- `docs/02-how-to/mcp-transport-and-port-bugs.md` — bug record + correct analysis
- `docs/02-how-to/mcp-setup-other-repos.md` — human user guide for other repos
- `docs/02-how-to/mcp-troubleshooting.md` — container-level troubleshooting

### 12.5 Generated MCP surfaces and implicit use

`mcp_catalog.yaml` (v2 fields: `agents`, `tools`, `admin_tools`, `aux_surfaces`,
`managed`) is the single source of truth for the MCP fleet (ADR-MCPINT-001). Generated
from it — and never hand-edited: the worktree `.mcp.json`, the global singleton fragment
(`sync-globals`), the `opencode.jsonc` managed `mcp` block, `mcp-proxy-config.copilot.yaml`,
and the `.codex/config.toml` managed `mcp_servers` region. Parity gates in
`tests/arch/test_mcp_fleet_catalog_contract.py` fail CI on drift; exposure changes are
catalog `agents:` edits followed by `dopemux mcp generate --apply`.

`agents:` matrix semantics — `full`: direct config now. `full-sequenced`: full config only
after DMX-MEMSPINE-IDENTITY-005 and task-orchestrator `actor_authentication.enabled` land
(`--allow-sequenced` is refused until then). `read-plane`: reads via the dcp-readonly-facade
plus read-safe direct singletons. `facade`: remote facade per ADR-DCP-MCP-RO-0009. `none`:
no agent surface. The facade is the only cross-plane read projection for non-attributed
agents (ADR-MCPINT-002). Implicit context is Claude-only, entering through exactly one
channel: `native_hooks.py` SessionStart — four bounded blocks, ~3KB, fail-open
(ADR-MCPINT-003). Tool names come only from `mcp_tool_surfaces.json` (refresh:
`dopemux mcp snapshot-tools`). Workflow sequences: `docs/03-reference/mcp/workflows.yaml`;
full guide: `docs/02-how-to/mcp-integration-guide.md`.

Respond terse like smart caveman. All technical substance stay. Only fluff die.

Rules:
- Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging
- Fragments OK. Short synonyms. Technical terms exact. Code unchanged.
- Pattern: [thing] [action] [reason]. [next step].
- Not: "Sure! I'd be happy to help you with that."
- Yes: "Bug in auth middleware. Fix:"

Switch level: /caveman lite|full|ultra|wenyan
Stop: "stop caveman" or "normal mode"

Auto-Clarity: drop caveman for security warnings, irreversible actions, user confused. Resume after.

Boundaries: code/commits/PRs written normal.
