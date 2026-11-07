---
id: rfc-2026-10-30-foundations-wave-1-plan
title: Foundations Wave 1 Implementation Plan
type: rfc
status: draft
author: claude-code
date: '2026-10-30'
created: 2026-10-30
updated: 2026-10-30
last_review: '2026-10-30'
next_review: '2027-01-28'
owner: '@hu3mann'
derived_from:
- docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md
prelude: Task-by-task implementation plan for Foundations Wave 1 (tests/arch in CI, ADHD engine MCP repair, dopemux adhd status, service port drift test, docs).
---
# Foundations Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Erratum (2026-10-30): CI runs Python 3.12.13 (uv honors `.python-version`); where this plan says 3.11 for CI, read 3.12.13.

**Goal:** Make the repo's contract tests run in CI, make the ADHD engine's MCP tools work on the real engine, add `dopemux adhd status`, and catch service port drift.

**Architecture:** Four independent code tasks with disjoint write sets (CI workflow; engine adapter methods plus a parity test; a new click command group; a drift test plus config default fixes), then one docs task. All new tests live in `tests/arch/` or `tests/unit/`, both of which CI runs once Task 1 lands.

**Tech Stack:** Python 3.11 in CI (3.12 locally), click, `requests` (core dependency; `httpx` is only in the `services` extra), pytest with `--import-mode=importlib` and strict markers, PyYAML, `uv --frozen`.

**Spec:** `docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md`

## Global Constraints

- Every new test passes under Python 3.11 with `uv sync --frozen --extra test --extra services`. No `skip`, `xfail` or `--deselect` to get green.
- Do not edit `services/adhd_engine/api/routes.py`, `services/adhd_engine/tests/test_state_contract.py`, `.mcp.json`, `mcp_catalog.yaml`, `.claude/statusline.sh`, `scripts/dopemux_dashboard.py`, or anything under `plugins/`.
- A task that needs a file outside its **Files** list stops and returns. Widening needs a supervisor amendment.
- Local runs use the repo venv: `/Users/hue/code/dopemux-mvp/.venv/bin/pytest` from the worktree root.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` (or the model that wrote the commit).
- Report each check as PASS, FAIL or NOT_RUN.

## Review Focus

1. **Engine reachable but `/health` missing (404) or not JSON** (an older engine). Expected: status follows `/state`, `engine_mode` is `unknown`, not `degraded`. Test: Task 3, `test_status_health_missing_is_unknown_mode`.
2. **`/state` answers 200 with a non-JSON body** (a proxy error page). Expected: `malformed`, exit 1. Test: Task 3, `test_status_non_json_body_is_malformed`.
3. **`DOPEMUX_ADHD_ENGINE_PORT=abc`.** Expected: the value is ignored with a one-line stderr warning naming the variable, and resolution continues; `url_source` shows what was used. Test: Task 3, `test_resolve_ignores_invalid_port_env_with_warning`.
4. **Engine slower than 2 s.** Expected: `unreachable`, with detail naming the timeout. Test: Task 3, `test_status_timeout_is_unreachable`.
5. **An energy or attention value the CLI has never seen** (the engine adds a level). Expected: shown verbatim; only a missing key or non-object body is `malformed`. Test: Task 3, `test_status_unknown_level_shown_verbatim`.

---

### Task 1: Run `tests/arch` in CI (W1)

**Files:**

- Modify: `.github/workflows/ci-complete.yml` (the `🧪 Unit Tests` job, after the step `▶️ Run dope-memory MCP endpoint gate`, about line 194)

**Interfaces:** none.

- [ ] **Step 1: Prove `tests/arch` passes in a CI-equivalent environment**

Run (from the worktree root; the env dir is throwaway):

```bash
export UV_PROJECT_ENVIRONMENT="$(mktemp -d)/ci311"
uv sync --frozen --python 3.11 --extra test --extra services
uv run --frozen --python 3.11 pytest tests/arch -n auto --maxfail=1 --disable-warnings --no-cov -q
```

Expected: `184 passed` (more once Tasks 2 and 4 land). Any failure: stop and return the output. Do not edit tests.

- [ ] **Step 2: Add the step**

Insert after the dope-memory step, same indentation:

```yaml
      # Separate pytest process, like the dope-memory gate: tests/arch imports
      # service packages that must not shadow modules tests/unit imports.
      - name: ▶️ Run arch contract gate
        run: |
          uv run --frozen pytest \
            tests/arch \
            -n auto --maxfail=1 --disable-warnings --no-cov
