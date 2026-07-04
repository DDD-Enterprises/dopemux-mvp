---
id: gpt55-mcp-architecture-investigation-research
title: GPT55 MCP Architecture Investigation Research
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Research brief for GPT-5.5 MCP architecture investigation.
---
# Research: GPT-5.5 MCP Architecture Investigation

## Summary

This packet packages two Claude workstreams for a GPT-5.5 Pro architecture pass:

- `claude/trusting-engelbart-d2fbfe`: original MCP fleet canonical audit/design branch and transcript series.
- `claude/mcp-fleet-audit-complete`: later follow-on branch with additional fixes, Exa retirement, PAL ensure hardening, PM source event promotion, personality gates, dead-surface quarantine clarification, and forgotten-feature archaeology.

The packet intentionally does not copy raw Claude transcripts. It provides digest metadata, branch evidence, source pointers, and a prompt that tells GPT-5.5 Pro to separate observed repo truth from transcript-derived advice.

## Current Baseline

- OBSERVED: `origin/main` resolves to `8f71ab9aff4802fb15d406fe654c6c601893cc42`, commit message `chore(mcp): quarantine dead fleet surfaces (#1001)`.
- OBSERVED: `claude/trusting-engelbart-d2fbfe` merge-base with `origin/main` is `0805dae06d45745011d4df2a8946ba1fbda34bb3`, so the branch's mainline audit/design work is already contained in current main.
- OBSERVED: `claude/mcp-fleet-audit-complete` merge-base with `origin/main` is `8f71ab9aff4802fb15d406fe654c6c601893cc42`, so it is follow-on work on top of current main.
- OBSERVED: the primary checkout remains detached and dirty; this packet was created in an isolated worktree.

## High-Signal Findings To Hand GPT-5.5

### MCP Fleet Architecture

- OBSERVED: the live fleet already moved toward a canonical catalog and generated-output model through `mcp_catalog.yaml`, `src/dopemux/mcp/default_catalog.yaml`, `src/dopemux/mcp/fleet_catalog.py`, and `src/dopemux/commands/mcp_commands.py`.
- OBSERVED: prior Claude audit identified repeated "shadow twin" problems: upstream vs in-repo ConPort, multiple PAL deployments, task-orchestrator Kotlin MCP vs Python service, upstream Serena wrapper vs local Serena implementation, gptr wrapper vs in-repo server, and dope-memory vs working-memory-assistant layout.
- OBSERVED: PR #1001 quarantined dead/decision-required fleet surfaces in generated configs, but later proof notes clarify the proven scope is narrower than the phrase "dead fleet surfaces" can imply.
- INFERRED: GPT-5.5 should design an architecture where one catalog is canonical, generated artifacts are deterministic projections, and every noncanonical/dead surface is explicitly archived or isolated.

### Memory And Context Planes

- OBSERVED: AGENTS.md states the Memory Trinity boundary: ConPort owns structured decisions/progress/context, dope-memory owns chronicle receipts, and dope-context owns code/docs retrieval.
- OBSERVED: the Claude addendum flags dormant features in ConPort graph code, dope-memory capture, Serena ADHD modules, and ADHD/task-orchestrator predictive risk code.
- INFERRED: the architecture should not simply wire all dormant features. It should first assign authority per plane, then promote only features whose canonical writer is clear.

### Lifecycle And Health

- OBSERVED: `claude/mcp-fleet-audit-complete` includes follow-on work for `dopemux mcp ensure`, PAL container recreation, compose-up timeout budgets, and consumed `pal-stdio` startup.
- OBSERVED: branch diffs include deletion of Exa source/registry/catalog entries and creation of ADR-223 to retire the Exa MCP server.
- INFERRED: GPT-5.5 should decide whether Exa retirement is now the preferred final design or whether the earlier target design's "wire-or-retire" decision needs reopening.

### ADHD, Serena, And Dormant Intelligence

- OBSERVED: the prior all-service audit found Serena enhanced F001 detection code exists but is not registered/callable through MCP.
- OBSERVED: Claude archaeology claims dormant Serena modules include complexity banding, focus manager, fatigue detection, untracked-work detector, adaptive learning, and cognitive-load orchestration.
- INFERRED: GPT-5.5 should propose a unified intelligence-plane design that avoids three independent complexity scoring systems across Serena, dope-context, and ADHD/task-orchestrator code.

### DCP And External Projection

- OBSERVED: the prior audit and branch work identify the DCP read-only facade as the strongest fail-closed pattern: read-only tools, untrusted-by-default envelopes, denylist/redaction, and proof/freshness gates.
- INFERRED: GPT-5.5 should generalize DCP facade envelope/provenance patterns across MCP servers instead of letting bridge/proxy layers appear authoritative.

## Key Risks

- HIGH: Transcript claims can be stale or overbroad. Use branch diffs and current source as proof.
- HIGH: Wiring dormant services without authority decisions will recreate the shadow-twin syndrome.
- HIGH: Generated config and global/client config drift can reintroduce retired surfaces if codegen is not canonical.
- MEDIUM: Some follow-on branch work may supersede the previous design, especially Exa retirement and PAL ensure behavior.
- MEDIUM: `claude/mcp-fleet-audit-complete` contains runtime-code changes and tests, so a pure architecture design should not assume it has merged until checked.
- MEDIUM: Raw transcript JSONL may contain private operational context; use digests and paths, not bulk transcript dumps.

## Candidate Verification Commands

```bash
git log --oneline origin/main..claude/mcp-fleet-audit-complete
git diff --name-status origin/main..claude/mcp-fleet-audit-complete
git merge-base origin/main claude/trusting-engelbart-d2fbfe
git merge-base origin/main claude/mcp-fleet-audit-complete
python -m json.tool task-packets/TP-DMX-GPT55-MCP-ARCHITECTURE-INVESTIGATION-20260704.json >/dev/null
git diff --check
```
