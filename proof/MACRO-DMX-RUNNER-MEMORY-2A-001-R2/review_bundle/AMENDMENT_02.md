# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Amendment 02: Claude Code stays on direct HTTP in 2A; suite-wide keychain guard

**Recorded:** 2026-11-01 (UTC), by the team lead (Control Tower supervisor session), after W07 returned NEEDS_SUPERVISOR.

## Ruling 1: Claude Code moves to the bridge in Wave 2B, not 2A

**Operator words (verbatim):** "Later, with 2B (Recommended)"

**In answer to (verbatim):** "When should Claude Code itself move onto the token bridge for ConPort and dope-memory?" The answer option read: "The tracked .mcp.json stays on direct HTTP; W07 keeps the bridge rendering available but not default. Codex still gets its gated bridge config now. Avoids Claude losing memory until a token is issued, and avoids Command Code, Grok and Copilot writing as runner:claude through the shared file. Enforce waits anyway for the container callers."

**Why it came up:**
- `.mcp.json` is tracked in git; the earlier research pass that called it untracked was wrong.
- W07 rendered Claude Code's ConPort and dope-memory entries through the bridge as `runner:claude`. That fails four parity and repair tests unless the tracked file is regenerated.
- Regenerating it would switch every Claude Code session in this repo to the bridge at merge time:
  - The bridge fails closed without a token, so Claude would lose both servers until `runner:claude` is issued.
  - Command Code, Grok and Copilot, which also read `.mcp.json`, would write as `runner:claude` (the Wave 2B design's shared-file finding).

**Effect on the design (2A revision 2):**
- G5 ("Claude Code keeps working on the same identity model") is deferred to Wave 2B, where the principal comes from the launching runner's environment marker instead of the shared file.
- In 2A, Claude Code keeps its direct HTTP entries: unverified in `log` mode, and rejected in `enforce`.
- So `enforce` cannot be switched on before 2B moves Claude Code. `enforce` was already blocked by the container callers (`W05_RETURN.md`).
- G4 (Codex through the gated bridge config) is unchanged.

**W07 correction:**
- The default Claude Code rendering (`_render_local_entry`, `_build_local_mcp_json`, and through them `init`, `ensure`, `add`, `repair-config`) stays as it was.
- The tracked `.mcp.json` is not changed.
- The bridge rendering for Claude Code is kept as a tested function that nothing calls by default, for 2B.

## Ruling 2: suite-wide keychain guard

**Operator words (verbatim):** "Yes, add the guard (Recommended)"

**In answer to (verbatim):** "Add an autouse test guard in tests/conftest.py so no test ever reads the real keychain (needed before you issue any token)?"

**Scope added to W07:** `tests/conftest.py`, for one autouse fixture only. It sets `dopemux.auth.keychain.SECURITY_BIN` to a missing path, as W05's `keychain_guard_plugin.py` does, so every `get_token` raises `KeychainError` unless a test installs its own stub. W03's tests set their own stub after it, so they keep working.

**Residual:** tests outside `tests/` (for example `services/*/tests`) are not covered by `tests/conftest.py`.

## Still not authorized

Push or PR; signing; the audit route; token issuance; migrations against a real database; the enforce switch; the ADR-MCPINT-002 amendment; the live Codex run; merge.
