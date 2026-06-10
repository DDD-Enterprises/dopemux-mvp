# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000G` · DCP · Authority Registry Hardening

════════════════════════════════════════════════════════════

## Objective

Create a machine-readable safety registry for MCP servers, slash commands, workflows, and agents with authority class, side-effect class, proof capture method, and gating before any routing logic depends on them.

**Runner**: Codex
**Audit**: Gemini/AGY
**Mode**: read-only

────────────────────────────────────────────────────────────

## Scope

### IN

* `.mcp.json`
* `mcp-proxy-config*`
* `.claude/commands`
* `src/dopemux/commands`
* `.github/workflows`
* `.github/agents`
* pre-commit hooks
* known forbidden seams

### OUT

* No workflow edits
* No command execution except `--help` or file reads
* No MCP writes
* No agent execution

────────────────────────────────────────────────────────────

## Exact Commands

```bash
set -euo pipefail

find .mcp.json mcp-proxy-config* .claude/commands src/dopemux/commands .github/workflows .github/agents .githooks -maxdepth 4 -type f 2>/dev/null \
  | sort > /tmp/dmx_0000g_authority_surface_files.txt

grep -RInE "write|delete|create|update|merge|approve|label|comment|execute|shell|subprocess|Desktop Commander|ConPort|dope-memory|task-orchestrator" \
  .mcp.json mcp-proxy-config* .claude/commands src/dopemux/commands .github/workflows .github/agents .githooks \
  > /tmp/dmx_0000g_mutation_keyword_hits.txt 2>/dev/null || true
```

────────────────────────────────────────────────────────────

## Required Artifacts

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0000G/
  PROOF.json
  AUDIT.md
  COMMAND_LOG.md
  MCP_AUTHORITY_REGISTRY.json
  SLASH_COMMAND_AUTHORITY_REGISTRY.json
  WORKFLOW_AUTHORITY_REGISTRY.json
  AGENT_AUTHORITY_REGISTRY.json
  FORBIDDEN_SEAMS_LEDGER.md
```

────────────────────────────────────────────────────────────

## Validation Gates

* Every listed surface has one of the required safety classes
* Unknown write-claimed surfaces are not marked safe
* DopeCode label is `DopeCode (legacy: Serena)` until runtime rename is proven
* Agents remain helpers unless runtime proves stronger authority

────────────────────────────────────────────────────────────

## Stop Conditions

* Registry tries to normalize unknowns
* Any bridge/proxy is promoted into authority
* Any workflow mutation is proposed

────────────────────────────────────────────────────────────

## Expected Output

A hardened authority registry that 0001 can use to safely route tasks without trusting unsafe surfaces.
