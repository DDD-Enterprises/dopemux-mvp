# W07 return — TP-DMX-RUNNERMEM2A-R2-W07-GENERATOR-GATE-001

**Child status:** NEEDS_SUPERVISOR (first round), then READY_FOR_AUDIT after the correction round. **Team lead disposition:** operator ruling recorded in `AMENDMENT_02.md` (`7e12c64c3`), one correction round, committed as `29203f1eb`. Audit: NOT_RUN (held for J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W07_EXECUTION_BINDING.json`, `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 197 assistant turns, both rounds (harness record) |
| First round | 725 s / 249,807 tokens / 117 tool uses |
| Correction round | 221 s / 267,757 tokens / 19 tool uses (as the completion notice reported them) |
| Caps | 120 min / 1.5M / 300 |
| advisor calls / subagents | 0 / 0 (structural count: Bash 60, Read 31, Write 2, Edit 41, SubagentHandback 2) |
| `cd` / file writes through Bash / live, keychain, `--apply`, `init` or `ensure` runs | 0 / 0 (one `cat > /dev/null` no-op) / 0 |

## Why it returned NEEDS_SUPERVISOR

The first round rendered Claude Code's ConPort and dope-memory entries through the bridge as `runner:claude`. The repo tracks `.mcp.json`, so four parity and repair tests outside W07's surface failed. Making them pass meant regenerating the tracked file, which would switch every Claude Code session in the repo at merge time.

The operator ruled "Later, with 2B (Recommended)" and added the suite-wide keychain guard (`AMENDMENT_02.md`). The correction restored the default Claude Code rendering and kept the bridge entry as an unused, tested function (`_render_claude_memory_bridge_entry`). It also added the autouse `_no_real_keychain` fixture to `tests/conftest.py`.

## Write surface

8 paths, all inside the W07 write_surface, with `tests/conftest.py` added by Amendment 02. `.mcp.json` and `schemas/` are untouched. No 2A commit touches `.github/`.

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| commit.verify pytest line + `tests/arch` MCP contracts + fleet catalog, merge-safety and repair tests | 0 | PASS: 260 passed |
| `cmp mcp_catalog.yaml src/dopemux/mcp/default_catalog.yaml` | 0 | PASS |
| `dopemux mcp generate --help` | 0 | PASS |
| Whole-2A set: W01-W07, W09, W10, guard, ConPort wiring, hooks, capture, ledgers, dope-memory endpoint, MCP lifecycle, W05's caller suites without the plugin, `tests/dcp`, `tests/pr_steward` (services venv) | 1 | 1,709 passed, 1 failed. The failure is `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`. It diffs from an old packet's base commit and lists `.github/workflows/` files that 2A never touched; it fails the same way on the main checkout. Pre-existing, not caused by 2A. |
| `git diff --check`, pre-commit (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child) | 1 | recorded: 14 failed, 5 passed, 30 errors before the code |
| Live `/health`, real keychain, `generate --apply`, a live Codex start | — | NOT_RUN (C10, B05) |

## What W07 built

- **Gate.** `evaluate_codex_memory_gate(repo_path, principal="runner:codex")` in `src/dopemux/commands/mcp_commands.py`, called from the in-repo apply path. Every check is evaluated, and each failure gets one line:
  - Check 1: dope-memory `/health` and ConPort REST `/health` both report `auth_mode == "enforce"` and `identity_required_writes is True`; ConPort also reports `auth_principal_column == "ok"`. Ports come from the checkout's envrc through the bridge's key-filtered reader.
  - Check 2: `get_token("runner:codex")` succeeds; the value is discarded.
- **Write path.**
  - `dopemux mcp generate --agent-matrix --apply` always writes the preview.
  - It writes `.codex/config.toml` (marker region, conport and dope-memory only, user keys preserved) only when the gate holds.
  - A dry run makes no probe and no keychain call.
  - `--agent-matrix` is required because the catalog's profiles make the profile plane the default.
- **`--allow-sequenced`** now stops with an error that explains the gate.
- **Catalog.**
  - conport and dope-memory `codex: full-sequenced` became `full` (released); all other rows are unchanged.
  - Bridge entries render despite the per-worktree skip, which still applies to every other server.
  - The two catalogs are byte-identical.
- **Codex entries.** The interpreter is bare `python`, the same choice as the legacy `--base-url` entry (`config/manager.py:721-726`); no `cwd` is rendered:

  ```toml
  [mcp_servers."conport"]
  command = "python"
  args = ["-m", "dopemux.mcp.http_stdio_bridge", "--server", "conport", "--principal", "runner:codex"]
  [mcp_servers."dope-memory"]
  command = "python"
  args = ["-m", "dopemux.mcp.http_stdio_bridge", "--server", "dope-memory", "--principal", "runner:codex"]
  ```

## Follow-up round under Amendment 03

The operator ruled "Allow log mode (Recommended)" (`AMENDMENT_03.md`, `4bf49fb32`).

**What changed:**
- Gate check 1 now passes for `auth_mode` `log` or `enforce`. `identity_required_writes` must still be `True`, and ConPort's `auth_principal_column` must still be `ok`. `off` fails with `auth_mode is 'off', expected 'log' or 'enforce'`.
- When the gate holds with any server in `log` mode, the apply prints one notice: Codex's writes are verified as `runner:codex`, and writers without a token are still accepted and recorded `unverified` until `enforce`.
- The help text, the `--allow-sequenced` error and the preview header now say "log or enforce".

**Commit and route:** `f88e99dcd` on top of `4bf49fb32`; files `mcp_commands.py`, `fleet_catalog.py` and the W07 gate test. The round took 143 s, 294,022 tokens (as the completion notice reported them) and 35 tool uses. advisor calls 0.

**Validation (team lead re-ran):** W07, catalog, arch and repair tests: 276 passed. The catalogs are byte-identical. `git diff --check` and pre-commit PASS.

**TDD:** this round the child wrote the code before the tests and recorded no failing run. The new assertions match the new messages exactly, so they cannot pass on the old code.

**Checked, not new:** `fleet_catalog.py:19` imports `mcp_commands` at module level, and that import exists at the base `97b6d5040`. `mcp_commands` imports `fleet_catalog` lazily, inside a function, and all three modules import cleanly in a fresh interpreter.

## Residual risks (for the audit and the live Codex run)

1. **Bare `python`** may not resolve to an interpreter with `dopemux` installed. If it doesn't, the server doesn't start (fails closed).
2. **The working directory Codex gives stdio servers is UNKNOWN.** The installed Codex 0.159.2 binary has a `cwd` field, and its error text implies a local server starts in the Codex process directory. The bridge's walk-up covers subdirectories. The live Codex run settles this.
3. **Defaults.** `merge_codex_config_toml` and `render_codex_managed_region` default to `released_only=False`. The only product caller and the parity check pass `True`.
4. **The gate imports the bridge's private envrc helpers** to reuse its password-skipping filter.
5. **The gate reads unauthenticated `/health` at generation time only.** If `enforce` is switched off later, nothing re-checks.
6. **`actor_authentication` wording still appears outside W07's surface:** `AGENTS.md:346` (W08) and `schemas/mcp/fleet-catalog.schema.json:148` (description text; schemas are out of scope).
7. **The `tests/conftest.py` guard does not cover `services/*/tests`.**
