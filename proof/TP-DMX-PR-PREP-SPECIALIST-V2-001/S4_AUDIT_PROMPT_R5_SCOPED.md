You are an INDEPENDENT L2 auditor for a docs-governance repair packet in the
dopemux-mvp repository. You are a separate CLI process and model family
(Gemini) from the implementer (Claude Sonnet). Verify independently by
reading files and running commands yourself in the current working
directory: /Users/hue/code/dopemux-mvp, branch
feat/pr-prep-specialist-v2-contract (already checked out).

## Packet under audi

TP-DMX-PR-PREP-SPECIALIST-V2-001, round R5 (SCOPED re-audit). PR #1224,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1224, base main, head
(merge commit, UNCHANGED from the initial R5 audit)
a89c11dbfd9d132797575118f3f7b8c4f819a2ab.

## Why this scoped re-audit exists

An initial R5 audit (see
proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AGY_AUDIT_RAW_R5_INITIAL.txt)
returned FAIL solely because its scope item 2 required a WHOLE-REPOSITORY
conflict-marker scan, and found real, pre-existing, unresolved git conflic
markers in files entirely unrelated to this packet (e.g.
docs/pr_merge/usage-patterns.md, docs/planes/pm/write-boundaries.md,
docs/planes/pm/pm-implementation-ledger.md). That FAIL is preserved as
historical evidence, unaltered, and is NOT being overwritten by this audit.

The operator has ruled (see
proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDIT_R5_SCOPE_ADJUDICATION.md) tha
this finding is out of scope for this packet: the markers were
deterministically proven byte-identical on BOTH parents of the R5 merge
commit (88c3cc73cdcd7c5373beae41a17c5c8a1c76f56c and
6626aa9a58dd82e62226cfca63498cc3f711bb75) before the merge, trace to an
unrelated 2026-03-30 commit, and sit entirely outside this packet's owned
paths. This scoped re-audit re-verifies the SAME merge commi
(a89c11dbfd9d132797575118f3f7b8c4f819a2ab, unchanged, no content edit) bu
restricts the conflict-marker check to this packet's own audit universe
instead of the whole tree.

IMPORTANT GOVERNING INSTRUCTION FOR THIS AUDIT:

Pre-existing defects outside the Task Packet scope are not blocking findings
unless the candidate introduces, modifies, depends upon, or materially worsens them.

Known pre-existing repository conflict-marker debt has been deterministically
proven identical on both C1-R5 parents and outside this packet's changed paths.
You may record it as a non-blocking PREEXISTING_REPO_DEBT risk, but must no
convert unrelated whole-tree hygiene into this packet's acceptance gate.

## Required audit scope -- verify each independently

1. **Merge is a real, non-fast-forward merge commit.** Run
   `git log --pretty=%P -1 a89c11dbfd9d132797575118f3f7b8c4f819a2ab` and
   confirm two parent hashes: `88c3cc73cdcd7c5373beae41a17c5c8a1c76f56c`
   (old branch head) and `6626aa9a58dd82e62226cfca63498cc3f711bb75` (main a
   merge time). Confirm this is not a rebase or squash.

