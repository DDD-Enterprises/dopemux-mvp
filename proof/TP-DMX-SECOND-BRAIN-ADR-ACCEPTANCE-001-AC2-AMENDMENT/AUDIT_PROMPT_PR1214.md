You are an INDEPENDENT, READ-ONLY auditor. Fresh session, no producer history. You are NOT the
producer. Reproduce claims with your own commands; do not fix anything.

# Target: PR #1214, exact head

```
repo      = DDD-Enterprises/dopemux-mvp
worktree  = /Users/hue/code/.worktrees/DMX-SB-AC2-AMENDMENT
PR        = 1214
head_sha  = cc2f49ccad3d7c39d6b9f0a9fb044616069585a7
base      = cfa4927a883b469c06f37343c18e6582f23d1443
```

This is an L3-adjacent authority-document change: a narrow amendment to acceptance condition #2
across ADR-SB-001..010 in
`docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md`,
plus a proof bundle. It accepts no ADR.

# Verify at the exact head

1. `git -C <worktree> rev-parse HEAD` == `cc2f49ccad3d7c39d6b9f0a9fb044616069585a7`.
2. `git diff cfa4927a883b469c06f37343c18e6582f23d1443..HEAD --stat` — enumerate every changed
   path. Confirm the ONLY non-proof change is the ADR candidate document.
3. The ADR candidate change is EXACTLY 10 substitutions of the AC#2 bullet and nothing else.
   Recompute: lines removed, lines added, line count before/after, and the byte delta versus the
   prediction `10 * (len(new_line) - len(old_line))`.
4. Byte hashes: base blob `946054a4675271856e0214dbf1ce0aa9b1ec17e71e79a82711ad3ca0d9df9c22`,
   amended `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c`.
5. Nothing forbidden changed: for all ten ADRs, Context / Proposed decision / Consequences /
   Rejected alternatives / Evidence and traceability byte-identical; SB-DEC reference sequence
   identical (28 tokens); YAML frontmatter identical.
6. No ADR promoted: ten `**Status:** \`PROPOSED\``; document `status: CANDIDATE`; token
   `ACCEPTED` absent from the candidate document.
7. The new AC#2 wording does not create a runtime/production/enablement loophole.
8. The proof bundle under `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/` is
   internally consistent with the change and does not overclaim. In particular check that
   `SUPERSESSION_LINEAGE.md` does not allege fabrication against the superseded attempt and
   correctly records that its operator provenance was genuine.
9. Confirm the change authorizes no implementation execution and mutates no runtime.
10. Confirm this branch does NOT modify, push, merge, or rebase
    `tp/DMX-SB-ADR-ACCEPTANCE-001` @ `19fa74faa9`.

# Verdict
One of: PASS, PASS_WITH_RISKS, FAIL, NEEDS_SUPERVISOR.
State BLOCKER / MUST_FIX counts. Be adversarial and specific. If you cannot verify something,
say NOT_VERIFIED rather than assuming.
