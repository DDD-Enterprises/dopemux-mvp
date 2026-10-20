# AUDITOR REPORT — PR #1456 L2 embedded audit (TP-DMX-PR1456-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.4.3, `gemini-4-argon-high` (operator-approved fallback; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands --output-format stream-json`, single shot, sealed run directory
- **Implementer**: Claude Code (Anthropic Claude) subagents under the MACRO-DMX-MCP-LIFECYCLE-REPAIR-001 supervisor — different runner and model family
- **Audited head**: `e58d322f1ecc8f97c0cdc61b7a57d9c1ef7bb0f3` · **Base**: `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (main) · **PR**: #1456 (draft)
- **Verdict**: **PASS** — findings: 0, risks: 3
- **Containment**: step types observed {'user_input': 1, 'agent_response': 262} (no tool steps); conversation `7a5db702-53fe-47a0-a576-e46ac1cf5c28`; duration 63.270001 s; usage {"input_tokens": 26268, "output_tokens": 5158, "thinking_tokens": 3518, "cache_read_tokens": 0, "total_tokens": 31426}; raw output sha256 `b797c0f7e2809d5a7c305600da7ff15a0094b00a46e23d129fd9341a94b8eddf`; prompt sha256 `5a4d1958f39c903f687f009272e76b66ae91d1903e699ae7aca535384bf85b34`
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json`; prompt `review_bundle/AUDIT_INPUT.md`; parsed verdict `review_bundle/AUDITOR_VERDICT.json`; CI evidence `review_bundle/CI_EVIDENCE.json`

## Fallback approval

Operator chat line (2026-10-20): "Run the final independent audit of PR #1456 with AGY model gemini-4-argon-high (same operator-approved fallback as PRs 1439 and 1440)." — gemini-3.1-pro-high is absent from `agy models` 1.4.3; same fallback the operator approved for PRs 1439 and 1440 on 2026-10-19.

## Findings

- none

## Risks (auditor-listed, all low)

- **RISK-01** (low) `src/dopemux/mcp/runtime_registry.py:206-258`: RuntimeRegistry.reconcile_stale_running(--apply) rewrites instances.json via save() without a cross-process file lock, so concurrent execution alongside dopemux mcp start/stop/restart/up/down or another reconcile could lose updates. This limitation is explicitly documented in the CLI help, docstring, and troubleshooting docs.
- **RISK-02** (low) `src/dopemux/mcp/runtime_registry.py:191-204`: RuntimeRegistry.find_stale_running() only marks a running instance stale when none of its recorded container_names are present in docker ps (not any(name in running for name in names)). If an instance ever spans multiple containers and experiences a partial container exit, it will remain marked running.
- **RISK-03** (low) `src/dopemux/commands/mcp_commands.py:1370-1391`: CLI unit tests cover compose environment injection for up, down, logs, start-all, and status --legacy-compose, but do not directly exercise mcp_ensure_cmd compose environment forwarding via _run_checked.

## Auditor rationale (verbatim)

Audited PR #1456 for DDD-Enterprises/dopemux-mvp at head SHA e58d322f1ecc8f97c0cdc61b7a57d9c1ef7bb0f3 against base SHA 95e95bee88cae5e6c95e6e34f7c28bb423ad9496 across all 9 changed files. (1) In src/dopemux/mcp/docker_runtime.py, env_with_compose_interpolation() safely derives HOST_CODE_PARENT_DIR and HOST_PROJECT_RELATIVE_PATH from product_root() only when unset/blank and when host_path_defaults=True, preserving operator overrides and failing closed when product_root() raises FileNotFoundError or when host_path_defaults=False is passed by callers that may start dope-context (mcp_up_cmd with dope-context, mcp_start_all_cmd, and mcp_ensure_cmd with dope-context). (2) In src/dopemux/mcp/runtime_registry.py and src/dopemux/commands/mcp_commands.py, dopemux mcp registry reconcile implements read-only stale detection (find_stale_running) and backup-first state reconciliation (reconcile_stale_running) that never deletes entries or touches containers, requires exactly one of --dry-run or --apply, and fails closed when the registry has parse_status == ERROR or Docker inspection is unavailable. (3) Architecture drift gate tests/arch/test_compose_required_vars.py and unit tests in tests/unit/ thoroughly verify the new behavior and fail-closed edge cases. Deterministic scan reported no instruction-like content (detected=false, match_count=0), confirmed by manual diff review.

## Auditor return (verbatim JSON)

