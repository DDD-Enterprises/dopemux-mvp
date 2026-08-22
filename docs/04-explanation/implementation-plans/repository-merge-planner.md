---
id: repository-merge-planner-implementation-plan
title: "Repository Merge Planner Implementation Plan"
type: explanation
status: draft
owner: "@hu3mann"
author: "@codex"
date: "2026-08-22"
last_review: "2026-08-22"
next_review: "2026-11-20"
prelude: "Five dependency-ordered PCP implementation packets."
tags: [implementation-plan, pcp, control-tower, repository-planner]
---

# Repository Merge Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or `superpowers:executing-plans`
> to implement the active packet task-by-task. Track steps with checkboxes.

**Goal:** Deliver a read-only interactive merge planner across Dopemux, dNh
CRM, and AdOps without creating a new authority plane.

**Architecture:** PCP Core remains generic. Dopemux-owned additive adapters
consume AdOps authority surfaces and existing dNh RDCP artifacts, then build a
deterministic portfolio projection for a loopback service and React UI. Live
GitHub refresh and conversation proposals are isolated in later L3 packets.

**Tech Stack:** Python 3, JSON Schema 2020-12, pytest, FastAPI-compatible
loopback patterns, TypeScript, React, MUI, Vite, Vitest.

**Spec:** `docs/91-rfc/repository-merge-planner.md`

## Global constraints

- Planner records always use `authority=NONE` and `surface_class=PROJECTION`.
- No repository, GitHub, Task Orchestrator, CRM, or conversation-source writes.
- Preserve PCP Core generic behavior and the DCP nine-family facade.
- Missing, stale, malformed, or conflicting evidence fails closed.
- No raw transcript persistence by default.
- No OpenRouter, OpenCode, custom proxy, or unapproved external spend.
- One frozen-head independent audit for each L2/L3 packet; no model-call rituals.

## File and packet decomposition

| Packet | Working software produced | Dependency |
|---|---|---|
| Foundation 001 | fixture-backed portfolio model, deterministic planner, first UI | design PR merged |
| AdOps 002 | source-backed AdOps PROJECT adapter and conformance fixtures | 001 accepted |
| dNh RDCP 003 | source-backed dNh RDCP bridge and conformance fixtures | 001 accepted |
| GitHub 004 | loopback read service and allowlisted live refresh | 002 + 003 accepted |
| Conversations 005 | allowlisted proposal intake and reconciliation UI | 004 accepted |

Each packet contains exact files, public interfaces, failing tests, commands,
proof requirements, and stop conditions. Packets 2 and 3 write only Dopemux;
the source repositories are read-only evidence providers.

## Execution order

- [ ] Merge or otherwise accept the design contract on PR #1247.
- [ ] Activate and execute `TP-DMX-PCP-PLANNER-FOUNDATION-001`.
- [ ] Freeze its portfolio/source contracts and record the accepted head.
- [ ] Execute `TP-DMX-PCP-ADOPS-EXTENSION-002`.
- [ ] Execute `TP-DMX-PCP-DNH-RDCP-BRIDGE-003`.
- [ ] Reconcile both adapters against the same foundation contract.
- [ ] Execute `TP-DMX-PCP-GITHUB-REFRESH-004`.
- [ ] Execute `TP-DMX-PCP-CONVERSATION-DECISIONS-005`.
- [ ] Run end-to-end fixture and read-only live validation.
- [ ] Leave merge, acceptance, and activation to Control Tower/human authority.

## Cross-packet interfaces

Foundation 001 produces:

```python
def load_source_snapshot(payload: Mapping[str, object]) -> SourceSnapshot: ...
def build_portfolio(sources: Sequence[SourceSnapshot]) -> PortfolioProjection: ...
def classify_conflicts(claims: Sequence[Claim]) -> tuple[Conflict, ...]: ...
def plan_merge_order(portfolio: PortfolioProjection) -> tuple[Recommendation, ...]: ...
def canonical_portfolio_bytes(portfolio: PortfolioProjection) -> bytes: ...
```

Extension packets produce:

```python
class ProjectExtensionAdapter(Protocol):
    extension_id: str
    def matches(self, generic_export: Mapping[str, object]) -> bool: ...
    def enrich(self, generic_export: Mapping[str, object], source_root: Path) -> SourceSnapshot: ...
```

GitHub 004 produces:

```python
class GitHubReadTransport(Protocol):
    def request(self, method: Literal["GET", "HEAD"], url: str,
                *, headers: Mapping[str, str]) -> ReadResponse: ...

async def refresh_portfolio(project_ids: Sequence[str]) -> RefreshResult: ...
```

Conversation 005 produces:

```python
def propose_decision(source: DecisionSource, normalized_text: str,
                     target: DecisionTarget) -> DecisionProposal: ...
def reconcile_proposal(proposal: DecisionProposal,
                       portfolio: PortfolioProjection) -> tuple[Conflict, ...]: ...
```

Later packets must consume these interfaces exactly or amend the active packet
before implementation. They may not silently fork the contract.

## Validation ladder

Every packet runs its targeted Python and UI tests first, then:

```bash
python scripts/docs_validator.py
python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text
git diff --check
```

L2/L3 packets then freeze the content head and undergo one independent audit
bound to that exact SHA. Proof-only successors use deterministic validation;
unchanged content is not re-audited.
