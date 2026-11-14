# Final fix wave report (base b8b5bf636)

## Commits
- 1bdfb3ff0 fix(cli): normalize adhd status URLs, keep human output on one line, assert timeout (F2, F3, F4)
- a4ac8fa26 fix(adhd-engine): lowercase non-enum energy/attention values; parity test static half needs no imports (F5, F6)
- 6df08459d test(arch): a registry compose service missing from compose.yml fails (F7)
- 1238e9267 docs: CI runs Python 3.12.13; tighten arch-gate wording, follow-ups and port names (F1, F9, F8 wording)
- 73f1691ca docs: adhd status URL normalization, one-line output, refreshed line refs (F2/F3 docs)
- 3b46fd6c5 ci: run the arch gate last in the unit job, serially (F8)

## F1 CI Python
- `docs/03-reference/ci-contract-gates.md` (What CI runs): setup-python installs 3.11, uv selects 3.12.13 from `.python-version`; reproduce with `uv sync --frozen --extra test --extra services` (no `--python`).
- `docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md`: lines 73, 85, 98, 190 corrected to 3.12.13 via `.python-version`.
- `docs/91-rfc/rfc-2026-10-30-foundations-wave-1-plan.md`: erratum line added under the "For agentic workers" note; plan not rewritten.
- Verified in the CI-equivalent env: `uv run --frozen python --version` printed 3.12.13.

## F2 URL handling (`src/dopemux/commands/adhd_commands.py`)
- Did not reuse `_base_from_url`: importing `dopemux.ui.service_endpoints` pulls `dopemux.instance_state`, which imports aiohttp and pydantic (measured: 168 extra modules). `ui/__init__.py` is empty. Also `_base_from_url("localhost:8095")` would parse `localhost` as a scheme. Implemented local `normalize_base_url` (lines 52-76): default `http://`, drop path/query/credentials, validate host and port, http/https only.
- `resolve_engine_url` (79-117): invalid `--url` (including empty string) raises `click.BadParameter(param_hint="--url")`, exit 2, no request sent. Invalid `DOPEMUX_ADHD_ENGINE_BASE_URL` is skipped with a stderr warning naming it.
- Tests (tests/unit/test_adhd_commands.py): `test_url_without_scheme_gets_http`, `test_url_path_is_dropped`, `test_invalid_url_option_is_usage_error` (6 params), `test_invalid_base_url_env_is_skipped_with_warning`, `test_base_url_env_without_scheme_is_normalized`.
- RED: 12 new tests failed before the change (scheme-less URL, path, usage errors, env skip, one-line, truncation); GREEN after: 40 passed.
- Docs: `docs/03-reference/adhd-status-cli.md` documents normalization, usage error, env warning; line references refreshed.

## F3 one-line human output
- `_one_line` collapses whitespace and caps each engine string at 200 chars (199 + `…`); applied to energy, attention, startup_error in `_human_line`. `StatusResult` gained a default `startup_error` field (human output only); `_json_payload` removes it, so `--json` keeps the same keys and the raw `detail`.
- Tests: `test_human_line_stays_one_line_for_multiline_startup_error` (also asserts JSON detail is raw and has no `startup_error` key), `test_human_line_truncates_long_engine_strings`. RED/GREEN as above.

## F4 timeout
- `test_requests_use_two_second_timeout` records kwargs of both `requests.get` calls and asserts `timeout=2.0` for each. Already true in code, so no RED.

## F5 lowercase (`services/adhd_engine/core/engine.py` get_energy_level, get_attention_state)
- Non-enum values use `str(value).lower()`; score lookup uses the lowercased level.
- Tests in `tests/arch/test_adhd_engine_mcp_parity.py`: `test_energy_level_lowercases_non_enum_values` ("HIGH" -> "high", 0.7), `test_attention_state_lowercases_non_enum_values`. RED: `assert 'HIGH' == 'high'`; GREEN after the fix.

## F6 parity test imports
- Module-level `services.*` imports removed; engine/models imported inside the `engine` fixture and the new unmocked test. Static test needs no imports.
- Added `test_cognitive_load_unmocked_is_in_unit_range` (fresh `ADHDAccommodationEngine()`, `0.0 <= load <= 1.0`); renamed the mocked test to `test_cognitive_load_returns_float_from_calculation`.

## F7 missing compose service
- `tests/arch/test_service_port_drift.py`: new `_missing_compose_services()`, `test_registry_services_exist_in_compose` (message names registry service and missing compose name), and `test_missing_compose_service_is_reported` (synthetic registry, proves detection). The missing-service note was removed from `not_comparable`. Real repo has zero instances, so it stays green. Docs updated.

## F8 CI step
- `.github/workflows/ci-complete.yml`: arch step moved to the end of the `tests` job (after the interactive import smoke), `-n auto` removed, comment kept plus a note why it is last; `--maxfail=1 --disable-warnings --no-cov` kept. `ci-contract-gates.md` command and local-run example updated.

## F9 docs wording (`docs/03-reference/ci-contract-gates.md`)
- "without skips" replaced: new tests have no skip markers; existing files have skip branches (`test_mcp_multiproject_contracts.py:513-526`) that do not fire in CI (`fetch-depth: 0`).
- Added `.claude/statusline.sh:220` (`nc -z -w 1 localhost 8096`) to the limits and the statusline follow-up, noting the literal rule cannot see `nc -z` forms.
- Port 3009 now named `gpt-researcher` (registry) / `gptr-mcp` (compose and catalog) in both places.

## Validation
- `/Users/hue/code/dopemux-mvp/.venv/bin/pytest tests/arch tests/unit/test_adhd_commands.py -q --no-cov -p no:cacheprovider`: 242 passed, no warnings.
- CI-equivalent (temp UV_PROJECT_ENVIRONMENT, Python 3.12.13, `uv sync --frozen --extra test --extra services`): `pytest tests/arch -q --disable-warnings --no-cov` 202 passed; `pytest tests/unit/test_adhd_commands.py -q --no-cov` 40 passed.
- pre-commit (scratch config, `node: system`) on `.github/workflows/ci-complete.yml`: "Validate GitHub Actions workflow syntax" Passed; other hooks skipped (no matching files) or Passed.
- `markdownlint -c .markdownlint.jsonc` on the 4 changed docs: exit 0. `scripts/docs_frontmatter_guard.py` on the 4 docs: "All docs have valid frontmatter."
- black applied to changed Python test/source files (adhd_commands.py unchanged by black after edit; engine.py not reformatted, only the two lines edited).

## Skipped / notes
- Nothing skipped. `task-packets/` remains untracked; nothing pushed.
- Black also reformatted two pre-existing long assert lines in test_adhd_engine_mcp_parity.py (same file, in write set).
