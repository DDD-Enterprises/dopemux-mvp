---
id: cs-series-tp-audit-2026-05-28
title: DMX-ORCH-CLAUDE-SURFACE — Terminal TP Integrity Audit
type: audit
owner: Claude Code (audit subagent)
date: 2026-05-28
status: complete
applies_to: DMX-ORCH-CLAUDE-SURFACE series (root 1b633d83-82c4-4e28-abd3-d5ab73321390)
---

# DMX-ORCH-CLAUDE-SURFACE — Terminal TP Integrity Audit (2026-05-28)

READ-ONLY audit of the 44 supplied terminal work-item IDs. No orchestrator writes, no commits, no
file edits except this report. Every claim below is backed by a `query_notes`/`query_items` response
or a `git` command run during the session.

## Summary line of counts

Of the 44 supplied IDs:

| Verdict | Count | IDs (short) |
|---|---|---|
| **OK** (proof-bundle filled + all cited SHAs exist & reachable from HEAD) | **21** | ea3c7e75, 8c416dd7, 3ad6fc5c, de11f528, d608fe75, 57107a51, 3b912d78, 82f5f7ee, 86e9ed6f, 4c58dc3f, 86ddea46, 682ed4f8, 8231cea8, cebc0daf, 2e872f3a, 7572f24f, 85d54be3, 69ef2690, 6a95b9c1, 86d3ac55, ed6c1f66 |
| **OK (no-commit / shared-commit, by design)** | **6** | b061482a (TP-CS-012 fold), d46dd106 (TP-CS-013 verify-only), 6ce7129a (TP-CS-011 partial), 6c1a96d3 (TP-CS-010 decision), efa0b33e (TP-CS-001 ADR, partial), b398378f (TP-CS-002 ADR, partial) |
| **OK (cancelled, gate-bypass by design)** | **2** | 7ab96d15 (TP-CS-081 orig), c272bdff (TP-CS-080 orig) |
| **SUSPECT: NO-SHA-CITED** (proof-bundle present, no SHA cited, repo change claimed) — *all work recovered in real commits; downgraded to PROOF-HYGIENE-FAILURE* | **11** | be81e50b, 31ed7abc, db1c31c2, be3d4ab0, 5adb5365, d637c0fa, d3ad9a63, 8e965a1f, ddcbe5bd, 9c2cb6be, cc5b7f4e |
| **SUSPECT: FORCE-TERMINAL-NO-PROOF** (no proof-bundle; terminal role + statusLabel=in-progress) | **2** | 475c0749 (TP-CS-100), 53b9bd58 (TP-CS-003) |
| **UNRESOLVABLE** (`query_items get` → "WorkItem not found"; present in FTS index only) | **2** | 96a1e31b (TP-CS-100 dup), 94f4c4dd (TP-CS-101) |

Total: 21 + 6 + 2 + 11 + 2 + 2 = **44**. Resolvable items audited: 42; unresolvable (FTS ghosts): 2.

## CRITICAL cross-cutting finding (not a per-item defect)

**The CS-series `/dx:` command deliverables and `orchestrator-note-filling-protocol.md` are GONE from
`origin/main`, deleted by an unrelated merge.** Every proof-bundle SHA verifies as existing and
reachable, but a later merge clobbered the files at the trunk tip:

- Commit `d8e0268d3` ("🎨 Palette: Enhanced Notification Scannability...") is a **merge commit on
  `origin/main`** that **deleted 24 files**, including ALL 17 newly-authored `/dx:` slash commands
  (backlinks, block, blocked, cancel, complete-tree, complete, context, depends, next, note, notes,
  preview, reopen, resume, search, start, tree) and `docs/03-reference/orchestrator-note-filling-protocol.md`.
- `d8e0268d3` arrived via **PR #720 "Palette" UX merge** (`fbcae03d6`, merged 2026-05-28 13:42 PDT).
  `git merge-base --is-ancestor d8e0268d3 fbcae03d6` → true.
