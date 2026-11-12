# Task E (cycle 4) — close Codex audit finding F1 at 43294e99b: repair only what dopemux rendered

Workspace: /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 (branch feat/mcp-just-works-m1, HEAD 43294e99b). Shared
workspace; preserve others' edits. You do NOT commit, stage, stash or push. Files you may change:
  src/dopemux/mcp/mcp_json.py · tests/unit/test_mcp_config_repair.py · tests/unit/test_mcp_commands_repair.py (only if a
  test there asserts the old preservation reason text) · claudedocs/mcp-just-works-design-2026-11-05.md (ONE appended bullet
  in "## Implementation amendments (2026-11-07)", append-only, nothing else in that file).
  docs/02-how-to/mcp-setup-other-repos.md ONLY if a sentence there states which URLs the repair replaces (grep "repair",
  "placeholder", "preserved"); if none does, do not touch it and say so.
Anything else → STOP and report. RED first. Do not reformat lines you did not touch. Keep added lines ≤ 88 chars.
Interpreter .venv/bin/python; tools /Users/hue/code/dopemux-mvp/.venv/bin/{black,isort,flake8}.

## The finding (Codex, independent audit at 43294e99b, medium, mcp_json.py:170)
`_url_is_repairable("http://localhost:${PORT:-3005}/sse")` is True because the template's DEFAULT is judged, but the
variable's VALUE is unknown at repair time: with PORT=`3005@remote.example` the expanded URL is
`http://localhost:3005@remote.example/sse`, host remote.example. The planner (mcp_json.py ~288-300, ~330) then treats the
operator's entry as ours and replaces it with a launcher entry. Both cycle-2/3 parsing fixes stay; this closes the claim gap.

## Fix (allowlist of dopemux's own templates; NEVER read environment values — a sourced envrc from another checkout must
## not steer repair, see the git-only identity design)
1. Module constant `_DOPEMUX_PORT_VARS = frozenset({"CONPORT_MCP_PORT", "DOPE_MEMORY_PORT", "TASK_ORCHESTRATOR_HTTP_PORT"})`
   — the only names dopemux has ever rendered into a url_template (verified in git history). Helper
   `_catalog_port_vars(catalog) -> frozenset[str]`: the `${NAME...}` names found in the catalog's url/url_template values
   (regex `\$\{([A-Z][A-Z0-9_]*)`), so a future catalog rename keeps working.
2. Helper `_self_rendered_template(url: str, port_vars: frozenset) -> bool`: True only for exactly the shape dopemux
   renders — literal `http://` or `https://`, literal host `localhost` or `127.0.0.1`, then `:${NAME}` or `:${NAME:-<digits>}`
   as the ONLY placeholder, in the port position, NAME in port_vars, then an optional literal remainder starting with
   `/`, `?` or `#` that contains no `$`, `{`, `}` or whitespace. One anchored regex is fine.
3. `_url_is_repairable(url, port_vars=None)`: missing → True (unchanged). Templated (`"${" in url`) →
   `not _placeholder_in_userinfo_or_host(url) and _self_rendered_template(url, port_vars or _DOPEMUX_PORT_VARS)`.
   Literal → the existing provably-local / no-credentials rule, unchanged. Remove `_neutralize_placeholders` if nothing
   else uses it (grep src and tests first; it is only used at the old line ~186) — do not leave dead code.
   Docstring: "True when the catalog may replace url: it is missing; or a literal URL on localhost/127.0.0.1 with no
   credentials; or a templated URL of exactly the shape dopemux renders itself (literal http(s) scheme, literal local
   host, one of dopemux's own port variables as the only placeholder in the port position, numeric or absent default,
   literal remainder). Any other template is operator-authored and preserved. Environment values are never inspected:
   a variable's value is unknown at repair time, so only the template's provenance is judged." Adjust the module/other
   docstrings that still say "provably local" for templates.
