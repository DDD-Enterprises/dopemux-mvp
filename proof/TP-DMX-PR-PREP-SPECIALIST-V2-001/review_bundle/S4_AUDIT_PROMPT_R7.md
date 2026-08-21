You are an INDEPENDENT L2 auditor for a docs-governance repair packet in the
dopemux-mvp repository. You are a separate CLI process and model family
(Gemini) from the implementer (Claude Sonnet). Verify independently by
reading files and running commands yourself in the current working
directory: /Users/hue/code/dopemux-mvp, branch
feat/pr-prep-specialist-v2-contract (already checked out).

## Packet under audi

TP-DMX-PR-PREP-SPECIALIST-V2-001, round R7 (compatible-drift closure
only). PR #1224, https://github.com/DDD-Enterprises/dopemux-mvp/pull/1224,
base main, head (merge commit) 488e6b89773255ac08b915a2bc6ba6e489a33ce2.

## Why R7 exists, and what it is NOT

R6 (commit f4fa9c2555cec4e1f40fc736c71609e55ecdb804, the R6 signed proof
head) was already independently audited PASS and reached
READY_FOR_OPERATOR_MERGE_DECISION. Since then, `main` advanced 16 commits
(base f0a0e839b456eab05aa6b3592fdebb31c488fa5b -> tip
75b4cfc581786a53445e412bfc8e25a6e0fdb978), entirely Second Brain ADR
contract/evidence work with ZERO path overlap with this packet's owned
surfaces (verified before merging: 58 files touched by main, 0 overlap
with the 105 files this branch has changed). The operator authorized a
narrow "R7 drift closure": merge current main with a normal merge commit,
verify nothing PR-Prep-owned changed, and re-verify the deterministic
gates -- NOT a new semantic repair round, NOT a re-audit of R1-R6
substance.

**Scope discipline: do NOT re-audit R1-R6 history or re-derive the R6
census from scratch. Your job is narrower: confirm the R7 merge is iner
with respect to this packet's content, and that everything R6 already
established remains true post-merge.**

## Required audit scope -- verify each independently

1. **Merge is a real, non-fast-forward merge commit.** Run
   `git log --pretty=%P -1 488e6b89773255ac08b915a2bc6ba6e489a33ce2` and
   confirm two parents: `f4fa9c2555cec4e1f40fc736c71609e55ecdb804` (R6
   head) and `75b4cfc581786a53445e412bfc8e25a6e0fdb978` (main at merge
   time).

2. **R6 substantive PR-Prep content is byte-unchanged.** Run
   `git diff --exit-code f4fa9c2555cec4e1f40fc736c71609e55ecdb804..488e6b89773255ac08b915a2bc6ba6e489a33ce2 -- docs/03-reference/pr-pipeline/prep docs/pr_prep docs/pr_merge tests/governance/test_pr_prep_contract_v2.py task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.md proof/TP-DMX-PR-PREP-SPECIALIST-V2-001 proof/pr_merge/embedded-audit/pr-1224`
   and confirm EMPTY output (exit 0). This is the core claim of R7: main's
   drift touched none of this.

3. **No new authority collision.** Run
   `git diff f4fa9c2555cec4e1f40fc736c71609e55ecdb804..75b4cfc581786a53445e412bfc8e25a6e0fdb978 --stat`
   (main's own drift) and confirm every changed path is under
   `docs/03-reference/architecture/second-brain/`, `schemas/second_brain/`,
   `proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/`,
   `scripts/governance/validate_second_brain_adr_contracts.py`,
   `task-packets/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001.json`, or
   `tests/governance/test_second_brain_adr_contracts.py` -- i.e. entirely
   disjoint from this packet's PR-Prep authority tree. Also confirm no
   changes to `schemas/proof/embedded_audit.schema.json` or
   `scripts/audit/local_audit_acceptance.py` (the embedded-audit trus
   machinery) in this drift.

4. **No unresolved conflict markers anywhere in the tree touched by this
   merge.** Run
   `git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- docs/03-reference/pr-pipeline/prep docs/pr_prep tests/governance/test_pr_prep_contract_v2.py task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json`
   and confirm no hits. (Do not scan the whole repository -- known
   pre-existing whole-tree conflict-marker debt outside this packet was
   already ruled out of scope at R5 and is not this audit's concern.)

5. **Semantic census remains clean post-merge.** Run a search for
   `TP-PRPS-000`, live checkmarked/bold `7-step`/`IMPLEMENTED AND
   COMPLIANT` claims across
   `docs/03-reference/pr-pipeline/prep/adapters/**` and
   `docs/pr_prep/adapters/**` and confirm every hit remains inside
   retrospective prose ("previously claimed...retired"), same as R6 lef
   it.

6. **Compatibility links still resolve.** Run your own link-resolution
   check across `docs/pr_prep/**` (non-archive) and confirm 0 broken
   links.

7. **Governance tests pass.** Run
   `python -m pytest tests/governance/test_pr_prep_contract_v2.py tests/governance/`
   and confirm the PR-Prep-specific file still shows 134 passed (unchanged
   from R6) and the full governance directory passes (a higher count than
   R6's 157 is expected and fine, since main's merge added
   `test_second_brain_adr_contracts.py` -- that is out of this packet's
   scope, just confirm nothing FAILS).

8. **Task packet still schema-valid.** Run
   ```
   python3 -c "
   import sys; sys.path.insert(0, 'src')
   from dopemux.orchestrator.validation.packets import validate_packet_file
   print(validate_packet_file('task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json'))
   "
   ```
   confirm status=PASS, 0 errors.

9. **origin/main drift.** Run `git fetch --prune origin` then
   `git rev-list --left-right --count HEAD...origin/main` and confirm 0
   behind.

10. **Overall coherence.** Is R7 genuinely just "R6's already-audited
    content, unchanged, merged with an unrelated, non-conflicting slice of
    main (Second Brain work), via a real merge commit, with zero semantic
    change to this packet's docs, tests, task-packet, or proof content"?
    State your verdict plainly. A blocking finding requires an ACTUAL
    change to this packet's owned content or a genuine new conflict --
    not the mere existence of unrelated main drift.

## Required output forma

Produce a verdict: PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR. Lis
findings per numbered scope item, noting what you executed vs. took on
faith.
