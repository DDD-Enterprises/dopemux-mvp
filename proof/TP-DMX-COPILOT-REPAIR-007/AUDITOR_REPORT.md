# Auditor Report — TP-DMX-COPILOT-REPAIR-007

**Auditor**: claude-sonnet-4.6 (embedded PAL codereview via gpt-5.2 expert model)
**Date**: 2026-05-26
**TP**: TP-DMX-COPILOT-REPAIR-007 — Copilot bounded PR repair scaffold
**Status**: PASS_WITH_RISKS (all HIGH findings resolved; MEDIUM findings resolved)

---

## Scope

Files reviewed:

- `schemas/copilot/repair_packet.schema.json`
- `templates/copilot/PR_REPAIR_PACKET.md`
- `tests/copilot_repair/test_repair_packet.py`
- `docs/ops/copilot-pr-repair-lane.md`

---

## Findings

### F-007-HIGH-1 — `generated_at` accepts arbitrary strings

**Severity**: HIGH
**Status**: RESOLVED

`generated_at` was typed only as `string` with no format or pattern constraint,
allowing values like `"banana"` to pass validation and undermine governance/
determinism expectations.

**Fix applied**: Added `pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"`
enforcing Zulu-form ISO 8601 timestamps.

**Tests added**: `test_generated_at_non_iso_fails`, `test_generated_at_date_only_fails`,
`test_generated_at_with_offset_fails`.

---

### F-007-MED-1 — `repo` accepts any non-empty string

**Severity**: MEDIUM
**Status**: RESOLVED

`repo` was constrained only to `minLength: 1`, allowing values without the
required `owner/repo` shape.

**Fix applied**: Added `pattern: "^[^/]+/[^/]+$"` and `description: "owner/repo format."`.

**Tests added**: `test_repo_no_slash_fails`, `test_repo_empty_fails`.

---

### F-007-MED-2 — `source_action_plan_id` unconstrained when string

**Severity**: MEDIUM
**Status**: RESOLVED

`source_action_plan_id` was typed as `["string", "null"]` with no length
constraint, allowing empty string `""` to silently carry a semantically-missing
reference.

**Fix applied**: Added `minLength: 1`.

**Test added**: `test_source_action_plan_id_empty_string_fails`.

---

### F-007-MED-3 — Jinja2 template render not validated in tests

**Severity**: MEDIUM
**Status**: ACCEPTED_RISK

The template uses Jinja2 syntax (`{% for %}`, `{% if %}`) but tests only
validate static substrings. A render test would confirm that governance
prohibitions survive template rendering and that items render deterministically.

**Risk accepted**: Jinja2 is not installed in the test environment. Renderer
is explicitly deferred as a separate concern. Template correctness in rendered
output is a remaining risk.

---

### F-007-LOW-1 — `source_item_id` in RepairItem allows empty string

**Severity**: LOW
**Status**: RESOLVED

`source_item_id` in RepairItem was `["string", "null"]` with no length
constraint, allowing `""` which is semantically equivalent to `null` but
distinct at the JSON level.

**Fix applied**: Added `minLength: 1`.

**Test added**: `test_source_item_id_empty_string_fails`.

---

### F-007-LOW-2 — No explicit `schema_version` const pin test

**Severity**: LOW
**Status**: RESOLVED

No test directly asserted that `schema_version.const == "1.0.0"`, leaving a
gap where a maintainer could change the const without a test failing.

**Fix applied**: Added `test_schema_version_const_is_pinned`.

---

### F-007-LOW-3 — No explicit `generated_at` / `repo` pattern pin tests

**Severity**: LOW
**Status**: RESOLVED

Schema structural checks for `generated_at` pattern and `repo` pattern were
missing, meaning tests would silently pass even if patterns were removed.

**Fix applied**: Added `test_generated_at_has_pattern` and `test_repo_has_pattern`.

---

## Remaining Risks

- Jinja2 render test not added — renderer is a separate concern; template
  governance prohibitions are validated as static text only.
- `generated_at` pattern enforces `Z` suffix only; fractional seconds
  (e.g. `2026-05-26T00:00:00.123Z`) are NOT accepted. Accepted: scaffold
  callers are expected to emit second-precision UTC timestamps.
- Jinja2 is not in the project dependencies; if a renderer is added later,
  tests should be updated to include a render-path governance check.

---

## Validation

| Check | Result |
|---|---|
| pytest tests/copilot_repair/ (64 tests) | PASS |
| pytest tests/pr_action_bridge/ tests/audit/ (136 prior tests) | PASS |
| copilot_authority const = "implementer-only" | PASS |
| mutation_performed const = false | PASS |
| Category enum excludes all 10 non-implementer categories | PASS |
| RepairItem.id pattern ^repair-[0-9]{4}$ | PASS |
| additionalProperties: false top-level | PASS |
| additionalProperties: false RepairItem | PASS |
| generated_at ISO Zulu pattern enforced | PASS |
| repo owner/repo pattern enforced | PASS |
| source_action_plan_id minLength: 1 | PASS |
| source_item_id minLength: 1 | PASS |
| Template: 7 prohibition statements present individually | PASS |
| Template: no trailing whitespace | PASS |
| Docs: no trailing whitespace | PASS |
| No tools/pr_merge import | PASS |
| No GitHub mutation calls | PASS |
| mypy | NOT_RUN |
| Jinja2 render-path governance test | NOT_RUN (Jinja2 not installed) |
