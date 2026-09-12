# Independent Audit

Status: PASS_WITH_RISKS
Audited head: b0c34632fc49d4ef4e8d84c242f65cc71195fb1d
Observed primary runtime model: grok-4.5-build

This report is a deterministic rendering of the preserved raw auditor response.
Schema adaptation only: BLOCKER maps to BLOCKING; finding IDs supply required titles; paths are retained in bodies.

## Findings

### F-CLOSURE-001-REPO-BINDING (MEDIUM, RESOLVED)
Path: .control-tower/bin/ct
Closure claim for JSON repo_binding is met in the frozen head. When require_identity_match is true, validate_packet_binding requires non-empty project_id, repo_marker, and origin_hint; restricts markers to the supported canonical set; rejects unsafe/relative-escape markers, symlinks, and escaping identity configs; compares marker project identity; and compares normalized exact origin with fail-closed rejection of credentialed, query, fragment, and malformed URLs. Focused tests cover happy path, origin mismatch, null binding, taskx marker, boolean-type rejection, unsafe markers, nested foreign fixtures, symlink markers, and escaping identity config.

### F-CLOSURE-002-MARKDOWN-IDENTITY (LOW, RESOLVED)
Path: .control-tower/bin/ct
Prior CORR-01 (first-heading bind) is not present in this head. packet_identity() for Markdown ignores fenced regions with nested-fence handling, collects every out-of-fence heading that yields a packet-ID candidate, and fails closed unless exactly one candidate remains. Tests cover JSON id, Task Packet colon/program/em-dash/backtick forms, nested fences, ambiguity, and invalid encoding. This closes the Markdown identity defect claimed by CLOSURE-003.

### F-CLOSURE-003-DIFF-PACKAGING (MEDIUM, RESOLVED)
Path: .control-tower/bin/ct
Packaging now separates COMMITTED_DIFF.patch (merge-base..head) from WORKTREE_DIFF.patch (dirty vs HEAD), captures GIT_STATUS separately, fails closed when required Git evidence is missing or git_capture fails, and documents that Git diffs do not contain untracked-file contents. README and tests assert the committed/dirty split and fsmonitor-disabled capture. This matches the CLOSURE-003 committed-diff packaging invariant.

### F-CLOSURE-004-ROUTING-SCOPE (MEDIUM, RESOLVED)
Path: .claude/llm.md
Supervised vs ordinary model-routing ambiguity is closed in instruction surfaces. llm.md and llms.md require validated packet routing for supervised work, preserve ordinary user/repository authority without inventing a packet, and state that attention presentation does not grant execution authority. AGENTS.md Control Tower Packet Workflow and related CONTROL_TOWER_ENTRY blocks repeat supervised-only scope. Template guidance in README states ROUTING_DECISION.template.json is schema-shape only with UNKNOWN placeholders, not availability or authority evidence.

### F-REPAIR-SCHEMA-ENFORCEMENT (LOW, RESOLVED)
Path: .control-tower/bin/ct
Shipped route_decision.schema.json and return_packet.schema.json are loaded and applied through _validate_schema for route and return-metadata paths. Blank required strings, L2/L3 audit.required=true, and return-pack non-empty reason/decision-needed are enforced. Unit coverage includes schema oracle cross-check against jsonschema for valid and invalid cases.

### F-REPAIR-VERIFY-ZIP (LOW, RESOLVED)
Path: .control-tower/bin/ct
verify-zip enforces single root, rejects unsafe/symlink members, and cross-checks SHA256SUMS.txt, FILE_INVENTORY.json path/sha256/bytes, and SECRET_SCAN_REPORT.json PASS/empty hits against member bytes. Tests cover tamper, duplicate inventory, and malformed inventory types.

### F-REPAIR-INVENTORY-EGRESS (LOW, RESOLVED)
Path: .control-tower/bin/ct
runner-inventory probes provider models only with explicit --probe-models; default path does not call agy models. tool_info marks failed version probes UNKNOWN rather than PROVEN.

