# AUDITOR REPORT — PR #1518 L2 embedded audit (TP-DMX-PR1518-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.5.13, `gemini-4-argon-high` (operator-requested route; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, prompt from the repo's trusted builder (`scripts.audit.pal_clink_runner --build-prompt`)
- **Implementer**: Claude Code (claude-fable-5-2 requested, linked session local_06ecd46b), a different runner and model family
- **Audited head**: `df8b6bc5d9f5de26041e5247c3c2b24380ab29f6` · **Base**: `8edff9b52480681d5eb7b420a3efcdf42ab4c36c` (the merge-base with main)
- **Verdict**: **PASS** · validation inside the audit: NOT_RUN
- **Containment**: stream step types ['agent_response', 'system_message', 'user_input'] only, no tool steps; AGY tool permissions were always-proceed, so this is observed, not enforced
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Evidence label**: **AUDITOR_WRITTEN_RAW_RETAINED**: the raw AGY stream, stderr and wrapper exit lines are in `review_bundle/`

## Why this audit

Cockpit audit finding G-2: the dashboard's task panel showed seeded sample tasks. This PR adds a read-only `GET /api/tasks` to
`services/adhd-dashboard` (`orchestrator_tasks.py`). It reads the Task Orchestrator MCP on `127.0.0.1:7890`, and only after Docker
labels show that this checkout's project owns the port; the one MCP tool it calls is `query_items`. In `ui-dashboard` the seeded
`TaskSequencer` panel is replaced by a read-only `TaskQueue` panel. This audit covers the whole PR diff: 14 files, six commits,
`8edff9b52..df8b6bc5d`.

## Operator approval of the audit route

Audit approval 2026-11-20T04:04:29Z: "Yes, audit #1518" (Claude Code session d3cf0485), on the route first requested
2026-10-30T10:37:01Z: "let's audit with agy argon 4, codex astra, and grok too" (cockpit work, reused here). Recorded per
docs/ops/embedded-audit.md "Packet-specific supervisor-approved fallback auditors": approval, bounded input, no-secret
constraints, exact invocation and verdict are in `PROOF.json` and `review_bundle/`.

## Auditor return (verbatim JSON)

