# Auditor Report — TP-CONPORT-PROJECT-WALL-RECOVERY-L3-FREEZE-001

**Packet series:** `CONPORT-PROJECT-WALL-RECOVERY-2026-08-02`
**Recovery content head:** `a39ea663dbf568cb3edf3ae39d756ce86532d07f`
**Claimed freeze branch:** `fix/conport-project-wall-recovery-2026-08-02`
**Draft PR:** https://github.com/DDD-Enterprises/dopemux-mvp/pull/1185
**Audit time (UTC):** 2026-08-03 (local auditor session)
**Auditor role:** independent freeze/L3 evidence auditor (not implementer)

---

## A) Verdict

# **NEEDS_SUPERVISOR**

**Not PASS** — open stop conditions + incomplete formal audit identity chain.
**Not PASS_WITH_RISKS** — cannot promote while (1) watchdog max-restart/alert-stop unproved, (2) formal Tier-1 auditor route not completed, (3) this auditor family overlaps implementer family.
**Not FAIL** — live evidence under `evidence/**` largely supports custody / isolation / single-child recovery / backup restore / write-guard claims; no falsified recovery claim found that requires overturning `ACCEPT_RUNTIME_RECOVERY_WITH_CONDITIONS`.

Operational recovery remains under prior supervisor input:

`SUPERVISOR_VERDICT=ACCEPT_RUNTIME_RECOVERY_WITH_CONDITIONS`

**`CONPORT_RECOVERY_READY_FOR_OPERATOR_MERGE_DECISION` is NOT allowed from this audit.**

---

## B) Model identity fields

| Field | Value |
|---|---|
| **requested** | Independent auditor different family/runtime than implementer (`grok-4.5`); Tier-1 preference Claude Code CLI Sonnet then Opus |
| **configured** | UNKNOWN as formal `embedded_audit.schema.json` route — this session is a general-purpose reviewer; no Tier-1 CLI (`claude-code-cli` / AGY / Gemini CLI) invocation captured with exit code in this run |
| **response_claimed** | Grok Build general-purpose auditor subagent (xAI family); distinct *session* from implementer; **not** distinct *family* from implementer |
| **proxy_reported** | UNKNOWN (no proxy attestation artifact) |
| **provider_attested** | UNKNOWN (no provider attestation artifact) |

### Identity chain integrity

| Check | Result |
|---|---|
| Implementer agent in PROOF | `grok-4.5` |
| Prior Tier-1 attempt | `review_bundle/auditor_identity_preflight.txt` requested Claude Code CLI; `review_bundle/claude_audit_stdout.txt` = session limit failure |
| This auditor | same vendor family as implementer (xAI/Grok) |
| Schema-representable auditor_model enum | cannot honestly use `sonnet` / `claude-sonnet-4.6` / `opus` / `gemini` |
| Formal independence for merge gate | **FAIL / incomplete** |

Stop condition from SUMMARY: **“Audit identity unknown”** still effectively holds for Tier-1 / provider-attested identity even though a substantive evidence review was performed.

---

## C) Findings

