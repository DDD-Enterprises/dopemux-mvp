# Formal Independent Audit — PR #1188 (ConPort Clean L3 Recovery)

## 1. Identity Block

| Field | Value |
|---|---|
| Tool | Claude Code CLI |
| Model | Sonnet 5 (`claude-sonnet-5`), self-attested via harness system context — this is a first-party runtime declaration, not a probed/inferred value |
| Session role | Independent formal auditor — no code in this PR was authored by this session |
| Implementer | Grok-4.5 (per `PROOF.json.agent`) |
| Independence | Confirmed. This session has made zero writes to source/impl/script files; only read/git/grep tools were used against the frozen content head |
| Note | An untracked `review_bundle/CLAUDE_IDENTITY_PREFLIGHT.txt` from a prior, incomplete audit attempt (empty stdout/stderr companions) exists in the worktree. It is stale and not part of this audit's basis — this report supersedes it |

## 2. Scope

- **Content head audited**: `95bdf0015730ab3087cf71e07eca2d4425b214ac` (= current branch tip, confirmed via `git rev-parse HEAD`)
- **Base**: `origin/main` = `fb710ef40500695882a5b421a3325150176fffa1` (verified current, not stale — `fb710ef405` is an ancestor of `origin/main` and `origin/main`'s tip equals it exactly)
- **Diff reviewed**: `git diff fb710ef405..HEAD` — 100 files, +3932/−21, across `compose.yml`, `docker/mcp-servers-source/conport/{start_with_info.sh,tests/test_start_with_info_supervision.py}`, `scripts/migration/{provision_conport_project_db.sh,rehome_conport_rows.sh,lock_legacy_conport_archive.sh,import_conport_export.py}`, `src/dopemux/tools/conport_client.py`, `tests/conftest.py`, `pytest.ini`, task-packets, docs, and the full `proof/TP-CONPORT-CLEAN-L3-RECOVERY-2026-08-02/` bundle
- **Commits inspected individually**: all 11 commits from `fb710ef405..HEAD`, including verifying the 4 trailing "proof-only" commits (`a4e4c877fb`, `aada46b59a`, `fd04b9406c`, `95bdf00157`) touch only `proof/` metadata, and that merge commit `5ab419b9e3` introduces no manual-resolution drift (non-proof diff vs `fb710ef405` is byte-identical in scope to the branch's own 13 authored files)
- Not modified by this session: confirmed via read-only tool usage throughout

## 3. Findings

| ID | Severity | Summary | Status |
|---|---|---|---|
| F-DOC-STALE-AUTOHEAL | MEDIUM | `docs/03-reference/systems/conport/db-project-wall-and-corpus-recovery-2026-08-02.md` describes outage prevention as a third-party **autoheal container + `docker.sock` + labels** (with its own before/after table and a `kill -9 $(pidof python...)` "autoheal regression test" showing 60s/78s/98s timings), which is a materially different, superseded design. The actually-shipped mechanism (verified in `compose.yml` and `start_with_info.sh`) explicitly states *"Third-party autoheal + docker.sock is intentionally NOT used"* and uses in-process PID1 supervision instead. The doc's "Latent bugs found, not fixed" §3 (info server binding 4005 vs 4004) is also stale — that bug **was fixed** later in this same branch (commit `6f4d6b11e3`, confirmed live in `start_with_info.sh` lines 84-89). | OPEN (non-blocking) |
| F-EVIDENCE-FAILED-PROBES | LOW | `evidence/refresh/pid1/{kill_rest,kill_info,kill_mcp}.txt` each record an initial substring-`pkill`-based kill attempt that **did not actually terminate the target child** (identical PIDs and unchanged `RestartCount` before/after, explicit `RECOVERY_TIMEOUT_OR_FAIL` logged for all three). The team correctly retried with a precise per-PID kill method (`host_kill_rest.txt`, `probe_kill_info.txt`, `probe_kill_mcp.txt`), which succeeded with real `RestartCount` increments and full boot logs — so the underlying supervision behavior **is** genuinely proven for all three required children. But the failed-probe files remain undisambiguated in the bundle, and `SUMMARY.md`'s clean "2s/5s/5s" recovery table does not disclose the earlier failed attempts. Evidence-hygiene issue, not a functional defect. | ACCEPTED_RISK |
| F-PID1-TESTS-STUB-ONLY | LOW | `test_start_with_info_supervision.py`'s kill/recovery/budget assertions run against a hand-written **stub reimplementation** of the supervisor logic, not the production `start_with_info.sh` via subprocess. Only `test_production_script_contains_fail_closed_contract` touches the real file, via shallow substring checks (`"wait -n" in text`, forbidden-pattern absence) rather than execution. `pid1_unit_tests: PASS` in `PROOF.json` therefore certifies the stub + the real script's textual shape, not the real script's executed behavior — that assurance comes entirely from the live-container evidence (which is adequate, per F-EVIDENCE-FAILED-PROBES resolution above). | ACCEPTED_RISK |

No CRITICAL or BLOCKING findings identified. No evidence of secrets, injection vectors, or destructive/irreversible operations in the reviewed scripts.

## 4. Topic-by-Topic Verdicts

**1. Authority and database boundaries (project wall, roles, CONNECT)** — **PASS**. `provision_conport_project_db.sh` creates one DB+role per project, revokes `CONNECT` from `PUBLIC`, whitelist-validates `--slug` against `^[a-z][a-z0-9_]{0,40}$` before SQL interpolation (no injection surface). Live evidence (`live_connect_mvp.txt`, `live_connect_adops.txt`, `privilege_matrix.txt`) shows genuine `psql` connection attempts with real `FATAL: permission denied` errors for mvp↔adops↔legacy cross-connect — not a config-file grep, an actual runtime probe.

**2. Migration correctness and idempotence** — **PASS**. `import_conport_export.py` uses a `_migration_ledger` in `custom_data` (`UNIQUE(workspace_id, category, key)`, `ON CONFLICT ... DO NOTHING`) keyed by old-ID, resolving relationships through the ledger map rather than content-matching (avoids collision risk with 294+209 near-duplicate summaries). This explicitly fixes 4 named defects in a prior non-idempotent script. `rehome_conport_rows.sh` is not strictly idempotent (no `ON CONFLICT`) but every copied table has a UUID `PRIMARY KEY`, so accidental re-run fails loudly on PK collision rather than silently duplicating — fail-closed, acceptable.

**3. Archive custody (legacy lock, archive_ro)** — **PASS**. `lock_legacy_conport_archive.sh` is idempotent (checked), revokes `CONNECT`/table grants from project roles and `PUBLIC` on the legacy DB, grants `SELECT`-only to `conport_archive_ro`, and does not drop/mutate legacy data. Live evidence (`archive_ro.txt`, `isolation/roles.txt`) confirms `archive_ro` cannot log in directly (`NOINHERIT`, no `LOGIN`) and has read-only grants.

**4. PID 1 supervision (start_with_info.sh wait -n, child death, siblings)** — **PASS, with F-PID1-TESTS-STUB-ONLY / F-EVIDENCE-FAILED-PROBES noted**. `start_with_info.sh` is `CMD` (no competing init/tini in the Dockerfile or compose), runs three children, uses `wait -n $CHILDREN` (a real bash 4.3+ multi-PID edge, correctly available on the `python:3.11-slim`/Debian base), identifies the dead child, `TERM`→`KILL`s siblings, records the failure, and `exit 1`s unconditionally so Docker's `restart: unless-stopped` recovers. Live kill/recovery is genuinely proven for all three children (REST, info, mcp-proxy) once the correct kill method was used.

**5. Bounded restart / failure budget / terminal alert** — **PASS**. `terminal_alert_probe.txt` shows a real drive-to-5-failures sequence producing `TERMINAL_ALERT` marker with correct fields, subsequent container entering a non-exiting `sleep 3600` loop (no restart storm), healthchecks correctly failing (`curl: (7) Failed to connect`) while the container itself stays `running` per Docker. `terminal_restore.txt` confirms operator-clear path exists.

**6. Rollback** — **PASS (implicit, not a named runbook)**. No dedicated "rollback" doc/section exists, but the design is rollback-by-construction: `rehome_conport_rows.sh` never mutates/deletes the source DB (`dopemux_knowledge_graph` retained intact, explicitly documented as reversible — "stop using the new database and nothing has been lost"); `lock_legacy_conport_archive.sh` only revokes grants, does not delete; row-cleanup used an exported+SHA256-verified backup before a transactional `DELETE` (`BEGIN`/`DELETE 2`/`COMMIT`). A named rollback runbook is a reasonable follow-up but its absence is not blocking given the underlying operations are already non-destructive/reversible.

**7. Write-guard enforcement** — **PASS**. `tests/conftest.py`'s `_block_live_conport_writes` autouse fixture patches `InstanceStateManager.save_instance_state` at the actual network chokepoint (not env vars, which the doc/code comments show were measured and found insufficient against a live ConPort — `resolve_conport_port(3004)` returns `3019` regardless of env because explicit args outrank env in precedence). Live evidence: `write_guard_after_delete.txt` (`before=763 after=763 delta=0`), `write_guard_tests.txt` (suite green), and `write_probe.txt` shows one **authorized** production write + cleanup DELETE, distinct from the guarded test path.

**8. Backup restoration evidence** — **PASS**. `data/backup_restore.txt` shows a real `pg_dump`→disposable-DB restore→count-match (`295/209/219/742` matching source) → disposable DB removed. `row_cleanup/backup_pre_delete.sha256` binds a SHA256 of the pre-delete backup.

**9. Proof-to-head binding** — **PASS, with a noted structural limitation**. Current `HEAD` (`95bdf00157`) matches the task's stated content head exactly. `PROOF.json`'s internal `content_head_frozen` field (`fd04b9406c`) necessarily lags `HEAD` by one commit — a proof file committed at SHA X cannot self-reference SHA X. The task correctly resolved this by specifying the audit head externally rather than trusting the file's self-reference; the final commit (`95bdf00157`) touches only `PROOF.json` + `review_bundle/CODEX_IDENTITY_*` (verified via `git show --stat`), no code.

**10. Absence of unrelated content (#1182, replan, policy churn)** — **PASS**. The merge commit `5ab419b9e3` pulls in #1182/#1184/#1187-originated files (e.g. `scripts/governance/validate_change_contract.py`, `proof/pr_merge/embedded-audit/pr-118{4,7}/`) but these arrive **from origin/main's side of the merge** — they predate `fb710ef405` (the diff base) and do not appear in `git diff fb710ef405..HEAD`. The actual PR diff's 13 non-proof files are exactly the ConPort recovery + PID1 + lock-script set; confirmed no `#1182` replan/wave-annotation files anywhere in the diff.

## 5. Final Verdict

**PASS_WITH_RISKS**

The core engineering (project wall, PID1 supervision, archive lock, migration idempotence, write-guard, backup/restore) is sound and independently, genuinely verified via live runtime evidence — not grep-as-verify. The residual risks are documentation/evidence-hygiene issues, not functional defects in the shipped code.

## 6. Residual Risks (bounded)

1. **Stale doc** (F-DOC-STALE-AUTOHEAL): `docs/.../db-project-wall-and-corpus-recovery-2026-08-02.md` describes an autoheal-container design that was superseded by PID1 supervision within the same branch, and misreports the info-port bug as unfixed. Should be corrected before/shortly after merge — an operator following its "Reproduce / verify" section will look for a nonexistent `autoheal` service.
2. **Evidence-bundle noise** (F-EVIDENCE-FAILED-PROBES): failed initial kill probes remain in the bundle without a note distinguishing them from the successful retries that actually establish the PASS verdicts.
3. **Unit-test fidelity gap** (F-PID1-TESTS-STUB-ONLY): the automated regression suite for PID1 supervision tests a stub, not the real script's execution; live-kill evidence currently substitutes for this but is a manual, one-time verification, not CI-repeatable.

None of these block merge on their own; #1 should be fixed to avoid misleading future operators.