```

- [ ] **Step 3: Validate the workflow**

Run: `pre-commit run --files .github/workflows/ci-complete.yml`
Expected: the "Validate GitHub Actions workflow syntax" hook passes.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci-complete.yml
git commit -m "ci: run tests/arch contract tests in the unit test job"
```

### Task 2: ADHD engine MCP methods on the real engine (W2)

**Files:**

- Modify: `services/adhd_engine/core/engine.py` (class `ADHDAccommodationEngine`; module-level result types next to the imports)
- Create: `tests/arch/test_adhd_engine_mcp_parity.py`

**Interfaces:**

- Produces, in `services/adhd_engine/core/engine.py`:
  - `ENERGY_SCORE: dict[str, float] = {"very_low": 0.1, "low": 0.3, "medium": 0.5, "high": 0.7, "hyperfocus": 0.9}` with a comment that these are nominal positions, not measurements.
  - `@dataclass(frozen=True) class EnergySnapshot: level: str; score: float`
  - `@dataclass(frozen=True) class AttentionSnapshot: state: str`
  - `class TaskAssessment` with `__init__(self, payload: dict)` and `dict(self) -> dict`
  - `ADHDAccommodationEngine.get_energy_level(self, user_id: str) -> EnergySnapshot` (async)
  - `ADHDAccommodationEngine.get_attention_state(self, user_id: str) -> AttentionSnapshot` (async)
  - `ADHDAccommodationEngine.get_cognitive_load(self, user_id: str) -> float` (async)
  - `ADHDAccommodationEngine.assess_task(self, title: str, description: str = "") -> TaskAssessment` (async)

- [ ] **Step 1: Write the static parity test**

`test_mcp_tool_engine_calls_exist_on_both_engines`: parse `services/adhd_engine/main.py` with `ast`; collect the attribute name of every `engine.<name>(...)` call inside an `async def` decorated with `mcp.tool()`; collect method names of class `ADHDAccommodationEngine` (parse `core/engine.py`) and class `_FallbackADHDEngine` (parse `main.py`).

```python
assert called, "no engine calls found in MCP tools; the parser is broken"
assert called >= {"get_energy_level", "get_attention_state", "get_cognitive_load", "assess_task"}
assert not (called - real_methods), f"missing on ADHDAccommodationEngine: {sorted(called - real_methods)}"
assert not (called - fallback_methods), f"missing on _FallbackADHDEngine: {sorted(called - fallback_methods)}"
```

- [ ] **Step 2: Run it and see it fail**

Run: `pytest tests/arch/test_adhd_engine_mcp_parity.py -q --no-cov`
Expected: FAIL, `missing on ADHDAccommodationEngine: ['assess_task', 'get_attention_state', 'get_cognitive_load', 'get_energy_level']`.

- [ ] **Step 3: Write the behavior tests**

Build the engine with `ADHDAccommodationEngine()` (no `initialize()`, no Redis). Seed `engine.current_energy_levels["u1"] = EnergyLevel.HIGH` and `engine.current_attention_states["u1"] = AttentionState.SCATTERED` (from `services.adhd_engine.core.models`).