| ID | Severity | Status | Title | Body |
|---|---|---|---|---|
| F-L3-WATCHDOG-INFINITE | **HIGH** | **OPEN** | Autoheal lacks proved max-restart / alert-stop | `compose.yml` autoheal env is only `AUTOHEAL_INTERVAL=15`, `AUTOHEAL_START_PERIOD=60`, `AUTOHEAL_DEFAULT_STOP_TIMEOUT=20`, label filter. Evidence `autoheal/config.txt` matches. No max-restart, backoff ceiling, or alert-stop. Single-child recovery works (~181s); permanent failure can flap indefinitely. Blocks merge-ready verdict per freeze stop conditions. Follow-up packet `TP-CONPORT-PID1-SUPERVISION-001` not implemented. |
| F-L3-AUDITOR-INDEPENDENCE | **BLOCKING** | **OPEN** | Formal independent audit identity incomplete | Tier-1 Claude route failed (session limit). This auditor overlaps implementer family (Grok/xAI). `embedded_audit.schema.json` has no enum for this route. Provider/proxy attestation UNKNOWN. Cannot satisfy “independent audit PASS/PASS_WITH_RISKS with model identity chain” for merge decision. |
| F-L3-RESIDUAL-PYTEST-ROWS | **MEDIUM** | **OPEN** | Two historical pytest instance_state rows remain in canonical DB | `reconciliation_counts.txt`: `pytest_rows=2`. `write_guard_before_after.txt`: before=765 after=765 delta=0. Guard holds now; residual disposition still required for clean READY. |
| F-L3-LEGACY-CONNECT | **MEDIUM** | **ACCEPTED_RISK** | Legacy archive still CONNECT-able by project roles | `isolation_matrix.txt` + `archive_writability.txt`: mvp/adops CONNECT to `dopemux_knowledge_graph` true; table SELECT/INSERT denied; `default_transaction_read_only=off`. Runtime DSN points at `conport_dopemux_mvp`. Acceptable for freeze; prefer REVOKE CONNECT + superuser-only archive later. |
| F-L3-PROCESS-EVIDENCE-GAPS | **MEDIUM** | **OPEN** | Weak pre-kill process selection evidence | `autoheal/ps_before.txt` is **empty**. `autoheal/pid_discovery.txt` is binary/unreadable. Recovery method claim “kill enhanced_server.py (REST)” cannot be independently re-derived from those two files. Timeline + autoheal log + container id stability still support *that a recovery happened*. |
| F-L3-DOC-OVERCLAIM | **LOW** | **OPEN** | Recovery doc overclaims cleanliness / recovery timing vs L3 evidence | Doc before/after table: pytest rows “~236 → **0**”; L3 evidence residual **2** in canonical. Doc autoheal table ~60–98s; L3 timeline unhealthy@147s restart@166s healthy@181s. Evidence is authority; doc soft-wrong on those metrics. |
| F-L3-POST15S-THIN | **LOW** | **OPEN** | 15s post-recovery stability thin | `autoheal/summary.txt` asserts `started_15s_later` equals post-restart StartedAt. `timeline.txt` ends at healthy@181s without extra samples. Accept as weak positive, not storm-disproof under load. |
| F-L3-SCHEMA-AUDITOR-ENUM | **INFO** | **OPEN** | embedded_audit schema cannot record this auditor honestly as non-SKIPPED | Required enums: `auditor_tool` excludes general-purpose/Grok; `auditor_model` excludes Grok. Existing author-time object also used invalid finding status `ACCEPTED_RISK_FOR_FREEZE` (fixed to `ACCEPTED_RISK` in this update). |
| F-L3-GIT-SHOW-SHELL | **INFO** | **OPEN** | Live `git show a39ea663db --stat` not re-executed in this auditor process | No shell in this auditor tool surface. Mitigations: `.git/refs/remotes/origin/fix/conport-project-wall-recovery-2026-08-02` = `a39ea663db…`; local `chore/orchestrator-db-defrag-2026-08-01` tip same SHA; reflog commit message `fix(conport): build project wall, recover 2025 corpus, stop silent outage`. Full `--stat` file list **NOT_RUN** live here. |
| F-L3-SOURCE-REHASH | **INFO** | **OPEN** | Source export SHA not rehashed in this session | Path exists: `docs/archive/generated/conport-migration/conport_export.json`. Claimed SHA-256 in evidence JSON only; live `shasum` **NOT_RUN**. |
| F-L3-CUSTODY-OK | **INFO** | **RESOLVED** | Custody ledger accounts for source with one quarantine | See §D custody. |
| F-L3-ISOLATION-OK | **INFO** | **RESOLVED** | Bidirectional project-wall CONNECT deny evidenced | See §D isolation. |
| F-L3-BACKUP-OK | **INFO** | **RESOLVED** | Disposable restore counts match destination claims | See §D backup. |
| F-L3-WRITE-GUARD-OK | **INFO** | **RESOLVED** | conftest write guard present; re-run delta 0 | See §D contamination. |

---

## D) L3 section satisfaction

