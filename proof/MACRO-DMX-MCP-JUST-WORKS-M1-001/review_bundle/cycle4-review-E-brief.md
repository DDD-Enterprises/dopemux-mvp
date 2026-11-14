# Review brief — Task E (cycle 4): config repair replaces only what dopemux rendered

Role: independent task reviewer, read-only (run tests/probes, change nothing). Fail closed.
Worktree /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1; subject = the uncommitted `git diff` (saved as
cycle4-review-E.diff). Allowed files: src/dopemux/mcp/mcp_json.py, tests/unit/test_mcp_config_repair.py,
tests/unit/test_mcp_commands_repair.py (reason-text assertions only), claudedocs/mcp-just-works-design-2026-11-05.md (one
appended amendment bullet), docs/02-how-to/mcp-setup-other-repos.md only if it stated the repair rule. Any other path is a finding.

The finding (Codex, independent audit at 43294e99b, medium): `_url_is_repairable` judged a template by its default, but a
port variable's value is unknown at repair time (PORT=`3005@remote.example` → host remote.example), so
`http://localhost:${PORT:-3005}/sse` was repairable and the planner would replace an operator endpoint.
Required fix: a templated URL is repairable only in the exact shape dopemux renders — literal http(s), literal
localhost/127.0.0.1, one of dopemux's own port variables (static set + names from the catalog's templates) as the ONLY
placeholder in the port position, numeric/absent default, literal remainder; everything else preserved; environment
values NEVER read; literal URLs keep the previous rule; `_neutralize_placeholders` removed if unused; planner reason text
changed; docstrings no longer claim "provably local" for templates; one design amendment bullet.

Check adversarially:
- Can any templated URL that an operator could have written still be repaired although its expansion may be non-local or
  credential-bearing? Try: an allowed name with extra text after the placeholder (`${CONPORT_MCP_PORT:-3005}@evil`,
  `${CONPORT_MCP_PORT:-3005}.evil`), two placeholders, an allowed name in the host or userinfo position, a default that is
  not digits, uppercase/lowercase host variants, IPv6, `https://localhost`, a path containing `${`, a catalog whose
  url_template uses a NEW variable name (is `_catalog_port_vars` wired at the call site and is the regex anchored?).
- Does the code read os.environ or any env file anywhere in the predicate path? It must not.
- Do the three catalog URLs still repair (planner-level test), and does Codex's example now land in `preserved` with the
  new reason text? Would the new tests fail on the old code (not tautological)?
- Is `_placeholder_in_userinfo_or_host` still used, and are its tests intact? Is `_neutralize_placeholders` really gone with
  no remaining references (grep src and tests)?
- Design amendment: appended only, accurate, consistent with the code; nothing else in that file changed.
Run and paste literally: `.venv/bin/python -m pytest tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_commands_repair.py -q`;
`/Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/mcp_json.py`; `git diff --stat`;
`.venv/bin/python scripts/docs_validator.py claudedocs/mcp-just-works-design-2026-11-05.md`.
Verdict: APPROVED or NEEDS_FIXES (path:line, severity, why, exact fix), then the one-line list of what an independent auditor
might still raise about `_url_is_repairable` and the planner's use of it.