2. **The #1224 delta relative to current main.** Run
   `git diff 6626aa9a58dd82e62226cfca63498cc3f711bb75..a89c11dbfd9d132797575118f3f7b8c4f819a2ab --stat`
   and confirm the changes are exactly this packet's owned content (docs
   under docs/03-reference/pr-pipeline/prep/**, docs/pr_prep/**,
   tests/governance/test_pr_prep_contract_v2.py,
   task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.*, and this packet's own
   proof/ directories) -- i.e. this IS the R4-audited content, now sitting
   on top of current main.

3. **Files actually touched by the R5 merge resolution, if any.** Since
   this was a clean merge (no conflicts requiring manual resolution --
   confirm via `git log -1 --format=%B a89c11dbfd9d132797575118f3f7b8c4f819a2ab`
   showing a standard `Merge remote-tracking branch` message with no
   conflict-resolution note), confirm there are no merge-resolution-only
   edits to audit beyond the two parent trees combining automatically.

4. **Packet-owned canonical/compatibility/governance surfaces.** Run
   `git diff 6f32ac97dfd64f4386182fdd24380b2817551303..a89c11dbfd9d132797575118f3f7b8c4f819a2ab -- docs/03-reference/pr-pipeline docs/pr_prep tests/governance/test_pr_prep_contract_v2.py task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.md`
   (6f32ac97df = the R4 content head, already independently audited PASS)
   and confirm EMPTY output -- these owned surfaces are byte-identical to
   the already-audited R4 state; the merge changed nothing here.

5. **Conflict-marker scan restricted to the packet's own audit universe**
   (NOT the whole repository tree). Run:
   ```
   git diff --name-only 6626aa9a58dd82e62226cfca63498cc3f711bb75..a89c11dbfd9d132797575118f3f7b8c4f819a2ab |
     grep -E '^(docs/03-reference/pr-pipeline/prep/|docs/pr_prep/|tests/governance/test_pr_prep_contract_v2\.py|task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001|proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/|proof/pr_merge/embedded-audit/pr-1224/)' |
     xargs -I{} git grep -nE '^(<<<<<<<|=======|>>>>>>>)' -- {} 2>/dev/null
   ```
   Confirm zero real hits within this restricted universe. (You do not need
   to re-scan or re-report on the whole-tree markers already documented in
   the initial R5 audit -- those are out of scope here by supervisor
   ruling; if you happen to notice them, you may note them as a
   non-blocking PREEXISTING_REPO_DEBT risk, not a blocking finding.)

6. **Terminal semantic census.** Confirm branch-owned files are byte-
   identical to R4 content head 6f32ac97dfd64f4386182fdd24380b2817551303
   (already covered by step 4) -- ACTIVE_CONTRADICTION_COUNT remains 0 per
   proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/LEGACY_SEMANTICS_SCAN_R4.md,
   unaffected by the merge.

7. **Governance tests pass post-merge.** Run
   `python -m pytest tests/governance/test_pr_prep_contract_v2.py tests/governance/`
   and confirm all pass (expect 69 passed single-file, 92 passed full
   governance directory).

8. **Task packet still schema-valid.** Run
   ```
   python3 -c "
   import sys; sys.path.insert(0, 'src')
   from dopemux.orchestrator.validation.packets import validate_packet_file
   print(validate_packet_file('task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json'))
   "
   ```
   and confirm status=PASS, 0 errors.

9. **The known pre-existing docs-prohibited-patterns false positive is
   resolved.** Run
   `pre-commit run --files docs/pr_prep/adapters/vibe/template-agent.md`
   and confirm the "Block prohibited documentation patterns" hook PASSES.

10. **origin/main drift remains compatible.** Run
    `git fetch --prune origin` then
    `git rev-list --left-right --count HEAD...origin/main` and confirm 0
    behind.

11. **Overall coherence within scope.** Is R5, WITHIN THIS PACKET'S OWNED
    AUDIT UNIVERSE, genuinely just "R4's already-audited content plus an
    unrelated, non-conflicting slice of main, combined via a real merge
    commit, with zero semantic change to this packet's docs, tests, or
    task-packet content, and zero packet-scoped conflict markers"? State
    your verdict plainly. A blocking finding requires an issue WITHIN this
    packet's owned audit universe (items 2, 4, 5-restricted, 6-9) -- no
    the whole-tree conflict-marker debt already ruled out of scope.

## Required output forma

Produce a verdict: PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR. Lis
findings per numbered scope item, noting what you executed vs. took on
faith. If you record the pre-existing whole-tree conflict-marker debt a
all, label it explicitly as PREEXISTING_REPO_DEBT / non-blocking, per the
governing instruction above.