| L3 section | Satisfied? | Evidence basis | Residual |
|---|---|---|---|
| **Custody** | **YES** (with documented quarantine) | `source_export_counts.json` SHA + counts; `source_ledger_reconcile.json` missing only context_link `33` → `unresolved_link`; `ledger_kinds.txt` sums to 742; `reconciliation_counts.txt` import 294 + non-import 1; dest decisions 295; timestamps min `2025-10-05 12:50:55+00`; excluded ChatRipperXXX + unprovisioned projects recorded; archive non-canonical + table write denied | Live rehash of export **NOT_RUN**; archive CONNECT residual |
| **Isolation** | **YES** (wall holds; legacy CONNECT residual) | `isolation_matrix.txt`: adops↛mvp CONNECT deny; mvp↛adops CONNECT deny; PUBLIC CONNECT/CREATE false on project DBs; mvp own DB OK; runtime `POSTGRES_URL` → `conport_dopemux_mvp` | mvp/adops still CONNECT to legacy `dopemux_knowledge_graph` |
| **Recovery** | **PARTIAL — single-child YES; bound YES on flap** | Timeline: kill~6s, unhealthy 147s, StartedAt change 166s, healthy+HTTP200 181s; container id prefix stable `9f2b390f67fb`; autoheal log restart line; compose label `autoheal=true` + autoheal service present | **No** max-restart/alert-stop; empty `ps_before`; binary `pid_discovery`; doc timing drift |
| **Backup** | **YES** | `public_sql.sha256` `e353c8cd…`; `existing_age_backup.sha256` `add7542d…`; `restore_verify.txt` decisions 295 / progress 209 / rels 219 / ledger 742 / import 294 / parent_of 109 / min_created match | Dump bytes themselves under `/tmp/...` not retained in proof tree (hashes only) — acceptable if operator still holds dumps |
| **Contamination** | **YES current path; residual historical OPEN** | `tests/conftest.py` autouse `_block_live_conport_writes` patches `InstanceStateManager.save_instance_state` → return False; no env-port side effects; `write_guard_before_after.txt` delta=0; 2 residual pytest workspaces listed in reconciliation | Residual 2 rows not dispositioned; guard is method-patch of one writer path — other write entrypoints not proved exhaustively in this freeze evidence set |

### Code / compose cross-check (repo working tree at head `a39ea663db`)

| Surface | Observed |
|---|---|
| `tests/conftest.py` | Autouse fixture patches `InstanceStateManager.save_instance_state`; rationale documents env-only guard failure |
| `compose.yml` mcp-conport | `labels: [autoheal=true]`; `CONPORT_DB_*` DSN wiring |
| `compose.yml` autoheal | `willfarrell/autoheal:latest`; socket mount; **no** max-restart env |
| Migration scripts allowlist paths | `import_conport_export.py`, `provision_conport_project_db.sh`, `rehome_conport_rows.sh` present under `scripts/migration/` |
| Recovery doc | Present at claimed path; narrative mostly consistent; metric overclaims noted above |

### Git head binding

| Check | Result |
|---|---|
| Remote freeze branch tip | `origin/fix/conport-project-wall-recovery-2026-08-02` → `a39ea663dbf568cb3edf3ae39d756ce86532d07f` |
| Local branch tip carrying same commit | `chore/orchestrator-db-defrag-2026-08-01` → same SHA |
| Reflog message | `fix(conport): build project wall, recover 2025 corpus, stop silent outage` |
| Live `git show --stat` | **NOT_RUN** (no shell) |
| History rewrite | No rewrite performed by this auditor; do not rewrite |

---

## E) Stop conditions — do they trigger?

From freeze SUMMARY stop table, re-evaluated:

| Condition | Auditor status | Triggers stop? |
|---|---|---|
| Source archive writable by runtime credentials | **cleared** (table R/W denied; CONNECT residual only) | No |
| Reconciliation cannot account for every migrated record | **cleared** (link 33 quarantined in ledger) | No |
| Backup cannot be restored | **cleared** (disposable restore verified in evidence) | No |
| Second canonical DB discoverable | **cleared with residual** (legacy exists; runtime selects project DB) | No (residual risk only) |
| Watchdog can flap indefinitely | **OPEN** | **YES** |
| Tests can still reach canonical ConPort | **OPEN residual** (2 historical rows; current guard holds) | **YES (soft / residual)** |
| Pushed head ≠ audited head | Recovery content head matches remote freeze tip `a39ea663db`; proof metadata may be successor — discipline required | Conditional |
| Concurrent automation unclassified changes | Author claims local-only; not re-verified live by this auditor | UNKNOWN→treat as residual |
| Audit identity unknown / incomplete | **OPEN** (Tier-1 failed; this auditor non-Tier-1 / family overlap) | **YES** |
| PR Steward not READY | `PROOF.json` `pr_steward_ready: NOT_RUN` | **YES** (expected until READY) |

**Stop conditions trigger: YES** — at least watchdog flap, audit identity, PR Steward, residual pytest.

Packet rule: *Stop with NEEDS_SUPERVISOR if any stop condition holds.* → obeyed.

---