- `test_energy_level_reads_engine_state`: `get_energy_level("u1")` gives `level == "high"`, `score == 0.7`.
- `test_unknown_user_gets_route_defaults`: `get_energy_level("nobody").level == "medium"`, `get_attention_state("nobody").state == "focused"`.
- `test_attention_state_reads_engine_state`: `get_attention_state("u1").state == "scattered"`.
- `test_cognitive_load_is_float_in_unit_range`: with `_calculate_cognitive_load` monkeypatched to an `AsyncMock(return_value=0.42)`, the result is `0.42`, and the mock was awaited with `"u1"`.
- `test_assess_task_uses_operator_and_marks_defaults`: with `assess_task_suitability` monkeypatched to an `AsyncMock(return_value={"suitable": True})`, `(await engine.assess_task("Write docs", "x")).dict()` equals `{"suitable": True, "defaults_used": ["complexity_score", "estimated_minutes"]}`; the mock's first argument is `engine.operator_user_id`; its `task_data` has `title == "Write docs"`, `description == "x"`, `complexity_score == 0.5`, `estimated_minutes == 30`.

Mark async tests the way existing async tests in `tests/unit` are marked (`asyncio_mode = auto` is set in `pytest.ini`, so plain `async def` works).

- [ ] **Step 4: Implement the four methods and three result types**

`get_energy_level` and `get_attention_state` read `current_energy_levels` / `current_attention_states` with defaults `EnergyLevel.MEDIUM` / `AttentionState.FOCUSED` and convert with `.value`, as `/api/v1/state` does. `get_cognitive_load` returns `float(await self._calculate_cognitive_load(user_id))`. `assess_task` calls `assess_task_suitability(self.operator_user_id, task_data)` with the four fields above and adds `"defaults_used": ["complexity_score", "estimated_minutes"]` to a copy of the result.

- [ ] **Step 5: Run the tests**

Run: `pytest tests/arch/test_adhd_engine_mcp_parity.py -q --no-cov`
Expected: 6 passed.

- [ ] **Step 6: Mutation check**

Rename `get_cognitive_load` to `get_cognitive_load_x` in a scratch edit, rerun Step 5, and record the parity failure naming `get_cognitive_load`. Revert the scratch edit (`git diff` shows only the intended change).

- [ ] **Step 7: Commit**

```bash
git add services/adhd_engine/core/engine.py tests/arch/test_adhd_engine_mcp_parity.py
git commit -m "fix(adhd-engine): implement the MCP tool methods on the real engine"
```

### Task 3: `dopemux adhd status` (W3)

**Files:**

- Create: `src/dopemux/commands/adhd_commands.py`
- Modify: `src/dopemux/cli.py` (an import plus `cli.add_command(adhd)` next to `from .commands.update_commands import update` / `cli.add_command(update)`, about line 3202)
- Create: `tests/unit/test_adhd_commands.py`

**Interfaces:**

- Produces, in `src/dopemux/commands/adhd_commands.py`:
  - `DEFAULT_ADHD_ENGINE_PORT: int = 3025` (Task 4 pins it to the registry)
  - `resolve_engine_url(cli_url: str | None, env: Mapping[str, str]) -> tuple[str, str]` returns `(base_url, source)`. Order: `cli_url` → `DOPEMUX_ADHD_ENGINE_BASE_URL` → `DOPEMUX_ADHD_ENGINE_PORT` → `ADHD_ENGINE_PORT` → `http://127.0.0.1:{DEFAULT_ADHD_ENGINE_PORT}`. `source` is one of `"--url"`, the variable name, or `"registry-default"`. A port variable that is not an integer from 1 to 65535 is skipped with a stderr warning naming it.
  - `@dataclass class StatusResult: status: str; url: str; url_source: str; engine_mode: str; energy: str | None; attention: str | None; session_minutes: int | None; detail: str` with `status` in `{"ok", "degraded", "unreachable", "malformed"}` and `engine_mode` in `{"normal", "fallback", "unknown"}`.
  - `fetch_status(base_url: str, url_source: str, timeout: float = 2.0) -> StatusResult`, using `requests.get` for `/api/v1/state` then `/health`.
  - `EXIT_CODES = {"ok": 0, "unreachable": 1, "malformed": 1, "degraded": 3}`
  - click group `adhd` with command `status` and options `--json` and `--url`.

