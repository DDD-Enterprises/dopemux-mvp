# Finding triage, PR 1500

This is the team lead's reading, not an audit. The implementer wrote it, so it cannot stand in for either auditor. All findings stay OPEN. Accepting a residual risk is the operator's decision.

Both auditors returned PASS_WITH_RISKS and answered all 12 questions PASS. They ran separately from the same prompt and neither saw the other's reply. No finding names a defect in the lock or in the `\Z` change, and neither auditor found a way to restore a revoked token. Nothing below needs a code change at this head.

| ID | Severity | Reading | Checked against the code |
|---|---|---|---|
| GROK-1 | medium | Disclosed. The lock is advisory and covers `dopemux auth` only. | `write_hashes` and `write_meta` have no callers outside `auth_commands.py`, and all six calls sit inside `exclusive_lock`. |
| GROK-2 | medium | Disclosed and real. `pyproject.toml` allows filelock >=3.12.0, and only 3.25.2 was tested. `uv.lock` pins 3.25.2. | Read filelock 3.25.2 `_unix.py`: `_acquire` discards a lock whose inode has `st_nlink == 0`. Behaviour of other versions is unknown. The contention test runs against whichever version is installed. Follow-up candidate: raise the floor. |
| GROK-3 | medium | Disclosed. Deployed images keep `$` until rebuilt. | `docs/02-how-to/runner-memory-identity.md` already requires a rebuild. No token exists yet. |
| GROK-4, AGY-1 | low | Both auditors, same point. A missing `filelock` gives a traceback rather than a clean error. | Fails closed: the import runs before any token is generated. `filelock` is a declared dependency. |
| GROK-5 | low | Disclosed and unchanged from PR 1498. | The order of `store_token` then `write_hashes` is as before, now inside the lock. |
| GROK-6 | low | Test-only copy of the pattern still ends in `$`. | `tests/unit/runner_memory_2a_r2_w06/test_local_writer_principals.py:28`. Not a runtime check. |
| AGY-2 | low | A rotate that fails after the keychain write leaves the keychain ahead of the hash file until rerun. | `auth_commands.py:145-148`. Same order as PR 1498. It fails closed for the new token. |
| AGY-3 | low | Cosmetic. The `CaptureError` text still shows `$`, the test-only pattern is as in GROK-6, and two test lines are long. | `capture_client.py:78` confirmed. The message describes the format and validates nothing. The long lines are `test_auth_helper.py:180` and `:194` (109 and 89 columns), one line off from AGY's citation. |
| AGY-4 | low | Hardening candidate from PR 1498, not caused by this change. The servers detect a changed hash file by mtime and size. A rotation keeps the size, so it relies on mtime advancing. | The stamp is at `conport/auth_identity.py:227` and `working-memory-assistant/auth_identity.py:186`, two lines from AGY's citation. A miss needs two writes inside one timestamp tick. Adding `st_ino` would close it. |

The auditors could not run anything, so the checks above are reads of the frozen code, not new test runs.
