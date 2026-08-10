# COMMAND_LOG — AC#2 acceptance-condition amendment

```bash
# custody
git fetch origin main; git rev-parse origin/main     # cfa4927a883b469c06f37343c18e6582f23d1443
git show origin/main:docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md \
  | shasum -a 256                                     # 946054a4… == FO-01 receipt value
grep -c "Machine contracts and denial fixtures parse and cover the decision\." <base>   # 10

# amendment (pure line substitution, 10x)
python3  # src.replace(OLD, NEW); assert count==10; assert OLD not in out

# falsifiable byte-delta test (002A lesson)
# predicted 10 x (391-69) = 3220 ; observed len(amended)-len(base) = 3220  -> PURE_LINE_REPLACEMENT
# round-trip: base.replace(OLD,NEW)==amended AND amended.replace(NEW,OLD)==base  -> both True

# invariants (all True)
#   Context / Proposed decision / Consequences / Rejected alternatives /
#   Evidence and traceability sections byte-identical across all 10 ADRs
#   SB-DEC reference sequence identical (28 tokens); frontmatter identical
#   10x **Status:** `PROPOSED`; token ACCEPTED absent; line count 375 -> 375

# independent audit (fresh session, read-only, no producer history)
~/.grok/bin/grok -m grok-4.5 --effort high --prompt-file AUDIT_PROMPT_AMENDMENT.md \
  --permission-mode auto --deny Write --deny Edit --deny MultiEdit --deny NotebookEdit \
  --output-format json --max-turns 120
# -> PASS_ADR_ACCEPTANCE_CONDITION_AMENDMENT ; 0 BLOCKER ; 0 MUST_FIX ; 1 nonblocking

# worktree (not the primary checkout)
git worktree add -b tp/DMX-SB-AC2-AMENDMENT /Users/hue/code/.worktrees/DMX-SB-AC2-AMENDMENT cfa4927a88
cp <amended> docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
shasum -a 256 <target>   # e4b28946… == audited amended hash

# preflight (AGENTS.md §4 step 10)
#
# FIRST RUN WAS A FALSE GREEN — recorded, not hidden.
# It executed while the worktree was still at origin/main with the amended file only
# copied (uncommitted), so `git diff --name-only <base>...<head>` saw an EMPTY diff:
python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text
#   status=PASS  max_lane=L0  model_audit_required=False  paths=0     <-- checked NOTHING
#
# paths=0 is the tell. Re-run AFTER committing, against a head that actually contains
# the change:
python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text
#   status=PASS  max_lane=L2  model_audit_required=True   paths=7
#   [L2] docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
#   [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/*  (6 files)
#
# and again on the proof-only successor:
#   status=PASS  paths=11  (same single L2 authority path, 10 x L0 proof)

pre-commit run --from-ref origin/main --to-ref HEAD   # 18 hooks, all Passed, no files modified
git diff --check                                       # clean
python3 scripts/audit/validate_audit_proof.py proof/.../PROOF.json   # 1/1 PASS (SKIPPED, truthful)
```

## Auditor findings addressed on this PR

| Finding | Action |
|---|---|
| P1 missing repo-bound Task Packet | added `task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT.json` |
| P1 no canonical embedded-audit proof | added schema-valid `PROOF.json` (status SKIPPED, truthful) + canonical `AUDITOR_REPORT.md` |
| P1 amendment audit session-ID mismatch | **producer error, corrected**: `019fe94f-…` -> `019fe93a-d8a9-7673-b69c-966e64b44e86` |
| P2 preflight ran against an empty diff | recorded above as a false green and re-run against the committed head |

The superseded pre-amendment acceptance branch `tp/DMX-SB-ADR-ACCEPTANCE-001` @ `19fa74faa9`
was inspected read-only and NOT modified, pushed, merged, rebased, or deleted.
