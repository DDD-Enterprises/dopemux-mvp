# Oversized artifacts excluded from git (GitHub >100MB limit)

Branch history was rebuilt on `main` without the blobs below. They remain
available in the operator's local recon worktree backup if needed; use
`COMMAND_LOG_SUMMARY.md`, `EVIDENCE_INDEX.md`, and the tracked inventory
snippets as the repo-bound substitutes.

| Artifact | Approx. size | Substitute in repo |
|----------|--------------|-------------------|
| `proof/TP-DCP-MCP-RO-0001/COMMAND_LOG.md` | 322 MB | `proof/TP-DCP-MCP-RO-0001/COMMAND_LOG_SUMMARY.md` |
| `audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/routing_model_raw.txt` | 333 MB | `inventory/ROUTING_MODEL_CONFIG_SURFACES.md` + `COMMAND_LEDGER.md` |
| `audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/commands/slash_agent_workflow_raw.txt` | 96 MB | `inventory/SLASH_AGENT_WORKFLOW_INVENTORY.md` |
| `audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/review/SECRET_REDACTION_REPORT.md` | 182 MB | `review/PACK2_BLOCKER_REPORT.md` |
| `audit_inputs/multi_model_orchestration_evidence/20260612T003401Z/review/DRIFT_CONTRADICTION_LEDGER.md` | 68 MB | `EVIDENCE_INDEX.md` |
| `audit_inputs/multi_model_orchestration_evidence/20260612T003401Z.zip` | 84 MB | Directory tree under `20260612T003401Z/` |
| `audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt` | 68 MB | `RECON_SUMMARY.md` + `RECON_FINDINGS.json` |

Do not re-add these paths without Git LFS or an external evidence store.