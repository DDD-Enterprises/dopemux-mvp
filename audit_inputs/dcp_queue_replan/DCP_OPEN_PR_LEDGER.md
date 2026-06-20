# DCP Open PR Ledger — Post Phase 1 Reconciliation

**Packet:** GB-DMX-DCP-QUEUE-REPLAN-001  
**Captured:** 2026-06-19  
**origin/main:** `724a25fa01c77f7f1fd6ccf8a78da09f082e0ded`

## Executive Summary

Seed state is **stale**. Phase 1 merge train (#908, #909, #906, #923, #915, #920) is **complete on main**. Legacy queue PRs #873 and #885 are **merged**; #878 is **closed unmerged**. The only **open DCP PR** is **#931** (OpenClaw routing contracts).

## Phase 1 Status

| PR | State | On main |
|----|-------|---------|
| #908 | MERGED | 0006 classifier provenance-hardening packet |
| #909 | MERGED | 0007 input-provenance contract packet |
| #906 | MERGED | Lane engine MVP (`decide_lane`) |
| #923 | MERGED | Lane engine postmerge hardening |
| #915 | MERGED | 0006 classifier provenance implementation |
| #920 | MERGED | Prompt 5 runway reconciliation |

Runtime evidence on main: `src/dopemux/dcp/lane_engine.py`, `routing_classifier.py`, `schemas/dcp/*`, `tests/dcp/*`.

---

## Open DCP PRs

### #931 — [codex] add OpenClaw DCP routing contracts

| Field | Value |
|-------|-------|
| State | OPEN |
| Head | `017dc52bd9163fb20514bdf295777f8fa435f833` |
| Base | `697a6a20` (6 commits behind main) |
| Mergeable | MERGEABLE |
| Checks | Green (25/25 pass or skip) |
| Threads | 0 unresolved active; 18 resolved |
| Lane | DCP_TOOLING_IMPLEMENTATION |
| Classification | **STALE_BASE** |

**Changed files:** 38 — `contracts/openclaw-dcp-routing/**`, contract tests, markdown-location-guard exception, `pyproject.toml`.

**Dependencies:** Merged #926 placed near-identical artifacts under `docs/03-reference/dcp/openclaw-routing/`. #931 relocates to `contracts/` and adds validation tests.

**Recommended action:** Rebase onto `origin/main`; decide whether `contracts/` supersedes docs mirror; then evaluate merge.

---

## Reviewed Closed/Merged DCP PRs (seed queue)

### #878 — DCP tooling design pack (CLOSED, not merged)

| Field | Value |
|-------|-------|
| State | CLOSED (2026-06-18) |
| Mergeable at close | CONFLICTING |
| Threads at close | 3 unresolved active (108, 111, 112) |
| Lane | DCP_TOOLING_DESIGN |
| Classification | **CLOSE_RECOMMENDED** (already closed) |

**Answers:**

- Still valid after Phase 1? **Partially** — design intent holds; packets/load-plan stale.
- Pre-Phase-1 assumptions? **Yes** — 103–115 deps not refreshed for lane engine/provenance landings.
- Packets need refresh? **Yes**
- Needs rebase? **Yes** (if resurrected as new PR)
- Next correct active PR? **No** — superseded as queue head by #931; only 101+102 partially landed via #885
- Revise or close? **Remain closed**; open fresh PR if tooling series continues

**On main today:** `proof/DMX-DCP-TOOLING-101,102`, `task-packets/generated/DMX-DCP-TOOLING-102.json` only — not full 15-packet series.

### #885 — DMX-DCP-TOOLING 101+102 (MERGED)

| Field | Value |
|-------|-------|
| Merged | 2026-06-18 |
| Classification | **SUPERSEDED** (as queue item — work landed) |

**Answers:**

- Depends on #878? Soft — merged without design PR
- Overlaps Phase 1? No hard overlap
- Wait for #878? N/A — already merged; 103+ not started

### #873 — GPT-5.5 evidence intake (MERGED)

| Field | Value |
|-------|-------|
| Merged | 2026-06-18 |
| Classification | **EVIDENCE_ARCHIVE_ONLY** |

**Answers:**

- Superseded by #920? Partially for runway narrative; unique `audit_inputs/` archive remains
- Close/rebase? N/A — merged

---

## Recommended Queue Order

1. **#931** — rebase + duplication review vs #926, then merge evaluation
2. **#878 successor** (new PR) — only if tooling 103–115 still planned; refresh packets first

## Blockers

- #931 stale base (6 commits)
- #931 / #926 semantic duplication across directory trees
- Tooling design series (#878) paused — packets 103–115 absent from main

## Outside Scope (noted)

Open non-DCP PRs: #936 (ConPort), #933 (RTE), #925 (PCP).