**Report (static only; no tests run)**

Scope is the four-file delta at a8b4015 against base a14ecfe. The head and hashes are supervisor-supplied custody observations. I did not observe them directly, so `observed_head` and `head_match` are null. The remote PR is still a draft at the predecessor.

- **C1 PASS.** Both `pr-policy` jobs gain `permissions: {}`. Triggers, `if` gates and steps are unchanged. The new test pins the empty permissions mapping, the `if` gate, no `uses`, run-only steps and no provider steps.
- **C2 PASS.** `pm_transition_work_item` raises RuntimeError unconditionally, so the all-status and clients-present/absent test matrix is accurate. The tests assert no client calls and no emitted events. The error message matches the regex. The product code is not weakened.
- **C3 PASS.** The added wrapper tests cover three cases: no orchestrator client, a non-adapter client, and a project-mismatched real adapter. In the mismatch case the `ValueError` fires before `_request_parts`, so the credential supplier and the transport are never touched. The diff touches no other test files, so existing v2 suites are unchanged. I could not see them.
- **C4 PASS.** The disclosure separates the scoped local pass from full CI, CodeQL closure, live behavior and signed acceptance, and it claims no historical acceptance. The 308+30+249=587 arithmetic is consistent, but the counts are author claims.

Residual risks are all low. Seven removed v1 tests covered event emission (`from_phase`, `blocker.cleared`), and I cannot see equivalent v2 coverage. The wrapper guards have only negative tests in this delta. The `isinstance` check admits only the sync adapter. The test only inspects the job-level permissions mapping, not the workflow-level one.

```json
{
"schema":"independent-audit/v1",
"status":"PASS_WITH_RISKS",
"subject":{"packet_id":"DMX-PR1501-FOLLOWUP-R1","repo":"DDD-Enterprises/dopemux-mvp","pinned_sha":"a8b401558adc5126a850dc38d76b26181d2b9df2","observed_head":null,"head_match":null,"base":"a14ecfe51f1b7bd90fb12f173d95d7dcdbe4905c","file_hashes":{".github/workflows/gemini-dispatch.yml":"c51a07c767c275724a63ff6aceff08b1ec400b6e0ae00c21c75e5cfa0591c595",".github/workflows/gemini-scheduled-triage.yml":"40721dd424bcb79c847ce8534a2b32fdd4101bfa81dc01460373342fae99a81d","tests/unit/dopemux/pm/test_writes.py":"305ab90872906bf86dc9c59e0a8cb2f0164b10fd9f56ce39522087348bbd875f","tests/unit/test_ci_subscription_policy.py":"cfcc3de4f2b920715049ada2d31ae0579505413b34e35a661cd2a79168c2b7de"}},
"auditor":{"runner":"Claude Code CLI 2.1.319 firstParty/max, no tools","model_requested":"claude-sonnet-5-5","model_observed":"UNKNOWN","effort":"UNKNOWN","independent_of_implementer":true},
"checks":[
{"id":"C1","command_or_method":"static diff and test read","exit_code":null,"bucket":"PASS","evidence":"permissions: {} added to both pr-policy jobs; triggers, if gates and steps unchanged; new test pins them."},
{"id":"C2","command_or_method":"static read of writes.py and tests","exit_code":null,"bucket":"PASS","evidence":"v1 function raises unconditionally; tests cover all PMTaskStatus values with clients present and absent, assert no client calls and no events."},
{"id":"C3","command_or_method":"static read of wrapper, adapter and tests","exit_code":null,"bucket":"PASS","evidence":"Non-adapter and project-mismatch rejections occur before credential and transport use; no other test files in the delta."},
{"id":"C4","command_or_method":"static read of disclosure","exit_code":null,"bucket":"PASS","evidence":"Full CI, CodeQL, live, final review and signed acceptance are stated as NOT_RUN; scoped local pass is separated; no invalid historical acceptance."}
],
"findings":[
{"id":"F1","severity":"low","location":"tests/unit/dopemux/pm/test_writes.py (removed tests)","summary":"Seven v1 tests removed, including event-emission behaviors (from_phase, blocker.cleared); equivalent v2 coverage is not visible.","evidence":"Deleted tests; no replacement in the delta."},
{"id":"F2","severity":"low","location":"tests/unit/dopemux/pm/test_writes.py:244-278","summary":"The added wrapper tests are negative-only; no positive authenticated pass-through case in this delta. The isinstance check admits only SyncOwnershipAdapter.","evidence":"writes.py:378; test bodies."},
{"id":"F3","severity":"low","location":"tests/unit/test_ci_subscription_policy.py:127-136","summary":"Only job-level permissions are asserted; workflow-level permissions are not checked. The model_steps assertion is weak for a job with no provider steps.","evidence":"Test body."}
],
"instruction_like_content":[],
"author_claims_not_reproduced":["308 policy, 30 legacy PM and 249 ownership/API/route tests passed (587)","precommit checks passed","harness failures as described"],
"remaining_risks":["Remote draft still at predecessor; local subject unpushed","Hosted CI, CodeQL closure, live behavior and signed acceptance not assessed","Inherited candidate acceptance not inferred"],
"unknowns":["Actual model and effort (no runtime receipt)","Existing v2 suite contents and identifier() validation rules","Direct observation of head and hashes"],
"skip_reason":null,
"unblock":null,
"acceptance":"NOT_GRANTED"
}
```
