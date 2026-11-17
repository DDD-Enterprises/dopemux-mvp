# AUDITOR REPORT — PR #1516 L2 embedded audit (TP-DMX-PR1516-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.5.9, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-fable-5-2 requested, linked session local_06ecd46b), a different runner and model family
- **Audited head**: `074606f397741a23c2d762c8600da9a0add91cd3` · **Base**: `8edff9b52480681d5eb7b420a3efcdf42ab4c36c` (main, the merge-base)
- **Verdict**: **PASS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'system_message', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw AGY stream, stderr and wrapper exit lines are in `review_bundle/`

## Why this audit

A source review for cockpit audit finding G-2 found that `TaskRecommender.get_current_recommendation` turned a failed ADHD Engine
read (for example HTTP 401) into energy and attention "unknown", fell through to the default advice and stamped it `LIVE`.
`074606f39` makes an unreadable engine state an error that names each failing endpoint, and adds tests that fail on the base
implementation (8 failed, 7 passed) and pass on the fix (18 passed in the service suite). This audit covers the whole PR diff:
`services/adhd-dashboard/task_recommender.py` and its test file.

## Operator approval of the audit route

Audit approval 2026-11-16T23:33:28Z: "Yes, audit #1516" (Claude Code session d3cf0485), on the route first requested
2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too" (cockpit work, reused here). Recorded per
docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input, no-secret
constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "ok",
  "verdict": "PASS",
  "findings": [],
  "risks": [
    "Validation tests were not executed by the embedded auditor because candidate checkout, execution, and tool usage are disabled by audit policy (validation_status=NOT_RUN).",
    "In _read_engine_field, a whitespace-only string value from the upstream engine would pass the `not isinstance(value, str) or not value` check, and non-JSON payloads on HTTP 200 responses rely on the outer exception handler in get_current_recommendation() rather than returning an endpoint-specific message."
  ],
  "rationale": "Verified repository (DDD-Enterprises/dopemux-mvp), pull request (1516), base SHA (8edff9b52480681d5eb7b420a3efcdf42ab4c36c), and head SHA (074606f397741a23c2d762c8600da9a0add91cd3) match the trusted audit parameters, and deterministic instruction-like content scan reported no matches (detected=false, match_count=0). In services/adhd-dashboard/task_recommender.py, TaskRecommender.get_current_recommendation() previously defaulted non-200 responses to {} and missing fields to 'unknown', allowing fabricated state advice to be stamped with StatusChip.LIVE. The diff introduces _read_engine_field() to validate HTTP 200 status, dict JSON payload structure, and non-empty string values for both /api/v1/energy-level/{user_id} and /api/v1/attention-state/{user_id}. When either field is unreadable, get_current_recommendation() now logs a StatusChip.BLOCKER error and returns {'error': ...} naming the failing endpoint(s) without generating a LIVE recommendation. Corresponding unit tests in services/adhd-dashboard/tests/test_task_recommender.py cover HTTP error statuses (401, 404, 500, 503), missing keys, None values, non-dict JSON payloads, combined endpoint failures, and valid readable state behavior. Delegation and tool calls were omitted per explicit trusted audit policy disabling tools and MCP.",
  "inspected_paths": [
    "services/adhd-dashboard/task_recommender.py",
    "services/adhd-dashboard/tests/test_task_recommender.py"
  ],
  "evidence_refs": [
    "repo:DDD-Enterprises/dopemux-mvp",
    "pr:1516",
    "base_sha:8edff9b52480681d5eb7b420a3efcdf42ab4c36c",
    "head_sha:074606f397741a23c2d762c8600da9a0add91cd3",
    "services/adhd-dashboard/task_recommender.py:L18",
    "services/adhd-dashboard/task_recommender.py:L171-L229",
    "services/adhd-dashboard/tests/test_task_recommender.py:L95-L187",
    "instruction_like_scan_summary:detected=false,match_count=0"
  ],
  "validation_status": "NOT_RUN"
}
```

## Findings (all OPEN)

| ID | Severity | Title | Status |
|---|---|---|---|
| none | | | |

## Corroboration (does not govern)

- **Grok** (grok-4.7, receipt `grok-4.7-build`, `init.tools == []`): PASS_WITH_RISKS; see `review_bundle/GROK_CORROBORATION.md`.
- **Codex** (advisory GitHub review of `074606f39`): no findings. **Copilot**: no open issues; it asked for human governance review of the missing MacroPacket and the audit.

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | PASS |
| 🧪 Unit Tests | PASS |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local: pytest tests (services/adhd-dashboard) | PASS |
| local: the new tests detect the defect on the base implementation | PASS |
| live ADHD Engine request | NOT_RUN |
| audit: validation inside the sealed AGY session | NOT_RUN |

The embedded-audit gate, recheck and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local pytest in services/adhd-dashboard passes at the audited head (18 passed). No CI job runs that directory's tests: pytest.ini has testpaths = tests, the unit gate collects tests/unit plus two files, and the workflows name adhd-dashboard only for container builds.
- Supervisor check of the shared AGY and Grok risk (a whitespace-only string, or the literal string 'unknown', still counts as readable state and reaches the default advice): accurate and OPEN. It is reachable at this head through the engine's prediction-override route: services/adhd_engine/api/routes.py writes request.override_value, typed Any in api/schemas.py, into current_energy_levels and current_attention_states for a user with a profile, and the two GET handlers return `value.value if hasattr(value, 'value') else str(value)`. The other writers (engine.py, core/engine.py) were not traced to their sources. The dashboard guard checks presence, not membership in the engine's EnergyLevel and AttentionState values; validating override_value in the engine, or membership in the dashboard, is a follow-up. OPERATOR: decision pending.
- Out of this PR's scope, seen during that check: the engine answers MEDIUM and FOCUSED for a user it has no reading for (routes.py, current_energy_levels.get(user_id, EnergyLevel.MEDIUM) and current_attention_states.get(user_id, AttentionState.FOCUSED)), so advice built on engine defaults can still be stamped LIVE. Not changed here.
- Grok's first risk is about what the sealed audit could not run: the service tests were run locally at the audited head (18 passed) and the new tests fail on the base implementation (8 failed, 7 passed); see LOCAL_VALIDATION.txt. CI state is in CI_EVIDENCE.json.
- The raw AGY stream (1 line) and the AGY CLI log copy (5 lines) contain the operator's home directory path, as in earlier bundles. Only the account email address was redacted (REDACTIONS.md).
- Audit scope: the whole PR diff, merge-base 8edff9b52 to 074606f39; main was still at the merge-base when the bundle was built.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Codex (advisory GitHub review) reviewed 074606f39 with no findings. Copilot reported no open issues and asked for human governance review of the missing MacroPacket and the audit, which was NOT_RUN at that time; they are not embedded auditors.
- No supervisor-issued MacroPacket exists for this work. Authority is the operator's requests recorded under fallback_auditor_approval and operator_decisions.
- The fix was not exercised against a live ADHD Engine.