- [ ] **Step 1: Write the tests**

Patch `dopemux.commands.adhd_commands.requests.get` with a fake that maps a URL suffix to `(status_code, body)` or raises `requests.ConnectionError` / `requests.Timeout`. Fixtures:

```python
MAIN_STATE = {"energy": "medium", "attention": "focused", "session_minutes": 0, "user_id": "op"}
PULSE_STATE = {**MAIN_STATE, "energy_level": "medium", "attention_state": "focused"}  # PR #1472 at ee00d3655
FALLBACK_HEALTH = {"overall_status": "🟡 Degraded", "service": "adhd-engine", "mode": "fallback", "startup_error": "x"}
NORMAL_HEALTH = {"overall_status": "🟢 Healthy", "components": {}}
```

- `test_resolve_order`: each source wins over every later one; with no inputs the result is `("http://127.0.0.1:3025", "registry-default")`.
- `test_resolve_ignores_invalid_port_env_with_warning` (Review Focus 3).
- `test_status_ok_main_shape`, `test_status_ok_pulse_shape`: status `ok`, energy `medium`, `engine_mode == "normal"`, exit 0.
- `test_aliases_win_over_originals`: body `{**MAIN_STATE, "energy_level": "high", "attention_state": "scattered"}` gives energy `high`, attention `scattered`.
- `test_status_degraded_on_fallback_health`: `degraded`, `engine_mode == "fallback"`, exit 3.
- `test_status_health_missing_is_unknown_mode` (Review Focus 1): `/health` 404 gives status `ok`, `engine_mode == "unknown"`.
- `test_status_connection_refused_is_unreachable`, `test_status_timeout_is_unreachable` (Review Focus 4), `test_status_non_2xx_is_unreachable` (500): exit 1.
- `test_status_non_json_body_is_malformed` (Review Focus 2), `test_status_missing_energy_is_malformed`: exit 1.
- `test_status_unknown_level_shown_verbatim` (Review Focus 5): energy `"recharging"` gives status `ok` and the human output contains `recharging`.
- `test_session_minutes_hidden_when_zero`: the human output for `MAIN_STATE` has no `session` text; with `session_minutes: 12` it contains `12`.
- `test_json_output_schema`: `--json` output parses; keys are exactly `status, url, url_source, engine_mode, energy, attention, session_minutes, detail`.

Invoke through `click.testing.CliRunner` on the `adhd` group.

- [ ] **Step 2: Run them and see them fail**

Run: `pytest tests/unit/test_adhd_commands.py -q --no-cov`
Expected: collection error, `No module named 'dopemux.commands.adhd_commands'`.

- [ ] **Step 3: Implement `adhd_commands.py` to the interfaces above, and register the group in `cli.py`**

`engine_mode`: `"fallback"` when `/health` returns a JSON object with `mode == "fallback"`; `"normal"` for any other 2xx JSON object without an `error` key; `"unknown"` otherwise. The human output is one line, for example `ADHD engine ok (http://127.0.0.1:3025, registry-default): energy medium, attention focused`. Add `degraded: engine running on its fallback class` or the failure detail when they apply.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/unit/test_adhd_commands.py -q --no-cov`
Expected: all passed.

- [ ] **Step 5: Check the command is wired**

Run: `/Users/hue/code/dopemux-mvp/.venv/bin/python -m dopemux adhd status --url http://127.0.0.1:9 ; echo "exit=$?"` (`src/dopemux/__main__.py` exists).
Expected: one `unreachable` line, `exit=1`.

- [ ] **Step 6: Lint and type-check**

Run: `flake8 src/dopemux/commands/adhd_commands.py tests/unit/test_adhd_commands.py` and `mypy src/dopemux/commands/adhd_commands.py`
Expected: no new findings in these files.

- [ ] **Step 7: Commit**

```bash
git add src/dopemux/commands/adhd_commands.py src/dopemux/cli.py tests/unit/test_adhd_commands.py
git commit -m "feat(cli): add read-only dopemux adhd status"
```

