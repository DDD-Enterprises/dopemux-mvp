# TP-CONPORT-PROJECT-WALL-RECOVERY-2026-08-02 — L3 Freeze Summary

## Supervisor input

`SUPERVISOR_VERDICT=ACCEPT_RUNTIME_RECOVERY_WITH_CONDITIONS`
Risk lane: **L3 red**
Required next verdict: `CONPORT_RECOVERY_READY_FOR_OPERATOR_MERGE_DECISION`
**This freeze does NOT claim that required next verdict.**

## Identity

| Field | Value |
|---|---|
| Repo | `/Users/hue/code/dopemux-mvp` |
| Remote | `https://github.com/DDD-Enterprises/dopemux-mvp.git` |
| Recovery content head | `a39ea663dbf568cb3edf3ae39d756ce86532d07f` |
| Freeze publish branch | `fix/conport-project-wall-recovery-2026-08-02` |
| Draft PR | https://github.com/DDD-Enterprises/dopemux-mvp/pull/1185 |
| Concurrent automation dirt | local only; not committed/pushed |

### Head classification

- **Recovery code content head:** `a39ea663db` (frozen, not rewritten).
- **Proof successor head:** any later commit that only adds `task-packets/TP-CONPORT-*` and `proof/TP-CONPORT-PROJECT-WALL-RECOVERY-2026-08-02/**` — classified as proof/publish metadata, not a silent rebinding of recovery code.

### Why not push to `chore/orchestrator-db-defrag-2026-08-01`

