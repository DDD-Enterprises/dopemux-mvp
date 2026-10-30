# Final review fix wave (one dispatch)

Branch `feat/foundations-wave-1`, base for this wave: `b8b5bf636`. Every item below is in scope. Anything not listed is out of scope.

## F1 (Important): CI does not run Python 3.11
`.python-version` pins `3.12.13`; CI's `uv sync --frozen --extra test --extra services` has no `--python`, so uv uses 3.12.13 even though `setup-python` installs 3.11 (`ci-complete.yml:173`, `:182`). Verified by the controller.
- `docs/03-reference/ci-contract-gates.md:26`: replace the sentence with the fact: setup-python installs 3.11, but uv selects 3.12.13 from `.python-version`; reproduce CI with `uv sync --frozen --extra test --extra services` (no `--python`).
- `docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md`: correct every statement that CI runs 3.11 (around lines 73, 85, 98, 190). Say CI runs 3.12.13 via `.python-version`.
- `docs/91-rfc/rfc-2026-10-30-foundations-wave-1-plan.md`: do not rewrite the plan. Add one erratum line directly under the "For agentic workers" note: "Erratum (2026-10-30): CI runs Python 3.12.13 (uv honors `.python-version`); where this plan says 3.11 for CI, read 3.12.13."

## F2: `dopemux adhd status` URL handling (`src/dopemux/commands/adhd_commands.py`)
`--url localhost:8095` (no scheme) currently reports `unreachable: InvalidSchema`. Normalize the way `src/dopemux/ui/service_endpoints.py` `_base_from_url` does (add `http://` when the scheme is missing, drop any path, validate the port). Reuse `_base_from_url` only if importing `dopemux.ui.service_endpoints` does not import Textual or other heavy UI modules (check `src/dopemux/ui/__init__.py`); otherwise implement the same rules in a small local function. An invalid `--url` is a usage error (`click.BadParameter`, exit 2). An invalid `DOPEMUX_ADHD_ENGINE_BASE_URL` is skipped with a stderr warning naming it, like the port variables. Tests: scheme-less `--url`, URL with a path, invalid `--url` exits 2, invalid base-URL env var skipped with warning. Document the normalization in `docs/03-reference/adhd-status-cli.md`.

## F3: human output stays one line (`adhd_commands.py`)
`startup_error` and other engine strings can be multi-line. In the human line only, collapse runs of whitespace to one space and truncate any single engine-supplied string to 200 characters with `…`. `--json` keeps raw values. Test: a multi-line `startup_error` renders on one line.

## F4: assert the 2 s timeout (`tests/unit/test_adhd_commands.py`)
Make the fake `requests.get` record kwargs; assert both calls receive `timeout=2.0`.

## F5: lowercase non-enum values (`services/adhd_engine/core/engine.py`)
Spec W2: ".level and .state are the enum's .value string, converted the way /state converts them" (`routes.py` lowercases non-enum values). In `get_energy_level` and `get_attention_state`, use `str(value).lower()` for non-enum values, then look up `ENERGY_SCORE` with the lowercased level. Test in `tests/arch/test_adhd_engine_mcp_parity.py`: seeding the raw string `"HIGH"` gives level `"high"` and score `0.7`.

## F6: parity test static half needs no imports (`tests/arch/test_adhd_engine_mcp_parity.py`)
Spec W2: static parity "needs no imports". Move the engine/models imports out of module level into the behavior tests or a fixture, so an engine import error cannot turn the static check into a collection error. Also add one unmocked case: `0.0 <= await engine.get_cognitive_load("u1") <= 1.0` on a fresh `ADHDAccommodationEngine()` (the reviewer got 0.81 offline), and rename or keep `test_cognitive_load_is_float_in_unit_range` so its name matches what it checks.

## F7: missing compose service fails (`tests/arch/test_service_port_drift.py`)
A registry `compose_service_name` that does not exist in `compose.yml` is currently "not comparable". Make it a failure naming the registry service and the missing compose name (zero instances at head, so this stays green).

## F8: CI step placement (`.github/workflows/ci-complete.yml`)
The arch step runs before steps that have no `if:`, so an arch failure hides their results. Move the step to be the last step of the `🧪 Unit Tests` job, and drop `-n auto` (serial is faster here: 6.8 s against 22.7 s). Keep the comment, `--maxfail=1 --disable-warnings --no-cov`.

## F9: docs wording (`docs/03-reference/ci-contract-gates.md`)
- "without skips": say that new tests in this wave have no skip markers, and that some existing `tests/arch` files have skip branches (`test_mcp_multiproject_contracts.py:513-526`) that do not fire in CI.
- Add `.claude/statusline.sh:220` (`nc -z -w 1 localhost 8096`; 8096 is in no registry, catalog or compose file) to the statusline follow-up, and note the literal rule cannot see `nc -z` forms.
- Where port 3009 is named, give both names: `gpt-researcher` (registry) / `gptr-mcp` (compose and catalog).

## Not in scope
`defaults_used` on error payloads (nit); anything else.
