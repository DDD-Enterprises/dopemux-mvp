# Independent L3 Audit (successor) — TP-DMX-TRUST-GATE-FAIL-CLOSED-001

**Audited commit (C1, unchanged)**: `352a3d888d1ce5116b9af65d696fe62373728a7c`
**This report supersedes `AUDITOR_REPORT.md` as the CONTROLLING audit.** `AUDITOR_REPORT.md`
(the Claude Code `quality-engineer` subagent audit) is retained as historical evidence
with `LIMITED` independence — same runtime/company family as the implementer — per
supervisor disposition of 2026-08-12. It is not deleted or rewritten.

## Why this report exists

Supervisor ruled the original audit insufficient for L3 sign-off: same-family/runtime
(Claude Code) independence between implementer and auditor is weaker than the L3 policy
requires. This report is a genuinely different-family/runtime audit, routed per the
supervisor's own preferred order. Full route-discovery evidence (AGY rejected —
non-functional; native Gemini CLI rejected — hard `IneligibleTierError`; CommandCode
accepted — functional, genuinely non-Anthropic model families available) is in
`review_bundle/AUDIT_ROUTE_DISCOVERY.md`.

## Auditor identity (ground truth, not self-report)

- **Tool/runtime**: CommandCode CLI v1.17.0 (`commandcode`), a separate coding-agent
  product from Claude Code.
- **Model — evidence-gathering phase** (diff review, full source read, targeted pytest
  run): `gpt-5.3-codex` (OpenAI), confirmed via the CLI's own `model_request_start` event
  metadata.
- **Model — continuation phase** (CLAIMED-state repro, last-writer-wins parent-vs-C1
  comparison, baseline-failure range trace, adversarial PASS-path hunt, final written
  report): `deepseek/deepseek-v4-flash` (DeepSeek, open-source), also confirmed via
  `model_request_start` metadata. This model switch was an unintended CLI default-fallback
  on session resume (documented in `AUDIT_ROUTE_DISCOVERY.md`), not a deliberate design —
  disclosed for full transparency.
- **Important caveat**: the continuation phase's own final-report text self-identified as
  "Anthropic Claude (Claude Sonnet 5)" — this is **factually wrong**, contradicted by the
  CLI's own API-level model metadata for every request in that phase. The proof record
  here uses the ground-truth metadata, not the model's self-description, as authoritative.
- **Independence conclusion**: both phases ran on models from vendors (OpenAI, DeepSeek)
  genuinely distinct from the implementer (Claude Code / Sonnet 5) and from the prior
  audit (Claude Code `quality-engineer` subagent, Sonnet 5). Different-family/runtime
  independence is satisfied for the full audit, despite the self-report defect.

## Verdict

**PASS_WITH_RISKS** — both findings (F001, F002) independently confirmed closed; all ten
invariants confirmed with file/line citations and live command output; changed-file
allowlist 100% compliant (14/14 files in C1); baseline test-suite failure independently
re-traced and confirmed `BASELINE_FAILURE_PROVEN_NONREGRESSION`. Four non-blocking risks
disclosed (two newly surfaced by this pass — R1/R2 below — refining rather than
contradicting the prior audit's risk set; R3/R4 new minor observations).

Full report with per-invariant citations, allowlist table, baseline-failure adjudication,
and additional findings: `review_bundle/INDEPENDENT_AUDIT_FINAL_REPORT.md`. Raw tool-call
transcript (git diff/show output, pytest runs, file reads):
`review_bundle/INDEPENDENT_AUDIT_TOOL_TRANSCRIPT.txt`.

### Risks disclosed by this audit (all non-blocking, all pre-existing — none introduced by C1)

- **R1**: a proof with both identities present-and-distinct but no `head_sha` (with
  `expected_head_sha` supplied) still reaches `PASS`. Pre-existing on parent; not
  introduced by C1; the core F001 identity-completeness fix is sound. Recommend follow-up
  ticket.
- **R2**: last-writer-wins guard aggregation — refines the prior audit's R1. This pass
  independently re-verified against BOTH parent and C1: parent reaches `PASS` for both
  proof orderings (incomplete-first and complete-first); C1 now fails closed for
  complete-first (the ordering where the incomplete proof lands last) but still reaches
  `PASS` for incomplete-first. C1 is confirmed a strict improvement, with the residual gap
  disclosed precisely.
- **R3**: in `control_snapshot._readiness()`, `CONFLICTING` status preempts appending
  other `blocking_reasons` for the same or other prerequisite packets — `blocking_reasons`
  may read empty even when conflicting evidence exists, because the overall status field
  already signals it. Arguably correct precedence; disclosed for completeness.
- **R4**: the new fixture `tests/dcp/fixtures/tp_dcp_0004_missing_tp0002_evidence/` omits
  a `tests/dcp/test_placeholder.py` present in the valid fixture it was copied from — no
  test impact (not exercised by the readiness assertions), but a minor consistency gap
  worth noting for future maintenance.

## Binding

This audit is bound to **C1 = `352a3d888d1ce5116b9af65d696fe62373728a7c`**, not to C2 or
this proof-only successor commit. No substantive content changed after C1. No merge,
close, mark-ready, force-push, or production mutation is authorized by this report.
