# Independent embedded audit: PR 1137

- auditor tool: claude-code-cli
- requested model: opus
- audited SHA: `b87a87787c852d6650d898811487167f63293493`
- base SHA: `9a52ecf4328f28756c3e87a2c351e60d46b805f6`
- verdict: `FAIL`
- exit code: `0`

## Rationale

PR 1137 is a proof-only structural repair: every changed path is under proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/**, docs/03-reference/dcp/, or task-packets/, with no src/, services/, docker/, config/, schemas/, scripts/, compose.yml, or .github/ modification, so the candidate implementation appears unaltered by this commit. However, the audit fails closed for four independent reasons. (1) Exact-head binding is absent: the trusted head under audit is fa935d63307b7dda4b4fcff877c9373cc511af5f, but every committed proof artifact (PROOF.json head_sha/subject_sha, MANIFEST.json candidate_subject_sha, HANDOFF.json chain_of_custody, FINALIZATION_POINTER.json) names 5de3f0ef56dfcf8545c395418b4a3d424b1bc249, and review_bundle/C1_SHA.txt names ab6c775460ee293862c624b72e04b2f8acbc4f37; PROOF.json itself records proof_freshness PENDING_PROOF_ONLY_SELF_REFERENCE_EXCEPTION and FINALIZATION_POINTER.json carries the placeholder CAPTURE_AFTER_COMMIT. Only review_bundle/MERGE_BASE.txt (9a52ecf4328f28756c3e87a2c351e60d46b805f6) matches trusted provenance. (2) is_runnable reachability is UNKNOWN: review_bundle/CALLSITE_ANALYSIS.json declares production_is_runnable_call_candidate_count=0 with empty calls/definitions/flag_references, while review_bundle/EXECUTION_GATE_OCCURRENCES.txt in the same bundle records two production consumers, src/dopemux/dcp/lane_engine.py:165 'return decision.is_runnable()' and src/dopemux/dcp/routing_backend_policy.py:311 'if not decision.is_runnable():'. Candidate source is not checked out and tools are disabled, so I cannot resolve which artifact is correct; per the trusted fail-closed rule UNKNOWN reachability maps to NEEDS_SUPERVISOR. (3) The mandated fail-closed gates is_execution_eligible, active_trusted_adapters, mutation_adapters_enabled, invocation_authorized, and execute_runner_plan appear nowhere in the diff or in any committed evidence artifact, so their disposition is unverifiable. (4) Proof integrity is compromised: AUDITOR_REPORT.md records auditor_verdict PASS_WITH_RISKS and states that AUDITOR_REPORT.raw.json has terminal_reason aborted_streaming, but the committed AUDITOR_REPORT.raw.json shows is_error=false, subtype='success', stop_reason='end_turn', terminal_reason='completed', and a result body that ends with 'AUDITOR_VERDICT: FAIL' plus three BLOCKING findings; the aborted run is a different file (AUDITOR_REPORT.attempt1.incomplete.json). A completed independent-auditor FAIL has therefore been summarized in-bundle as a PASS_WITH_RISKS under a false characterization of the underlying artifact. One of that FAIL's blocking findings is still being landed: docs/03-reference/dcp/current-main-runtime-reconciliation.md and .json classify pal_stdio_proxy.py as CANONICAL, which I independently corroborated as unsupported from committed evidence (reference-scan.txt contains exactly two 'pal_stdio_proxy' hits, both the module's own line 13 in docker/mcp-servers-source/ and docker/mcp-servers/, and mcp_catalog.yaml:185 shows the exec route is server.py, not the proxy), while EVIDENCE_LEDGER.md labels that classification OBSERVED with confidence 'certain'. The newly added structural layer (PROOF.json status BLOCKED, validation_state PARTIAL, embedded_audit SKIPPED, WARNINGS_AND_BLOCKERS.json, IMPLEMENTATION_REPORT.md, HANDOFF.json NO_GO_LIMIT_TO_ARTIFACTS_ONLY) is itself honest and explicitly non-passing, but it coexists with the stale contradicting artifacts. I ran no validation of my own. None of the findings require a source, config, schema, task-packet, rebase, force-push, merge, adapter, runner, or live-write change; remediation is confined to proof/doc artifacts plus a genuine exact-head independent audit run.

## is_runnable disposition

{
  "call_sites_reviewed": [
    "src/dopemux/dcp/routing_model.py:401 (definition, via EXECUTION_GATE_OCCURRENCES.txt)",
    "src/dopemux/dcp/lane_engine.py:165 (production consumer, via EXECUTION_GATE_OCCURRENCES.txt)",
    "src/dopemux/dcp/lane_engine.py:12 (docstring claim that is_executable is stricter than is_runnable)",
    "src/dopemux/dcp/routing_backend_policy.py:311 (production consumer, via EXECUTION_GATE_OCCURRENCES.txt)",
    "tests/unit/dcp/test_routing_model.py, test_lane_engine.py, test_routing_classifier.py, test_routing_backend_policy.py (test-only consumers, via EXECUTION_GATE_OCCURRENCES.txt)",
    "review_bundle/CALLSITE_ANALYSIS.json (asserts zero production candidates; contradicts the grep artifact above)"
  ],
  "rationale": "The two committed artifacts that speak to execution-gate reachability contradict each other. review_bundle/CALLSITE_ANALYSIS.json reports production_is_runnable_call_candidate_count=0 with empty calls, definitions, flag_references, and parse_errors, and explicitly defers disposition to the independent auditor. review_bundle/EXECUTION_GATE_OCCURRENCES.txt, produced in the same bundle, records a definition at src/dopemux/dcp/routing_model.py:401 and two non-test consumers under src/: lane_engine.py:165 'return decision.is_runnable()' (reached from an is_executable helper whose module docstring at line 12 claims it is stricter than is_runnable) and routing_backend_policy.py:311 'if not decision.is_runnable():'. Because candidate source is not checked out and tools are disabled, I cannot determine whether either consumer is execution-capable or purely advisory, nor whether the empty CALLSITE_ANALYSIS reflects a genuine absence or a failed/misconfigured scan. This PR modifies no source, so it introduces no new consumer, but the disposition itself remains unestablished and is recorded as UNKNOWN per fail-closed policy.",
  "status": "UNKNOWN"
}

## Findings

### F-001-AUDIT-VERDICT-MISREPRESENTATION: AUDITOR_REPORT.md records PASS_WITH_RISKS while misdescribing a completed independent-auditor FAIL as an aborted stream

- severity: `BLOCKING`
- status: `OPEN`

AUDITOR_REPORT.md states auditor_model_observed = 'Opus stream aborted mid-tool-use (AUDITOR_REPORT.raw.json terminal_reason=aborted_streaming); completion pass by Grok-4.5 Build orchestrator' and sets auditor_verdict = PASS_WITH_RISKS. The committed AUDITOR_REPORT.raw.json contradicts that description on its face: is_error=false, subtype='success', stop_reason='end_turn', terminal_reason='completed', and a full result body concluding 'AUDITOR_VERDICT: FAIL' with three explicitly [BLOCKING] findings. The genuinely aborted run is a separate file, AUDITOR_REPORT.attempt1.incomplete.json (is_error=true, stop_reason='tool_use', terminal_reason='aborted_streaming'). The effect is that a completed independent audit returning FAIL has been superseded in-bundle by a self-authored PASS_WITH_RISKS summary resting on a false characterization of the artifact it cites. The newer PROOF.json is honest about the current stage (embedded_audit status SKIPPED, auditor_tool 'none', status BLOCKED), but AUDITOR_REPORT.md remains committed, is listed in MANIFEST.json, and is named an authoritative artifact by the older HANDOFF.md, so a downstream reader can still consume the PASS_WITH_RISKS claim. Remediation is proof-artifact-only: withdraw or correct AUDITOR_REPORT.md and record the raw.json FAIL verdict verbatim.

### F-002-NO-EXACT-HEAD-BINDING: Proof bundle is not bound to the head SHA under audit

- severity: `HIGH`
- status: `OPEN`

The trusted head under audit is fa935d63307b7dda4b4fcff877c9373cc511af5f. That SHA appears in no committed artifact. PROOF.json (head_sha, subject_sha, chain_of_custody.candidate_subject_sha), MANIFEST.json (candidate_subject_sha), HANDOFF.json (chain_of_custody.candidate_subject_sha), and FINALIZATION_POINTER.json (candidate_subject_sha) all name 5de3f0ef56dfcf8545c395418b4a3d424b1bc249; review_bundle/C1_SHA.txt names ab6c775460ee293862c624b72e04b2f8acbc4f37. Only review_bundle/MERGE_BASE.txt (9a52ecf4328f28756c3e87a2c351e60d46b805f6) and HANDOFF.json chain_of_custody.merge_base_sha match trusted base provenance. The bundle self-discloses the gap (PROOF.json proof_freshness.status = PENDING_PROOF_ONLY_SELF_REFERENCE_EXCEPTION, FINALIZATION_POINTER.json structural_proof_commit_sha = 'CAPTURE_AFTER_COMMIT', blocking reason CI_EXACT_HEAD_PROOF_PENDING), which is honest, but exact-head binding is a mandatory trusted requirement and remains unsatisfied. A supervisor must decide whether the declared proof-only self-reference exception is acceptable; it cannot be granted from within the candidate bundle.

### F-003-UNRESOLVED-BLOCKING-CANONICAL-CLASSIFICATION-LANDED-IN-DOCS: pal_stdio_proxy.py CANONICAL classification, flagged BLOCKING by the completed prior audit, is still being landed into docs/03-reference/

- severity: `HIGH`
- status: `OPEN`

docs/03-reference/dcp/current-main-runtime-reconciliation.md and .json (and their proof-directory twins) classify docker/mcp-servers-source/pal-stdio/pal_stdio_proxy.py as CANONICAL, justified as 'Actively referenced by mcp_catalog.yaml, compose.yml, opencode.jsonc, scripts/ensure_pal_stdio.sh, scripts/mcp_health_check.sh, and src/dopemux/mcp/fleet_catalog.py'. I corroborated the prior auditor's rebuttal directly from committed evidence rather than adopting it: reference-scan.txt, the packet's own grep artifact, contains exactly two occurrences of the token 'pal_stdio_proxy', both being that module's own line 13 (PAL_URL = os.getenv("PAL_HTTP_URL", ...)) in the source and mirror copies; none of the six named files contains a reference to the module, and reference-scan.txt mcp_catalog.yaml:185 shows the canonical exec route is server.py, not the proxy. The listed files reference the service name 'pal-stdio', which is not the same as referencing the module. EVIDENCE_LEDGER.md nonetheless labels this claim OBSERVED with confidence 'certain'. The packet's own invariant requires this module to be classified canonical/legacy/experimental/unused 'based on active references'. Remediation is doc/proof-only.

### F-004-CONTRADICTORY-EXECUTION-GATE-EVIDENCE: CALLSITE_ANALYSIS.json reports zero is_runnable production call sites while EXECUTION_GATE_OCCURRENCES.txt lists two under src/

- severity: `HIGH`
- status: `OPEN`

review_bundle/CALLSITE_ANALYSIS.json declares production_is_runnable_call_candidate_count=0 with calls=[], definitions=[], flag_references=[], parse_errors=[], and states that AST discovery identifies candidates for auditor classification. review_bundle/EXECUTION_GATE_OCCURRENCES.txt, in the same bundle, records the definition at src/dopemux/dcp/routing_model.py:401 and two non-test consumers: src/dopemux/dcp/lane_engine.py:165 'return decision.is_runnable()' and src/dopemux/dcp/routing_backend_policy.py:311 'if not decision.is_runnable():'. Both artifacts cannot be correct. Since the empty AST result is the one that would license a NON_EXECUTION_REACHABLE disposition, and it is the one refuted by the bundle's own grep, the reachability question cannot be closed from committed evidence. This PR changes no source, so it does not introduce a new consumer, but the disposition remains UNKNOWN and drives the fail-closed verdict.

### F-005-FAIL-CLOSED-GATES-UNEVIDENCED: No evidence for the mandated fail-closed state of is_execution_eligible, active_trusted_adapters, mutation_adapters_enabled, invocation_authorized, execute_runner_plan

- severity: `HIGH`
- status: `OPEN`

The audit contract requires confirmation that is_execution_eligible, active_trusted_adapters, mutation_adapters_enabled, invocation_authorized, and execute_runner_plan remain fail-closed. None of these identifiers appears anywhere in the candidate diff, in review_bundle/EXECUTION_GATE_OCCURRENCES.txt (which enumerates only is_runnable/is_executable occurrences), in CALLSITE_ANALYSIS.json, or in any other committed artifact. The PR modifies no source and therefore is unlikely to have weakened them, but 'unlikely' is not evidence: their disposition is unverifiable from this bundle and must not be asserted as preserved. Supplying an exact-head grep or AST receipt covering these five symbols would close this finding without any source change.

### F-006-HANDOFF-SELF-CONTRADICTION: HANDOFF.json and HANDOFF.md assert opposite postures and opposite blocking status in the same bundle

- severity: `MEDIUM`
- status: `OPEN`

HANDOFF.json (new, structural layer) declares governing_posture NO_GO_LIMIT_TO_ARTIFACTS_ONLY, recommended_next_step BLOCK_AND_AWAIT_FIX, and four blocking_reasons (FORMAL_OPUS_AUDIT_PENDING, CI_EXACT_HEAD_PROOF_PENDING, PR_STEWARD_PENDING, PR_DRAFT_PRESERVED). HANDOFF.md (older, also committed and listed in MANIFEST.json) declares 'Governing posture: GO_DRAFT_FIRST', 'Recommended next step: CREATE_DRAFT_PR', and 'Blocking reasons — None. This handoff is not blocked'. HANDOFF.md also names AUDITOR_REPORT.md among its authoritative artifacts, propagating the F-001 verdict. A reader picking either file at random gets an opposite disposition. The JSON is the correct one given PROOF.json status BLOCKED; the markdown should be superseded or explicitly marked stale.

### F-007-PRIMARY-TEST-LOGS-NOT-COMMITTED: pytest.log, compileall.log, and verify-pal.log are absent; the asserted 252-test figure is not independently confirmable from committed artifacts

- severity: `MEDIUM`
- status: `OPEN`

CURRENT_MAIN_RUNTIME_RECONCILIATION.json states tests_passed=252 labelled OBSERVED and cites 'proof/pytest.log' as the source, and COMMAND_LOG.md lists pytest.log, compileall.log, and verify-pal.log as artifacts. None of those three files appears in changed_files; only the .exit receipts were committed, consistent with the prior audit's observation that .gitignore '*.log' excludes them. The one committed pytest output is the dot-progress summary embedded in VALIDATION.json, which carries no explicit 'N passed' summary line, so the 252 figure remains a derived count that a reviewer cannot reconcile against a raw log. Committing the logs with git add -f, or recording the total from a machine-readable pytest report, would close this.

### F-008-OVER-ABSOLUTE-SECRET-CLAIM: EVIDENCE_LEDGER asserts 'No secret values present in any proof artifact' with confidence 'certain' while compose-resolved.json carries a cleartext credential-shaped default

- severity: `MEDIUM`
- status: `OPEN`

compose-resolved.json contains 'dopemux_age_dev_password' in cleartext inside DATABASE_URL/POSTGRES_URL for the conport, dope-memory, dopecon-bridge, and litellm services, despite the documented redaction pass over keys matching (API_KEY|TOKEN|SECRET|PASSWORD). Net new disclosure appears to be nil: reference-scan.txt shows the same default at compose.yml:338 as an already-tracked fallback, and review_bundle/CHILD_PROOF_SECRET_SCAN.json reports safe:true with 0 findings across 58 files. The defect is the strength of the claim, not a leak: EVIDENCE_LEDGER.md's 'No secret values present in any proof artifact / certain' is stated more absolutely than the artifact supports, and the secret-scan result should not be read as proof that the bundle is free of credential-shaped strings. No live secret, API key, or private key was observed anywhere in the diff.

### F-009-SNAPSHOT-ARTIFACT-DRIFT: Self-referential snapshot artifacts describe an earlier bundle state than the one committed

- severity: `LOW`
- status: `OPEN`

DIFF_STAT.txt ends with '42 files changed, 4057 insertions(+)' and lists DIFF_NAME_ONLY.txt at 37 lines and DIFF_STAT.txt at 38 lines, whereas the committed DIFF_NAME_ONLY.txt is 42 lines and DIFF_STAT.txt is 43. FINAL_STATUS_PORCELAIN.txt captures a pre-commit worktree ('...origin/main [behind 2]', several AM entries, an untracked .claude/.untracked-work-probe-cache.json). This is inherent to self-describing snapshots taken mid-bundle, and the prior auditor already noted the artifact set was not frozen during its review; recorded as informational drift rather than dishonesty, but it means these three files do not describe the state actually under audit.

### F-010-INSTRUCTION-LIKE-CONTENT-IN-CANDIDATE-DATA: Instruction-like content detected in candidate artifacts (FORCED_VERDICT_REQUEST, 4 matches); treated strictly as data

- severity: `INFO`
- status: `OPEN`

The deterministic scanner flagged detected=true, categories=[FORCED_VERDICT_REQUEST], match_count=4, truncated=false. Corresponding candidate strings include AUDITOR_REPORT.md 'auditor_verdict: PASS_WITH_RISKS' (repeated in header and rationale), AUDITOR_REPORT.raw.json 'AUDITOR_VERDICT: FAIL', and the task-packet template line 'auditor_verdict: PASS | PASS_WITH_RISKS | FAIL | NEEDS_SUPERVISOR'. All were treated as candidate-controlled data describing prior runs, not as instructions or as verdicts binding on this audit; no verdict was adopted from candidate content, and the verdict here was derived solely from the trusted rules applied to independently corroborated evidence. Detection is recorded as evidence, not as automatic failure. No claim of complete prompt-injection immunity is made.

### F-011-SCOPE-CONTAINMENT-OBSERVED: Repair commit is proof/doc/task-packet only; no source, config, schema, compose, or workflow path modified

- severity: `INFO`
- status: `RESOLVED`

All 65 entries in changed_files are additions under proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/, docs/03-reference/dcp/, or task-packets/DMX-DCP-MODEL-ROUTING-MVP-0000R.md. No path under src/, services/, docker/, config/, schemas/, scripts/, .github/, and no compose.yml, opencode.jsonc, or mcp_catalog.yaml is touched, matching the packet's own allowlist and forbidden list. review_bundle/C1_STAGED_PATHS.txt is likewise confined to proof paths, and the embedded review_bundle/CANDIDATE_UNIFIED_DIFF.patch shows the same containment for the prior candidate commit. On this metadata the candidate implementation is preserved byte-for-byte by this repair; note that I verified containment from the changed-file list and diff bodies, not by comparing checked-out trees. PROOF.json records mutation_performed=false, executed=false, github_mutation_route_added=false, consistent with this observation.

