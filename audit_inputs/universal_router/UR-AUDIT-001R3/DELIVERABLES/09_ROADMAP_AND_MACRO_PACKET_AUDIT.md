# 09 — Roadmap & Macro-Packet Audit

## A. Roadmap ordering (`18`) vs prompt-required order
Required: contracts → read-only CLI → append-only journal → capability-snapshot ingestion → existing-subsystem
adapters → Codex advisory adapter → proof references → shadow evaluation → manual operator acceptance → one
execution adapter at a time → bounded escalation → automatic routing after certification.

Architecture Steps 1–12 / packets UR-TP-001…012 match this order **exactly**. First release = Steps 1–9 =
packets 001–009 = releases R1 advisory foundation + shadow/acceptance, max state `OPERATOR_ACCEPTED`. Steps
10–12 (R2–R4) are future-gated with explicit go/no-go ("Step 10 cannot start merely because step 9 is complete").

Dependencies/gates/stop-conditions/proof/rollback are present per step; no automatic execution, no subagent
fanout, no premature service, no oversized mixed packets. **Ordering: PASS.**

**Codex-as-first-advisory-adapter evidence basis (prompt requirement):** UR-INV-003 shows Codex had the only
*successful contained smoke* (probe-ok JSON, JSONL, output-schema, read-only sandbox, ephemeral session), while
the Claude Code bare smoke was *unavailable* (never reached a provider, zero usage). Choosing Codex as the first
**advisory** adapter (UR-TP-006, non-executing) is therefore **evidence-grounded, not model-family bias**; the
architecture keeps Codex only "leading candidate, not accepted decision" for *execution* (UR-OQ-019 DEFERRED) and
records Codex hard tool-denial UNKNOWN. This is the correct posture.

## B. Macro-packet classification (all 12)

| Packet | Objective | First-release? | Classification | Notes |
|---|---|---|---|---|
| UR-TP-001 Contracts | strict versioned contracts + schemas + fixtures | Yes | **EXECUTABLE_AFTER_PATH_RESOLUTION** | greenfield paths verified absent; must cite tracked canonical contract paths (UR-AUDIT-R3-001) + pin PR Steward (UR-AUDIT-R3-004); strict schemas are the packet gate (UR-AUDIT-R3-003) |
| UR-TP-002 Read-only CLI/engine | `route explain/recommend/inspect/validate`, deterministic | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | `route` noun free (verified); must not rewrite `routing`; no path may enter handoff/execution |
| UR-TP-003 Append-only journal | SQLite triggers/WAL/replay | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | confirm `.dopemux/` gitignore (verified); hash-chain hardening (P3-005) |
| UR-TP-004 Snapshot ingestion | import/TTL/expiry, no live probe | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | UR-OQ-013/014 constrain, not block, static ingestion |
| UR-TP-005 Existing-subsystem read adapters | DCP/Freeflow/LiteLLM/RTE/proof/handoff/audit/PR refs | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | gated by UR-OQ-002/003/004/005/020 read-interface unknowns → artifact-first fallback specified |
| UR-TP-006 Codex advisory adapter | non-executing recommendation | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | reacquire Codex help if version drifts; no invocation path |
| UR-TP-007 Proof/governance refs | validate/attach canonical refs | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | UR-OQ-020 version compat; canonical proof/handoff docs tracked (provenance matrix) |
| UR-TP-008 Shadow eval/cert harness | replay/metrics/report | Yes | BLOCKED_BY_UNKNOWN_RUNTIME (soft) | UR-OQ-017 corpus size; no live execution; can build harness+fixtures now, certification later |
| UR-TP-009 Manual operator acceptance | accept/reject/correction events | Yes | EXECUTABLE_AFTER_PATH_RESOLUTION | no implicit acceptance; UR-OQ-018 issuer for approval-required paths |
| UR-TP-010 First execution adapter | one Codex execution adapter | **Future-gated** | DESIGN_BLUEPRINT_ONLY / BLOCKED_BY_UNKNOWN_RUNTIME | packet itself states exact Codex invocation is UNKNOWN (UR-OQ-007/009); "Absence is a hard stop" |
| UR-TP-011 Bounded escalation | budgets/demotion | Future-gated | DESIGN_BLUEPRINT_ONLY | needs ≥25 accepted executions + new approval |
| UR-TP-012 Narrow automatic lane | one certified auto route | Future-gated | DESIGN_BLUEPRINT_ONLY | needs ≥100 certified executions + new ADR + human promotion |

Every packet carries objective, IN/OUT scope, allowlist, exact commands, validation gates, proof requirements,
rollback, stop conditions, embedded audit, and PR Steward readiness (common envelope). Baseline/final commands
capture `git status/diff --check/diff --stat/diff` and exit codes into `COMMAND_RESULTS.json` — good current-head
proof discipline. Stale-branch protection = base branch pinned by SHA per child packet.

## C. Packet schema conformance & red flags
- No invalid/nonexistent scope paths at first-release packets (greenfield paths verified absent → to be *created*
  by their packet, which is legitimate).
- No dependency-on-unmerged-work presented as ready; 010–012 explicitly `NOT_ISSUED`.
- No premature tests, no red-lane changes, no oversized slices (each packet is commit-sized, single-implementer,
  single worktree).
- Embedded audit is **not** self-audit: default Claude Code Sonnet `--tools "" --no-session-persistence
  --permission-mode plan`; a Claude implementation "cannot audit its own implementation session." Skipped audit
  → packet BLOCKED (not pass).
- Future-gated packets are correctly **not** presented as ready.

## D. Which packet may be issued first?
**UR-TP-001** may be issued first, classified **EXECUTABLE_AFTER_PATH_RESOLUTION**. Local implementation and
validation can proceed immediately; the two resolution steps that gate the *PR/merge* are: (1) cite tracked
canonical contract/authority paths from `13_PROVENANCE_RESOLUTION.md` instead of bundle archive names
(UR-AUDIT-R3-001, closes UR-OQ-001 authority axis), and (2) pin the canonical PR Steward invocation before opening
the PR (UR-AUDIT-R3-004 / UR-OQ-006). The packet's own gate — strict schemas + fixtures — must be met before
sign-off (UR-AUDIT-R3-003). No packet may be issued that reaches handoff/execution in the first release.
