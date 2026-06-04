---
id: DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER
title: Dcp Dr External Constraints Ledger
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-09-02'
prelude: Dcp Dr External Constraints Ledger (reference) for dopemux documentation
  and developer workflows.
---
# DCP External-Constraints Ledger (TP-DCP-DR-INTAKE-0001) — **COMPLETE (DR-DCP-001..015)**

> [!NOTE]
> **Provenance**: `EXTERNAL_PROPOSED`
> **Status**: Preservation Only (Design Input / External Research)

> Status: **complete**. All 13 operator-run Deep Research reports ingested. Run **inline** (no agent spawn — reports were already in-context; budget optimization vs the planned Haiku worker). Full report texts preserved at `artifacts/dcp/dr/DR_DCP_0*.md`.
> **Authority class (every entry):** `VENDOR_DOCS / EXTERNAL_CONSTRAINT_SYNTHESIS / LOWER_THAN_REPO_RUNTIME`. External docs **inform** the synthesis; they never override repo/runtime evidence. Today 2026-06-03.

## How COMPRESS-0001 must use this
- Feed the **load-bearing constraints** below into the synthesis pack §9 (External Research Findings) and as hard gates in the GPT-5.5 prompt.
- Any repo/runtime claim must cite **repo evidence**, not these reports.
- These reports repeatedly **corroborate** the repo campaign (esp. TO projection-first + undefined `LIVE_WRITE_READY`), which raises confidence — but corroboration ≠ authority promotion.

---

## Per-report ledger

### DR-DCP-001 · GitHub Actions / Branch Protection / Merge Queue
- **GitHub is the merge authority; DCP is not.** Pattern: **one stable required gate** (unique name e.g. `dcp-gate`, on `pull_request` **+ `merge_group`**, final aggregator `if: always()`) + **advisory** (non-required) PR Steward.
- `ready_for_review` is **not** in `pull_request` defaults (opened/synchronize/reopened). `workflow_dispatch` = recompute; **rerun ≠ dispatch**; **no empty commits**.
- Required-check truth table: **workflow-skipped → Pending (blocks)**; **job-skipped → Success (passes)**; accepted conclusions = `success|skipped|neutral` only. Bind by **latest SHA** (7-day freshness); merge-group has its **own SHA**. **Rulesets layer** (most-restrictive wins) — harvest classic **and** rulesets.
- `pull_request_target` + untrusted checkout = repo-compromise foot-gun.
- **Feeds:** GITHUB-0001, PR-0001, OPENPRS-0001.

### DR-DCP-002 · Copilot PR Repair Lane
- Copilot cloud agent = **bounded implementer only**, never authority (no approve / merge / mark-ready / resolve-threads / bypass). Current docs: `@copilot` PR comment **pushes to the PR branch by default**.
- Workflows on Copilot pushes are **held by default** until a human approves. Triggers only from **write-access** users. **Agents secrets** are separate from Actions secrets; **content exclusions do NOT apply** to cloud agent. One branch / one PR per task.
- **Feeds:** ACTION-0001 (repair/Copilot lane), the "implementer ≠ authority" gate.

### DR-DCP-003 · MCP / Task Orchestrator Write Contract
- MCP = plumbing, **not** a write-safety model. **Three separate tools**: read-only / dry-run / live-write (NOT a `dryRun` flag). Tool annotations (`readOnlyHint` etc.) are **hints, untrusted** — host enforces class.
- Dry-run returns a **proof bundle** (resolved immutable target IDs, canonical payload, payload fingerprint, preconditions/version tokens, idempotency-key preview, preview hash). Live-write requires **dry-run proof hash + write_intent_id + durable idempotency_key + preconditions + read-after-write verify + append-only receipt + declared rollback mode**.
- Use own `_meta` namespace (`dopemux.io/*`). **Corroborates repo:** TO = projection-first; no live writes until contract proven (repo: `LIVE_WRITE_READY` undefined).
- **Feeds:** TO-0002, TO-0004, the live-write-readiness decision.

