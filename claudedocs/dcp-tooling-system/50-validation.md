# DCP Contract-Promotion + Tooling Layer v1 — Validation Record

**Date:** 2026-06-12 · **Method:** 4-lens multi-agent adversarial review (Sonnet×4, each instructed to refute, grounded against repo code) + Opus reconciliation.
**PAL note:** PAL MCP not loaded this session (ToolSearch verified) — per the documented fallback hierarchy, validation ran as independent multi-agent adversarial review instead of `pal/analyze→thinkdeep→challenge→consensus`. This is the declared substitution, not a silent downgrade.

## 1. Round summary

| Lens | Findings | Blockers | Adopted |
|---|---|---|---|
| Determinism / fail-closed / enforcement-truth | 11 | 2 | 9 |
| Security / injection / authority laundering | 10 | 3 | 9 |
| Feasibility / sequencing / collisions | 12 | 3 | 11 |
| Completeness vs constraint corpus | 16 | 2 | 14 |
| **Total** | **49 raw → 39 unique** | — | **~43 dispositions, 4 rejected/qualified** |

All blockers were adopted and are reflected in the rev-2 plan + design amendments A1–A16 + body edits (B.3/B.5/B.6, D-D, D-E). The validation round **changed the design materially** — it was not a rubber stamp.

## 2. Blocker dispositions (the ones that mattered)

