# Independent Embedded Audit — TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001

**Auditor tool:** `claude-code-cli`  
**Auditor model:** `sonnet` (Claude Code independent session, print/plan mode)  
**Auditor provider:** local CLI  
**Auditor runner:** independent-session (not implementer)  
**Auditor session:** `TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001-audit`  
**Invocation:** `claude -p <adversarial-checklist> --permission-mode plan` (read-only tools)  
**Timestamp (UTC):** 2026-07-27T04:40:10Z  
**Base SHA audited against:** `2e3fb08fc16f03d7566200497018fc9b4bd088ad`  
**Raw transcript:** `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/review_bundle/CLAUDE_AUDIT_RAW.txt`

## Verdict

**PASS_WITH_RISKS**

Policy change is minimal, fail-closed, and correctly scoped in code. Non-blocking residual risks documented below. No packet stop condition is tripped by the code itself.

Validation observed by auditor: full `tests/pr_steward` suite PASS (235+ tests; subsequent implementer re-run after pin tests also exit 0).

## Adversarial checklist

| # | Check | Verdict |
|---|---|---|
| 1 | MEMBER works only when roster is exactly `[PR author]` | **PASS** |
| 2 | COLLABORATOR remains rejected | **PASS** |
| 3 | Second trusted human disables solo path | **PASS** |
| 4 | Stale or partial SHA remains rejected | **PASS** |
| 5 | Foreign comment author remains rejected | **PASS** |
| 6 | MEMBER cannot waive CI/audit/proof/threads/unknown/unclassified/harvest | **PASS** |
| 7 | Generic bots cannot use solo-human path | **PASS** (config-enforced via roster; not code-level `[bot]` reject) |
| 8 | Org-owned app path (`security_release_app`) unchanged | **PASS** |
| 9 | No code outside allowlist changed | **PASS** after F-1 remediation (stage only allowlisted paths; exclude tool-generated `.claude/*`) |

Additional:

- Association acceptance never replaces roster check — **PASS**
- `trusted_author_associations` not reused for solo path — **PASS**
- `SOLO_OWNER_ASSOCIATION_MISMATCH` when both present and differ — **PASS**
- Public diagnostics `SOLO_OWNER_AUTHOR_NOT_OWNER` / `SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER` preserved — **PASS**
- Receipt never fabricates GitHub APPROVED review; `auto_merge_enabled=False` — **PASS**

## Findings

### F-1 · MEDIUM · allowlist escape in working tree (remediated for commit)

Tool-generated `.claude/claude_config.json` / probe cache appeared in the worktree. Not packet scope. **Remediation:** do not stage those paths; commit only allowlist.

### F-2 · MEDIUM (pre-existing) · roster sourced from checkout, not proven from `origin/main`

Docstring claims “trusted main ref”; classifier resolves `known_reviewers.json` from the running checkout. Predates this packet. MEMBER widening makes roster strength more load-bearing. **Out of scope** for this packet; recommend separate HIGH follow-up.

### F-3 · LOW · no code-level bot login rejection on solo path

Item 7 holds because roster is `["hu3mann"]`. Optional future one-line guard. Not required by packet.

### F-4 · LOW · pin-test gaps (partially addressed)

Implementer added: `HARVEST_INCOMPLETE` under MEMBER other-gates table; MEMBER PR + absent comment association activation pin.

### F-5 · NIT · ADR frontmatter dates

Align `date` / `last_review` / `next_review` — remediating to consistent 2026-07-27 / +90d.

## Remaining risks

1. `MEMBER` is weaker GitHub claim than `OWNER` (org membership, not user-owned OWNER). Strength rests on exact single-person trusted roster + independent gates.
2. Missing-association tolerance: if one of PR/comment association is present and solo-operator, path may activate (fail-closed only when both missing). Inherited from #1131; pinned by tests.
3. End-to-end live GitHub association for org case is fixture-proven, not live-observed in this audit.
4. Trust-root recursion: deploying PR itself will still hit `SECURITY_RELEASE_APPROVAL_REQUIRED` under pre-merge main policy until bootstrap merge — expected.

## Recommendation

Proceed to commit/PR with explicit path staging. Bootstrap merge posture per packet: one-time administrative merge only when CI green, proof current to exact head, and sole Steward blocker is association recursion itself.