### DR-DCP-004 · Auditor Runtime Capabilities
- Default route ordering: **Codex CLI first** (hard read-only sandbox, `codex exec`, `--output-schema`), **Gemini second w/ caveats** (sandbox off by default; `plan` mode "not yet fully functional"; **Antigravity replaces Gemini CLI 2026-06-18** for some tiers), **Claude Code = soft/policy read-only only** (no hard OS sandbox found → NEEDS_SUPERVISOR for hard-RO lanes), **Copilot = locally-proven-only**, **AGY + PAL `clink` = UNKNOWN → supervisor-gated**.
- Min proof envelope per run: raw stdout/stderr, exit code, invocation string, binary version, model id, output SHA-256.
- **Feeds:** AUDIT-0001 (auditor-router / PAL-clink capability table — note repo HAS `tools/auditor_router/pal_clink.py`, so PAL clink is partly observable, but DR rates it UNKNOWN externally → reconcile in AUDIT-0001).

### DR-DCP-005 · Proof / Provenance / Evidence
- **Compose existing standards**, don't invent: in-toto Statement (subject+predicate) + DSSE (signing envelope) + SLSA provenance (build) + **SLSA VSA (policy verdict)** + Sigstore bundle + SPDX/CycloneDX (SBOM, separate). **Pointer-first**: reference native attestations by digest; don't reserialize.
- `CONTROL_PROOF_POINTERS.json` = discovery/routing; `PROOF.json` = machine summary. Mandatory fields: `headSha`, `dirtyWorktree`, `mixedShaArtifactSet`, `validationState`, **`auditorVerdict` (distinct from validationState)**. **Never self-hash `PROOF.json`** (hash from outer index). Proof grades: traceable → replayable → deterministically-replayable → release-grade.
- **Feeds:** PROOF-0001, the "generic proof representation (pointer/index/schema)" decision.

### DR-DCP-006 · SQLite / Event-Store / Idempotency
- SQLite as **append-only system of record**, single effective writer, WAL discipline, local FS only. **Snapshot-first exporter**: true read-only open → **Backup API** to fresh file → reopen `immutable=1` → query/hash the snapshot. **Never** checkpoint / journal-flip / raw-copy / `nolock` the live DB; `query_only` is **not** a safety rail.
- Two idempotency identities: **semantic caller key** + **canonical request hash** (RFC 8785). **Transactional outbox** = atomic local commit + at-least-once dispatch + idempotent sinks ("exactly-once" end-to-end is a lie). **Disable external gateways during replay.** Version floor: WAL-reset fix **3.51.3 / 3.50.7 / 3.44.6**.
- **Feeds:** STATE-0001 (event-store/exporter discipline), the event-store red lane.

### DR-DCP-007 · macOS / iMessage / TCC / launchd  *(dNh red lane)*
- Reading `~/Library/Messages/chat.db` needs **Full Disk Access for the exact responsible binary** (not Files&Folders, not a SIP problem). **launchd jobs do NOT inherit Terminal FDA** — grant the real worker or use a signed helper + PPPC (bundle-id or path + code-requirement).
- Safe read = snapshot-first (Backup API, `mode=ro`, immutable only on the snapshot). **Never auto-**grant FDA / reset TCC / disable SIP / upload chat.db without explicit consent. Capture metadata-not-content for proof.
- **Feeds:** RUNTIME-0001 (dNh red lanes), XPROJ-0001.

### DR-DCP-008 · Telegram Approval Callbacks  *(dNh red lane)*
- `callback_data` (1–64 bytes) carries an **opaque single-use action_id only**; business context server-side. **At-least-once delivery** → dedupe receipts on `update_id`+`callback_query.id`, dedupe **effects** on `action_id`+`effect_id`. **Pre-bind** approval to user/chat/message/thread/policy-verdict-hash/proof-pointer/expiry **before** sending; `answerCallbackQuery` immediately (~10s window).
- Telegram = **evidence, never sole authority** for red-lane writes. Approval-**policy** changes = control-plane (higher risk than single approvals); invalidate pending buttons on policy change.
- **Feeds:** RUNTIME-0001 (dNh), the approval/proof model.

