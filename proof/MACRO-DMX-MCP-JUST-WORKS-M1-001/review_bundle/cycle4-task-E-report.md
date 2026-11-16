# Task E (cycle 4) implementer report — as delivered 2026-11-09 (sonnet implementer; controller-verified below)

`_url_is_repairable` repairs a templated URL only when it has exactly the shape dopemux renders. Three test files pass together (129 passed). black --check exits 1 only on untouched lines. No commit/stage/stash/push; environment values never read.

## 1. RED (new tests before the fix: 15 failed, 77 passed)
Flipped/new table cases failing on the old code: `http://localhost:${PORT:-3005}/sse`, `${CONPORT_PORT:-3005}`, `http://127.0.0.1:${PORT}/mcp`, `${PORT-3005}`, `${PORT:-3005}/sse?u=ws://x`, `${PORT:-3005}/${P:-a/b}`, `localhost:3005/sse?x=${Q:-a/b}`, `${CONPORT_MCP_PORT:-abc}`, `${CONPORT_MCP_PORT:-3005}/${P:-x}`, `${CONPORT_MCP_PORT:-3005}${X:-}/sse` (all expected False); plus test_catalog_port_vars_from_default_catalog, test_catalog_port_vars_reads_names_only_from_url_values, test_self_rendered_template_rejects_generic_port_variable, test_planner_preserves_generic_port_template_and_repairs_dopemux_template, test_templated_remote_launcher_url_is_preserved_not_replaced (new reason text). Remote-host, userinfo, `@remote.example` and the True controls already behaved correctly before the fix.

## 2. mcp_json.py change
Removed `_neutralize_placeholders` (no other use in src or tests). Added `_DOPEMUX_PORT_VARS = frozenset({CONPORT_MCP_PORT, DOPE_MEMORY_PORT, TASK_ORCHESTRATOR_HTTP_PORT})`, `_PLACEHOLDER_NAME = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")`, `_SELF_RENDERED` (anchored via fullmatch): `https?://(?:localhost|127\.0\.0\.1):\$\{(NAME)(?::-[0-9]+)?\}(?:[/?#][^${}\s]*)?`. Helpers `_catalog_port_vars(catalog)` (names from the catalog's url / url_template values) and `_self_rendered_template(url, port_vars)` (fullmatch + name in port_vars). `_url_is_repairable(url, port_vars=None)`: missing → True; templated → `not _placeholder_in_userinfo_or_host(url) and _self_rendered_template(url, port_vars or _DOPEMUX_PORT_VARS)`; literal → existing rule (parse, `${}` netloc backstop, local host, no credentials); the `templated and not host` branch dropped (templates no longer reach it). Docstring per the brief. Call site: `_url_is_repairable(url, _DOPEMUX_PORT_VARS | _catalog_port_vars(catalog))`. Preservation reason (both places): "operator URL preserved (not a literal local URL and not a dopemux-rendered template)".

## 3. Tests
Existing table flipped to False with comments (generic/non-dopemux names, incl. the cycle-3 controls and `localhost:3005/sse?x=${Q:-a/b}` — not in the brief's list but follows from the rule). New False cases: `-abc` default, extra path placeholder, `${X:-}` after the port, remote host, `user@`, `@remote.example`. New True: no-default form, `https://127.0.0.1:${DOPE_MEMORY_PORT:-3020}/mcp`, `?x=1` query. New tests: catalog names from the real default catalog (`fleet_catalog.load_root_catalog`), names only from url values, generic-name rejection, planner-level preserve-vs-repair. Existing preserved-entry test asserts the new reason; no test in test_mcp_commands_repair.py asserted the old text (file untouched).

## 4. GREEN / tools
pytest (config_repair, commands_repair, stdio_proxy): 129 passed in 3.61s. black --check: would reformat mcp_json.py and the test file, hunks only on pre-existing lines (mcp_json.py 233/267/344/379/407/420 vs edits at 121-227 and 318-360; test file 64/141/164/229; one hunk that landed in an added assertion was restructured away). isort exit 0. flake8 F/E7/E9/W6 exit 0 (both files). docs_validator + frontmatter_guard on the design doc: exit 0. diff --stat: design doc +1, mcp_json.py 91 (+/-), test file 120 (+/-); 175 insertions, 37 deletions. No added .py line > 88 chars (the design bullet is one long line like its neighbours).

## 5. How-to
No change needed: its only repair sentence says repair-config restores the catalog shape and preserves unknown custom entries; it never states which URLs are replaced. The manual recipe (line ~466) writes URL-style entries by hand, which the new rule preserves, as the design bullet says.

## 6. Design amendment
One bullet appended at the end of "## Implementation amendments (2026-11-07)" (last section), brief text verbatim; nothing else changed.

## 7. Deviations / STOP
None. Advisor not called.

## 8. What an auditor might still raise
`_catalog_port_vars` trusts the catalog (possibly the target checkout's via --repo): a renamed/added template variable widens repairability by design. Hand-written URL-style entries stay as they are (how-to does not say so). Literal localhost URLs are still replaced regardless of what runs there. `_placeholder_in_userinfo_or_host` is redundant on the templated path (kept for defence in depth). Only uppercase variable names are self-rendered. `frozenset[str]` annotations need Python ≥3.9 (repo runs 3.12).

## Controller verification (2026-11-09)
git status: exactly the 3 files. No `os.environ`/`getenv` anywhere in mcp_json.py. Design doc delta = 1 added line (the bullet). `_SELF_RENDERED` anchored via fullmatch as reported; call site unions the catalog names. Controller run: 173 passed across config_repair, commands_repair, stdio_proxy, launcher tests; flake8 rc=0 on both files; 0 added .py lines > 88. Diff saved as cycle4-review-E.diff (sha256 f5509e98a35fc20d…).
