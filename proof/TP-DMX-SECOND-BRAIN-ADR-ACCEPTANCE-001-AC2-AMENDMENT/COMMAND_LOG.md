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
python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text
pre-commit run --from-ref origin/main --to-ref HEAD
git diff --check
```

The superseded pre-amendment acceptance branch `tp/DMX-SB-ADR-ACCEPTANCE-001` @ `19fa74faa9`
was inspected read-only and NOT modified, pushed, merged, rebased, or deleted.