| Finding | Disposition |
|---|---|
| `project_gate` = WARNING = scanner exits 0 → contract-file guard was non-blocking AND contradicted the existing fixture (which already says hard_block) | **ADOPTED** — lane restored to hard_block; sanctioned-change protocol (B.6) added as the release valve; contract paths join the frozen fallback |
| Circular protection: the data file configures the gate that guards the data file | **ADOPTED** — hard_block + fallback coverage + CODEOWNERS as Wave-0 operator item + CI consistency gate; honest v1 trust-model statement (repo write access + human review is the boundary) |
| `dcp accept` agent self-approval (asserted strings, no deny list, no TTY) | **ADOPTED** — TTY + typed-confirm with non-interactive refusal (the real barrier), PreToolUse deny matcher (defense-in-depth), T6 policy registration, path sanitization |
| TP-104 CI invocation fiction (`--packet-id` doesn't exist; changed-files mechanism unspecified; the gate blocks its own wiring TP) | **ADOPTED** — argparse moved to TP-103; CHANGED_FILES fragment reuse specified; B.6 covers workflow-edit TPs; warn→enforce staging |
| Receipt forgery window pre-commit + `.dcp/` not actually gitignored + "receipts even on denial" stated as present capability | **ADOPTED** — hash-lock at evidence-pack into committed PROOF.json as the tamper anchor; gitignore added in TP-106; capability relabeled NOT_IMPLEMENTED until TP-106 |
| Fail-open window between TP-103 (adds hard_block lanes) and TP-105 (upgrades fallback) | **ADOPTED** — fallback regeneration + equality test moved into TP-103 |
| Equivalence corpus self-contradiction (TP-102 adds detectors ⇒ equivalence with frozen rules impossible by construction) | **ADOPTED** — corpus scoped to the 5 pre-existing rules; new lanes validated as net-new coverage |
| Appendix B(2) command-surface spec + delete list unclaimed by any scope item | **ADOPTED** — explicitly out-scoped to DX-overhaul (scope doc edited) |
| TP-DCP-0002 derivation history absent → authority lineage of C3/C4/C5 unstated | **ADOPTED** — history section added; TP-109 dependency corrected |

## 3. Major dispositions (abridged — full agent reports in session transcript)

**Adopted:** real multi-pattern redactor replacing the placeholder stub (the stub misses `ghp_` short forms, URL-auth, PEM, Bearer, KEY=VALUE) · injection-template constraint on data-file text reaching `additionalContext` · DR-015 §8 fields restored (helper_version, policy_version, timing, model, mutations, sensitivity — no silent drops) · provenance honesty ("validated by first producer" retracted; in-schema tags with named reconciliation targets) · receipts.py subprocess self-trigger (git-file parsing preferred + exemption) · lazy CLI import (6.3k-line non-lazy cli.py) · both proof validators in TP-108 backward-compat · manifest `ci_gates` cross-file validation (a level claim can't cite a nonexistent gate) · "fail-closed" classifier relabeled fail-safe-advisory for v1 (truth in labeling) · self-cert truthiness bypass (absent identity fields → WARNING) · `gh api` pattern scoping · TP-101 after PR #862 · 102/113 CI-file serialization · diff_text dead-parameter correction · test_16 root cause (packet-anchored base ref, not schema edits) + replacement path · early-wave auditor-separation procedure · PROVISIONAL-class resolution gate · skills-reference-data rule · plugin never-list automated lint · P6 critical-path acknowledgment · version precedence rule · "L3(split)" formal definition · live-head_sha vs fixture-SHA clarification.

**Rejected / qualified (with reasons):**
1. *"Promote crypto signing into v1"* (security lens implied) — **qualified**: threat model is local-first single-operator; the committed-PROOF.json hash-lock covers the auditable-evidence need; crypto identity remains V2. The reviewer's premise (local receipts tamperable pre-commit) is conceded and now stated honestly rather than engineered away.
2. *"PreToolUse deny matcher for `dcp accept` is bypassable by obfuscation"* — **conceded and retained anyway** as defense-in-depth; the TTY refusal is the load-bearing control. Documented as such.
3. *Determinism lens's framing that fallback design "presupposes #858 merged"* — **qualified**: adopted as a hard dependency + re-scope clause on TP-105 (introduce the guard if #858 stalls), rather than redesigning around #858's absence.
4. *Completeness lens's suggestion that C2 fields must be fully repo-reconciled before any schema evolution* — **qualified per the audit's own must-fix #2 clause (b)**: fields may carry EXTERNAL_PROPOSED/SYNTHESIS_INVENTED tags instead of reconciliation; what's prohibited is laundering, not tagged external proposals.

## 4. Verification of constraint adherence (post-amendment)

| Constraint | Status |
|---|---|
| Audit must-fix #1 (per-field provenance) | PASS (A4 closes the C2 gap) |
| Must-fix #2 (no circular fixture validation) | PASS (provenance-completeness gate in TP-106; option-(b) tagging used where reconciliation pending) |
| Must-fix #3 (subprocess re-scope) | PASS (read-only git carve-out cited; receipts.py approach explicit) |
| Must-fix #4 (auditor ≠ implementer) | PASS-procedural pre-TP-110 (A13), runtime-enforced after |
| Must-fix #5 (derive-or-defer) | PASS (TP-DCP-0002 history recorded; PROVISIONAL gate in TP-109) |
| Five build-time red lines | PASS (restated per TP; merge seam untouched anywhere in design) |
| L-06 (config ≠ enforcement; CI duplicates) | PASS (CI named the only authority tier throughout; local = convenience) |
| DR-015 Never-list | PASS (no channels/monitors/agent-override/auto-approve anywhere; TP-114 lint automates it) |
| D8 v1 dry-run set | PASS (no live writers introduced; LIVE_WRITE_READY untouched, blocked-posture) |
| Appendix B coverage | 7 covered, 3 explicitly out-scoped with owner (B2→DX-overhaul, B6→DX-overhaul P6, B9→DX-overhaul); 0 silent gaps post-amendment |

## 5. Validation buckets (this design phase)

**PASS**
- 5-agent investigation grounded in file:line evidence; key claims (scanner callers, lane diff, supervisor_accepted, PR #858 delegation) independently cross-confirmed by ≥2 passes.
- 4-lens adversarial round executed; every blocker reconciled into the docs; rejected findings carry written reasons.
- Internal consistency pass: scope ↔ design ↔ plan aligned post-amendment (gate-open criteria, L3(split), dependency graph).

**FAIL**
- None outstanding: all adopted blockers have document-level fixes. (The findings themselves were FAILs of the rev-1 design — recorded above as dispositions.)

**NOT_RUN (with residual risk)**
- No code was executed or written — this is a design/plan phase; every TP's validation section defines the run-time checks. Residual risk: implementation may surface constraints the static review missed (mitigated by per-TP audits + staged enforcement).
- PR #858 CI status remains unverified (checks null) — TP-105 carries the hard dependency.
- PAL multi-model consensus NOT_RUN (server absent) — the multi-agent round substitutes but uses a single model family (Sonnet lenses + Opus reconciliation); a cross-vendor PAL pass at TP-authoring time would add diversity. Recommended when PAL returns.
- Operator approval of scope/plan NOT_RUN — required before TP authoring/orchestrator load.

## 6. Verdict

**Design + plan: VALIDATED-WITH-AMENDMENTS (all amendments applied).** Ready for operator review. The single most consequential outcome of validation: the contract files' own guard moved from a non-blocking warning to a hard block with an auditable approval-artifact carve-out — without that, the entire promotion ladder could have been silently edited out from under itself.
