# W03 return — TP-DMX-RUNNERMEM2A-R2-W03-AUTH-COMMANDS-001

**Child status:** READY_FOR_AUDIT. **Team lead disposition:** committed as `27d8caa82` after a diff re-read of the keychain module and a cross-check of the hash-file contract; no correction round. Audit: NOT_RUN (held for J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W03_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Precondition (B01) | `KEYCHAIN_ACL_RESULT.md` (`0e231b49d`) |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 39 assistant turns (harness record) |
| Duration / tokens / tool uses | 249 s / 95,350 / 28 (caps 90 min / 1.0M / 200) |
| Attempts | 1 |
| advisor calls / subagents | 0 / 0 (structural count: Bash 10, Read 3, Write 10, Edit 4, SubagentHandback 1) |
| `cd` / edits through Bash / `security` or `auth issue` runs | 0 / 0 / 0 |

## Write surface

11 paths, all inside the W03 write_surface. The `cli.py` change is 5 added lines: the import and `cli.add_command(auth)`. `~/.config/dopemux/auth` does not exist on the host after the run.

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| `pytest tests/unit/runner_memory_2a_r2_w03/` | 0 | PASS: 38 passed |
| `dopemux auth --help` | 0 | PASS (issue, list, revoke, rotate) |
| W01, W06, CLI capture and hooks suites | 0 | PASS: 141 passed, 1 skipped |
| Hash-file contract cross-check (temp `HOME`, worktree venv) | 0 | PASS. A hash file written by `dopemux.auth.hashfile` verifies the token as `runner:codex` on both dope-memory's and ConPort's `AuthGate("enforce")`; a wrong token stays `unverified`; `auth_hash_file` is `ok`; directory 0700, file 0600 |
| `git diff --check`, pre-commit (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child) | 2 | recorded: collection errors before the module existed |
| Real keychain write via `security -i`, exit 44 for a missing item, `-U` update, locked keychain | — | NOT_RUN; first exercised by the operator's `dopemux auth issue <principal> --apply` |

## Helper API for W02, W04 and W05

`dopemux.auth`:

| Kind | Names |
|---|---|
| Keychain | `get_token(principal) -> str`, `store_token(principal, token)`, `delete_token(principal) -> bool` |
| Tokens and principals | `generate_token()`, `hash_token(token)`, `validate_principal(p)`, `is_known_principal(p)` |
| Constants | `KNOWN_PRINCIPALS`, `SERVICE = "dopemux-mcp"` |
| Errors | `AuthError`, with subclasses `InvalidPrincipalError`, `KeychainError` (and its subclass `TokenNotFoundError`), `HashFileError` |

`dopemux.auth.hashfile` holds the hash file (`memory-token-hashes.json`) and a date-only sidecar (`memory-token-meta.json`, principal to created/rotated times; no tokens or hashes).

## Notes for the audit

- **Token out of argv.** Writes send `add-generic-password -U -s dopemux-mcp -a <principal> -w <token>` on `security -i` stdin. argv is `["-i"]`. Output is captured and never logged or returned. Success requires the read-back to match (constant-time compare), because `security -i` can exit 0 after a failed command.
- **Leading dash.** `generate_token` redraws any token that would start with `-`. That excludes 1 in 64 values and costs no meaningful entropy.
- **Exit 44** as "item not found" comes from macOS `security(1)` behaviour. It has not been observed here: UNKNOWN until a live run.
- **No transaction.** `issue` and `rotate` write the keychain, then the hash file, then the sidecar. A failure partway leaves a state that re-running the command repairs. A keychain-only token has no hash and verifies nothing.
