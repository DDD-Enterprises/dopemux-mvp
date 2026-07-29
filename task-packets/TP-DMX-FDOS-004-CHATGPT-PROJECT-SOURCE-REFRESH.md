---
id: TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH
title: Tp Dmx Fdos 004 Chatgpt Project Source Refresh
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
prelude: Tp Dmx Fdos 004 Chatgpt Project Source Refresh (explanation) for dopemux
  documentation and developer workflows.
---
# TP-DMX-FDOS-004 · ChatGPT Project · Authoritative 40-Source Refresh

## 0. Execution Directive

Execute this packet in **Claude Code using Sonnet** as the primary implementer.

This is a repository inspection, source-governance, deterministic assembly, and packaging task. It is not a broad architecture rewrite.

The implementer must perform an independent embedded audit before final proof return.

Preferred embedded auditor route:

1. AGY / Google Antigravity with Sonnet, when available and invocation/model selection are proven
2. Claude Code CLI Sonnet in a separate non-implementer session
3. Claude Code CLI Opus when Sonnet lacks depth or capacity
4. Gemini CLI for broad-context contradiction review

Do not use the implementing session as the formal auditor.

---

## 1. Packet Identity

```yaml
packet_id: TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH
project: dopemux-mvp
repository: DDD-Enterprises/dopemux-mvp
packet_class: governance-and-packaging
risk_class: MEDIUM
parent_packet: TP-DMX-FDOS-003-CHATGPT-PROJECT-UPLOAD-SET-THREADS-REPO-MAP
target_branch: docs/TP-DMX-FDOS-004-project-source-refresh
base_branch: main
base_sha_policy: resolve-current-origin-main-at-execution
final_packet: true
```

**Execution deviation (recorded, not silently applied):** the harness had already
provisioned a dedicated worktree/branch for this exact task
(`.claude/worktrees/chatgpt-40-source-refresh-f84dfc`, branch
`claude/chatgpt-40-source-refresh-f84dfc`) before this session began, sitting
clean at `origin/main`. Rather than nest a second worktree inside it, that
worktree/branch was used directly as the dedicated execution worktree for
this packet in place of `docs/TP-DMX-FDOS-004-project-source-refresh` /
`../dopemux-mvp-wt-TP-DMX-FDOS-004`. `EXECUTION_BASE_SHA` was resolved from
`origin/main` at execution time as specified.

Do not pin execution to the authoring-time `main` SHA.

At execution time:

1. fetch `origin`
2. resolve the current `origin/main`
3. record that SHA as `EXECUTION_BASE_SHA`
4. build all current-authority claims from that exact commit
5. recheck `origin/main` and open PR heads before final packaging
6. record drift rather than silently rebasing or laundering it

**EXECUTION_BASE_SHA: `5f862d36f5417801b9fe148fccbb439731627234`**

---

## 2. Objective

Produce a deterministic, evidence-backed replacement for the current ChatGPT Project source set containing **exactly 40 upload files**.

The replacement set must:

* represent current `main`, not historical upload copies
* preserve the repository truth hierarchy
* remove stale, duplicated, case-specific, generated-noise, and incorrectly scoped sources
* include current embedded-audit and PR Steward governance
* include a machine-readable source manifest with exact source paths and hashes
* include a freshness policy
* include a complete open-PR impact ledger
* treat unmerged PRs as candidate future authority only
* identify which open PRs require regeneration if merged
* produce a ZIP and SHA-256 sidecar
* not modify the ChatGPT Project or upload files to ChatGPT

The package may be valid for current `main` while material PRs remain open, but it must not call itself permanently final.

See `task-packets/generated/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.json`
for the full schema-valid packet record (steps, verification commands, commit
allowlist, PR body) and `out/chatgpt-project-upload-set/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH/`
for all generated artifacts. The full packet directive text (sections 3-30 of
the authoring prompt: scope, invariants, worktree procedure, source
resolution, open-PR classification rules, validation gates, embedded audit
and PR Steward requirements, proof bundle contract, and final report format)
is preserved in this session's `proof/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH/`
evidence trail and in the PR body; it is not duplicated verbatim a second
time in this file to avoid two divergent copies of the same governing text.

## Final Disposition

`CURRENT_MAIN_VALID_PENDING_OPEN_PR_REFRESH` -- see
`out/chatgpt-project-upload-set/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH/UPLOAD_FILES/39_PROJECT_SOURCE_MANIFEST.json`
and `40_OPEN_PR_IMPACT_LEDGER.md` for the authoritative record.
