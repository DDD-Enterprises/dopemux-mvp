# Evidence Index

- RUN_ID: `20260612T003401Z`
- Branch: `codex/gpt55-recon-chain`
- Head: `ac3a26f746e472feb8a31f1b634d8c0432e08db6`
- Status: `EVIDENCE_READY_WITH_GAPS`

## Pytest Network Stop Condition

Status: BLOCKED_RUNTIME_UNSAFE_NETWORK

During the repo-wide pytest collection/run, a pytest subprocess was observed holding an external HTTPS connection.

Action taken:
- pytest subprocess terminated
- partial pytest log preserved
- no retry attempted
- no test result marked green
- Pack 2 classified as evidence-ready-with-gaps / blocked for runtime network uncertainty

Reason:
This packet is evidence-only. Unexpected live external network activity during a repo-wide test suite crosses into unsafe runtime uncertainty.

Required follow-up:
- identify test/process responsible
- rerun only under a network-deny harness or targeted offline-safe tests
- do not claim repo-wide tests passed

## Files

- `ATTACH_TO_GPT55_PRO.md`
- `COMMAND_LEDGER.md`
- `EVIDENCE_INDEX.md`
- `MISSING_INPUTS_FOR_GPT55_PRO.md`
- `commands/dopemux_help.txt`
- `commands/dopetask_help.txt`
- `commands/final_file_list.txt`
- `commands/final_git_status.txt`
- `commands/find_agent_workflow_dirs.txt`
- `commands/find_files_max4.txt`
- `commands/find_surfaces.txt`
- `commands/git_branch.txt`
- `commands/git_diff_name_only.txt`
- `commands/git_diff_stat.txt`
- `commands/git_head.txt`
- `commands/git_remotes.txt`
- `commands/git_root.txt`
- `commands/git_status_short.txt`
- `commands/git_worktree_list.txt`
- `commands/mcp_inventory_raw.txt`
- `commands/proof_contracts_raw.txt`
- `commands/pwd.txt`
- `commands/routing_model_raw.txt`
- `commands/service_compose_raw.txt`
- `commands/slash_agent_workflow_raw.txt`
- `inventory/DOPEMUX_CLI_SURFACES.md`
- `inventory/DOPETASK_RUNTIME_SURFACES.md`
- `inventory/FILE_SURFACE_INVENTORY.md`
- `inventory/MCP_SERVER_TOOL_INVENTORY.md`
- `inventory/PROOF_PACKET_CONTRACTS.md`
- `inventory/REPO_STATE.md`
- `inventory/ROUTING_MODEL_CONFIG_SURFACES.md`
- `inventory/SERVICE_COMPOSE_PORT_MAP.md`
- `inventory/SLASH_AGENT_WORKFLOW_INVENTORY.md`
- `review/DRIFT_CONTRADICTION_LEDGER.md`
- `review/PACK2_BLOCKER_REPORT.md`
- `review/SECRET_REDACTION_REPORT.md`
- `snippets/RUNTIME_ENTRYPOINT_SNIPPETS.md`
- `tests/TEST_AND_CI_EVIDENCE.md`