4. Call site (~288): `url_ok = _url_is_repairable(current_url, _DOPEMUX_PORT_VARS | _catalog_port_vars(catalog))`.
   Preservation reason text (~291-296) currently "non-localhost or credential URL preserved": change to
   "operator URL preserved (not a literal local URL and not a dopemux-rendered template)". Update any test asserting
   the old text (grep tests/unit for the old string).
5. Design amendment (append ONE bullet at the end of "## Implementation amendments (2026-11-07)"), in the style of the
   existing bullets: "**Config repair replaces only what dopemux rendered (cycle 4, Codex audit F1 at 43294e99b).**
   `_url_is_repairable` accepts a templated URL only in the exact shape dopemux renders (literal local host, one of its own
   port variables — `CONPORT_MCP_PORT`, `DOPE_MEMORY_PORT`, `TASK_ORCHESTRATOR_HTTP_PORT`, or any name in the catalog's
   templates — as the only placeholder, in the port position); every other template is operator-authored and preserved,
   and environment values are never read, so a port variable set to `3005@remote.example` cannot make an operator
   endpoint look local. Hand-written URL-style `.mcp.json` files (how-to, manual recipe) are therefore preserved, not
   repaired."

## Tests (RED first; keep the failing output)
tests/unit/test_mcp_config_repair.py, parametrized `test_url_is_repairable_templated_and_literal` — expected now:
  False: "http://localhost:${PORT:-3005}/sse" (Codex's example); "http://localhost:${CONPORT_PORT:-3005}/sse" (not a
  dopemux name — flip from True, say why in a comment); the cycle-3 controls "http://localhost:${PORT:-3005}/sse?u=ws://x"
  and "http://localhost:${PORT:-3005}/${P:-a/b}" (generic names — flip, comment); "http://localhost:${CONPORT_MCP_PORT:-abc}/sse";
  "http://localhost:${CONPORT_MCP_PORT:-3005}/${P:-x}"; "http://localhost:${CONPORT_MCP_PORT:-3005}${X:-}/sse";
  "http://remote.example:${CONPORT_MCP_PORT:-3005}/sse"; "http://user@localhost:${CONPORT_MCP_PORT:-3005}/sse";
  "http://localhost:${CONPORT_MCP_PORT:-3005}@remote.example/sse".
  True: the three catalog URLs (already there); "http://localhost:${CONPORT_MCP_PORT}/sse" (no default);
  "https://127.0.0.1:${DOPE_MEMORY_PORT:-3020}/mcp"; "http://localhost:${CONPORT_MCP_PORT:-3005}/sse?x=1".
  Every earlier not-repairable case stays False; every literal case keeps its expectation.
Add: `test_catalog_port_vars_from_default_catalog` (the three names come out of the real default catalog);
`test_self_rendered_template_rejects_generic_port_variable`; a planner-level test (existing fixture style in that file or
test_mcp_commands_repair.py): a conport entry whose url is "http://localhost:${PORT:-3005}/sse" is PRESERVED with the new
reason, while "http://localhost:${CONPORT_MCP_PORT:-3005}/sse" is repaired to the launcher entry.

## Validation you run and paste literally
  .venv/bin/python -m pytest tests/unit/test_mcp_config_repair.py tests/unit/test_mcp_commands_repair.py tests/unit/test_mcp_stdio_proxy.py -q
  /Users/hue/code/dopemux-mvp/.venv/bin/black --check <touched .py files>   (untouched-line hunks expected; report literally)
  /Users/hue/code/dopemux-mvp/.venv/bin/isort --check-only <touched .py files>
  /Users/hue/code/dopemux-mvp/.venv/bin/flake8 --select F,E7,E9,W6 src/dopemux/mcp/mcp_json.py
  .venv/bin/python scripts/docs_validator.py claudedocs/mcp-just-works-design-2026-11-05.md; .venv/bin/python scripts/docs_frontmatter_guard.py claudedocs/mcp-just-works-design-2026-11-05.md
  git -C /Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1 diff --stat
Report: RED output · the mcp_json.py diff · GREEN · tool outputs · whether the how-to needed a sentence (and what) ·
deviations/STOP · one-line list of what an auditor might still raise.
