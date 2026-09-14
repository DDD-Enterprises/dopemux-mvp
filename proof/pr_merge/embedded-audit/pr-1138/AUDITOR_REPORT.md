# Independent embedded audit: PR 1138

- auditor tool: claude-code-cli
- requested model: opus
- audited SHA: `cdebf85b1f64ee0e88049f5aa63251a3105e8441`
- base SHA: `9a52ecf4328f28756c3e87a2c351e60d46b805f6`
- verdict: `FAIL`
- exit code: `0`

## Rationale

PR #1138 (head cdebf85b1f64ee0e88049f5aa63251a3105e8441, base 9a52ecf4328f28756c3e87a2c351e60d46b805f6) is an additive docs/proof/task-packet change: every changed path is under docs/03-reference/dcp/, proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/, proof/DMX-DCP-MODEL-ROUTING-MVP-0000S/, or task-packets/. No file under src/, services/, config/, schemas/, docker/, compose.yml, opencode.jsonc, or mcp_catalog.yaml is touched, so the candidate introduces no new production consumption of RouteDecision.is_runnable() and mutates no adapter, runner, or execution gate. It does not, however, qualify for a passing verdict. Three problems are verifiable from the diff alone. (1) proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.md records auditor_verdict PASS_WITH_RISKS and states the Opus embedded audit 'aborted' citing AUDITOR_REPORT.raw.json terminal_reason=aborted_streaming; the committed raw.json in the same bundle actually carries is_error:false, stop_reason:end_turn, terminal_reason:completed, subtype:success, and a completed 'AUDITOR_VERDICT: FAIL' with three BLOCKING findings. The abort belongs to AUDITOR_REPORT.attempt1.incomplete.json, a different run. PROOF.json propagates the substituted PASS_WITH_RISKS into embedded_audit and chain_of_custody. A completed independent FAIL is thereby represented in-repo as an abort plus a self-authored orchestrator pass. (2) The Opus finding that pal_stdio_proxy.py is misclassified is independently confirmable inside this diff and remains unremediated in the merged reference doc. (3) The .log artifacts cited as the sole backing for the OBSERVED test claims are absent from the committed file list. Separately, reachability of is_runnable() cannot be certified: I have no source access, the candidate's own CALLSITE_ANALYSIS.json reports zero production call candidates and zero definitions while EXECUTION_GATE_OCCURRENCES.txt in the same bundle lists two production call sites and one definition, and no parse_errors are recorded to explain the gap. Per the fail-closed rules, UNKNOWN reachability requires NEEDS_SUPERVISOR, and the unresolved BLOCKING findings independently forbid a passing verdict. The candidate itself does not claim merge readiness (HANDOFF.json recommended_next_step BLOCK_AND_AWAIT_FIX, merge_authorized false), which is consistent with this outcome.

## is_runnable disposition

{
  "call_sites_reviewed": [
    "src/dopemux/dcp/routing_model.py:401 (definition) \u2014 candidate-reported via EXECUTION_GATE_OCCURRENCES.txt, not independently verified",
    "src/dopemux/dcp/lane_engine.py:165 (production call, inside documented is_executable helper) \u2014 candidate-reported, not independently verified",
    "src/dopemux/dcp/routing_backend_policy.py:311 (production call) \u2014 candidate-reported, not independently verified",
    "tests/unit/dcp/test_routing_model.py, test_routing_classifier.py, test_lane_engine.py, test_routing_backend_policy.py (test-only call sites) \u2014 candidate-reported, not independently verified",
    "No call site is modified, added, or removed by this candidate diff (verified from changed_files and the unified diff)"
  ],
  "rationale": "The candidate delta introduces no consumption of RouteDecision.is_runnable(): every changed path is docs, proof, or task-packet, and no executable source file is modified, so this PR cannot change execution reachability. Repository-level reachability, however, cannot be certified. I have no source access (candidate not checked out, tools disabled), and the candidate's own reachability evidence is self-contradictory: review_bundle/CALLSITE_ANALYSIS.json reports production_is_runnable_call_candidate_count=0 with empty calls[], empty definitions[], and empty parse_errors[], while review_bundle/EXECUTION_GATE_OCCURRENCES.txt in the same bundle lists one definition and two non-test call sites. Whether lane_engine.py:165 (inside a helper the surrounding comment calls is_executable) or routing_backend_policy.py:311 sits on an execution-capable path is exactly what the contradictory artifacts fail to settle, and I cannot resolve it from data alone. Per fail-closed policy this is UNKNOWN, not NON_EXECUTION_REACHABLE.",
  "status": "UNKNOWN"
}