### Task 4: Service port drift test (W4)

**Files:**

- Create: `tests/arch/test_service_port_drift.py`
- Modify: `src/dopemux/config/manager.py:192-202` and `:612-624` (Dope layout defaults)

**Interfaces:**

- Consumes: `parse_port_mapping`, `load_registry`, `load_compose` from `tests.arch.test_registry_compose_alignment` (importable under `--import-mode=importlib`; verified); `DEFAULT_ADHD_ENGINE_PORT` from `dopemux.commands.adhd_commands` (Task 3).

- [ ] **Step 1: Write the tests**

Ports from the catalog (`mcp_catalog.yaml` → `servers`): use `reserved_port`, else `default_port_base`, else the port in `url`/`url_template` (`${VAR:-N}` resolves to `N`).

- `test_registry_matches_catalog`: for each name in both the registry and the catalog, registry `port` equals the catalog port, unless excepted.
- `test_registry_matches_compose_for_non_smoke`: for each registry service with `enabled_in_smoke` false, its `port` is among the compose host ports of `compose_service_name`. Services with no host `ports:` or with `network_mode` are printed as not comparable and do not fail.
- `test_no_unknown_port_literals`: in `src/dopemux/config/manager.py`, `scripts/dopemux_dashboard.py`, `.claude/statusline.sh`, `mcp_server_health_report.sh`, `scripts/mcp_health_check.sh`, `src/dopemux/ui/service_endpoints.py` and `src/dopemux/profile_detector.py`, every match of `(?:localhost|127\.0\.0\.1):(\d{2,5})\b` is a registry host port or a catalog port, unless excepted as `(file, port)`.
- `test_named_defaults_match_registry`: in `manager.py`, the URL port on each line defining `adhd_engine_url`, `leantime_url`, `serena_url` and `litellm_url` equals the registry port of `adhd-engine`, `leantime`, `serena` and `litellm`.
- `test_cli_default_port_matches_registry`: `DEFAULT_ADHD_ENGINE_PORT` equals the registry `adhd-engine` port.
- `test_no_stale_exceptions`: every exception entry still matches a live difference.

Initial `EXCEPTIONS` (each entry with `reason` and `follow_up`):

| Kind | Key | Reason |
|---|---|---|
| catalog | `task-orchestrator` | Two processes share the name: Python orchestrator `8000` (registry) and Kotlin MCP `7890` (catalog). Map item S2. |
| compose | `dopecon-bridge-alt` | Registry alt entry `3000`; its compose service `dopecon-bridge` publishes only `3016`. |
| literal | `scripts/dopemux_dashboard.py`, `8095` | Stale script uses the container port; retire or repair it (follow-up). |
| literal | `scripts/dopemux_dashboard.py`, `8005` | Same script; ConPort port in no registry or compose. |
| literal | `scripts/dopemux_dashboard.py`, `8003` | Same script; Serena port in no registry or compose. |

- [ ] **Step 2: Run them and see the expected failures**

Run: `pytest tests/arch/test_service_port_drift.py -q --no-cov`
Expected: FAIL on `manager.py` literals `3007` and `3008` and on named defaults `adhd_engine_url` (3008 vs 3025), `leantime_url` (3007 vs 8080) and `serena_url` (3010 vs 3006). Every other test passes. If anything else fails, stop and return it; it is a difference the spec did not list.

- [ ] **Step 3: Fix the defaults in `manager.py`**

