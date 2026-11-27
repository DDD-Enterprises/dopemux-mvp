# AUDITOR REPORT — PR #1524 L3 embedded audit (TP-DMX-PR1524-L3-AUDIT-001)

- **Auditor**: AGY CLI 1.5.18, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-fable-5-2 requested, linked session local_06ecd46b), a different runner and model family
- **Audited head**: `467f1dfc23bc25455804223e26d11d4930c98947` · **Base**: `0aa2cf3497c59f8c607f92986d01e7b7f2620919` (the merge-base with main)
- **Verdict**: **PASS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'system_message', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw AGY stream, stderr and wrapper exit lines are in `review_bundle/`

## Why this audit

G-2 slice 4: the cockpit's task queue gains **Start** (a queue item) and **Finish** (a work item). `services/adhd-dashboard` adds
`POST /api/tasks/{item_id}/transition`, which sends `advance_item` to the Task Orchestrator MCP on `127.0.0.1:7890` with the fixed
actor `operator:cockpit` (recorded, unverified until Wave 2C). It needs `DASHBOARD_API_KEY`, proves port ownership before and after
reading the item's role under one lock, and sends only `start` from `queue` or `complete` from `work`. It is the first non-runner
writer to the workflow authority, hence lane L3. This audit covers the whole PR diff: 10 files, five commits, `0aa2cf349..467f1dfc2`.

## Operator approval of the audit route