### F-GOV-CODEQL-DISPOSITION (MEDIUM, OPEN)
Path: .control-tower/bin/ct
REPAIR-002 CodeQL alert disposition remains not independently confirmable from the supplied content-only materials: original alert text/locations are not in this audit bundle. Reviewed scan_files behavior is consistent with fail-closed unscannable handling and constant-label sinks that omit matched secret bytes, but consistency is not proof of the specific alert IDs. This does not by itself show a live credential leak in the diff.

### F-TEMPLATE-VALIDATE-SHAPE-ONLY (LOW, ACCEPTED_RISK)
Path: .control-tower/templates/ROUTING_DECISION.template.json
ct validate-route accepts the placeholder template because placeholders are non-blank strings that satisfy schema/shape checks. README and AGENTS.md already state template validation proves shape only and does not prove authority, availability, independence, CI, merge, or activation. Residual misuse risk remains if an operator treats template PASS as a real routing decision.

### F-SCHEMA-SUBSET-COUPLING (LOW, ACCEPTED_RISK)
Path: .control-tower/bin/ct
The hand-rolled JSON-Schema subset rejects unsupported keywords. Current shipped schemas stay within the supported set, so this is not a present functional defect; future schema edits using unsupported keywords would break validation until the validator is updated in lockstep.

### F-AUTHORITY-PRESERVATION (INFO, RESOLVED)
Path: AGENTS.md
Instruction integrations are additive inside CONTROL_TOWER_* markers. Kit text preserves repository governance precedence, supervised-only extra workflow, operator-only gates, and that packaging/kit reports do not grant acceptance, merge, upload, or activation authority. No operator-gate bypass, credential exposure, or protection/activation mutation appears in the auditable changed sources.

### F-INCREMENTAL-ROUTE-AMENDMENT (INFO, RESOLVED)
Path: task-packets/TP-DMX-CONTROL-TOWER-SUPERVISOR-KIT-CLOSURE-003.json
Incremental prior_head..head changes only CLOSURE-003 invariants to the user-approved Grok final-audit selector (from Claude Sonnet medium). No CLI, test, or native governance source changed in that increment. Full allowlist and incremental allowlist checks report PASS with empty unexpected paths. Packet and supplied route both name grok-4.5 / high effort for the final audit; route audit.independence remains PROPOSED rather than proven.

## Residual Risks
- This is a content-only audit: no tools were run here; focused-test PASS (36), precommit/commit receipts, change-contract PASS, and route/packet validation receipts are implementer-supplied evidence and were cross-checked against source but not re-executed by this auditor.
- CI for exact head b0c34632fc49d4ef4e8d84c242f65cc71195fb1d is explicitly NOT_RUN; historical CI success at b99e0f57 is not current-head acceptance and was not converted into this verdict.
- Route records audit.independence=PROPOSED; actual auditor runtime identity is unavailable pre-invocation and must be established from invocation metadata before treating independence as proven.
- Secret scanning remains heuristic; PASS does not prove an archive contains no sensitive data.
- CodeQL alert disposition for the repair slice remains not independently matchable to alert records from this bundle alone.
- No operator risk acceptance, Steward READY, merge permission, or activation authority is inferred or granted by this verdict.

## Identity Basis
Actual runtime identity is unavailable pre-invocation. Requested auditor selector from route/packet/request metadata: grok-4.5 (high effort, runner grok-cli). Historical prior audit metadata only (not this invocation): model=sonnet, runner=claude-code-cli, effort=medium, head=4b31331b93fae6ffb98d23b4c0cfa1df7f5e55d5.

## Scope Basis
Exact binding base=6a728f74c0311967f83213513308f97613e3f28d head=b0c34632fc49d4ef4e8d84c242f65cc71195fb1d prior_head=d43ee015c94a1daba7bc265131c9b84485468347 worktree_head=b0c34632fc49d4ef4e8d84c242f65cc71195fb1d. Reviewed full auditable sources under changed/* (instruction/cli/tests/other_changed), authority/*, packet/TASK_PACKET.json, route/ROUTE_DECISION.json, allowlist checks, commit objects, finding_fix_map, and supplied focused/precommit/CI receipts. Historical proof/** excluded from substantive content review per binding.
