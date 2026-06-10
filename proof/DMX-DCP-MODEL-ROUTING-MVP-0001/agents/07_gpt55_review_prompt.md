# GPT-5.5 Review Prompt — 0001

You are GPT-5.5 Pro supervisor.

Review DMX-DCP-MODEL-ROUTING-MVP-0001.

**Input**:
- GPT55_REVIEW_BRIEF.md
- PROOF.json
- AUDIT_SUMMARY.md
- AUDITOR_A_REPORT.md (Claude Sonnet 4.6)
- AUDITOR_B_REPORT.md (Gemini 2.5 Pro)
- PAL_CHAIN.md
- Staged diff proof (FINAL_STATUS_PORCELAIN.txt, STAGED_DIFF_NAME_ONLY.md, STAGED_DIFF_STAT.md)

**Check**:
1. Design-only scope maintained?
2. No runtime routing?
3. Dual independent audit complete?
4. PAL chain status acceptable?
5. Staged diff proof real and clean?
6. No authority leaks?
7. Proof consistency maintained?

**Return**:
- verdict: ACCEPT_FOR_PR / ACCEPT_WITH_RISKS / NEEDS_REPAIR / BLOCKED
- reasoning
- required_fixes (if any)
- pr_readiness
- merge_readiness