```json
{
  "status": "completed",
  "verdict": "PASS",
  "findings": [],
  "risks": [
    {
      "id": "RISK-1",
      "severity": "low",
      "path": "ui-dashboard/src/App.tsx",
      "summary": "Replacing <TaskSequencer cognitiveState={...} onError={reportTaskError} /> with <TaskQueue /> removes the call site of reportTaskError in DashboardApp; if reportTaskError is no longer referenced elsewhere in App.tsx and tsconfig enforces noUnusedLocals during tsc typechecking, the production TypeScript build should be verified in CI."
    },
    {
      "id": "RISK-2",
      "severity": "low",
      "path": "services/adhd-dashboard/orchestrator_tasks.py",
      "summary": "read_task_queue performs two docker ps checks (up to 5s timeout each) and two sequential MCP initialize + tools/call HTTP sessions (up to 5s timeout each for 'work' and 'queue' roles), bounding worst-case latency at ~20s under hung local dependencies."
    }
  ],
  "rationale": "Audited PR 1518 at head SHA df8b6bc5d9f5de26041e5247c3c2b24380ab29f6 against base SHA 8edff9b52480681d5eb7b420a3efcdf42ab4c36c across all 14 changed files. The changes introduce a read-only GET /api/tasks endpoint in services/adhd-dashboard and replace the seeded TaskSequencer panel in ui-dashboard with a read-only TaskQueue component backed by the Task Orchestrator MCP on 127.0.0.1:7890. Security and isolation controls are well-implemented: orchestrator_tasks.py verifies git checkout identity and Docker container port ownership (including container_id continuity) both before and after querying the MCP server to prevent cross-project data leakage or TOCTOU container-replacement races, strips host filesystem paths from public responses and error reasons, and restricts MCP interaction strictly to read-only query_items calls. The frontend parser and component validate payloads strictly, isolate queue failures from the main ADHD state alert, prevent stale request overwrites via a request counter ref, and provide comprehensive unit and integration tests on both backend and frontend.",
  "inspected_paths": [
    "claudedocs/design/ui-dashboard-audit-2026-10-30.md",
    "services/adhd-dashboard/README.md",
    "services/adhd-dashboard/backend.py",
    "services/adhd-dashboard/orchestrator_tasks.py",
    "services/adhd-dashboard/requirements.txt",
    "services/adhd-dashboard/tests/test_orchestrator_tasks.py",
    "ui-dashboard/src/App.taskQueue.test.tsx",
    "ui-dashboard/src/App.test.tsx",
    "ui-dashboard/src/App.tsx",
    "ui-dashboard/src/components/TaskQueue.tsx",
    "ui-dashboard/src/components/TaskSequencer.tsx",
    "ui-dashboard/src/components/__tests__/TaskQueue.test.tsx",
    "ui-dashboard/src/taskQueue.test.ts",
    "ui-dashboard/src/taskQueue.ts"
  ],
  "evidence_refs": [
    "repo:DDD-Enterprises/dopemux-mvp#pr:1518@df8b6bc5d9f5de26041e5247c3c2b24380ab29f6",
    "base:8edff9b52480681d5eb7b420a3efcdf42ab4c36c",
    "services/adhd-dashboard/backend.py:get_tasks",
    "services/adhd-dashboard/orchestrator_tasks.py:resolve_expected_project",
    "services/adhd-dashboard/orchestrator_tasks.py:check_port_owner",
    "services/adhd-dashboard/orchestrator_tasks.py:list_role_items",
    "services/adhd-dashboard/orchestrator_tasks.py:read_task_queue",
    "services/adhd-dashboard/tests/test_orchestrator_tasks.py:TestParsing",
    "services/adhd-dashboard/tests/test_orchestrator_tasks.py:TestPortOwner",
    "services/adhd-dashboard/tests/test_orchestrator_tasks.py:TestReadTaskQueue",
    "services/adhd-dashboard/tests/test_orchestrator_tasks.py:TestMcpClient",
    "ui-dashboard/src/taskQueue.ts:parseTaskQueue",
    "ui-dashboard/src/components/TaskQueue.tsx:TaskQueue",
    "ui-dashboard/src/App.tsx:DashboardApp",
    "ui-dashboard/src/components/__tests__/TaskQueue.test.tsx",
    "ui-dashboard/src/App.taskQueue.test.tsx"
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
- **Codex** and **Copilot** (advisory GitHub reviews of `dd0c809ef`): 1 and 3 findings, fixed in `3dda9ec38` and `df8b6bc5d`, 4 threads resolved. Codex's review-summary comment records a completed review of `df8b6bc5d` with no findings; Copilot did not review the fix commits.

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
| live: GET /api/tasks from a host-run backend at the audited head, against the Task Orchestrator MCP on 127.0.0.1:7890 | PASS |
| browser: the ok panel | PASS |
| browser: the unavailable, empty and wrong_project panel states | NOT_RUN |
| live: a container replacement during a read | NOT_RUN |
| audit: validation inside the sealed AGY session | NOT_RUN |

The embedded-audit gate, recheck and PR Steward fail until this proof is signed and pushed.

## Remaining risks

- Validation was not run inside the sealed audit sessions (validation_status=NOT_RUN); local pytest in services/adhd-dashboard (76 passed), tsc, vitest (150/150) and vite build pass at the audited head. No CI job runs services/adhd-dashboard/tests: pytest.ini has testpaths = tests, the unit gate collects tests/unit plus two files, and the workflows name adhd-dashboard only for container builds.
- Corroborating Grok G-1 (LOW, OPEN): The post-read owner check treats an unchanged container id as proof the publisher stayed the same. Docker keeps that id across stop and start, so the same container can pass both checks while another publisher holds port 7890 during list_role_items.
- Corroborating Grok G-2 (LOW, OPEN): The route and README state that GET /api/tasks always returns HTTP 200 with status ok, empty, unavailable, or wrong_project. get_tasks does not catch exceptions. resolve_expected_project catches only OSError and SubprocessError, and list_role_items parses the MCP body outside the transport try.
- Supervisor check of AGY RISK-1 (App.tsx: reportTaskError might be left unused, which noUnusedLocals would reject): not a defect at this head. reportTaskError is still passed to TeamDashboard in App.tsx, and `npx tsc --noEmit` exits 0 at the audited head (LOCAL_VALIDATION.txt).
- Supervisor check of AGY RISK-2 (worst-case latency of one /api/tasks request): accurate and OPEN. OWNER_CHECK_TIMEOUT_S and MCP_TIMEOUT_S are 5.0 s each in orchestrator_tasks.py; one request makes two owner checks and reads two roles, so a hung Docker and a hung MCP could hold it for about 20 s. Not measured live; the two live reads at the audited head took under 1 s. OPERATOR: decision pending.
- Supervisor check of Grok G-1 (same container id after stop and start): accurate and OPEN. read_task_queue compares the owner's container id before and after the read, and `docker stop` followed by `docker start` keeps that id. The repo's switch-project removes and recreates the container, which changes the id and is caught; stopping and restarting the same container around another publisher, inside one request, is not. It needs local Docker access. Not exercised. OPERATOR: decision pending.
- Supervisor check of Grok G-2 (HTTP 500 where the README says always 200): partly accurate and OPEN. get_tasks has no catch-all and resolve_expected_project catches only OSError and SubprocessError, so an unexpected exception becomes HTTP 500. The parse path Grok names is not one of them at this head: dopemux.mcp.tool_snapshot.parse_mcp_response_body returns None for a body it cannot parse, and extract_tool_payload and parse_item_list raise McpReadError for every shape they do not accept, which read_task_queue answers as unavailable. Both functions were read in full, and 33 malformed or unusual replies were run through that expression for both roles in the audit worktree: none raised anything other than McpReadError (PARSE_PROBE.txt). On a 500 the panel shows a failure and no items. OPERATOR: decision pending.
- Supervisor check of Grok's risks R1 and R4 (compose container): accurate and OPEN. backend.py imports orchestrator_tasks at import time, which imports dopemux.mcp; the Dockerfile copies src/dopemux and this PR adds pyyaml to requirements.txt. No image was built or run for this audit, so the README's statement that the compose container always answers unavailable is NOT_RUN, and a failed import there would take down every route of the service. The cockpit's task panel needs a host-run backend to show items.
- Supervisor check of Grok's risk R2 (what the response can carry): accurate and OPEN, low. The expected project id is returned without _public_id; the ids seen from resolve_identity_view are a directory name plus a hash, not a path. Container names appear in the reason of a refusal; they carry a project name, not a path. The route keeps the dashboard's API-key check.
- Supervisor check of Grok's risk R3 (modules outside the diff, tests not executed in the audit): DEFAULT_TO_PORT is the int 7890 and DockerContainerInfo.published_ports is List[int] at this head; the tests were run locally (76 passed); live requests gave the verdicts OK (after the switch) and WRONG_PROJECT (before it). match_target and identity_from_docker_labels are outside this diff and were not re-audited.
- Grok's risk R5 (provenance not checked inside the sealed audit): the supervising session built the diff from git objects in a worktree at the audited head, read the PR's head and review threads from GitHub, and recorded CI in CI_EVIDENCE.json.
- The raw AGY stream (1 line) and the AGY CLI log copy (6 lines) contain the operator's home directory path, as in earlier bundles. Only the account email address was redacted (REDACTIONS.md). LOCAL_VALIDATION.txt shows the home directory as ~.
- Audit scope: the whole PR diff, merge-base 8edff9b52 to df8b6bc5d; when this bundle was built main had moved to ba5c3e07b (#1514, #1517, #1516) without touching this PR's files, scripts/audit, scripts/governance, schemas/proof, config/audit or .github/workflows. The PR branch is behind main and was not merged or rebased.
- Auditor model identity: requested gemini-4-argon-high; provider-attested identity UNKNOWN; recorded as the schema family value 'gemini'.
- AGY tool permissions were always-proceed; containment rests on the observed absence of tool steps.
- Advisory GitHub reviews, not embedded auditors: Codex and Copilot each reviewed dd0c809ef (Codex 1 P2 finding, Copilot 3 findings, all in services/adhd-dashboard/orchestrator_tasks.py). The fixes are 3dda9ec38 and df8b6bc5d and all 4 threads are resolved. Codex's review-summary comment records a completed code review of df8b6bc5d with has_any_findings=false (2026-11-19T21:54:38Z) and Codex added a thumbs-up reaction; there is no Codex review object on that commit. Copilot did not review 3dda9ec38 or df8b6bc5d.
- No supervisor-issued MacroPacket exists for this work. Authority is the operator's requests recorded under fallback_auditor_approval and operator_decisions.
- Live reads of GET /api/tasks from a host-run backend returned status ok (40 items, total 528): the supervising session at aaa5a31d3 (2026-11-19) and at the audited head (2026-11-20T04:11:01Z), the implementing session at the audited head (2026-11-19T21:52:34Z). Before the port was switched the same request answered wrong_project (supervising session, aaa5a31d3). The responses, metadata and the browser screenshot hold real task titles and host paths; they stay in custody.
- Not exercised: the unavailable, empty and wrong_project panel states in a browser (vitest only); a container replacement during a live read (pytest only); the backend inside the compose container. Port ownership is read from Docker labels, so /api/tasks works only for a host-run backend; the service README says so.
- Panel limits seen in the live reads, not defects against this PR's claims: the store's newest modified_at is 2026-10-07 and the panel shows the read time, not item age; every row says 'complexity unknown' because the orchestrator's list mode does not return complexity; review-role items are not listed (the roles read are work and queue).
- Port 7890 was switched from another project to dopemux-mvp for the live reads, on the operator's approval ('Yes, switch it', 2026-11-19T21:23:28Z). It still serves dopemux-mvp. OPERATOR: decide whether to switch it back.
