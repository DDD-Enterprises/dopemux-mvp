# TP-CONPORT-CLEAN-L3-RECOVERY — Clean candidate summary


## Stage-2 refresh (2026-08-03)

Supervisor: `AUTHORIZE_STAGE_2_REFRESH_AND_VALIDATION_ONLY`

| Role | SHA |
|---|---|
| Pre-refresh tip | `2f4303a1be` |
| Merged main | `fb710ef405` |
| Merge commit | `5ab419b9e3` |
| Overlap | COMPATIBLE (0 paths) |
| Impl blob identity | IDENTICAL (13 non-proof paths) |

See `evidence/refresh/VALIDATION_SUMMARY.md` and `evidence/refresh/REFRESH_RECORD.md`.

Policy PR #1187 merged on main. Baseline doctor placeholder failure is BASELINE_EXISTING (main+branch).

## Supervisor

`AUTHORIZE_ONE_CLEAN_L3_REPAIR`
Required next: `CONPORT_RECOVERY_CLEAN_CANDIDATE_READY_FOR_OPERATOR_MERGE_DECISION`
PR #1185 retained as custody evidence (not merge candidate).

## Heads

| Role | SHA |
|---|---|
| Base | `origin/main` `525ddb5fe5` |
| Clean recovery transplant (8 files == a39ea) | `80e3ed2f42` |
| Content tip (PID1 + wall + pins) | see branch tip after proof commit |
| Recovery source (not rebased) | `a39ea663db` |

## Patch identity

All eight recovery files blob-match `a39ea663db` at transplant commit `80e3ed2f42` (see `evidence/patch_identity/identity.txt`).

Tip vs main contains only ConPort recovery + PID1 + lock script. **No PR #1182 files.**

## Delivered

1. Clean worktree/branch from `origin/main`
2. PID1 supervision (`start_with_info.sh` wait -n, exit 1; failure budget; no autoheal/docker.sock)
3. Project wall: legacy CONNECT revoked for project roles
4. Two historical pytest rows deleted after export+backup
5. Separate PR Steward policy restore (PR #1187)

## Live PID1 recovery (bash builtin kill)

| Child killed | Recovered (s) |
|---|---|
| enhanced_server (REST) | **2** |
| server.py sse (MCP) | **5** |
| info_server | **5** |

Docker `restart: unless-stopped`; container name `mcp-conport` stable; no foreign worktree replace.

## Wall

- mvp ↛ adops CONNECT: denied
- adops ↛ mvp CONNECT: denied
- mvp ↛ legacy CONNECT: **denied** (post lock)
- PUBLIC CONNECT/CREATE on project DBs: false
- archive role CONNECT to legacy: true

## Row cleanup

- Exported 2 rows; provenance pytest/tmp; pre-guard timestamps
- Backup SHA: `e2f1b8806505532ec08985dbc0ed18b728bc5cdc439d939e1a43b3c68ba6615a`
- DELETE 2 exact IDs; custom_data 765→763; decisions 295; ledger 742
- pytest residual **0**; write-guard delta **0** after delete

## Residual / blockers for READY

- Independent Tier-1 audit (non-Grok) still required on exact tip
- PR #1187 (policy) must merge first
- PR Steward READY on audited head after policy lands
- Permanent-failure terminal budget proved in unit tests; live 5-failure storm not re-run (bounded by unit + config)

## Do not

- Merge PR #1185
- Delete source export archive
- Force-push or rewrite a39ea / #1185 branch
