# DMX-DCP-MODEL-ROUTING-MVP-0000 — MUTATION_RED_LANE_LEDGER.md

## Mutation-Capable Seams (OBSERVED)

### Explicitly Forbidden (DCP Test + AGENTS.md)

| Seam | Path | Mutation Type | Evidence | Status |
|------|------|---------------|----------|--------|
| PR Merge Specialist | src/dopemux_pr_merge_specialist/ | PR merge, review thread resolve, batch_resolve_and_merge | DCP test_16 + AGENTS.md §Hard Blocks | FORBIDDEN |
| Batch Resolve Script | scripts/batch_resolve_and_merge.py | PR merge automation | DCP test_16 + AGENTS.md | FORBIDDEN |
| Gemini Review Workflow | .github/workflows/gemini-review.yml | PR review/comment (currently modified in worktree) | git status + DCP test failure | CONFLICTING (worktree dirty) |

### Write-Claimed MCP Servers

| Seam | Path | Mutation Type | Evidence | Status |
|------|------|---------------|----------|--------|
| ConPort | compose.yml:conport + conport_mcp_stdio.py | Decision append, progress update, knowledge graph write | compose.yml + .mcp.json | UNKNOWN (write contract enforcement) |
| Desktop Commander | registry.yaml | Process spawn, FS operations, terminal commands | registry.yaml | UNKNOWN (terminal mutation) |
| Task Orchestrator | services/task-orchestrator/server.py | Task state transitions, workflow writes | server.py + mcp-proxy-config | UNKNOWN (write authority) |
| Dope-Memory | .mcp.json + dope-memory service | Chronicle append, reflection writes | .mcp.json | FORBIDDEN (hard block: correction/append/reflection writes) |

### Dopetask Mutating Commands (Help Surface Only — Not Executed)

| Seam | Command | Mutation Type | Evidence | Status |
|------|---------|---------------|----------|--------|
| Task Packet Execution | scripts/dopetask run-task | Workspace creation, task execution | --help | NOT RUN (hard block) |
| Task Packet Promotion | scripts/dopetask promote-run | Completion token issuance | --help | NOT RUN (hard block) |
| Task Packet Commit | scripts/dopetask commit-run | Git commit (allowlist-enforced) | --help | NOT RUN (hard block) |
| Task Packet Loop | scripts/dopetask loop | Full lifecycle execution | --help | NOT RUN (hard block) |
| TP Series Exec | scripts/dopetask tp series exec | DAG-aware series execution | --help | NOT RUN (hard block) |
| TP Series Finalize | scripts/dopetask tp series finalize | PR creation for completed series | --help | NOT RUN (hard block) |

### Workflow Mutating Surfaces

| Seam | Path | Mutation Type | Evidence | Status |
|------|------|---------------|----------|--------|
| PR Steward | .github/workflows/pr-steward.yml | PR labels, comments, merge readiness | workflow file | OBSERVED (mutating) |
| CI Status | .github/workflows/ci-complete.yml | Commit status updates | workflow file | OBSERVED (mutating) |
| Gemini Dispatch/Plan/Execute/Review | .github/workflows/gemini-*.yml | PR review, comment, plan execution | workflow files | OBSERVED (mutating) |
| Security Review/Scan | .github/workflows/security-*.yml | Security alerts, PR comments | workflow files | OBSERVED (mutating) |
| Container Publish | .github/workflows/containers.yml | Package/container publish | workflow file | OBSERVED (mutating) |
| Ruff Format | .pre-commit-config.yaml | Auto-format on commit | pre-commit config | OBSERVED (mutating) |

### DCP Schema-Defined Red Lanes

| Seam | Schema | Mutation Class | Evidence | Status |
|------|--------|----------------|----------|--------|
| Mutation Class Taxonomy | schemas/dcp/dcp_mutation_class.schema.json | Mutation classification | schema file | OBSERVED |
| Red Lane Report | schemas/dcp/dcp_red_lane_report.schema.json | Red lane reporting | schema file | OBSERVED |
| Red Lane Taxonomy | schemas/dcp/dcp_red_lane_taxonomy.schema.json | Red lane classification | schema file | OBSERVED |

**Total Red Lanes Catalogued**: 18
**Explicitly Forbidden**: 3 (pr_merge_specialist, batch_resolve_and_merge, dope-memory writes)
**Write-Claimed but UNKNOWN Enforcement**: 4 (conport, desktop-commander, task-orchestrator, dope-memory)
**Mutating Workflows/Hooks**: 6 workflows + 1 pre-commit
**Not Executed (Hard Blocks)**: 6 dopetask commands
