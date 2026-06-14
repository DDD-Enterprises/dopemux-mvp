# DX Overhaul — Phase 2 Workflow Maps (As-Is → Target)

**Date**: 2026-06-11 · **Inputs**: Phase 1 synthesis (`01-research-synthesis.md`), DR-DCP-015 (`research/DR-DCP-015-dcp-tooling-layer.md`), operator scope decisions (`00-process.md`).
**Status**: Draft for PAL validation + operator approval (Phase 2 → 3 gate).

---

## 0. Target-state primitives (defined once, referenced everywhere)

Every target workflow below composes the same small set of primitives. This is the DR-DCP-015 doctrine applied to dopemux: **LLMs reason (skills), hooks enforce (deterministic), CLI standardizes (`dopemux dcp`), receipts record, supervisor decides.**

| Primitive | What it is | Builds on (existing) |
|---|---|---|
| **P1. Five core contracts** | Red-lane taxonomy · receipt schema · mutation classes · approval artifact · path/resource maps. Locked FIRST (DR: BUILD_AFTER_CORE_CONTRACTS). | `schemas/proof/*`, `config/repo_hygiene/*`, `src/dopemux/dcp/red_lane_rules.py`, AGENTS.md §9 proof contract |
| **P2. `dopemux dcp` CLI** | Deterministic helpers: `preflight · status · next · evidence-pack · prompt · verify-proof · red-lines · accept`. JSON + human output, receipt per run. | `scripts/preflight.sh`, `validate_audit_proof.py`, `src/dopemux/dcp/` (read-only code already exists) |
| **P3. Session bootstrap hook** | SessionStart orients every session: active packet, orchestrator queue, ConPort context, chronicle recap, git posture, red-lane policy version. Graceful degradation per backend. | `native_hooks.py` `_on_session_start` + orchestrator cache (already live) |
| **P4. DCP plugin (source-compiled)** | One installable package: read-only skills + deterministic hooks + narrow MCP helpers. `defaultEnabled: false`; no monitors/channels/default-agent override (DR Never-list). | `templates/skills/` + `sync_repo_skills.py` build pattern |
| **P5. Doctrine sync** | ONE canonical governance source compiled into per-tool surfaces (CLAUDE.md, copilot-instructions, GEMINI.md, opencode, supervisor bundle) + CI drift gate. Extend via rules/schemas/path-maps, never per-tool prose forks. | `.claude/modules/shared/governance-principles.md` as canonical; existing skill-sync pattern |
| **P6. Stable MCP topology** | HTTP-singleton per workspace: task-orchestrator HTTP cutover (POC-verified), dope-memory `/mcp` (PR #857), ConPort port unification, ghost-entry removal. Multi-session safe. | `mcp_catalog.yaml`, `scripts/mcp-wrappers/` |
| **P7. Evidence pipeline** | Auto-assembled evidence package per PR (proof bundle + audits + reviews + readiness) and a supervisor **verdict ingestion** artifact (signed acceptance record consumed by `steward_gate`-style validation). Stops at the merge button. | `MERGE_READINESS.json`, `PROOF.json`, `steward_gate.py` `supervisor_accepted` carveout (exists, unplumbed) |
| **P8. Receipts** | Every helper run (skill/hook/CLI/wrapper) emits a chainable receipt per DR §8 schema. Receipts feed proof bundles. | `proof/` conventions; new `.dcp/receipts/` evidence path |

**Hard invariants (unchanged)**: DCP-RED-MERGE-SEAM-0001; `LIVE_WRITE_READY` undefined/blocking; supervisor/human performs merge; no auto-approve.

---

## W0. Session start & context bootstrap (cross-cutting)

**As-is**: SessionStart hook injects ≤3 orchestrator items *only if* a ≤4h cache exists; ConPort orient is doctrine ("call get_active_context") not mechanism; `/dx:load` specified but never built; fresh worktree sessions start cold; 4 memory systems with no unified recall.
**Pain**: every interruption costs a manual re-orientation; agents skip the convention silently.

**Target**: open any tool in any worktree → oriented automatically.
1. SessionStart (P3) runs `dopemux dcp preflight --bootstrap` → one composed context block: active packet, next action (`dcp next`), orchestrator queue (live or cached), last chronicle recap, dirty-tree warning, policy version.
2. Non-Claude tools get the same via `dopemux dcp status` (documented as step 1 in their synced doctrine, P5).
3. Receipt emitted (P8); stale/unavailable backends reported honestly (fail-honest pattern from T1 remediation).

| Step | Surface | Det/LLM |
|---|---|---|
| Gather state (git, packet, queue, recap) | CLI (P2) | Deterministic |
| Compose orientation block | SessionStart hook (P3) | Deterministic template |
| "What should I do next?" reasoning | model w/ injected context | LLM |

**Build**: extend `_on_session_start` to call `dcp preflight --bootstrap`; kill the dead `/dx:load` spec by making it automatic; `/dx:load` alias for manual re-orient.

## W1. Feature design & brainstorming

**As-is**: `/sc:brainstorm` (SuperClaude doctrine) or ad-hoc chat; briefs logged to ConPort only if the agent remembers; no bridge from brainstorm → packet.
**Target**: `/design <idea>` → Socratic brainstorm (skill) → structured brief saved to ConPort + chronicle → offers `dcp-task-packet-author` handoff → packet draft → operator approves → load into orchestrator.

| Step | Surface | Det/LLM |
|---|---|---|
| Elicit requirements, explore options | skill (brainstorm) | LLM |
| Brief persistence (ConPort decision + chronicle) | CLI/MCP write via documented path | Deterministic call, LLM content |
| Packet drafting | skill `dcp-task-packet-author` (manual-invoke only) | LLM |
| Packet schema validation | `dcp verify-packet` (P2) | Deterministic |

**Build**: brief→packet handoff prompt; packet validator already exists (`dopetask-canonical-spec.json`) — wrap in CLI.

## W2. Research

**As-is**: `/research:quick|deep|report` work when gpt-researcher MCP is up; DR results (like DR-DCP-015) arrive via ChatGPT web and are hand-pasted; no intake structure.
**Target**: `/research <q>` routes quick/deep automatically; `dcp-dr-intake` skill (DR §5, V1 model-invocable) turns prompts into intake briefs with output contracts; results auto-saved to `claudedocs/research/` + indexed (dope-context) + recap to chronicle; supervisor DRs ingested by dropping the file — hook detects + registers it.

| Step | Surface | Det/LLM |
|---|---|---|
| Route quick vs deep | skill heuristic | LLM (cheap) |
| Execute research | gpt-researcher/Exa MCP | External |
| Persist + index + receipt | CLI (P2) | Deterministic |
| Synthesis/report | skill | LLM |

**Build**: consolidate 4 research commands → 1 router + report; DR-intake skill; auto-index on save.

## W3. Planning & architecture

**As-is**: PAL chains per AGENTS.md §5 run when the agent is diligent; TP authoring is hand-rolled markdown/JSON; load plans loaded by **manual MCP calls**; plan-mode guidance hooks exist; `/dx:plan-enter/exit` stranded on a side branch.
**Target**: `/plan <scope>` → PAL chain orchestrated by skill (analyze → thinkdeep → challenge → planner per risk class) → plan doc → `dcp-task-packet-author` → schema-validated TP series + load plan → **`dopemux dcp load-plan apply`** replays it into the orchestrator idempotently → operator `dcp accept` gates the load.

| Step | Surface | Det/LLM |
|---|---|---|
| Risk classing (which PAL chain) | CLI `dcp red-lines` + rules | Deterministic, LLM advisory for gray |
| PAL chain execution | PAL MCP via skill | LLM (external models) |
| TP schema validation | CLI | Deterministic |
| Load-plan replay into orchestrator | CLI wrapper (orchestrator write = mutation class → requires `dcp accept` first) | Deterministic |

**Build**: load-plan loader (top-10 pain #8); plan skill encoding chain selection; TP validator CLI wrap.

## W4. Implementation

**As-is**: `/dx:next` → `claim_item` → worktree (manual or `dopemux worktree create`) → code → validators via pre-commit/CI → proof bundle hand-assembled → `advance_item complete`. Edit-nudge hook reminds about evidence notes. Local `.githooks` activation UNKNOWN → failures discovered in CI (PR #854 fix-waves were exactly this).
**Target**: `/work` (evolved `/dx:implement`) = claim → worktree + MCP wiring auto-provisioned (P6) → bounded prompt rendered (`dcp prompt implement`) → code with PreToolUse red-lane guard + post-edit validator hook → `dcp evidence-pack` assembles proof continuously → complete-gate passes because evidence already exists.

| Step | Surface | Det/LLM |
|---|---|---|
| Claim + worktree + MCP provisioning | CLI | Deterministic |
| Scoped implementation prompt | `dcp prompt implement` | Deterministic render, packet content LLM-authored |
| Coding | model | LLM |
| Path/scope/red-lane guard | PreToolUse hook (P1 contracts) | Deterministic |
| Post-edit schema/test checks | PostToolUse hook + CLI (advisory; commit-gate blocks) | Deterministic |
| Proof assembly | `dcp evidence-pack` (P8 receipts feed it) | Deterministic |
| Complete gate | orchestrator proof-bundle note gate (exists) | Deterministic |

**Build**: worktree+MCP one-shot provisioner (`dopemux worktree create --wired`); evidence-pack; red-lane PreToolUse upgrade of the existing dormant enforcement; install `.githooks` in `dopemux init`/bootstrap (close the local-enforcement gap).

## W5. Debugging

**As-is**: `/debug` (RCA loop doc) + PAL `debug`; evidence scattered; chronicle captures only if agent stores it.
**Target**: `/debug <symptom>` → systematic-debugging skill drives reproduce→isolate→fix; every hypothesis/test logged as receipts; fix lands via W4 machinery; chronicle gets the RCA automatically (`memory_store` via hook on completion).

Surfaces: skill (reasoning) + CLI (test execution receipts) + dope-memory (RCA persistence). **Build**: thin — mostly skill consolidation + receipt wiring.

## W6. Refactoring & quality

**As-is**: `/sc:improve`, `/code-review`, PAL codereview/refactor — strong tools, no proof linkage; "simplify" passes leave no trace.
**Target**: `/review` and `/refactor <scope>` run the existing engines but emit receipts + structured findings that `dcp-proof-reviewer` can audit; refactors over N files require a packet (red-lane rule: scope class).

Surfaces: skills/PAL (judgment) + CLI receipts + red-lane scope rule. **Build**: thin wrapper + scope rule.

## W7. Documentation

**As-is**: Best-enforced workflow already (frontmatter guard with --fix, placement/filename/root hygiene, markdownlint — local+CI). Pain: agents discover rules at CI time; ADR/RFC commands aspirational; doc placement knowledge lives in prose.
**Target**: PostToolUse hook auto-runs `docs_frontmatter_guard --fix` + placement check on every doc write (instant feedback instead of CI round-trip); `/doc adr|rfc|howto` renders from templates via deterministic CLI; placement rules become path-map data (P1 contract 5) consumed by hook + CI identically.

**Build**: post-edit docs hook; template renderer; delete the 8 aspirational doc commands (hard-delete decision).

## W8. Git → CI → PR → review → merge

**As-is**: branch/commit/push manual; CI fires 7 blocking + advisory jobs; gemini quota noise; evidence for supervisor hand-assembled; verdict manual with **no ingestion path**; human merges. Recurring CI failure classes (frontmatter, hygiene, proof schema, Docker context, CVE pins) burn whole sessions (observed: PR #854).
**Target ("automate to the merge button")**:
1. **Prevent**: W4/W7 hooks + installed git hooks catch the recurring failure classes pre-push.
2. **Auto-fix lane**: CI failure → classifier matches known classes → bounded fix branch/commit via existing machinery (each fix a receipt; novel failures escalate to operator).
3. **Evidence assembly**: on PR open/update, `dcp evidence-pack --pr` composes proof bundle + embedded audit + reviews + MERGE_READINESS into one artifact; posted as PR comment + DCP-facade-readable.
4. **Supervisor loop**: supervisor reads evidence via DCP facade (Phase-1 tools live) → issues verdict → `dopemux dcp accept --verdict <file>` records the **signed acceptance artifact** → validation (steward_gate pattern) marks PR "READY — awaiting human merge".
5. **Merge**: human/supervisor clicks. Post-merge bookkeeping (orchestrator advance, chronicle, ledger) fires from merge webhook.

| Step | Surface | Det/LLM |
|---|---|---|
| Failure classification | CLI rules; LLM advisory for novel | Det first |
| Auto-fixes | bounded scripts (the PR-854 playbook codified) | Deterministic; LLM only for content-judgment fixes w/ receipt |
| Evidence assembly | CLI | Deterministic |
| Verdict | **supervisor only** | Human/supervisor |
| Verdict ingestion | CLI + schema validation | Deterministic |
| Merge | human | Human |

**Build**: failure-class classifier + fix lane; `evidence-pack --pr`; verdict artifact schema (P1 contract 4) + `dcp accept --verdict`; merge webhook bookkeeping. **Never**: auto-approve/auto-merge (DR Never-list = existing invariants).

**Concurrency requirement (observed 2026-06-12)**: the fix lane MUST claim a per-PR/per-failure-class lock before acting. Live precedent: two sessions raced the same `.opencode` hygiene failure on PRs #854/#855 with conflicting strategies (allowlist vs. remove) — one fix had to be discarded mid-flight. Claim artifact = a receipt (P8) that other agents check before starting; stale claims expire by TTL.

## W9. DevOps / stack operations

**As-is**: compose stack + `dopemux health` + smoke scripts; MCP fleet drift diagnosed by hand; Scout CVE waves fixed reactively.
**Target**: `dopemux dcp doctor` — one deterministic diagnosis of stack + MCP fleet (transports, ports, ghosts, worktree wiring) with fix suggestions; scheduled CVE-pin freshness check; stack mutations remain explicit operator commands (red-lane: runtime class).

**Build**: doctor command (absorbs `health` + MCP checks); P6 topology work is the prerequisite.

## W10. Multi-instance / worktree / multi-project

**As-is**: worktree CLI works; MCP follow-the-worktree is partial; **second session kills first** (stdio singleton); cross-project items contaminate shared queues; `dopemux init` scaffolds but doesn't provision MCP for foreign repos.
**Target**: any number of sessions across any worktrees/projects coexist: HTTP-singleton servers per workspace (P6); `dopemux init` provisions full MCP wiring + hooks + doctrine for ANY repo (the dNh-CRM/adOps profile pattern from DR §10: core + profile + repo evidence layer); orchestrator queries scoped per project root.

**Build**: P6 cutover; `init` provisioning; project-profile packaging (dcp-core / dcp-profile-X).

---

## Appendix A — DR-DCP-015 §14 repo-evidence answers (from Phase 1)

| DR question | Repo answer (evidence) |
|---|---|
| Red-lane paths? | Partial taxonomy exists: `src/dopemux/dcp/red_lane_rules.py` + `red_lane_scanner.py` (read-only), `config/repo_hygiene/root_hygiene_policy.json`, hard-blocked files (`queue_drain.py`, `batch_resolve_and_merge.py`), `.validator_scope.json`. Contract 1 = consolidate these into one taxonomy. |
| Task-orchestrator write semantics? | 14 MCP tools; mutating: `manage_items`, `manage_notes(upsert)`, `manage_dependencies`, `advance_item`, `claim_item`, `complete_tree`, `create_work_tree`. Proof-bundle note gates `advance_item(complete)` (v3.x + `.taskorchestrator/config.yaml`). No dry-run support OBSERVED. |
| Dopetask execution? | External `dopetask==0.5.1` binary behind `scripts/dopetask` shim; repo owns wrapper only. Execution semantics UNKNOWN — needs evidence before any exec wrapper. |
| CRM/client/identity mutators? | None in this repo (dNh-CRM is a separate repo; its profile package owns those rules). dopemux external writers: GitHub via `gh`/specialist CLIs, Leantime bridge, orchestrator, ConPort/dope-memory writes. |
| Existing proof artifacts? | `proof/<TP>/PROOF.json` + `embedded_audit` (schema-enforced in CI), `AUDITOR_REPORT.md`, `MERGE_READINESS.json`, `AUDITOR_ROUTE.json`, `MULTI_MODEL_PR_AUDIT.json`, load plans. Receipt schema (contract 2) generalizes these. |
| Schemas for post-edit validation? | `schemas/proof/*`, `dopetask-canonical-spec.json`, docs frontmatter rules, `model-routing.policy.yaml` consistency tests, routing schemas. |
| Current approval artifact? | `supervisor_accepted: true` carveout in `steward_gate.py`/classifier — **exists but unplumbed**; CODEOWNERS human review (@hu3mann). Contract 4 formalizes it. |
| Cockpit commands? | `dopemux cockpit` (Textual TUI, INFERRED), ui-dashboard (partial real data), `dopemux status`. |
| Existing Claude/Codex wrappers? | `.claude/` full harness; `scripts/mcp-wrappers/*`; Codex governed by AGENTS.md without exec wrapper profiles — DR's read-only Codex wrapper is net-new. |
| Allowed external systems? | GitHub, Leantime, LiteLLM-routed providers, Exa/GPT-Researcher, Docker/GHCR, DHI (flaky). No allowlist doc — contract 5 captures it. |
| Branch protection / PR authority? | CODEOWNERS @hu3mann all paths; `allow_governed_automerge: false`; ci-summary required-check registration UNKNOWN (must verify + register — cheap early win). |
| Receipt signing vs hashing? | No signing infra in repo; proof uses paths + schema, hashes partial. Recommend SHA-256 hashing now, HMAC optional later. OPERATOR DECISION at Phase 3. |

## Validation record & amendments (PAL analyze, gemini-2.5-pro, 2026-06-11)

**Verdict**: strategy sound; contracts-first sequencing and deterministic-vs-LLM split explicitly endorsed. Four amendments adopted:

1. **P1 contracts ship as versioned machine-readable schemas** (JSON Schema/Pydantic) in a dedicated versioned location from `v0.1.0` — not prose. All other components depend on that package.
2. **P6 MCP cutover is CRITICAL PATH** — elevated to first build wave alongside P1; requires a migration + rollback plan; W10 (and parts of W0/W4) are infeasible until it lands. Hard replace, not coexist (SQLite contention).
3. **W8 auto-fix lane constrained**: v1 permits ONLY idempotent, non-logic changes (formatting, frontmatter, hygiene allowlists, manifest/pin bumps from explicit rules). Anything touching the AST or dependency graph becomes a **suggested-fix PR comment**, never an applied commit. Every auto-fix = attributable commit + receipt. This is the guard against DR §13's hidden-auto-fix anti-pattern and the spirit of no-auto-approve.
4. **Deterministic-vs-LLM boundary codified as an ADR** in Phase 3 — every future check must declare which side it lives on.

**Quick wins endorsed for earliest scheduling**: publish P1 schemas v0.1.0; scaffold `dopemux dcp` as a thin wrapper over existing validators; manually consolidate the 4+ doctrine files into one canonical source before building the sync tool; plumb `supervisor_accepted` → PR label/status check as the first slice of P7.

## Appendix B — Phase 3 input checklist

Architecture phase must produce: (1) the five contracts as schemas/data files; (2) command-surface spec (~6 verb entrypoints + power-user familes + delete list); (3) hook spec (upgraded dispatcher + new guards/receipts); (4) `dopemux dcp` CLI spec; (5) plugin packaging + doctrine-sync design; (6) MCP topology target (P6); (7) evidence/verdict pipeline design (P7); (8) cross-project profile model; (9) migration/cleanup plan (hard-delete list); (10) verification strategy per AGENTS.md.