```json
{
  "status": "ok",
  "verdict": "PASS",
  "findings": [],
  "risks": [
    {
      "id": "RISK-01",
      "severity": "low",
      "path": "src/dopemux/mcp/runtime_registry.py",
      "summary": "RuntimeRegistry.reconcile_stale_running(--apply) rewrites instances.json via save() without a cross-process file lock, so concurrent execution alongside dopemux mcp start/stop/restart/up/down or another reconcile could lose updates. This limitation is explicitly documented in the CLI help, docstring, and troubleshooting docs.",
      "evidence_ref": "src/dopemux/mcp/runtime_registry.py:206-258"
    },
    {
      "id": "RISK-02",
      "severity": "low",
      "path": "src/dopemux/mcp/runtime_registry.py",
      "summary": "RuntimeRegistry.find_stale_running() only marks a running instance stale when none of its recorded container_names are present in docker ps (not any(name in running for name in names)). If an instance ever spans multiple containers and experiences a partial container exit, it will remain marked running.",
      "evidence_ref": "src/dopemux/mcp/runtime_registry.py:191-204"
    },
    {
      "id": "RISK-03",
      "severity": "low",
      "path": "tests/unit/test_mcp_commands_lifecycle.py",
      "summary": "CLI unit tests cover compose environment injection for up, down, logs, start-all, and status --legacy-compose, but do not directly exercise mcp_ensure_cmd compose environment forwarding via _run_checked.",
      "evidence_ref": "src/dopemux/commands/mcp_commands.py:1370-1391"
    }
  ],
  "rationale": "Audited PR #1456 for DDD-Enterprises/dopemux-mvp at head SHA e58d322f1ecc8f97c0cdc61b7a57d9c1ef7bb0f3 against base SHA 95e95bee88cae5e6c95e6e34f7c28bb423ad9496 across all 9 changed files. (1) In src/dopemux/mcp/docker_runtime.py, env_with_compose_interpolation() safely derives HOST_CODE_PARENT_DIR and HOST_PROJECT_RELATIVE_PATH from product_root() only when unset/blank and when host_path_defaults=True, preserving operator overrides and failing closed when product_root() raises FileNotFoundError or when host_path_defaults=False is passed by callers that may start dope-context (mcp_up_cmd with dope-context, mcp_start_all_cmd, and mcp_ensure_cmd with dope-context). (2) In src/dopemux/mcp/runtime_registry.py and src/dopemux/commands/mcp_commands.py, dopemux mcp registry reconcile implements read-only stale detection (find_stale_running) and backup-first state reconciliation (reconcile_stale_running) that never deletes entries or touches containers, requires exactly one of --dry-run or --apply, and fails closed when the registry has parse_status == ERROR or Docker inspection is unavailable. (3) Architecture drift gate tests/arch/test_compose_required_vars.py and unit tests in tests/unit/ thoroughly verify the new behavior and fail-closed edge cases. Deterministic scan reported no instruction-like content (detected=false, match_count=0), confirmed by manual diff review.",
  "inspected_paths": [
    ".env.example",
    "docs/02-how-to/mcp-transport-and-port-bugs.md",
    "src/dopemux/commands/mcp_commands.py",
    "src/dopemux/mcp/docker_runtime.py",
    "src/dopemux/mcp/runtime_registry.py",
    "tests/arch/test_compose_required_vars.py",
    "tests/unit/test_mcp_commands_lifecycle.py",
    "tests/unit/test_mcp_runtime_launcher.py",
    "tests/unit/test_mcp_runtime_registry.py"
  ],
  "evidence_refs": [
    "src/dopemux/mcp/docker_runtime.py:36-74 (COMPOSE_HOST_PATH_VARS and env_with_compose_interpolation host_path_defaults logic)",
    "src/dopemux/commands/mcp_commands.py:285-291 (mcp_up_cmd conditional host_path_defaults='dope-context' not in svc_list)",
    "src/dopemux/commands/mcp_commands.py:328-337 (mcp_down_cmd env_with_compose_interpolation injection)",
    "src/dopemux/commands/mcp_commands.py:360-395 (mcp_status_cmd legacy and fallback ps env injection)",
    "src/dopemux/commands/mcp_commands.py:409-418 (mcp_logs_cmd env injection)",
    "src/dopemux/commands/mcp_commands.py:445-468 (mcp_start_all_cmd host_path_defaults=False fail-closed preservation)",
    "src/dopemux/commands/mcp_commands.py:1257-1265,1372-1391 (_run_checked env parameter and mcp_ensure_cmd conditional host_path_defaults)",
    "src/dopemux/commands/mcp_commands.py:2098-2150 (mcp_registry_reconcile_cmd CLI flags and fail-closed checks)",
    "src/dopemux/mcp/runtime_registry.py:191-258 (RuntimeRegistry.find_stale_running and reconcile_stale_running)",
    "tests/arch/test_compose_required_vars.py:19-45 (drift gate for compose.yml required variables)",
    "tests/unit/test_mcp_runtime_launcher.py:69-132 (unit tests for env_with_compose_interpolation)",
    "tests/unit/test_mcp_runtime_registry.py:193-314 (unit tests for find_stale_running and reconcile_stale_running)",
    "tests/unit/test_mcp_commands_lifecycle.py:280-521 (CLI lifecycle env propagation and registry reconcile unit tests)",
    ".env.example:58 (documentation comment on derived host path variables)",
    "docs/02-how-to/mcp-transport-and-port-bugs.md:185-318 (Bug 4 and Bug 5 root cause, fix, and verification documentation)"
  ],
  "validation_status": "NOT_RUN"
}
```

## Acceptance

NOT_GRANTED by this report. Acceptance and merge belong to the operator; this bundle records the executed independent audit for the trusted embedded-audit gate.
