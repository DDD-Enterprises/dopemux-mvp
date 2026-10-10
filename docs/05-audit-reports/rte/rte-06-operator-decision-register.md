---
id: rte-06-operator-decision-register
title: Rte 06 Operator Decision Register
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-12'
last_review: '2026-04-12'
next_review: '2026-07-11'
prelude: Rte 06 Operator Decision Register (reference) for dopemux documentation
  and developer workflows.
---
# RTE-06 Operator Decision Register

This register records the remaining operator and governance questions that the packet stream could not close in code.

Primary authority:

- `docs/05-audit-reports/rte-state-of-work-audit-20260410.md`
- `docs/03-reference/task-packets/rte-04-fl-routing-and-benchmark-governance-evidence.md`
- `docs/03-reference/task-packets/rte-05-canon-reconciliation-matrix.md`

Decision state legend:

- `pending` means no operator decision is recorded in repo truth
- `decided` means an operator-approved policy exists in repo truth

## OQ-1 Promotion thresholds

- Question: What `contract_score` and `evidence_score` thresholds qualify a benchmark candidate for production promotion?
- Why it matters: benchmark outputs can produce `recommended_for_review`, but there is no repo-truth threshold for when that recommendation may translate into routing change.
- Current options:
  - require explicit numeric thresholds per archetype and profile before any production promotion
  - allow a single temporary global threshold for the first benchmark season
  - keep promotion fully manual with no numeric threshold policy
- Recommended option: require explicit numeric thresholds per archetype and profile before any production promotion
- Owner: operator / benchmark governance authority
- Blockers to decision: live benchmark evidence is still partial and BM-LIVE remains staged
- Downstream effect: this controls when review packets can move from `recommended_for_review` into actual route promotion workflows
- Current state: `pending`

## OQ-2 Benchmark budget caps

- Question: What per-run and per-candidate budget caps are allowed for live benchmark execution?
- Why it matters: BM-LIVE is partially wired, but broader live benchmark campaigns should not run without explicit spend boundaries.
- Current options:
  - fixed caps for both per-run and per-candidate live benchmark spend
  - staged caps that expand only after repeated low-risk benchmark runs
  - no global caps, case-by-case manual authorization only
- Recommended option: staged caps that start conservative and require explicit review before expansion
- Owner: operator / budget authority
- Blockers to decision: no benchmark-season budget policy is recorded in repo truth
- Downstream effect: controls whether benchmark campaigns can move beyond isolated live-capable tests
- Current state: `pending`

## OQ-3 Phase S policy-gating posture

- Question: What governance posture applies to Phase S given the absence of adjacent JSON schema coverage?
- Why it matters: Packet 01 added a minimum gate before Phase S dispatch, but the higher-level policy for synthesis without neighboring schemas is still undecided.
- Current options:
  - require policy-gated review before any broader Phase S live use
  - allow Phase S for bounded lanes only while schema gaps remain
  - treat current minimum runtime gate as sufficient until a later schema rollout
- Recommended option: allow Phase S only for bounded reviewed lanes until schema-adjacent policy is explicitly defined
- Owner: operator / extraction governance authority
- Blockers to decision: no repo-truth policy file defines the acceptable synthesis governance boundary
- Downstream effect: controls whether Phase S can expand beyond the current bounded live-readiness posture
- Current state: `pending`

## OQ-4 Local and open-weight graduation criteria

- Question: Under what conditions can local or open-weight candidates graduate out of `experimental_lab`?
- Why it matters: benchmark recommendation states already distinguish experimental-only outcomes, but the graduation rule is not defined.
- Current options:
  - require contract pass plus repeated benchmark wins plus governance review
  - require governance review only, with no hard benchmark threshold
  - keep local/open-weight routes permanently experimental in this cycle
- Recommended option: require contract pass, repeated benchmark wins, and explicit governance review
- Owner: operator / benchmark governance authority
- Blockers to decision: promotion thresholds and budget caps are still unresolved
- Downstream effect: affects profile-fit synthesis, blocked-lane handling, and FL-ROUTE posture
- Current state: `pending`

## OQ-5 OpenClaw write authority

- Question: Should OpenClaw have read-only or read-write authority over benchmark artifacts and review outputs?
- Why it matters: benchmark governance packets and review flows depend on whether OpenClaw may directly write operator-visible outputs.
- Current options:
  - read-only review authority with proposal output only
  - bounded write authority for specific governance packet classes
  - full read-write authority over benchmark artifacts
- Recommended option: read-only review authority with proposal output only
- Owner: operator / artifact-governance authority
- Blockers to decision: no repo-truth write policy names OpenClaw authority for benchmark artifacts
- Downstream effect: controls how governance packets, review packets, and decision logs may be populated
- Current state: `pending`

## Packet 06 carry-over: FL_INT ladder posture

- Question: Should the current FL_INT ladder slugs remain benchmark-only future targets, or should they be replaced with confirmed registry models before any production use?
- Why it matters: Packet 04 made current ladder truth explicit, but the operator choice to keep or replace those slugs is still open.
- Current options:
  - keep current slugs as benchmark-only future targets
  - replace them with confirmed registry models now
  - split benchmark ladders from production-allowed ladders explicitly
- Recommended option: split benchmark ladders from production-allowed ladders explicitly
- Owner: operator / routing authority
- Blockers to decision: canonical registry confirmation is incomplete for the current ladder set
- Downstream effect: affects FL_INT production safety claims and future benchmark reporting
- Current state: `pending`

## Packet 06 carry-over: BM-LIVE expansion authority

- Question: What exact preconditions must be true before benchmark execution expands from the current partial live posture to broader BM-LIVE campaigns?
- Why it matters: current repo truth shows `runtime_v5_extraction` can run live, while `fl_int` and other adapters remain fixture-backed.
- Current options:
  - require all OQ-1 through OQ-5 to be decided before any broader BM-LIVE
  - allow limited expansion after OQ-2 only
  - allow organic expansion based on ad hoc operator approval
- Recommended option: require OQ-1 through OQ-5 to be resolved before broader BM-LIVE expansion
- Owner: operator / benchmark governance authority
- Blockers to decision: unresolved budget, promotion, and authority policies
- Downstream effect: controls whether benchmark live execution remains partial or becomes an active campaign lane
- Current state: `pending`