Audit approval 2026-11-27T04:55:54Z: "Freeze and audit now" (Claude Code session d3cf0485), on the route first requested
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
    "External writer TOCTOU window: while _WRITE_LOCK serializes requests within the backend process and re-verifies the port 7890 container ID after reading the item role, an external runner writing directly to port 7890 can still transition the item between read_item_role and send_transition; parse_transition_result mitigates this by detecting unexpected (previousRole, newRole) pairs and surfacing them in reason.",
    "Unverified actor attribution: transitions are sent as actor {id: 'operator:cockpit', kind: 'user'}, which the Task Orchestrator records without cryptographic verification until Wave 2C lands.",
    "Browser-bundled API key: when VITE_DASHBOARD_API_KEY is configured for the frontend, the secret is present in client bundle assets, so the backend must remain bound to 127.0.0.1 as documented in services/adhd-dashboard/README.md.",
    "Candidate tests were reviewed statically from the diff only and were not executed in this embedded audit because candidate code execution and tools are disabled (validation_status=NOT_RUN)."
  ],
  "rationale": "Audited PR #1524 for repository DDD-Enterprises/dopemux-mvp at head SHA 467f1dfc23bc25455804223e26d11d4930c98947 against base SHA 0aa2cf3497c59f8c607f92986d01e7b7f2620919. Provenance metadata (repo, pr_number, head_sha, base_sha) and the 10 changed files in the diff match the trusted envelope, and instruction_like_scan_summary reported no detections (detected=false, match_count=0). The change implements the Start/Finish task transition slice (POST /api/tasks/{item_id}/transition) across the ADHD dashboard backend and UI. On the backend, handle_transition_request fails closed (403 when DASHBOARD_API_KEY is unset, 401 when X-API-Key does not match via hmac.compare_digest, 400 on malformed JSON body), enforces a strict send-site allow-list in _check_call (only query_items get and single-item advance_item with trigger start or complete), validates lowercase UUID item_id and UUID request_id, serializes read-check-write under _WRITE_LOCK, verifies port 7890 project ownership and container_id continuity both before and after reading the item role, enforces role preconditions (start only from queue, complete only from work), distinguishes pre-send failures (McpReadError -> nothing was written) from post-send failures (TransitionOutcomeUnknown -> outcome is unknown), and bounds/sanitizes orchestrator error text without leaking internal session details or container IDs. On the frontend, TaskQueue.tsx and taskQueue.ts expose only Start on queue items and Finish on work items, avoid optimistic state mutations by always re-reading GET /api/tasks after a write, prevent superseded reads from falsely confirming transitions, and respect brand status color tokens.",
  "inspected_paths": [
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md",
    "services/adhd-dashboard/README.md",
    "services/adhd-dashboard/backend.py",
    "services/adhd-dashboard/orchestrator_transitions.py",
    "services/adhd-dashboard/tests/test_orchestrator_transitions.py",
    "ui-dashboard/src/components/TaskQueue.tsx",
    "ui-dashboard/src/components/__tests__/TaskQueue.test.tsx",
    "ui-dashboard/src/components/__tests__/TaskQueue.transitions.test.tsx",
    "ui-dashboard/src/taskQueue.test.ts",
    "ui-dashboard/src/taskQueue.ts"
  ],
  "evidence_refs": [
    "services/adhd-dashboard/backend.py:468-493 (post_task_transition route wiring, X-API-Key pass-through, and fallback 500 JSON contract payload)",
    "services/adhd-dashboard/orchestrator_transitions.py:59-77 (ALLOWED_TRIGGERS, EXPECTED_MOVE, ACTOR, _UUID regex, _WRITE_LOCK, and TransitionOutcomeUnknown)",
    "services/adhd-dashboard/orchestrator_transitions.py:130-199 (_check_call send-site allow-list and _call_tool pre-send vs post-send error classification)",
    "services/adhd-dashboard/orchestrator_transitions.py:254-290 (parse_transition_result role validation, unexpected move detection, cascade reporting, and bounded refusal reason/missing_notes extraction)",
    "services/adhd-dashboard/orchestrator_transitions.py:295-368 (transition_item UUID/trigger validation, _WRITE_LOCK serialization, dual check_owner verification with container_id equality, and role precondition check)",
    "services/adhd-dashboard/orchestrator_transitions.py:374-408 (handle_transition_request fail-closed DASHBOARD_API_KEY check and hmac.compare_digest verification)",
    "services/adhd-dashboard/tests/test_orchestrator_transitions.py:124-638 (unit test coverage for allow-list, UUID validation, dual ownership checks, role preconditions, lock serialization, MCP error isolation, and FastAPI route integration)",
    "ui-dashboard/src/taskQueue.ts:79-129 (triggerFor mapping and parseTransitionResult schema validation)",
    "ui-dashboard/src/components/TaskQueue.tsx:100-109 (confirm helper requiring non-superseded fresh read listing the item in work or queue)",
    "ui-dashboard/src/components/TaskQueue.tsx:182-230 (transition handler guarding concurrent clicks via writing.current, posting with crypto.randomUUID(), and re-reading queue state)",
    "ui-dashboard/src/components/__tests__/TaskQueue.transitions.test.tsx:83-276 (UI tests verifying Start/Finish controls, pending state, confirmed/unconfirmed/refused/failed states, color tokens, and superseded read handling)"
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
- **Codex** (advisory GitHub review of `8f874437f`): a P2, fixed in `467f1dfc2`, and a P1 about the missing packet, settled by the operator's waiver; both threads resolved. **Copilot** did not review this PR.

## Validation

| Check | Result |
|---|---|
| 📊 CI Pipeline Summary | PASS |
| 🧪 Unit Tests | PASS |
| independent embedded audit | FAIL |
| PR Steward / final readiness | FAIL |
| local: pytest tests (services/adhd-dashboard) | PASS |
| local: npx tsc --noEmit (ui-dashboard) | PASS |
| local: npx vitest run (ui-dashboard) | PASS |
| local: npx vite build (ui-dashboard) | PASS |
| local: npx eslint src (ui-dashboard) | FAIL |
| live: a Start or Finish write against the Task Orchestrator on 127.0.0.1:7890 | NOT_RUN |
| live: the orchestrator's refusal shape (missingNotes) | NOT_RUN |
| browser: Start and Finish in the cockpit | NOT_RUN |
| audit: validation inside the sealed AGY session | NOT_RUN |

The embedded-audit gate, recheck and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local pytest in services/adhd-dashboard (181 passed), tsc, vitest (174/174) and vite build pass at the audited head. No CI job runs services/adhd-dashboard/tests: pytest.ini has testpaths = tests, the unit gate collects tests/unit plus two files, and the workflows name adhd-dashboard only for container builds.
- Corroborating Grok G-1 (LOW, OPEN): The confirmed action chip drops the orchestrator anomaly note whenever the fresh read lists the clicked item in the returned new role. A Start/Finish whose previous/new roles differ from queue→work or work→terminal still renders [CONFIRMED] when that new role is work or queue and visible in the first 20 rows.
- Corroborating Grok G-2 (LOW, OPEN): The browser parser accepts any contract body with a known status and, for applied, a new_role. It does not require item_id to equal the row that was clicked. The backend parser does require that match before it will report applied.
- AGY risk (OPEN): External writer TOCTOU window: while _WRITE_LOCK serializes requests within the backend process and re-verifies the port 7890 container ID after reading the item role, an external runner writing directly to port 7890 can still transition the item between read_item_role and send_transition; parse_transition_result mitigates this by detecting unexpected (previousRole, newRole) pairs and surfacing them in reason.
- AGY risk (OPEN): Unverified actor attribution: transitions are sent as actor {id: 'operator:cockpit', kind: 'user'}, which the Task Orchestrator records without cryptographic verification until Wave 2C lands.
- AGY risk (OPEN): Browser-bundled API key: when VITE_DASHBOARD_API_KEY is configured for the frontend, the secret is present in client bundle assets, so the backend must remain bound to 127.0.0.1 as documented in services/adhd-dashboard/README.md.
- AGY risk (OPEN): Candidate tests were reviewed statically from the diff only and were not executed in this embedded audit because candidate code execution and tools are disabled (validation_status=NOT_RUN).
- Supervisor check of Grok G-1 (a cyan confirmed chip hides the orchestrator's anomaly note): accurate and OPEN, low. In TaskQueue.tsx, actionLines for the confirmed phase prints only the new role and drops result.reason, while the unconfirmed phase prints it. The backend puts an unexpected move in reason while still answering applied. The note is hidden only when the item lands in work or queue and is listed: a Finish that cascades always lands in terminal and shows as unconfirmed with its note. OPERATOR: decision pending.
- Supervisor check of Grok G-2 (the browser does not check that the answer's item_id is the clicked item): accurate and OPEN, low. parseTransitionResult in taskQueue.ts does not read item_id. The backend builds every answer from the item id in the request path and parse_transition_result refuses to report applied for another item, so a mismatched answer would need a broken or hostile backend on 127.0.0.1:8097. Defence in depth only. OPERATOR: decision pending.
- Supervisor check of Grok's risks on the key and loopback: accurate and OPEN. The route fails closed without DASHBOARD_API_KEY and compares X-API-Key in constant time, but it does not check the client address, and the cockpit's copy of the key (VITE_DASHBOARD_API_KEY) is in the browser bundle. Safety rests on running the backend on 127.0.0.1, as the README says.
- Supervisor check of Grok's risk on more than one backend process: accurate and OPEN. The lock that serialises the role read and the write is per process; two uvicorn workers could both read queue and both send start, and the second start would move the item work to review. The README's command starts one process; nothing enforces it.
- Grok's risks on the external-writer window, unverified actor, complete skipping review, and cascades restate limits the PR body and README already record; AGY raised the same first three. They stay OPEN.
- Grok's risk on helpers outside the diff (check_port_owner, _post, extract_tool_payload) is answered by the PR #1518 audit, which covered them at df8b6bc5d, and by the local test runs here; main has not changed them since.
- Grok's risk on provenance not re-fetched inside the sealed audit: the supervising session built the diff from git objects in a worktree at the audited head, read the PR head and review threads from GitHub, and recorded CI in CI_EVIDENCE.json.
- Audit scope: the whole PR diff, merge-base 0aa2cf349 to 467f1dfc2; when this bundle was built main had moved to 44e5ac3cc (#1513) without touching this PR's files, scripts/audit, scripts/governance, schemas/proof, config/audit or .github/workflows. The PR branch is behind main and was not merged or rebased.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Advisory GitHub reviews, not embedded auditors: Codex reviewed 8f874437f with 2 findings. P2 (a confirming read that a newer Refresh replaced could still turn an action cyan) was fixed in 467f1dfc2, the audited head, and its thread resolved. P1 (no supervisor-issued packet for a new workflow writer, AGENTS.md section 3) was settled by the operator's waiver and its thread resolved. Codex's review-summary comment for 467f1dfc2 says completed with has_any_findings=true and posted no new review or thread; read as referring to those two. Copilot did not review this PR; the operator chose to freeze without asking it ('Freeze and audit now').
- No supervisor-issued MacroPacket or Task Packet exists for this work. The operator waived the requirement for this change ('Waive it, record why', 2026-11-22T16:11:42Z) after being told a packet written then could bind only the remaining steps, not the implementation. Authority is the operator's requests recorded under fallback_auditor_approval and operator_decisions.
- Not exercised: any live write (deliberately; the orchestrator on 127.0.0.1:7890 holds the operator's real tasks), the orchestrator's refusal shape live, Start and Finish in a browser, and the backend inside the compose container, where the route can never prove port ownership and answers unavailable. The write route works only for a host-run backend; the service README says so.
- Known limits recorded in the PR, not defects against its claims: Finish never shows the cyan confirmed state because the panel lists only work and queue items; Start confirms only when the item is among the first 20 work items; complete moves work straight to terminal, skipping review, and can complete parent items (the response reports how many); an item with no matching note schema completes ungated.