- The files were **never restored** after `d8e0268d3` (`git log d8e0268d3..origin/main -- <file>` empty).
- At `origin/main` tip (`755bf3846`) the ONLY surviving `/dx:` command is `implement.md` (TP-CS-041,
  which landed via separate PR #721 with no overlap).
- `git ls-tree -r origin/main -- .claude/commands/dx/` → only `implement.md`.

Net effect: the orchestrator marks TP-CS-030/031/032/033/034/035/036/037/038/039/042/043/044/045
(and the protocol doc TP-CS-054) terminal/done attesting to commits that existed at completion time,
but those deliverables are absent from current `main`. This is a **trunk-state regression** introduced
by a cross-PR merge collision, NOT a proof-bundle falsification. Recommended action: restore the
deleted files on `main` (cherry-pick / revert the deletion portion of `d8e0268d3`) and add a guard so
UX-branch merges cannot silently delete `.claude/commands/dx/**`.

## Full audit table

Legend: PB = proof-bundle note present. Conf = self-reported confidence. SHA-in-HEAD reflects state
at audit time (HEAD = descendant of both series branches AND, after a mid-session merge, of origin/main).

| TP | Item (short) | PB? | Conf | Cited SHA(s) | SHA exists & in HEAD? | Verdict |
|---|---|---|---|---|---|---|
| TP-CS-019 | ea3c7e75 | Y | VERIFIED | e65cc2525 | YES/YES | OK |
| TP-CS-044 | 8c416dd7 | Y | (terse PASS) | 27b5124da | YES/YES | OK (file gone from main*) |
| TP-CS-031 | 9c2cb6be | Y | — | PLACEHOLDER `<to be filled…>` | — | SUSPECT NO-SHA → recovered c8c90c3ec (file gone from main*) |
| TP-CS-026 | 5adb5365 | Y | — | none (claims AGENTS.md) | — | SUSPECT NO-SHA → recovered de8131033 |
| TP-CS-037 | 3ad6fc5c | Y | VERIFIED | 7ba885448 | YES/YES | OK (file gone from main*) |
| TP-CS-036 | de11f528 | Y | VERIFIED | 7ba885448 | YES/YES | OK (file gone from main*) |
| TP-CS-043 | d608fe75 | Y | (terse PASS) | 27b5124da | YES/YES | OK (file gone from main*) |
| TP-CS-032 | 57107a51 | Y | (terse PASS) | 5bc16027d | YES/YES | OK (file gone from main*) |
| TP-CS-045 | 3b912d78 | Y | (terse PASS) | 27b5124da | YES/YES | OK (file gone from main*) |
| TP-CS-027 | d637c0fa | Y | — | none (claims copilot-instructions.md) | — | SUSPECT NO-SHA → recovered de8131033 |
| TP-CS-038 | 82f5f7ee | Y | (terse PASS) | 5bc16027d | YES/YES | OK (file gone from main*) |
| TP-CS-020 | be81e50b | Y | — | none (claims .claude/CLAUDE.md) | — | SUSPECT NO-SHA → recovered ab4c45c74/e9389765d |
| TP-CS-035 | 86e9ed6f | Y | (terse PASS) | a14a7bd2e | YES/YES | OK (files gone from main*) |
| TP-CS-012 | b061482a | Y | (folded) | 3b39c3dfa (shared w/ TP-CS-011) | YES/YES | OK (no independent commit, by design) |
| TP-CS-030 | ddcbe5bd | Y | — | PLACEHOLDER `<to be filled…>` | — | SUSPECT NO-SHA → recovered c8c90c3ec (file gone from main*) |
| TP-CS-022 | 4c58dc3f | Y | VERIFIED | 61094ccf6 | YES/YES | OK |
| TP-CS-042 | 86ddea46 | Y | (terse PASS) | 27b5124da | YES/YES | OK (file gone from main*) |
| TP-CS-039 | 682ed4f8 | Y | VERIFIED | 7ba885448 | YES/YES | OK (file gone from main*) |
| TP-CS-081(orig) | 7ab96d15 | N (0 notes) | — | none | — | OK (cancelled — statusLabel=cancelled) |
| TP-CS-041 | 8231cea8 | Y | (PASS) | 06d560303 | YES/YES | OK (PR #721; implement.md present on main) |
| TP-CS-013 | d46dd106 | Y | PARTIAL (not VERIFIED) | 3b39c3dfa (verify-only) | YES/YES | OK (verification packet, by design) |
| TP-CS-025 | be3d4ab0 | Y | — | none (claims 2 files) | — | SUSPECT NO-SHA → recovered f45c5f107 |
| TP-CS-054 | cc5b7f4e | Y | — | none (claims protocol doc) | — | SUSPECT NO-SHA → recovered de8131033 (file gone from main*) |
| TP-CS-080(orig) | c272bdff | N (0 notes) | — | none | — | OK (cancelled — statusLabel=cancelled) |
| TP-CS-011 | 6ce7129a | Y | PARTIAL (not VERIFIED) | 3b39c3dfa | YES/YES | OK (canonical config commit) |
| TP-CS-033 | cebc0daf | Y | (terse PASS) | 5bc16027d | YES/YES | OK (file gone from main*) |
| TP-CS-024 | db1c31c2 | Y | — | none (claims governance-principles.md) | — | SUSPECT NO-SHA → recovered f45c5f107 |
| TP-CS-029 | 8e965a1f | Y | — | none (claims PERSONA_INDEX.md) | — | SUSPECT NO-SHA → recovered de8131033 |
| TP-CS-028 | d3ad9a63 | Y | — | none (claims agents.instructions.md) | — | SUSPECT NO-SHA → recovered de8131033 |
| TP-CS-034 | 2e872f3a | Y | (terse PASS) | 5bc16027d | YES/YES | OK (file gone from main*) |
| TP-CS-021 | 31ed7abc | Y | — | none (claims authority-matrix.md) | — | SUSPECT NO-SHA → recovered e9389765d |
| TP-CS-100(dup) | 96a1e31b | UNRESOLVABLE | — | — | — | UNRESOLVABLE (get → not found; FTS-only) |
| TP-CS-101 | 94f4c4dd | UNRESOLVABLE | — | — | — | UNRESOLVABLE (get → not found; FTS-only) |
| TP-CS-100 | 475c0749 | N (codereview note only, no PB) | — | none (assessment) | — | SUSPECT FORCE-TERMINAL-NO-PROOF (terminal+in-progress) |
| TP-CS-081 | 7572f24f | Y | VERIFIED | 92cf9005d | YES/YES | OK |
| TP-CS-060 | 85d54be3 | Y | (PASS; pytest 3/3) | f34f253a3 | YES/YES | OK (PR #722) |
| TP-CS-002 | b398378f | Y | PARTIAL (not VERIFIED) | 18fef811c | YES/YES | OK |
| TP-CS-010 | 6c1a96d3 | Y | (decision; files=0) | none (by design) | — | OK (decision-only, no commit) |
| TP-CS-061 | 69ef2690 | Y | (PASS; pytest 3/3) | f34f253a3 (shared) | YES/YES | OK (PR #722) |
| TP-CS-003 | 53b9bd58 | N (0 notes) | — | none (self-hosting scaffold) | — | SUSPECT FORCE-TERMINAL-NO-PROOF (terminal+in-progress) |
| TP-CS-110 | 6a95b9c1 | Y | (PASS) | f34f253a3 (shared) | YES/YES | OK (PR #722) |
| TP-CS-001 | efa0b33e | Y | PARTIAL (not VERIFIED) | b24014fcc | YES/YES | OK (ADR) |
| TP-CS-080 | 86d3ac55 | Y | VERIFIED | 903ff57ec | YES/YES | OK |
| TP-CS-023 | ed6c1f66 | Y | VERIFIED | 45af0a915 (push 61094ccf6..45af0a915) | YES/YES | OK |

`*` "file gone from main" = the proof-bundle's commit genuinely exists and is reachable, but the
delivered file was subsequently deleted from `origin/main` by `d8e0268d3` (#720 Palette merge). See
the CRITICAL finding above. The completion itself is NOT phantom; the trunk regressed.

### Git verification evidence (all SHAs)

`git rev-parse --verify <sha>^{commit}` + `git merge-base --is-ancestor <sha> HEAD` + `… origin/main`,
run as a batch. Result: **all 15 cited SHAs and all 5 recovered cluster SHAs EXIST and are ancestors
of both HEAD and origin/main**:

```
e65cc2525 27b5124da 7ba885448 5bc16027d a14a7bd2e 3b39c3dfa 61094ccf6
06d560303 92cf9005d f34f253a3 18fef811c b24014fcc 903ff57ec 45af0a915
ab4c45c74  (recovered: TP-CS-020)
e9389765d  (recovered: TP-CS-020/021)
f45c5f107  (recovered: TP-CS-024/025)
de8131033  (recovered: TP-CS-026/027/028/029/054)
c8c90c3ec  (recovered: TP-CS-030/031)
→ EXISTS=YES, anc_HEAD=YES, anc_origin/main=YES for every one.
```

No phantom (non-existent or unreachable) SHA was found anywhere.

## SUSPECT items — detail & recommended action

### Class A — PROOF-HYGIENE-FAILURE (downgraded from NO-SHA-CITED): 11 items

These proof-bundles asserted a repo change but cited no commit SHA (8 cite nothing; 2 — TP-CS-030/031
— literally contain the placeholder string `<to be filled by next session after push>`). **Severity
downgraded from CRITICAL to MEDIUM**: `git log --all --grep="TP-CS-NNN"` recovered a real, reachable
commit for every one. The work landed; only the citation is missing. Root cause is a single operator
habit, not 11 independent incidents — the bundles were written in-session BEFORE a later batched commit
(combined commit messages naming multiple TPs), and the SHA was never back-filled into the note.

| TP | Item | Claimed file(s) | Recovered commit (reachable) |
|---|---|---|---|
| TP-CS-020 | be81e50b | .claude/CLAUDE.md | ab4c45c74, e9389765d |
| TP-CS-021 | 31ed7abc | authority-matrix.md | e9389765d |
| TP-CS-024 | db1c31c2 | governance-principles.md | f45c5f107 |
| TP-CS-025 | be3d4ab0 | integration-bridge.md, event-patterns.md | f45c5f107 |
| TP-CS-026 | 5adb5365 | AGENTS.md | de8131033 |
| TP-CS-027 | d637c0fa | .github/copilot-instructions.md | de8131033 |
| TP-CS-028 | d3ad9a63 | config/instructions/agents.instructions.md | de8131033 |
| TP-CS-029 | 8e965a1f | .claude/personas/PERSONA_INDEX.md | de8131033 |
| TP-CS-054 | cc5b7f4e | docs/03-reference/orchestrator-note-filling-protocol.md | de8131033 (BUT file later deleted from main — see CRITICAL) |
| TP-CS-030 | ddcbe5bd | .claude/commands/dx/next.md | c8c90c3ec (file later deleted from main) |
| TP-CS-031 | 9c2cb6be | .claude/commands/dx/context.md | c8c90c3ec (file later deleted from main) |

Common signature: all are "Phase 3 doctrine" / "Phase 2 read-command" docs-only TPs whose bundles say
`Codereview: self-review` and `Precommit: NOT_RUN (docs only)`. Timestamps cluster tightly
(2026-05-27 23:18, 23:52, 23:59, 2026-05-28 00:23 UTC).

**Recommended action**: (1) back-fill the recovered SHA into each proof-bundle note for audit
traceability; (2) fix the docs-only proof-bundle template so "commit + push + record SHA" is a required
step even for documentation changes (the complete-gate checks for a *filled* proof-bundle but does not
parse the SHA, so placeholders pass). Tracking SHAs above are sufficient to confirm no work was lost
(except via the unrelated #720 deletion).

### Class B — FORCE-TERMINAL-NO-PROOF: 2 items

| TP | Item | Title | State anomaly |
|---|---|---|---|
| TP-CS-003 | 53b9bd58 | Create CS sibling series + Phase 1 children + cross-series BLOCKS | role=terminal, **statusLabel=in-progress** |
| TP-CS-100 | 475c0749 | Assess upstream claude-plugins/task-orchestrator/ | role=terminal, **statusLabel=in-progress**; has a `codereview`-key inventory note but NO `proof-bundle` note |

Both reached `role: terminal` WITHOUT a `proof-bundle` note, and both carry the contradictory
`statusLabel: in-progress`. Both share `roleChangedAt: 2026-05-27T23:09:18` exactly — a single bulk
force-move during Phase 1 scaffolding, not random sloppiness. **Mitigant**: both are coordination /
read-only-assessment packets that produce orchestrator state (work-items, dependencies) or a research
inventory rather than a repo commit, so the missing commit SHA is expected. But the complete-gate
contract (proof-bundle required for `task-packet`) was not satisfied and the terminal+in-progress state
is internally inconsistent. **Recommended action**: either (a) re-classify these as non-`task-packet`
schema (coordination/assessment) so the gate doesn't apply, or (b) file a minimal proof-bundle note
("no repo change; orchestrator-state/assessment only") and re-derive a coherent statusLabel. Treat as
LOW/MEDIUM data-integrity, not lost work.

### Class C — UNRESOLVABLE IDs: 2 items

| Supplied ID | FTS title | `query_items get` result |
|---|---|---|
| 96a1e31b-c04d-4564-939e-a61e7da78ca4 | TP-CS-100: Assess upstream… | "WorkItem not found" |
| 94f4c4dd-5fc4-4324-b836-468b00dec8cc | TP-CS-101: Decide and implement pl… | "WorkItem not found" |

Both IDs appear in the orchestrator's FTS index (they show up in `query_items search query="TP-CS"`)
but **cannot be fetched by UUID** via `query_items get`, and `query_notes list` fails for them. The
container is healthy (known-good IDs resolve normally before and after). This is an FTS-index ↔
items-table inconsistency: stale/orphaned FTS rows for items that no longer exist in the items table.
`96a1e31b` is a superseded TP-CS-100 duplicate (the live TP-CS-100 is `475c0749`); `94f4c4dd` is
TP-CS-101 (the "decide and implement plugin path" follow-on). **Recommended action**: rebuild/reconcile
the orchestrator FTS index against the items table; investigate how a deleted item leaves FTS rows
behind (possible bug in the external stdio MCP, consistent with the known timestamp/overview bugs).
These two could NOT be audited for proof integrity — they may never have been genuine terminal
task-packets, or were deleted post-completion.

## Coverage sanity-check result

The 44 IDs were sourced from an FTS search for "TP-CS" among terminal items.
`query_items search query="TP-CS" scope={ancestorId:1b633d83…, role:"terminal"} limit=100` returns
**exactly 44 hits, `truncated: false`** — i.e. the supplied list IS the complete FTS-terminal "TP-CS"
set; nothing was dropped from it. A second scoped search (`query="orchestrator"`, `tags:[dmx-orch-claude-surface]`)
returned 23 terminal items, all a subset of the 44 — no new IDs surfaced.

Caveat: FTS-based enumeration can only find items the index knows about. Two of the 44 (`96a1e31b`,
`94f4c4dd`) are in the FTS index but absent from the items table (Class C), so the count of genuinely
resolvable terminal items is **42**, not 44. Conversely, any terminal `task-packet` whose title lacks
"TP-CS" AND lacks the keywords searched would be invisible to this method; the broken
`query_items operation=overview` (timestamp-parse bug) prevented an authoritative full enumeration. On
the available evidence the 44 looks complete for the "TP-CS"-titled terminal set, with the 2 phantom-FTS
caveats noted.

## Tooling caveats encountered

- **Branch discrepancy vs prompt**: the prompt stated the working branch was
  `dx-implement-orchestrator-rewrite`. At audit start it was actually `claude/tp-dmx-orch-followup-packets`
  (HEAD `500ab4459`), a descendant of BOTH `task-orchestrator-claude-surface` and
  `dx-implement-orchestrator-rewrite` and of the then-`origin/main` (`ef0c30bf4`). The
  `merge-base --is-ancestor … HEAD` reachability test was therefore *stronger* than the prompt assumed
  (HEAD contained all series work + 32 extra commits).
- **HEAD moved mid-session**: partway through, the working tree switched to `main` and `origin/main`
  advanced from `ef0c30bf4` to `755bf3846` (PRs #720, #721, #722, #716 all merged 2026-05-28 ~13:39–13:43
  PDT, concurrent with this audit). Reachability was re-verified after the move: both series branches
  remain ancestors of the new HEAD, and all cited/recovered SHAs are now also ancestors of `origin/main`.
  This mid-session merge is what surfaced the CRITICAL #720-deletion finding.
- **`query_items operation=overview` is broken** ("Error parsing time stamp") — not used, per prompt.
- **Two `query_notes(list)` calls failed** for `96a1e31b` and `94f4c4dd`; root cause was "WorkItem not
  found" (Class C), not a transient container error — confirmed by direct `query_items get`.
- All orchestrator calls were issued sequentially (single shared stdio container); git checks were batched.

## Bottom line

- **No phantom/rebased-away completions found.** Every cited and every recovered SHA exists and is
  reachable from HEAD and origin/main.
- **The real risk is the opposite of phantom completion**: genuine, committed CS-series deliverables
  (17 `/dx:` commands + the note-filling protocol doc) were **silently deleted from `origin/main`** by
  the #720 "Palette" UX merge (`d8e0268d3`). Marked-done work-items now point at files that no longer
  exist on the trunk. This is the highest-priority remediation item.
- **11 proof-bundles are hygiene-deficient** (no SHA cited; work confirmed landed) — a template/process
  fix, not lost work.
- **2 items are force-terminal without proof** (TP-CS-003, TP-CS-100) with inconsistent statusLabel —
  schema/state cleanup.
- **2 supplied IDs are unresolvable** (FTS-index ghosts) — orchestrator index reconciliation needed.