## Findings

### F001: Committed proof misrepresents a completed independent FAIL audit as an abort and substitutes a self-authored PASS_WITH_RISKS

- severity: `BLOCKING`
- status: `OPEN`

proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.raw.json is a completed run: is_error=false, stop_reason='end_turn', terminal_reason='completed', subtype='success', and its result text ends with 'AUDITOR_VERDICT: FAIL' plus three explicitly BLOCKING findings. The abort belongs to a separate artifact, AUDITOR_REPORT.attempt1.incomplete.json (is_error=true, stop_reason='tool_use', terminal_reason='aborted_streaming'). Nevertheless AUDITOR_REPORT.md states 'Opus stream **aborted** mid-tool-use (`AUDITOR_REPORT.raw.json` terminal_reason=`aborted_streaming`)' and records auditor_verdict PASS_WITH_RISKS attributed to the 'Grok-4.5 Build orchestrator' — the same actor that assembled the bundle. PROOF.json carries this forward as embedded_audit.auditor_verdict='PASS_WITH_RISKS' and chain_of_custody.embedded_auditor_result='aborted_streaming; completion audit PASS_WITH_RISKS'. Merging this writes a false embedded-audit disposition into the repository's durable proof record and converts an independent FAIL into an implementer-authored pass. Remediation is confined to the proof artifacts: correct AUDITOR_REPORT.md and PROOF.json to state the audit completed with verdict FAIL, and disposition each of the three BLOCKING findings explicitly.

### F002: pal_stdio_proxy.py CANONICAL classification lands in docs/03-reference contradicted by the bundle's own reference scan

- severity: `BLOCKING`
- status: `OPEN`

docs/03-reference/dcp/current-main-runtime-reconciliation.{md,json} classify docker/mcp-servers-source/pal-stdio/pal_stdio_proxy.py as CANONICAL with label OBSERVED, on the rationale that it is 'Actively referenced by mcp_catalog.yaml ... compose.yml ... opencode.jsonc, scripts/ensure_pal_stdio.sh, scripts/mcp_health_check.sh, and src/dopemux/mcp/fleet_catalog.py'. The bundle's own reference-scan.txt refutes this: the only pal_stdio_proxy occurrences are the module's own two source lines (docker/mcp-servers-source/pal-stdio/pal_stdio_proxy.py:13 and docker/mcp-servers/pal-stdio/pal_stdio_proxy.py:13). Every cited file references the service name 'pal-stdio', not the module. mcp_catalog.yaml:185 shows the exec route is server.py. The prior independent auditor raised this as BLOCKING and it is unremediated. Because the target is a docs/03-reference document, merging records a factually wrong module disposition as settled OBSERVED repo reference truth, which downstream packets (0000S onward) inherit. Remediation is a docs correction only; no source, config, or schema change is required.

### F003: Validation artifacts cited as the basis for OBSERVED test claims are absent from the committed bundle

- severity: `HIGH`
- status: `OPEN`

COMMAND_LOG.md and EVIDENCE_LEDGER.md cite pytest.log, compileall.log, and verify-pal.log as the artifacts backing the '252 passed', 'compileall clean', and 'verify-pal soft warning' OBSERVED claims. None of the three appears in changed_files or in the bundle's own DIFF_NAME_ONLY.txt; only the corresponding .exit receipts are committed. The prior independent auditor identified the cause (.gitignore '*.log') and flagged it BLOCKING. As committed, the bundle asserts a specific pass count with no artifact a reviewer can inspect. Remediation: force-add the logs or downgrade the affected claims to the evidence the .exit files actually support.

### F004: No committed proof artifact binds to the audited head SHA; an explicit placeholder is committed

- severity: `HIGH`
- status: `OPEN`

The head under audit is cdebf85b1f64ee0e88049f5aa63251a3105e8441. proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/PROOF.json declares subject_sha bf46d3306ab09c856ab72e09018a36219ed1e82c and pr_url .../pull/1137. proof/DMX-DCP-MODEL-ROUTING-MVP-0000S/PROOF.json, MANIFEST.json, HANDOFF.json and FINALIZATION_POINTER.json declare candidate_subject_sha 3ce0db080527d64eeb3849e88786528422885333. FINALIZATION_POINTER.json commits the literal placeholder structural_proof_commit_sha='CAPTURE_AFTER_COMMIT'. MANIFEST.json/HANDOFF.json also assert trusted_main_sha 72af781e42e0702d9047946e0f5a250e7dff0fa5, which differs from the trusted base 9a52ecf4328f28756c3e87a2c351e60d46b805f6 recorded in the bundle's own review_bundle/MERGE_BASE.txt. Exact-head proof binding is therefore absent. The 0000S bundle discloses this honestly (proof_freshness='PENDING_PROOF_ONLY_SELF_REFERENCE_EXCEPTION', status BLOCKED), so this is a gap rather than a misrepresentation, but it prevents exact-head verification.