Set `adhd_engine_url` to `http://localhost:3025`, `leantime_url` to `http://localhost:8080` and `serena_url` to `http://localhost:3006`, in both the class defaults and the dict.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/arch/test_service_port_drift.py -q --no-cov`, then `grep -rn -E "localhost:(3007|3008|3010)" src tests`.
Expected: drift tests pass; the grep finds nothing. No test pinned the old defaults on 2026-10-30; `tests/integration/test_dope_layout.py` uses a different settings class.

- [ ] **Step 5: Mutation checks**

In scratch edits, reverted afterwards, record that each of these fails the named test:

- change `adhd-engine`'s `port` in `services/registry.yaml` to `3026` → `test_cli_default_port_matches_registry` and `test_named_defaults_match_registry`;
- delete the `8003` exception → `test_no_unknown_port_literals`;
- add an exception for a port nobody uses → `test_no_stale_exceptions`.

- [ ] **Step 6: Commit**

```bash
git add tests/arch/test_service_port_drift.py src/dopemux/config/manager.py
git commit -m "test(arch): catch service port drift; fix stale Dope layout defaults"
```

### Task 5: Docs and agent docs (W5)

Starts after Tasks 1-4 are committed.

**Files:**

- Create: `docs/03-reference/adhd-status-cli.md`, `docs/03-reference/ci-contract-gates.md`
- Modify: `docs/00-MASTER-INDEX.md` (Reference → Configuration list), `docs/docs_index.yaml` (`reference:` block), `.claude/claude.md` (section "⚙️ Commands & Environment", two bullets), `AGENTS.md` (section 3 "Default Behavior", two bullets with the same facts)

**Interfaces:** Consumes the names, options, exit codes and exception table from Tasks 1-4.

- [ ] **Step 1: Write `adhd-status-cli.md`**

Reference frontmatter as in `docs/03-reference/filesystem-guide.md`. It covers:

- usage, `--json` and `--url`;
- the URL resolution order;
- the statuses and exit codes;
- what `degraded` means;
- the limit that a failing `/state` still returns normal-looking defaults;
- what it does not do (no per-user routes, no break or focus verbs).

- [ ] **Step 2: Write `ci-contract-gates.md`**

It covers what `tests/arch` checks and that CI now runs it; how to run it locally; the four drift rules; how to add an exception (reason and follow-up required, stale entries fail); and the follow-ups from the spec's section 10.

- [ ] **Step 3: Index and agent-doc entries**

`.claude/claude.md` and `AGENTS.md` each get:

- "`tests/arch` runs in CI (unit test job); run `pytest tests/arch` before pushing changes to the registry, compose, the MCP catalog, personas or ports";
- "read ADHD engine state with `dopemux adhd status` (`--json` for scripts); exit 3 means the engine runs on its fallback class".

Keep these edits in sections PR #1484 does not touch (it edits `AGENTS.md` sections 8 and 9.1 and `.claude/claude.md` "Detailed Information Locations").

- [ ] **Step 4: Docs gates**

Run on every new or changed doc: `python scripts/docs_frontmatter_guard.py <files>`, `markdownlint -c .markdownlint.jsonc <files>`, `python scripts/check_docs_hygiene.py --check` (only the existing `docs/runbooks/ddd-release-gate-app.md` violation may remain).
Expected: guard and markdownlint clean.

- [ ] **Step 5: Commit**

```bash
git add docs/03-reference/adhd-status-cli.md docs/03-reference/ci-contract-gates.md docs/00-MASTER-INDEX.md docs/docs_index.yaml .claude/claude.md AGENTS.md
git commit -m "docs: dopemux adhd status, CI contract gates, agent guidance"
```

### Task 6: Freeze checks (supervisor)

- [ ] **Step 1:** Rerun Task 1 Step 1 (CI-equivalent `tests/arch` on 3.11). Expected: all pass, including the new tests.
- [ ] **Step 2:** Run `pytest tests/unit -n auto -q --no-cov` in the repo venv. Expected: no new failures against `origin/main`. Compare against a run on `origin/main` if any fail.
- [ ] **Step 3:** Run `python scripts/governance/validate_change_contract.py --base origin/main --head HEAD`. Expected: `status=PASS`, `max_lane=L2`. Record it for the MacroPacket.
- [ ] **Step 4:** Push the branch and open a draft PR (operator-approved step). The one final audit runs on the operator's route after #1482, #1472 and #1483 merge (spec section 5).
