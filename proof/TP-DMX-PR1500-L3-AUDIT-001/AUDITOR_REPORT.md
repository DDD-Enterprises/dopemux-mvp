# AUDITOR REPORT — PR #1500 L3 embedded audit (TP-DMX-PR1500-L3-AUDIT-001)

- **Governing auditor**: Grok CLI 1.0.70, `grok-4.5`, tool-less recipe, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Corroborating auditor**: AGY 1.5.0, `gemini-4-argon-high`, same prompt
- **Implementer**: Claude Code (claude-opus-5-5, one session), a different runner and model family from both auditors
- **Audited head**: `9fbd5fe27da6b21b58c59df34a34c14671ab5007` · **Base**: `583720375df69fbe50f7b8a6b199eaf026f46fb5` (main, the merge-base)
- **Verdict**: **PASS_WITH_RISKS** · validation inside the audit: NOT_RUN
- **Containment**: `init.tools == []`, 0 tool_use blocks
- **Input**: 62,985 tokens; all 13 changed files with full file text; delivery token echoed
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: raw streams, stderr and wrapper exit lines are in `review_bundle/`

## Auditor return (verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    {
      "severity": "medium",
      "id": "F1",
      "title": "Advisory lock only covers dopemux auth writers",
      "evidence": "src/dopemux/auth/hashfile.py exclusive_lock docstring and write_hashes/write_meta: writers must call exclusive_lock; write_hashes/write_meta do not self-lock. Hand edit of memory-token-hashes.json bypasses mutual exclusion (disclosed).",
      "detail": "A concurrent non-CLI writer or manual edit can still race with CLI apply paths."
    },
    {
      "severity": "medium",
      "id": "F2",
      "title": "filelock version floor untested",
      "evidence": "hashfile.py imports filelock.FileLock; disclosed only 3.25.2 tested while dependency allows >=3.12.0. filelock 3.25 deletes lock file on release and rechecks st_nlink.",
      "detail": "Older allowed filelock builds may lack the st_nlink recheck; mutual exclusion under those versions is not evidenced here."
    },
    {
      "severity": "medium",
      "id": "F3",
      "title": "auth_identity.py changes require image rebuilds not run in CI",
      "evidence": "docker/mcp-servers-source/conport/auth_identity.py and services/working-memory-assistant/auth_identity.py both change _PRINCIPAL_RE/_SHA256_HEX_RE to \\Z; disclosed no image build in CI.",
      "detail": "Deployed memory images keep old $ anchors until rebuilt."
    },
    {
      "severity": "low",
      "id": "F4",
      "title": "Missing filelock yields ImportError not HashFileError",
      "evidence": "hashfile.py exclusive_lock: from filelock import FileLock, Timeout inside the CM; auth_commands apply paths catch (AuthError, OSError) only.",
      "detail": "Fail-closed (no unlocked apply) but operator message is a traceback rather than the HashFileError path."
    },
    {
      "severity": "low",
      "id": "F5",
      "title": "Pre-existing keychain/hash partial-failure window unchanged",
      "evidence": "auth_commands issue/rotate: store_token then write_hashes inside exclusive_lock; disclosed crash between keychain write and hash write still orphans keychain item.",
      "detail": "Not worse than PR 1498; revoke still removes hash before delete_token so a revoked hash does not survive a failed keychain delete."
    },
    {
      "severity": "low",
      "id": "F6",
      "title": "Test-only principal pattern still uses $",
      "evidence": "tests/unit/runner_memory_2a_r2_w06/test_local_writer_principals.py PRINCIPAL_RE = re.compile(...$); production _INTERNAL_PRINCIPAL_RE in capture_client.py uses \\Z.",
      "detail": "Does not affect runtime identity checks."
    }
  ],
  "risks": [
    "Lock is advisory and CLI-only; same-user hand edits or future callers of write_hashes without exclusive_lock reintroduce lost-update races.",
    "Only filelock 3.25.2 evidenced; pyproject allows older 3.12+ where delete-on-release / st_nlink behaviour may differ.",
    "No real macOS keychain or live server validation in this message; stub security only.",
    "Both memory images must be rebuilt for \\Z server-side; CI at this head did not build them (implementer claim).",
    "Crash/SIGKILL after keychain store_token and before write_hashes still leaves keychain ahead of hash file (pre-existing).",
    "Overlap tests use 0.5s window and Thread + store_token wrap; extreme scheduling could hide a missing lock (implementer notes slow machine hides bug, never fails a correct build).",
    "Library internals of filelock (deleted lock file vs waiter holding old fd) cannot be verified from this message alone."
  ],
  "rationale": "Apply paths for issue, rotate and revoke load hashes, run keychain ops and both atomic writes inside hashfile.exclusive_lock with preconditions re-checked under the lock; dry-run and list correctly stay unlocked. exclusive_lock maps filelock Timeout to HashFileError and releases in a finally around yield, so AuthError/OSError/ClickException paths release. Six production identity/token patterns move from $ to \\Z; principal and writable-token character classes still exclude whitespace and shell metacharacters in the security -i line. Overlap and newline tests exercise the named defects and would fail if lock or anchors regressed. Residual risks are advisory scope, untested filelock floor, unrebuilt images, and pre-existing partial-state orphans—not an open restore-revoked-hash race in the CLI writers. Instruction-like scanner reported detected=false. Auditor validation_status is NOT_RUN; implementer CI/unit claims are treated as claims only.",
  "inspected_paths": [
    "docker/mcp-servers-source/conport/auth_identity.py",
    "services/working-memory-assistant/auth_identity.py",
    "src/dopemux/auth/hashfile.py",
    "src/dopemux/auth/keychain.py",
    "src/dopemux/auth/tokens.py",
    "src/dopemux/commands/auth_commands.py",
    "src/dopemux/memory/capture_client.py",
    "tests/unit/runner_memory_2a_r2_w01/test_auth_identity.py",
    "tests/unit/runner_memory_2a_r2_w02/test_auth_identity.py",
    "tests/unit/runner_memory_2a_r2_w03/test_auth_commands.py",
    "tests/unit/runner_memory_2a_r2_w03/test_auth_helper.py",
    "tests/unit/runner_memory_2a_r2_w03/test_auth_overlap.py",
    "tests/unit/runner_memory_2a_r2_w06/test_local_writer_principals.py"
  ],
  "evidence_refs": [
    "src/dopemux/commands/auth_commands.py: issue/rotate/revoke --apply bodies wrap load_hashes, store_token/delete_token, write_hashes, write_meta in with hashfile.exclusive_lock()",
    "src/dopemux/auth/hashfile.py: exclusive_lock FileLock(auth_dir/LOCK_FILE_NAME, mode=0o600), LOCK_TIMEOUT_SECONDS=30.0, Timeout->HashFileError, try/yield/finally release",
    "src/dopemux/auth/keychain.py: _WRITABLE_TOKEN_RE ...\\Z; store_token builds add-generic-password line with principal and token",
    "src/dopemux/auth/tokens.py: PRINCIPAL_RE ...\\Z",
    "src/dopemux/memory/capture_client.py: _INTERNAL_PRINCIPAL_RE ...\\Z",
    "docker/mcp-servers-source/conport/auth_identity.py and services/working-memory-assistant/auth_identity.py: _PRINCIPAL_RE and _SHA256_HEX_RE ...\\Z",
    "tests/unit/runner_memory_2a_r2_w03/test_auth_overlap.py: revoke-vs-issue/rotate, dual issue/rotate, busy lock, cross-process contention to 100",
    "instruction_like_scan_summary: detected=false"
  ],
  "validation_status": "NOT_RUN",
  "model_self_reported": "grok-4.7",
  "delivery_token": "7b70c3814838c28f2b54d8cd10199493",
  "question_results": [
    {
      "id": "Q1",
      "result": "PASS",
      "evidence": "auth_commands.py issue/rotate/revoke apply: with hashfile.exclusive_lock(): load_hashes, _require_* (issue/rotate), keychain store/delete, write_hashes, write_meta all inside. Dry-run/list intentionally unlocked. write_hashes/write_meta themselves do not take the lock (caller contract)."
    },
    {
      "id": "Q2",
      "result": "PASS",
      "evidence": "hashfile.exclusive_lock creates FileLock on a fixed path per call; filelock coordinates across threads/processes on that path. Contention test (4 processes × 25) expects counter==100. Cannot verify from this message: filelock 3.25.2 source for deleted lock file + waiter holding old fd, Soft vs Unix backend, or behaviour of allowed <3.25 versions."
    },
    {
      "id": "Q3",
      "result": "PASS",
      "evidence": "exclusive_lock: acquire; try/yield/finally release. Timeout -> HashFileError from None (no unlocked proceed). Exceptions from the with-block propagate after finally; CM does not swallow. KeyboardInterrupt in the block still runs finally via contextlib. SIGKILL: OS drops flock; lock file may remain—unverified library recovery."
    },
    {
      "id": "Q4",
      "result": "PASS",
      "evidence": "Apply always enters exclusive_lock first; busy lock raises HashFileError. _ensure_private_dir OSError before acquire; apply catches OSError. Missing filelock: ImportError before any secret write (fail closed, not HashFileError). LOCK_TIMEOUT_SECONDS=30 > keychain TIMEOUT_SECONDS=10 write+read-back."
    },
    {
      "id": "Q5",
      "result": "PASS",
      "evidence": "Failure before write_hashes: hash unchanged. After store_token before write_hashes: orphaned/mismatched keychain (disclosed, pre-existing). Revoke writes hash removal then meta then delete_token; failed delete leaves hash removed so revoked hash does not verify. Lock closes the revoke-then-restore race tested in test_auth_overlap.py."
    },
    {
      "id": "Q6",
      "result": "PASS",
      "evidence": "Lock at ~/.config/dopemux/auth/memory-token-hashes.lock, FileLock mode=0o600, dir chmod 0700 via _ensure_private_dir. Same-user home; other accounts blocked by modes. Servers only read hash JSON (mtime/size refresh); extra lock file does not change reader protocol. Symlink attacks on 0700 auth_dir require same-user (stated non-protection class)."
    },
    {
      "id": "Q7",
      "result": "PASS",
      "evidence": "Fixed to \\Z: tokens.PRINCIPAL_RE, keychain._WRITABLE_TOKEN_RE, capture_client._INTERNAL_PRINCIPAL_RE, both servers' _PRINCIPAL_RE and _SHA256_HEX_RE. \\Z rejects trailing newline that $ accepted; other inputs unchanged. Server patterns match each other and CLI principal class. Left $ patterns (migrations/version/Codex heading) are not identity checks. Test-only w06 PRINCIPAL_RE still uses $."
    },
    {
      "id": "Q8",
      "result": "PASS",
      "evidence": "keychain.store_token line uses principal matching [a-z0-9_.:-] only and token matching [A-Za-z0-9_-] with \\Z; no spaces or metacharacters to split security -i argv. generate_token also rejects leading '-'."
    },
    {
      "id": "Q9",
      "result": "PASS",
      "evidence": "Dry-run issue/rotate still _require_* + _show_plan without lock; revoke dry-run _load_hashes() for malformed fail; list unlocked. generate_token only moved under lock on apply. filelock imported inside exclusive_lock so get_token/hash reads stay free of it."
    },
    {
      "id": "Q10",
      "result": "PASS",
      "evidence": "Newline tests fail under $; overlap tests fail without lock per implementer no-op experiment; cross-process contention pins exclusion. Weaknesses: contention never red-first against production bug; 0.5s window; .callback + store_token wrap. Untested: real keychain, live server, other filelock versions, ImportError path, SIGKILL."
    },
    {
      "id": "Q11",
      "result": "PASS",
      "evidence": "All 13 paths serve lock, \\Z identity hardening, or tests. instruction_like_scan detected=false. No secrets/credentials/emails in diff. No text that alters this audit contract treated as authority."
    },
    {
      "id": "Q12",
      "result": "PASS",
      "evidence": "Revoked hash restore via CLI race: fixed by lock (overlap tests). Remaining restore path: hand-edit hash file. Valid token loss: crash after keychain before hash (pre-existing). Wrong-principal verify: digest->principal map with compare_digest; newline principals rejected. Deadlock: no nested lock in apply; 30s timeout. Fail open: not on lock/import failure. Tested: lock coverage, Timeout fail-closed, \\Z anchors, security -i charset, dry-run/list unlocked, revoke hash-before-delete ordering."
    }
  ]
}
```

## Corroboration (does not govern)

**AGY** (`gemini-4-argon-high`, self-reported `Gemini 4 Argon (High)`): PASS_WITH_RISKS over the same prompt, 4 low findings, 12 of 12 questions PASS. Delivery of the whole prompt is proven in `review_bundle/AGY_RUN_RECORD.md`. Raw reply: `review_bundle/AGY_VERDICT.json`.

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| GROK-1 | MEDIUM | Advisory lock only covers dopemux auth writers | OPEN |
| GROK-2 | MEDIUM | filelock version floor untested | OPEN |
| GROK-3 | MEDIUM | auth_identity.py changes require image rebuilds not run in CI | OPEN |
| GROK-4 | LOW | Missing filelock yields ImportError not HashFileError | OPEN |
| GROK-5 | LOW | Pre-existing keychain/hash partial-failure window unchanged | OPEN |
| GROK-6 | LOW | Test-only principal pattern still uses $ | OPEN |
| AGY-1 | LOW | Missing `filelock` package raises uncaught `ModuleNotFoundError` instead of `HashFileError` / `ClickException` | OPEN |
| AGY-2 | LOW | Mid-`rotate` failure after keychain overwrite leaves keychain and hash file out of sync until retry | OPEN |
| AGY-3 | LOW | Stale `$` anchor in error message text and one test-file helper regex, plus two E501 lines in test file | OPEN |
| AGY-4 | LOW | Server hash-file refresh stamp uses `(st_mtime_ns, st_size)` without `st_ino` | OPEN |

Team-lead reading, not an audit: `review_bundle/FINDING_TRIAGE.md`. No finding names a defect in the lock or the `\Z` change, and none needs a code change at this head.

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | PASS |
| 🧪 Unit Tests | PASS |
| 📚 Documentation Check | PASS |
| 🔒 Security Review | PASS |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local: CI fast unit gate command at the head | PASS |
| local: all Wave 2A suites plus tests/test_dcp_surface_guard.py | PASS |
| local: exclusive_lock disabled, tests must fail | PASS |
| local: change contract | PASS |
| local: mypy on the auth package | FAIL |
| local: red_lane_scanner --files | FAIL |
| local: check_root_hygiene.py --all-files | FAIL |
| review bots at the head | PASS |
| audit: validation inside the sealed sessions | NOT_RUN |
| live: real macOS keychain, live server, image rebuild, other filelock versions | NOT_RUN |

The embedded-audit gate and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- GROK-1 (MEDIUM, OPEN): Advisory lock only covers dopemux auth writers
- GROK-2 (MEDIUM, OPEN): filelock version floor untested
- GROK-3 (MEDIUM, OPEN): auth_identity.py changes require image rebuilds not run in CI
- GROK-4 (LOW, OPEN): Missing filelock yields ImportError not HashFileError
- GROK-5 (LOW, OPEN): Pre-existing keychain/hash partial-failure window unchanged
- GROK-6 (LOW, OPEN): Test-only principal pattern still uses $
- AGY-1 (LOW, OPEN): Missing `filelock` package raises uncaught `ModuleNotFoundError` instead of `HashFileError` / `ClickException`
- AGY-2 (LOW, OPEN): Mid-`rotate` failure after keychain overwrite leaves keychain and hash file out of sync until retry
- AGY-3 (LOW, OPEN): Stale `$` anchor in error message text and one test-file helper regex, plus two E501 lines in test file
- AGY-4 (LOW, OPEN): Server hash-file refresh stamp uses `(st_mtime_ns, st_size)` without `st_ino`
- Grok risk: Lock is advisory and CLI-only; same-user hand edits or future callers of write_hashes without exclusive_lock reintroduce lost-update races.
- Grok risk: Only filelock 3.25.2 evidenced; pyproject allows older 3.12+ where delete-on-release / st_nlink behaviour may differ.
- Grok risk: No real macOS keychain or live server validation in this message; stub security only.
- Grok risk: Both memory images must be rebuilt for \Z server-side; CI at this head did not build them (implementer claim).
- Grok risk: Crash/SIGKILL after keychain store_token and before write_hashes still leaves keychain ahead of hash file (pre-existing).
- Grok risk: Overlap tests use 0.5s window and Thread + store_token wrap; extreme scheduling could hide a missing lock (implementer notes slow machine hides bug, never fails a correct build).
- Grok risk: Library internals of filelock (deleted lock file vs waiter holding old fd) cannot be verified from this message alone.
- AGY risk: Auditor tool execution is disabled by HARD RULE 1; all test results, linter results, and CI checks are implementer claims and `validation_status` is explicitly `NOT_RUN`.
- AGY risk: Cannot verify `pyproject.toml`, `uv.lock`, or installed `filelock` library internals from this message alone; while `filelock` 3.25.2 rechecks `st_nlink` after `flock` to close the unlink-on-release race, earlier versions allowed by `>=3.12.0` were not tested.
- AGY risk: Real macOS `/usr/bin/security` keychain operations, live server processes, and Docker image rebuilds for `conport` and `working-memory-assistant` (which copy `auth_identity.py` at build time) were not run.
- AGY risk: `hashfile.write_hashes()` and `hashfile.write_meta()` remain public module functions that do not themselves acquire or assert `exclusive_lock()`, relying on callers (`auth_commands.py`) to wrap writes in `with hashfile.exclusive_lock():`.
- Audit scope: both auditors saw the whole diff 583720375...9fbd5fe27, 13 files, with full file text.
- The auditors could not run anything. Team-lead spot checks of their claims matched the code, with two AGY line citations off by one or two lines (FINDING_TRIAGE.md). These are not a re-audit.
- Auditor model identity: requested grok-4.5; init.model grok-4.5; receipt grok-4.5-build; self-reported grok-4.7, where PR 1498's run self-reported grok-4; provider attestation UNKNOWN.
- Which auditor governs was a team-lead call, stated to the operator and not overruled, following PR 1498's ruling. The operator did not rule on it for this PR. The two verdicts agree, so it does not change the result.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- AGY's process did not exit after its result and was stopped by the wrapper, so its wrapper exit is 137 (AGY_RUN_RECORD.md). The verdict is unaffected.
- This PR ran without a MacroPacket. Its authority is the operator's 'Merge, fix next' ruling; no TP_ROUTE was emitted before the work.