## F) `CONPORT_RECOVERY_READY_FOR_OPERATOR_MERGE_DECISION`

### **NOT ALLOWED**

Required before that verdict (from freeze SUMMARY + packet invariants):

1. Watchdog max-restart/alert-stop **proved** or **explicitly supervisor-accepted** with open follow-up `TP-CONPORT-PID1-SUPERVISION-001` bound.
2. Residual pytest rows dispositioned (delete/quarantine/accept with owner).
3. Independent audit **PASS** or **PASS_WITH_RISKS** with complete model identity chain from a **Tier-1 or supervisor-approved** route that is **family-distinct** from implementer.
4. PR Steward **READY** on exact audited head SHA.

None of 1–4 fully closed at this audit.

**Also must not:** merge PR #1185 from this report alone; delete source export archive; rewrite `a39ea663db`; claim final packet complete.

---

## Evidence inventory reviewed

| Path | Role |
|---|---|
| `SUMMARY.md` | Freeze narrative + stop table |
| `PROOF.json` | Structured claims + prior embedded_audit stub |
| `evidence/source_export_counts.json` | Source SHA/counts |
| `evidence/source_ledger_reconcile.json` | Missing ID accounting |
| `evidence/ledger_kinds.txt` | Ledger kind histogram |
| `evidence/rel_types.txt` | Relationship types |
| `evidence/reconciliation_counts.txt` | Dest counts + residual pytest |
| `evidence/isolation_matrix.txt` | Project wall + ACL |
| `evidence/archive_writability.txt` | Archive R/W deny + runtime DSN |
| `evidence/write_guard_before_after.txt` | delta=0 |
| `evidence/autoheal/*` | Config, timeline, log, summary, listeners |
| `evidence/backup/*` | SHA files + restore verify |
| `docs/03-reference/systems/conport/db-project-wall-and-corpus-recovery-2026-08-02.md` | Operator recovery record |
| `tests/conftest.py` | Write guard |
| `compose.yml` | autoheal + conport labels/DSN |
| `review_bundle/*` | Failed Claude Tier-1 preflight |
| Git refs/logs | Head binding to `a39ea663db` |

### Missing / unusable artifacts

- `evidence/autoheal/ps_before.txt` empty
- `evidence/autoheal/pid_discovery.txt` binary
- Live `git show --stat`
- Live source export rehash
- PR Steward READY artifact
- Max-restart proof

---

## Consistency notes (non-blocking unless noted)

1. Source context_links 111 vs ledger context_link 110 + unresolved_link 1 — **consistent**.
2. parent_link 109 + context_link 110 = 219 entity_relationships — **consistent** with dest rels / restore.
3. decisions 294 import-tagged + 1 non-import = 295 — **consistent**.
4. Doc “0 pytest rows” vs evidence 2 — **doc overclaim** (LOW).
5. Author-time `freeze_verdict: NEEDS_SUPERVISOR` and `merge_ready: false` — **correct posture**; this audit **keeps** that posture.

---

## What this audit does *not* claim

- Live DB re-query (used frozen evidence files only).
- Full suite re-run.
- Secret scan / pre-commit re-run.
- Security sign-off on Docker socket autoheal for multi-tenant hosts (compose already warns).
- Approval to merge.

---

## Required next actions (ordered)

1. **Supervisor:** either accept watchdog flap risk bound to `TP-CONPORT-PID1-SUPERVISION-001`, or require proof of max-restart/alert-stop before merge decision.
2. **Tier-1 re-audit** (Claude Code Sonnet/Opus preferred) after session limit clears — fill non-UNKNOWN identity quintuple with provider attestation where available.
3. Disposition residual 2 pytest rows in canonical DB.
4. PR Steward READY on exact audited head (content head `a39ea663db` and/or declared proof-successor head per `head_classification`).
5. Only then consider `CONPORT_RECOVERY_READY_FOR_OPERATOR_MERGE_DECISION`.

---

## Auditor sign-off

| Item | Value |
|---|---|
| Verdict | **NEEDS_SUPERVISOR** |
| Merge decision allowed | **NO** |
| Recovery evidence broadly credible | **YES** under `ACCEPT_RUNTIME_RECOVERY_WITH_CONDITIONS` |
| Confidence | **high** on evidence-file consistency; **medium** on live runtime (not re-probed); **certain** that merge-ready verdict is not earned |
| History rewrite | none |
| Archives deleted | none |
| Merge performed | none |