Remote tip moved to `d3dbe23a42` (PR #1182 repair). Local push was non-fast-forward. Supervisor forbade rebase/rewrite of `a39ea663db`. Dedicated freeze branch + draft PR used instead.

## Recovery tip allowlist (`a39ea663db`)

- `compose.yml`
- `docs/03-reference/systems/conport/db-project-wall-and-corpus-recovery-2026-08-02.md`
- `pytest.ini`
- `scripts/migration/import_conport_export.py`
- `scripts/migration/provision_conport_project_db.sh`
- `scripts/migration/rehome_conport_rows.sh`
- `src/dopemux/tools/conport_client.py`
- `tests/conftest.py`

Branch lineage vs `main` also contains prior orchestrator defrag/replan commits (`a905161eb0`, `b457505ddd`).

## Freeze gates

| Gate | Result |
|---|---|
| `git diff --check` origin/main...a39ea | PASS (0) |
| Packet schema (freeze + 4 follow-ups) | see PROOF.json |
| Focused tests (instance_state / start_crit_gaps / conport adapter) | PASS |
| Write-guard before/after custom_data count | PASS (delta=0) |
| Changed-file pre-commit | PASS (0) |
| Secret scan on changed files | PASS (template/title false positives only) |
| Concurrent dirt excluded | PASS |

## L3 evidence (live)

### Data custody

| Item | Value |
|---|---|
| Source export | `docs/archive/generated/conport-migration/conport_export.json` |
| Source SHA-256 | `99e457d6fcdd21bb954987ce0d1eabe35ab442ba9face51db9b91a20d7df5bb6` |
| Source counts | decisions 294, progress 209, context_links 111, system_patterns 3, custom_data 14 |
| Dest DB | `conport_dopemux_mvp` |
| Dest counts | decisions **295**, progress **209**, relationships **219**, ledger **742** |
| Import-tagged decisions | **294**; min `created_at` **2025-10-05 12:50:55+00** |
| Non-import decisions | **1** (expected residual) |
| Ledger kinds | decision 294, progress_entry 209, context_link 110, parent_link 109, custom_data 14, system_pattern 3, legacy_context 2, unresolved_link 1 |
| Missing source IDs | context_link **33** only — ledger key `unresolved_link:33` (dangling target `python-tmux-research` absent from export) |
| Duplicate decision summaries | 0 |
| Deliberately excluded | ChatRipperXXX SQLite (24/63); other unprovisioned projects; pytest rows left in legacy archive |
| Archive non-canonical | runtime `POSTGRES_URL` → `conport_dopemux_mvp`; app role **table INSERT denied** on `dopemux_knowledge_graph` |

### Isolation

| Probe | Result |
|---|---|
| adops → `conport_dopemux_mvp` CONNECT | DENIED |
| mvp → `conport_adops` CONNECT | DENIED |
| mvp → own DB | OK |
| PUBLIC CONNECT on project DBs | false |
| PUBLIC CREATE on project DBs | false |
| mvp → legacy CONNECT | true (no table grants; SELECT/INSERT denied) |
| Runtime discovery | single `mcp-conport`, DSN database `conport_dopemux_mvp` |

### Recovery (autoheal)

Kill `enhanced_server.py` (REST) inside `mcp-conport`:

| Event | t (s) |
|---|---|
| Kill sent | ~6 |
| Docker health → unhealthy | **147** |
| Container restart (StartedAt change) | **166** |
| Healthy + HTTP 200 | **181** |
| 15s later StartedAt stable | yes (no storm in observation window) |

Autoheal log: `Container /mcp-conport ... found to be unhealthy - Restarting container now`.
Same container name/id prefix retained (restart, not foreign replace).

**Gap:** `willfarrell/autoheal` has no proven hard max-restart/alert-stop. Permanent failure can flap indefinitely. Stop-condition risk remains.

### Backup

| Item | Value |
|---|---|
| Public-schema dump SHA-256 | `e353c8cd65fa8e668387333751b114a7d7550833411d595cf57ac80165cc4ba5` |
| Existing age gzip backup SHA-256 | `add7542dd7dc5fa3806e436b902ad1f48b0a0527ac2bed7a743d11cdb541e98a` |
| Disposable restore | postgres:16-alpine + uuid-ossp |
| Restored counts | decisions 295, progress 209, rels 219, ledger 742, import 294, parent_of 109 |
| min created_at | 2025-10-05 12:50:55+00 |
| Disposable cleanup | container removed |

### Test contamination

| Item | Result |
|---|---|
| Guard | autouse patch `InstanceStateManager.save_instance_state` |
| Integration re-run delta | **0** new custom_data rows |
| Residual pytest workspaces in canonical | **2** historical rows (`2026-08-02T22:29Z`, pre-commit timestamp) |
| Production authorized path | REST `/health` healthy on published host port 3019 |

## Follow-up packets (created, not implemented)

1. `TP-CONPORT-MIGRATION-GATE-DEADLOCK-001`
2. `TP-CONPORT-SCHEMA-SEED-SEPARATION-001`
3. `TP-CONPORT-PID1-SUPERVISION-001`
4. `TP-WORKTREE-AUTOMATION-CUSTODY-001`

## Stop conditions evaluation

| Condition | Status |
|---|---|
| Source archive writable by runtime credentials | **cleared** (table write denied; CONNECT residual) |
| Reconciliation cannot account for every migrated record | **cleared** (link 33 quarantined in ledger) |
| Backup cannot be restored | **cleared** (disposable restore verified) |
| Second canonical DB discoverable | **cleared with residual** (legacy exists; runtime selects one) |
| Watchdog can flap indefinitely | **OPEN** — no max-restart/alert-stop proof |
| Tests can still reach canonical ConPort | **OPEN residual** — 2 historical rows; current guard holds |
| Pushed head ≠ audited head | depends on successor proof commit discipline |
| Concurrent automation unclassified changes | **cleared** (not pushed) |
| Audit identity unknown | must be filled by independent audit |
| PR Steward not READY | expected until audit closes |

## Freeze verdict

**NEEDS_SUPERVISOR** for merge readiness.

Operational recovery remains accepted under `ACCEPT_RUNTIME_RECOVERY_WITH_CONDITIONS`.
Do **not** issue `CONPORT_RECOVERY_READY_FOR_OPERATOR_MERGE_DECISION` until:

1. watchdog max-restart/alert-stop proved or accepted via follow-up `TP-CONPORT-PID1-SUPERVISION-001`;
2. residual pytest rows dispositioned;
3. independent audit PASS/PASS_WITH_RISKS with model identity chain;
4. PR Steward READY on exact audited head.
