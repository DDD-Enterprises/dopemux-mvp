---
id: gpt55-mcp-architecture-bundle-00-evidence-triage
title: GPT55 MCP Architecture Bundle 00 Evidence Triage
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 0 input bundle for evidence triage and missing input discovery.
---
# Bundle 00: Evidence Triage

## Purpose

Give GPT-5.5 enough input to classify evidence quality and ask for missing inputs before any architecture design starts.

## Required Uploads

1. `prompt-00-evidence-triage.md`
2. `readme.md`
3. `research.md`
4. `branch-work-audit.md`
5. `transcript-digest.md`
6. `source-manifest.md`
7. `pre-run-evidence.md`
8. `docs/06-research/2026-07-04-dopemux-service-investigation/research.md`
9. Recent synthesis attachment `252931e6-3387-4b90-a8c0-47fa3f942310/pasted-text.txt`
10. Recent synthesis attachment `ad6a0ce8-671c-4ddc-9dda-a6c7d93ed2f8/pasted-text.txt`

## Optional Uploads

- `docs/06-research/2026-07-04-dopemux-service-investigation/service-gap-matrix.md`
- `AGENTS.md`
- `SERVICE_CATALOG.md`

## Data To Collect Before Running

```bash
git rev-parse HEAD
git status --short --branch
git log --oneline --decorate -20
git branch --contains claude/trusting-engelbart-d2fbfe --all
git merge-base origin/main claude/trusting-engelbart-d2fbfe
git merge-base origin/main claude/mcp-fleet-audit-complete
gh pr view 1002 --json number,state,mergedAt,headRefOid,baseRefName,mergeable,statusCheckRollup
```

## Redaction Rules

- Do not upload raw `.env` files.
- Do not upload raw `docker compose config` output.
- Do not upload raw Claude transcript JSONL.

## Expected GPT-5.5 Phase Output

- evidence classification table
- missing-input request list
- authority conflicts
- PR #1002 reconciliation gate
- stale/advisory input list
- decision whether Phase 1 can proceed