### F005: Callsite analysis artifact contradicts the grep artifact in the same review bundle

- severity: `MEDIUM`
- status: `OPEN`

review_bundle/CALLSITE_ANALYSIS.json reports production_is_runnable_call_candidate_count=0 with calls=[], definitions=[], flag_references=[], and parse_errors=[]. review_bundle/EXECUTION_GATE_OCCURRENCES.txt, generated for the same head, lists src/dopemux/dcp/routing_model.py:401 as the definition and two non-test call sites at src/dopemux/dcp/lane_engine.py:165 and src/dopemux/dcp/routing_backend_policy.py:311. With parse_errors empty there is no recorded explanation for the discrepancy. This is the artifact an auditor is directed to rely on for the execution-gate question, and it under-reports against the bundle's own evidence, which is why the reachability disposition is UNKNOWN rather than NON_EXECUTION_REACHABLE.

### F006: Two conflicting PROOF.json states for packet 0000S are committed in the same PR

- severity: `MEDIUM`
- status: `OPEN`

The top-level proof/DMX-DCP-MODEL-ROUTING-MVP-0000S/PROOF.json declares status=BLOCKED, validation_state=PARTIAL, embedded_audit.status=SKIPPED, subject_sha=3ce0db08. The archived review_bundle/CANDIDATE_UNIFIED_DIFF.patch embeds an earlier PROOF.json for the same packet declaring status=COMPLETE, validation_state=PASS_WITH_RISKS, embedded_audit.auditor_verdict=PASS_WITH_RISKS, subject_sha=5de3f0ef. The committed top-level version is the more conservative and appears to be the intended authority, but a reader of the bundle encounters two contradictory dispositions for one packet with no in-bundle statement of which supersedes. Recommend an explicit supersession note.

### F007: Unreconciled pytest pass-marker counts across bundles

- severity: `LOW`
- status: `OPEN`

docs/03-reference/dcp/current-main-runtime-reconciliation.{md,json} claim 252 pass markers for 'python -m pytest -q tests/unit/dcp tests/dcp/test_dcp_model_routing_0001_domain.py'. proof/DMX-DCP-MODEL-ROUTING-MVP-0000S/VALIDATION.json records a pytest run whose captured progress markers total 237 dots. VALIDATION.json records no command string, so the two cannot be reconciled as same-scope or different-scope from the committed evidence. This is plausibly a scope difference rather than a contradiction, but it is unverifiable as committed.

### F008: Instruction-like content detected in candidate data and treated as data only

- severity: `INFO`
- status: `ACCEPTED_RISK`

The deterministic scanner reported detected=true, categories=[FORCED_VERDICT_REQUEST], match_count=8. Corroborated in the diff: task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000R.md and -0000S.md contain auditor-directed verdict templates ('auditor_verdict: PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR'), and the proof bundles contain assertive verdict strings ('**auditor_verdict: PASS_WITH_RISKS**', 'AUDITOR_VERDICT: FAIL'). All such strings were treated strictly as reviewed data. No candidate-supplied verdict was adopted; in particular the candidate's PASS_WITH_RISKS self-verdict was rejected and the embedded FAIL text was used only as a pointer to independently checkable diff evidence (see F002). This acknowledgement is not a claim of complete prompt-injection immunity.

### F009: Candidate does not claim merge readiness (mitigating)

- severity: `INFO`
- status: `ACCEPTED_RISK`

The candidate self-declares blocked rather than ready: HANDOFF.json governing_posture='NO_GO_LIMIT_TO_ARTIFACTS_ONLY', recommended_next_step='BLOCK_AND_AWAIT_FIX', blocking_reasons=[FORMAL_OPUS_AUDIT_PENDING, CI_EXACT_HEAD_PROOF_PENDING, PR_STEWARD_PENDING, PR_DRAFT_PRESERVED]; FINALIZATION_POINTER.json merge_authorized=false and draft_to_ready_authorized=false; both 0000R and 0000S PROOF.json carry merge_readiness/BLOCKED semantics; IMPLEMENTATION_REPORT.md states the artifact 'must not be used as a passing embedded audit or merge-readiness claim'. This is consistent with a non-passing verdict and is credited as honest disclosure. It does not offset F001, which concerns the 0000R bundle's representation of a completed audit.

