# AGY findings: supervisor triage

Written by the team lead after AGY returned, at head 97b79962936da518888c12f3ff1ae8b6f0084eda.

This is not an audit. The team lead supervised the implementation, so this reading has no independence and changes no finding. Every finding stays OPEN until the operator decides. Grok's verdict governs.

Result: no finding needs a code change at this head. AGY-1 needs a decision before anything supplies a proxy token.

| ID | AGY | Reading | Evidence |
|---|---|---|---|
| AGY-1 (F-01) | MEDIUM | Accurate, but matches the accepted design and cannot happen at this head. | `PROXY_TOKEN_PROVIDER` returns None in `server.py:33` and `conport_mcp_stdio.py:30`, so no proxy token exists. RFC line 95 specifies the fallback, and `test_rest_writes.py:317` pins the stored principal. |
| AGY-2 (F-02) | LOW | Accurate and already disclosed. | `docs/02-how-to/runner-memory-identity.md:321`. |
| AGY-3 (F-03) | LOW | Accurate. A mismatched body workspace is ignored, not rejected, when the path workspace is blank. The write still lands on the bound workspace. | `_write_ids`, then `validate_write_ids` (`auth_identity.py:140-181`). Read, not run over HTTP. |
| AGY-4 (F-04) | LOW | True only if the SQL is run by hand. The real path handles it. | `_skip_existing_add_columns` (`sqlite_migrations.py:63`), outside AGY's input. Run on throwaway databases: see below. |
| AGY-5 (F-05) | LOW | Accurate; not disclosed before. Hardening, since stdin comes from the local runner and the default peer is 127.0.0.1. | `http_stdio_bridge.py:340, 520, 549, 635` (AGY cited 521, 550, 638). `--base-url` can name another peer. |
| AGY-6 (F-06) | LOW | Accurate, and reaches further than AGY said: see below. | `.match` with `$` accepted `runner:codex\n`; `.fullmatch` refused it. |

Security risk AGY listed outside its findings: `enhanced_server.py:505` checks schema `public`, while `008_write_principal.sql:52` checks `current_schema()`. On a non-public default schema, enforce would reject writes (fail closed) and log would store them without a principal, with a warning. Enforce is not reachable in 2A.

## AGY-1: decide before supplying a proxy token

If a later wave gives the proxy a token, a caller with no token would be stored as `internal:bridge-proxy`, a verified-looking principal, and only the `auth_unverified_calls` counter would show the real caller was unverified. The behavior is intended today, but anyone wiring that token should choose it deliberately.

## AGY-4: runs on throwaway SQLite files

| Case | Result |
|---|---|
| Fresh ledger, first boot | v1.3.0 applied, no error |
| Second boot of the same ledger | nothing to apply, no error, one v1.3.0 row, all columns present |
| Version row removed, columns present | re-recorded, no error |
| Raw SQL file re-run by hand | `duplicate column name: write_principal` |

## AGY-6: the principal has the same gap

AGY walked through a token with a trailing newline, which the read-back catches. `validate_principal` (`tokens.py:35`) has the same gap, and the principal comes before `-w` on the `security -i` line (`keychain.py:107`), so a principal ending in a newline would split that command in two. `dopemux auth issue` and `rotate` accept such a value (`auth_commands.py:75`). Reaching it takes an operator typing a literal newline into their own command, so this is not a privilege boundary.

What `security` does with the split line is UNKNOWN: this was read, not run, because no keychain use was authorized. Using `fullmatch` in these checks would close it.

## The two questions AGY could not answer

Q3 (routes) and Q5 (migrations) were UNKNOWN because the answers sit outside AGY's 13 files. Checked at the head:

- ConPort: every non-GET route is under `/api/` or is `/mcp` (`enhanced_server.py:284-319`), and `_count_writes` treats any non-safe `/api/` route as a write.
- ConPort `/mcp`: `dispatch_map` has 16 tools. All 9 write tools are in `REST_WRITE_TOOLS`; the other 7 are reads (`get_*`, `search_content`).
- ConPort `/mcp` batch: a list body fails at `mcp_request.get`, so nothing is dispatched.
- dope-memory: the 5 write routes depend on `write_identity`; the 5 others are reads.
- Migrations: see AGY-4.

These are the team lead's checks too, not audit coverage of Q3 or Q5.