### DR-DCP-009 · Twenty CRM Writeback  *(dNh red lane)*
- Schema-**generated** API (tenant-specific; the workspace's own docs are authoritative, not public docs). **No native idempotency header** → DCP owns dedupe: unique custom `externalId`/`proofId` + **upsert** + match on **exactly one unique key** (People=`email`, Companies=`domain`); zero-or-many → stop+escalate.
- OAuth scopes coarse (`api`/`profile`) → least-privilege via **roles**, one client per lane. No general audit-log API → keep **own immutable ledger**. **Hard red lines (supervisor):** Metadata API writes, deletes, identity/relation changes, ambiguous match, Send Email.
- **Feeds:** RUNTIME-0001 (dNh), XPROJ-0001.

### DR-DCP-010 · Control Cockpit UX
- Not "pick one UI": **artifact-first truth + CLI primary + read-only TUI + GitHub/TO as projection; web tower later.** **Risk instrument panel, not green-badge theatre** — unknowns/incomplete are **first-class states**; every surface shows an **authority badge** (Authoritative / Derived / Projection).
- Automate detection / summarization / proof-collection / watch / route-**suggestion**; keep live-writes / red-lane approval / route-override / **merge** manual. MVP = canonical MD/JSON + `dopemux` CLI + GitHub check-summary projection + optional TUI. **Corroborates repo:** cockpit already under construction (TUI + Palette).
- **Feeds:** COCKPIT-0001, UX-0002, UX-0003, UX-0004.

### DR-DCP-011 · Platform / Control-Plane Patterns  *(the architecture steer)*
- **DCP ≈ Backstage (catalog/portal) + OPA (policy decision ≠ enforcement) + provenance-verifier + thin supervised action-broker.** **NOT** Temporal / Argo / Tekton / Humanitec (durable execution / runtime authority).
- Own: normalization, derived status, proof verification, policy interpretation, action-intent generation. **Don't own:** durable queues, replay, retries, deploy graphs, mutable runtime truth. Tasks/workflows = **projections** (source_system, source_ref, observed_at, freshness, deep-links), never native execution objects. **Capability-based adapter contract** (`entity.read`, `observation.stream`, `evidence.stream`, `action.dry_run`, `action.submit` → returns **external authority ref**, not a DCP-native execution object).
- **Feeds:** the synthesis core — "where DCP Core lives", "generic vs project-specific", "TO projection-only".

### DR-DCP-012 · Agent Automation Security
- **Two-phase**: unprivileged phase reads untrusted PR/builds with **no secrets + minimal token** → separate privileged phase acts only on **bounded evidence** (hashes/verdicts/attestations), never raw untrusted artifacts or arbitrary model output. **Taint** everything outside the trusted policy/config path.
- Secret hierarchy: **OIDC first → secret-broker → GH secrets → PAT (break-glass only)**. Never `pull_request_target` + untrusted checkout; pin actions to full SHA; no secrets in argv/cache. **Implementer / auditor / supervisor separation; no self-certifying loop; no agent marks its own work ready.** MCP: per-server scoped creds, pinned schema hashes, `additionalProperties:false`, no shell passthrough, server isolation. **PR comments / external docs = data, not authority.**
- **Feeds:** the red-lane + role-separation synthesis, AUDIT-0001, ACTION-0001.

### DR-DCP-013 · External Constraints Synthesis  *(meta)*
- Status **PARTIAL / FAIL-CLOSED** (ran without repo mounted — correct fail-closed result). Verdict: `ACCEPT_AS_EXTERNAL_BASELINE` · `DO_NOT_TREAT_AS_RUNTIME_VALIDATION` · `DO_NOT_USE_AS_FINAL_ARCHITECTURE` · `FEED_INTO_5.5_SYNTHESIS_PACK`. Explicitly says: **return to the repo evidence campaign** before synthesis. It defines the walls of the maze, not the doors in the repo.

### DR-DCP-014 · Memory / Context / Chronicle Architecture Patterns  *(pairs with MEMCTX-0001)*
- **Hard layer separation:** `source-truth ≠ index ≠ projection ≠ chronicle ≠ proof` — don't let layers cosplay as each other. `authority_tier` ⊥ `confidence` (never derive one from the other; a bridge mirror can be high-confidence yet non-authoritative).
- **Four freshness clocks** carried separately (source / index / retrieval / artifact) — no single fake `updated_at`. Mirrors/bridges default **non-authoritative, read-only** (Backstage readonly-mirror temperament).
- **Roles:** decision store = intent/rationale/owner/supersession (NOT receipts/proofs/embeddings/logs); retrieval/index = rebuildable, always source-pointed, never legal truth; chronicle = append-only temporal receipts, corrections via compensating events (never edit-in-place), NOT runtime state; proof = external verifiable (in-toto/SLSA), referenced by receipts not inlined; cockpit timeline = projection only, badge authority/freshness/completeness/direct-vs-derived.
- **v1 = READ-ONLY across all adapters**, except an optional **DCP-owned append-only chronicle namespace**. Provides the **Evidence-Hit contract** (17 fields incl. source_sha, index_timestamp, authority_tier, derived_direct_flag, partial_result_flag) + **Chronicle Receipt contract** (~22 fields) → directly seed deferred `RETRIEVAL-0001` + `CHRONICLE-0001`.
- **Anti-patterns:** retrieval-as-truth, mirror-as-authority, bridge-as-authority, chronicle-as-runtime-state, progress-as-workflow-legality, cache-freshness-as-source-freshness, cockpit-as-proof, confidence-as-authority, propagated-context-as-memory, summary-without-lineage.
- **Feeds:** MEMCTX-0001 (evidence pairing) + deferred MEMCTX-0002/CHRONICLE-0001/RETRIEVAL-0001 + COMPRESS memory decisions. *External patterns only — repo runtime (MEMCTX-0001) outranks.*

### DR-DCP-015 · DCP Tooling Layer (skills/plugins/hooks/CLI)  *(pairs with TOOLING-0001)*
- **Verdict `BUILD_AFTER_CORE_CONTRACTS`** — lock 5 contracts first: red-lane taxonomy, receipt schema, mutation classes, approval artifact, project path/resource maps. Principle: **"LLMs reason, hooks enforce, CLI helpers standardize, proof records, supervisor decides."**
- **Deterministic-vs-LLM split:** hooks/CLI enforce (forbidden-path, schema validation, receipts, known red-lanes); skills teach/synthesize (packet authoring, PR/arch reading); final approval = supervisor-only. Hard blocks in `UserPromptExpansion` + `PreToolUse` + Git/pre-commit + **CI duplicates** — NOT prompt/agent hooks ("probabilistic guard = vibe plane").
- **Plugin v1:** `defaultEnabled:false`; **NO monitors, NO channels, NO default-agent override**; `commands/`→skills. Side-effectful skills → `disable-model-invocation:true`; stingy `allowed-tools`.
- **`dopemux dcp` CLI** owns the boring-critical: preflight/status/next/evidence-pack/prompt/verify-proof/red-lines/render-to --dry-run/accept — read-only / dry-run / local-metadata only. Receipt schema (~20 fields) reinforces DR-014's chronicle contract.
- **Cross-project packaging:** `dcp-core` + `dcp-profile-dopemux` + `dcp-profile-dnh-crm` + repo-local evidence; extend via **rules/schemas/path-maps, not forked prompts**; repo-local must not weaken core denies.
- **NEVER build:** channels, default-agent override, auto-approve/merge/resolve, CRM/client send from skills/hooks, broad live-writer plugin. Client hooks bypassable (`--no-verify`) → duplicate gates in CI.
- **Feeds:** TOOLING-0001 (evidence pairing) + deferred HOOKS/SKILLS/PLUGIN/CLI-HELPERS + COMPRESS tooling decisions. *External patterns only — repo runtime (TOOLING-0001) outranks.*

### DR-DCP-016 · Memory + Tooling Constraints Synthesis  *(consolidates 013+014+015 — most COMPRESS-ready)*
- **Consolidated synthesis** of DR-013/014/015 into actionable contracts. **10 severity-rated constraints:** layer separation (source/index/projection/chronicle/proof), `authority_tier ⊥ confidence`, multiple freshness clocks, append-only chronicle w/ correction links, pointer-first proof, **v1 read-only except DCP-owned append-only chronicle**, deterministic-hooks-outrank-LLM, `BUILD_AFTER_CORE_CONTRACTS`, cockpit/TO = projection-not-authority, no hidden-authority surfaces, repo-runtime-outranks-research + no self-certifying loops.
- **Ready-made contract specs** (directly seed the deferred design packets): **Evidence-Hit** (17 fields), **Chronicle-Receipt** (~24 fields), **Memory/Context Adapter** (role/ownership/write-perms/authority/freshness/mutation-type), **Helper-Receipt** (~20 fields), **Red-line Hook** (deterministic precedence `block>ask>warn>allow`, intercept prompt-expansion + tool-use, receipts even on denial), **Plugin/Skill Manifest** (mutation-class/allowed-tools/model-invocation-limits/opt-in; v1 defaultEnabled:false + disable-model-invocation + no channels/monitors/default-agent).
- **Control split (one line):** skills/subagents synthesize · hooks/CLI enforce · Git/CI duplicate critical checks · humans approve anything risky.
- **Feeds:** deferred MEMCTX-0002/CHRONICLE-0001/RETRIEVAL-0001 + tooling design family + COMPRESS memory & tooling decisions. **COMPRESS should read this file directly** (`dr/DR_DCP_016_MEMORY_TOOLING_CONSTRAINTS_SYNTHESIS.md`). *External — repo runtime (MEMCTX-0001/TOOLING-0001) outranks.*

---

## Consolidated DCP shape (emergent across 003 / 005 / 010 / 011 / 012 / 014 / 015 / 016)
1. **DCP Core = evidence / readiness / proof / policy / action-planning authority.** Reads every surface; writes none until a contract is proven. It is not TO, Dopetask, GitHub, the CRM, or a runtime.
2. **Everything external is a projection or a gated delegated-execution target** (GitHub=merge authority, TO=work-graph projection, CRM/Telegram/macOS=red-lane writers).
3. **Proof = pointer-first, digest-anchored, in-toto/SLSA/Sigstore-composed; `auditorVerdict` ≠ `validationState`.**
4. **Cockpit = artifact+CLI first, risk-panel, authority-badged, projection-labeled; web later.**
5. **Security = two-phase + taint + OIDC + role-separation + no self-certifying loop + fail-closed.**

## Consolidated synthesis gates (for the GPT-5.5 prompt — expanded from DR-013's 8)
```md
## External Constraint Gates (DR-DCP-001..013 — VENDOR_DOCS, lower than repo runtime)
1. Any repo/runtime claim must cite repo evidence, not DR reports.
2. GitHub is merge authority; DCP uses one stable required gate + advisory steward; harvest classic + ruleset policy on the latest/queue SHA.
3. Task Orchestrator stays projection-first; live writes only behind a proven three-lane (read/dry-run/live) contract with idempotency + receipts + read-after-write.
4. MCP tool annotations/metadata are not authority; host enforces tool class.
5. Proof is pointer-first, digest-anchored, chain-of-custody preserving; auditorVerdict is separate from machine validation; never self-certify or self-hash.
6. Event-store reads use snapshot/export discipline (Backup API → immutable snapshot); never mutate the live DB; semantic key + canonical hash idempotency; outbox = at-least-once + idempotent sinks.
7. Agent automation is two-phase with tainted untrusted input, OIDC-first secrets, role separation, and no self-certifying implementer/auditor/readiness loop.
8. Red-lane writes (CRM, Telegram, iMessage/macOS, identity, approval-policy) require supervisor gates, exact-match resolution, reserved correlation IDs, and an independent proof ledger.
9. Copilot/agent implementers are patch producers only — never approval/merge/ready/resolve authority.
10. Unknown runtime state fails closed.
```
