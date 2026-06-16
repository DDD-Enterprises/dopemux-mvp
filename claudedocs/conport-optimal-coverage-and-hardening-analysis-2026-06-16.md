# DMX-CONPORT-OPTIMAL — Coverage & Hardening Analysis

**Type:** analysis dossier · **Status:** draft for operator review · **Date:** 2026-06-16
**Author:** Claude (Opus 4.8) orchestrating a 17-agent adversarial workflow + live-runtime verification + a gpt-5.2 external review
**Subject:** Expand and optimize the analysis behind the loaded 18-packet `DMX-CONPORT-OPTIMAL` series; classify every gap; identify defects to fix at source; surface what the series was about to build on sand.

---

## 0. Provenance & method (verified vs inferred)

| Dimension | Value |
|---|---|
| Repo state analyzed | `main` @ `a740edc40`; ConPort source @ `a3c2e61ac` ("fix(conport): cold-start grant and unified query 500s" #894, 2026-06-16) |
| Live runtime inspected | container `mcp-conport` (image `dopemux-conport`, ports 3004–3005) + DB `dopemux-postgres-age` (`apache/age:release_PG16_1.6.0`, db `dopemux_knowledge_graph`, user `dopemux_age`) via `docker exec` + `psql` |
| Loaded series | `DMX-CONPORT-OPTIMAL`, 18 packets (101–109, 201–206, 301–303), orchestrator root `44452f53`, 21 BLOCKS edges, `get_next_item=101` — **NOT perturbed by this analysis** |
| Adversarial pass | Workflow `wf_5b4a82ff-801`: 6 specialist lenses (35 findings) → 6 cross-refutations → 3 discovery rounds (+22 gaps) → completeness critic. Final synthesize step **failed on a session-usage limit**; register synthesized by the orchestrator from raw materials. |
| External review | PAL `consensus` tool down (3× `-32000`); substituted single-model PAL `chat` with **gpt-5.2** (OpenAI). grok-4.1 second-vendor pass failed (PAL disconnected). |
| Files read directly (this session) | `enhanced_server.py` (:196–217, :2000–2044), `schema.sql` (:100–259), `migrations/001_*.sql` (:101–145, :272–335), `migrations/` dir listing, `Dockerfile`, `.mcp.json`, `TP-202` JSON, `_AUTHORING_KIT.md`; live DB schema (`pg_tables`, `information_schema.columns`, `pg_namespace`) |

**Confidence labels** used below: `RUNTIME-VERIFIED` (I queried the live DB/container), `CODE-VERIFIED` (I read the file:line), `WORKFLOW` (agent-reported, not personally re-read), `INFERRED`, `REFUTED`.

**Honest limitations.**
- Discovery hit the **round cap (3), not dryness** — round 3 still surfaced 5 new gaps; **the gap space is not exhausted**.
- The synthesize agent died on a usage limit; this register is the orchestrator's synthesis, not the workflow's.
- PAL multi-model consensus was unavailable; only one external model (gpt-5.2) reviewed the central decision.
- The **traversal endpoint was not `curl`-tested**; live-image version vs `main` HEAD not reconciled (#894 recently touched this surface). These are residual `UNKNOWN`s.

---

## 0.5 Post-authoring correction — PR #894 reconciliation (git-verified)

After authoring the Tier-0 packets, a direct `git show a3c2e61ac` of PR #894 ("fix(conport): cold-start grant and unified query 500s") showed it **already resolved two traversal sub-findings** that the adversarial workflow had reported from a pre-#894 mental model:

- **CTE column bug RESOLVED** — #894 changed the recursive CTE `r.target_item_id::int`/`source_item_id` → `r.source_id::text`/`target_id::text` (git-diff proven). Current `unified_queries.py` is correct.
- **`int(decision_id)` cast RESOLVED** — #894 changed `decision_id=int(decision_id)` → `decision_id=decision_id` (git-diff proven, `enhanced_server.py`). #894 also copied `unified_queries.py` into the image (matches §2's live-container finding). Its commit message even cites "DMX-CONPORT-OPTIMAL-101" — #894 was a partial execution of this series.

**What survives unchanged:**
- **The core finding STANDS** — #894's `--stat` touched only `enhanced_server.py`/`unified_queries.py`/`schema.sql`; it added **no migration-apply path** (grep confirms none in startup). T0-MIGRATE (migrations-never-applied, RUNTIME-VERIFIED via psql) is unaffected.
- **One surviving traversal bug:** `max_depth` is still unclamped at `enhanced_server.py:2023` (B-MAXDEPTH, latent/low).

**Effect on the register below:** §3.1 **T0-TRAVERSE** collapses to a regression-guard + the `max_depth` clamp (Tier-0 packet 002 was authored VERIFIED-NO-OP-aware; TP-203 corrected to match). §3.2 **B-INT-UUID** → RESOLVED. The earlier-session read that showed the pre-#894 code reflected stale state; the live, git-clean HEAD has the fixes. This correction is the analysis self-correcting against runtime truth.

---

## 1. Headline — the series was about to build on sand

The loaded series is **correctness-focused** (4 named bugs) + knowledge-graph/context modeling (Tier 2) + retrospective (Tier 3). The adversarial pass + runtime verification found a **root cause beneath all of Tier-2/Tier-3 that the plan did not have**:

> **The ConPort server never applies its migrations.** `enhanced_server.py::_ensure_schema` runs only base `schema.sql`; the `migrations/*.sql` files are never executed by the server, and nothing in the postgres infra or compose applies them either. **RUNTIME-VERIFIED:** the live DB contains only `decisions` + `entity_relationships`. `decision_relationships`, `review_reminders`, `adhd_metrics`, `decision_patterns`, the multi-tenancy tables, and migration 001's 14 "enhanced decision" columns **do not exist**.

Consequence: **five queued feature packets target objects that don't exist at runtime.**

| Packet | Targets | Runtime reality |
|---|---|---|
| TP-303 | write `decision_relationships` | table absent (migration 001 never applied) — RUNTIME-VERIFIED |
| TP-302 | write `review_reminders` | table absent — RUNTIME-VERIFIED |
| TP-301 | set decision outcome/review columns | columns absent (`decisions` has only `id:uuid`, base fields) — RUNTIME-VERIFIED |
| TP-203 | fix relationship traversal | CTE + `int(decision_id)` bugs **RESOLVED by #894** (see §0.5); surviving = `max_depth` unclamped at `:2023` |
| TP-202 | write `entity_relationships` | table exists, but has no writers and a broken reader |

**gpt-5.2 review (verbatim gist):** gated + fail-closed migration apply is correct for an audit-grade memory server; silent auto-apply "turns process-start into a state-mutating event" and breaks replayability. **No feature packet — including TP-202 — should run pre-foundation**; writing under wrong-schema assumptions risks "poisoning canonical memory" and masking the foundation problem. Biggest underweighted risk: **irreversible divergence of canonical memory via schema drift + replay incompatibility** once writes land — "worse than downtime."

---

## 2. Two workflow claims REFUTED by runtime (truth over fluency)

The adversarial agents reasoned from the Dockerfile and over-claimed; the live container corrected them. Recorded so no future reviewer re-spends effort:

| Workflow claim | Runtime truth | Verdict |
|---|---|---|
| `unified_queries.py` not copied → `unified_query_api = None` → endpoints 500 unconditionally | File **is** present at `/app/unified_queries.py` in the running image | **REFUTED** |
| `ag_catalog`/AGE schema "never created" | `ag_catalog` schema **exists** (apache/age base image provides it) | **REFUTED** |
| Multi-tenant `user_id` impersonation / access-table leak (NEW-unauth-user_id, access-table-never-consulted) | multi-tenancy tables (`users`/`workspaces`/`user_workspace_access`) **absent** at runtime | **MOOT** (migration 003 never applied) |

The traversal endpoint therefore fails (if it fails) at **query time** (bad column names + uuid/int cast), not via a `None` guard.

---

## 3. Synthesized risk register (deduped, prioritized)

Disposition key: **T0** = new Tier-0 foundation (blocking) · **AMEND** = edit an existing loaded packet · **HARDEN** = companion default-off seam · **DOC** = document-only verdict · **DROP** = closed/moot. Each row carries the strongest evidence + refutation outcome.

### 3.1 Tier-0 foundation (NEW — blocks Tier-2/Tier-3)

| ID | Finding | Evidence | L/I | Disposition |
|---|---|---|---|---|
| T0-MIGRATE | Server never applies migrations; required tables/columns absent at runtime | `_ensure_schema` runs `schema.sql` only (WORKFLOW :408–475); live DB has 2 tables (RUNTIME-VERIFIED) | H/H | **T0** gated idempotent ordered runner + checksummed `schema_version` + fail-closed health gate |
| T0-TRAVERSE | ~~CTE refs `source_item_id`/`target_item_id`, `::int` on uuid~~ **RESOLVED by #894** (git-diff). Surviving: `max_depth` unclamped at `:2023` | #894 diff (git-VERIFIED); live cols `source_id`/`target_id` uuid (RUNTIME-VERIFIED) | L/L | **T0-002** regression-guard (VERIFIED-NO-OP) + `max_depth` clamp owned by TP-203 |
| T0-HEALTH | `/health` is blind to AGE/`ag_catalog` + schema_version → health lies while graph broken | `init_connections` does no AGE/graph validation (WORKFLOW); survived refutation ("`/health` blind to ag_catalog" — kept IN_SCOPE) | H/M | **T0** + AMEND TP-101/106 (fail health if expected schema absent) |

### 3.2 Confirmed bugs (AMEND loaded packets — no DAG change)

| ID | Finding | Evidence | L/I | Disposition |
|---|---|---|---|---|
| B-INT-UUID | ~~`int(decision_id)` crashes on uuid input~~ **RESOLVED by #894** (`decision_id=int(...)` → `decision_id=...`, git-diff) | git-VERIFIED at HEAD a3c2e61ac | — | RESOLVED — TP-203 records VERIFIED-NO-OP |
| B-MAXDEPTH | `max_depth = int(...)` unclamped → recursive-CTE DOS | `enhanced_server.py:2019` (CODE-VERIFIED); **LATENT** — masked because endpoint already errors | M/M | **AMEND TP-203** (cheap clamp alongside the fix) |
| B-RECENT-HOURS | `recent_activity` unbounded `hours` param + string-interpolated SQL | WORKFLOW (round 2); distinct site from B-MAXDEPTH | M/L | **AMEND** the recent-activity packet (verify injection surface) |
| B-PROMOTE-PCT | `promote_all` emits event with `percentage=0` (drops real value) | WORKFLOW; dark method on 3005 | M/L | **AMEND TP-107** (carry percentage or omit) |
| B-AUTOFORK | auto-fork refetch path raises AttributeError | WORKFLOW (round 2); adjacent to TP-107 | H/M | **AMEND TP-107** |
| B-DEADLOG | `conport_client.py` `logger.error` after `return` (dead) | `services/adhd_engine/conport_client.py:~42` (WORKFLOW); trivial real defect, survived refutation | H/L | **HARDEN** (trivial) or fold into client packet |

### 3.3 Operator-decision seams (HARDEN — default-off) — re-based on the :3005 agent surface

> **Surface reframing (RUNTIME-VERIFIED):** agents bind ConPort at `:3005` FastMCP (`server.py`), per `.mcp.json:5` (`localhost:3005/sse`) — **not** the `:3004` HTTP surface the seed security analysis assumed. On 3005 `fork_instance`/`promote`/`promote_all` are **advertised `@mcp.tool()`s, not "dark methods"**, and there is **no search tool** (bearing on TP-205/206). All access-control hardening must target 3005, or both surfaces explicitly.

| ID | Finding | Evidence | L/I | Disposition |
|---|---|---|---|---|
| H-AUTH | No auth gate on writes (any caller writes any workspace_id) | security lens; facts hold, verdict OPERATOR_DECISION after refutation | M/H | **HARDEN H-101** auth-token seam (default-off), on :3005 |
| H-AUDIT | No write audit log | security lens; "negative claim is strongest part" (survived) | M/M | **HARDEN H-102** append-only audit row (always-on-safe) |
| H-RATELIMIT | No rate limiting | devops lens → **DEFER** (L/L); panel did not sustain urgency | L/L | **HARDEN H-103** seam (default-off) *or* DOC — operator call |
| H-DARKSCOPE | fork/promote/promote_all callable by any agent | refined: advertised on 3005, not hidden (1b) | M/L | **HARDEN** admin-scope flag (default permissive) |

### 3.4 Reclassified / document-only (DOC)

| ID | Finding | Panel verdict | Disposition |
|---|---|---|---|
| 3c | DB-level FK + CHECK on `entity_relationships` (no FK; `relationship_type` bare VARCHAR; `strength` not `metadata`) | **OPERATOR_DECISION** (downgraded from plan's "mandatory headline") — app-layer enum may suffice; only integrity arg is orphan-edge accumulation | **DOC** + optional HARDEN H-201-cond; **correct TP-202 S1** which wrongly asserts a `metadata` column (table has `strength`) |
| 5a | entity vocab `{builds_upon,validates,extends,implements,depends_on,supersedes}` forks from `decision_relationships` vocab `{builds_upon,supersedes,conflicts_with,validates,implements,questions}` (share 3/6) | **OPERATOR_DECISION / document-only** | **DOC** reconciliation table in TP-109 (do not force-merge) |
| 5b | entity vs decision relationship table consolidation | **DEFER** (survived) | **DOC** non-goal rationale |
| 6a | authority/source_surface response labels | single-plane = implicitly canonical | **DOC** non-goal |

### 3.5 Dropped / moot (DROP)

| ID | Why closed |
|---|---|
| 4a typed-degradation contract | **DEFER** — devops refutation: over-scoped; keep only the dead-logger fix (B-DEADLOG) |
| 4b DCP facade degradation | **REFUTED** — "unverified premise is false; it IS handled"; verify, then likely no TP-206 amend |
| 4d task-orchestrator 127 placeholders | **DEFER** — cannot substantiate under any lens; separate product TP |
| NEW-search-content-cross-workspace-poison | **REFUTED** — non-issue; recorded to prevent phantom-bug TP effort |
| multi-tenant user_id leaks | **MOOT** — tables absent at runtime (§2) |

### 3.6 Residual / needs-a-probe (from the completeness critic — NOT yet dispositioned)

- **3005 vs 3004 binding** is the pivot for all of §3.3 — re-confirm which surface the orchestrator/agents actually use in production vs dev. (`.mcp.json` says 3005; verify no override.)
- **`info_server` SSE port-mismatch discovery bug** (OPERATOR_DECISION) — auto-config/ADR-2 surface, outside series scope.
- **`recent_activity` view is instance-blind** (worktree multi-instance crosstalk) — consistency gap in the instance model.
- **Second MCP surface parity** (3005 vs 3004 tool sets) frames several per-surface findings; no loaded packet owns cross-surface parity.
- Because discovery was **cap-bounded**, treat §3 as a high-coverage floor, not a ceiling.

---

## 4. Tier-0 foundation design (consensus-validated)

Derived from the gpt-5.2 review + governance (deterministic, append-only, replayable, fail-closed):

1. **Gated, not auto.** Migration apply is an **explicit operator-invoked** action (runner / one-shot job), **never** silent on every server start. Rationale: process-start must not be a state-mutating event.
2. **Idempotent + ordered.** Apply in numeric order; each migration guarded (`IF NOT EXISTS` / advisory-locked) so re-runs are no-ops.
3. **Recorded + checksummed `schema_version`.** Persist applied version **and a checksum of each migration file** in-DB so `schema_version = N` means *the same N everywhere*, not "whatever N was in this image" (tamper-evident chain).
4. **Fail-closed health gate.** If expected migrations are absent or partially applied, the server reports **degraded** and **refuses writes** (reads policy = open question below). Partial-apply ⇒ degraded until a known-good version is reached.
5. **Acceptance test (rebuild-from-zero determinism):** "DB + append-only log of operator actions → rebuild from zero → identical schema + behavior."
6. **No feature packet runs first** — including TP-202 — until the gate is green. (gpt-5.2 explicitly closed the "TP-202 is safe-first" door.)

**Open design questions to resolve when authoring the Tier-0 packet(s):**
- (Q1) Migration history **append-only/audited in-DB** (recommended) vs an external operator log?
- (Q2) When degraded: **read-only** (reads allowed, writes refused) vs **refuse all traffic**?

---

## 5. Coverage matrix (capability × surface × covered-by × verdict)

| Capability | Surface | Covered by | Trinity status | Verdict |
|---|---|---|---|---|
| Decisions/progress/context write | 3005 `server.py` / 3004 `enhanced_server.py` | base schema (live) | canonical | OK; needs §3.3 auth seam (operator) |
| Decision genealogy graph | `decision_relationships` | TP-303 | in-scope | **blocked on T0-MIGRATE** |
| Entity graph (cross-type) | `entity_relationships` | TP-202/203 | in-scope | **blocked on T0-TRAVERSE + T0-MIGRATE** |
| Relationship traversal API | `unified_queries.py` + :2009 handler | TP-203 | in-scope | **dead at runtime → T0-TRAVERSE** |
| Decision retrospective | migration-001 enhanced cols | TP-301 | in-scope | **blocked on T0-MIGRATE** |
| Review reminders | `review_reminders` | TP-302 | in-scope | **blocked on T0-MIGRATE** |
| Search / DCP facade | (no search tool on 3005) | TP-205/206 | in-scope | re-scope: 3005 has no search surface |
| AuthZ / audit / rate-limit | middleware | — | operational (NOT a Trinity non-goal) | **HARDEN** default-off seams |
| Multi-tenant isolation | migration-003 tables | — | absent at runtime | **MOOT** until 003 applied |

---

## 6. DAG-safety & sequencing

- **Amendments (§3.2, §3.4 corrections)** edit only `invariants`/`steps`/`commit.verify` text in packets that already touch the relevant files → **zero `depends_on` changes**; the loaded orchestrator topology (root `44452f53`, 21 edges, recorded `task_orchestrator_uuid`s) stays byte-identical. Re-run `tp:validate` per amended packet.
- **Tier-0** loads as a **separate orchestrator root** that logically blocks TP-202/203/301/302/303; stored as its own tree so it never perturbs `44452f53` (consistent with the orchestrator HTTP-singleton/stdio-contention notes).
- **HARDENING** series (§3.3) sequences strictly after the Stabilize tier (101–109), also a separate root.

---

## 7. Recommended next actions (for operator decision)

1. **Author the Tier-0 foundation packet(s)** per §4 (gated migration runner + checksummed schema_version + fail-closed gate + traversal fix), resolving Q1/Q2. *This is the new critical path.*
2. **Apply the §3.2/§3.4 in-place amendments** to TP-101/106/107/202/203/109 (DAG-safe).
3. **Author the companion `DMX-CONPORT-HARDENING`** series for §3.3 seams (default-off), re-based on :3005.
4. **Reframe TP-301/302/303** notes to depend on Tier-0 (tables/columns come from migrations, which Tier-0 now actually applies).
5. **Close residual probes** (§3.6) — especially confirming the 3005/3004 production binding and curl-testing the traversal endpoint — before finalizing the security verdicts.

> This dossier is the analysis deliverable. The packet authoring (Tier-0 + amendments + HARDENING) is paused pending operator go-ahead and a fresh session budget (the workflow tripped a usage limit). The companion verdict ADR records the durable scope/boundary decisions.
