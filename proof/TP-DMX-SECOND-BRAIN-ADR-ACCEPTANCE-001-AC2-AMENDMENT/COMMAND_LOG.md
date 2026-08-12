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
#   ^^^ SUPERSEDED — INCOMPLETE FOR FINAL-SLICE COVERAGE. See "Final-slice re-run" below.
#   This run is preserved as historical evidence of what was actually executed at the time.
#   It is NOT deleted or back-dated. It predates commit 48098c8178, which added two L2
#   authority-metadata records, so its "same single L2 authority path" claim understates
#   the authority surface of the final slice.

pre-commit run --from-ref origin/main --to-ref HEAD   # 18 hooks, all Passed, no files modified
git diff --check                                       # clean
python3 scripts/audit/validate_audit_proof.py proof/.../PROOF.json   # 1/1 PASS (SKIPPED, truthful)
```

### Final-slice re-run — supersedes the `paths=11` record above

Raised by automated PR review (chatgpt-codex-connector, P2, "Re-run preflight after final
authority additions") and confirmed: the recorded `paths=11` run did not cover the final slice.
Re-run against the current PR comparison, actual verbatim result:

```bash
python3 scripts/governance/validate_change_contract.py \
  --base origin/main --head HEAD --format text
```

```text
status=PASS
max_lane=L2
model_audit_required=True
proof_only=False
paths=16
  [L2] docs/03-reference/architecture/second-brain/adr-candidates/ADR_CANDIDATE_AMENDMENT_HEAD.json
  [L2] docs/03-reference/architecture/second-brain/adr-candidates/ac2-acceptance-condition-amendment.json
  [L2] docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AC2_AMENDMENT_RECEIPT.json
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDITOR_REPORT.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDITOR_REPORT_AMENDMENT.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDITOR_REPORT_PR1214.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/C1_CONTENT_HEAD.txt
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/COMMAND_LOG.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/CONFLICT_NOTICE_CONCURRENT_ACCEPTANCE.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/GROK_AUDIT_ROUTE_CUSTODY.json
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/GROK_SCHEMA_REPRESENTATION_GAP.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/PROOF.json
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/SUPERSESSION_LINEAGE.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/source-base-second-brain-adr-candidates.md
  [L0] task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT.json
```

**Three L2 authority paths, not one — `paths=16`, not 11.** The two additional L2 records are
`ADR_CANDIDATE_AMENDMENT_HEAD.json` and `ac2-acceptance-condition-amendment.json`, added at
`48098c8178` after the earlier run.

`COMMAND_LOG.md` and the task packet were already in the changed-path set before this correction,
so recording it does not alter the set; the result above remains accurate for the head that
carries it. `max_lane` stays L2 and `model_audit_required` stays true — unchanged from the
earlier record.

Note this is the same coverage-lag defect that `PROOF.json` already discloses for the bound Grok
audit (`cc2f49ccad` predates `48098c8178`); it recurred here in the preflight record.

### S4 invariant validation is now executable — was a no-op

Also raised by automated PR review (P2, "Replace no-op invariant validation") and confirmed. The
task packet's S4 step — the central scope invariant — was recorded as:

```text
python3 - <<'PY'
# per-ADR section comparison + SB-DEC sequence + frontmatter
PY
```

A comment-only heredoc: it read nothing, compared nothing, and exited 0. Any change to forbidden
sections, frontmatter, statuses, or SB-DEC references would have satisfied it while the packet
claimed the invariant was verified.

Replaced with an executable byte round-trip check. It asserts both SHA-256 values, that the
pre-amendment AC#2 line occurs exactly 10x in the frozen base and 0x in the candidate (and the
converse for the amended text), and — the load-bearing part — that reversing exactly those ten
replacements reconstructs the frozen base **byte-for-byte**, with the forward direction
reproducing the candidate. Any edit anywhere else in the document breaks that equality.

The replacement was verified to actually fail, not merely to pass:

```text
control (unmodified tree)                         exit 0   S4 PASSED
flip one **Status:** PROPOSED -> ACCEPTED         exit 1   S4 FAILED (3 checks)
corrupt one SB-DEC reference                      exit 1   S4 FAILED (3 checks)
tamper frontmatter source_candidate_sha256        exit 1   S4 FAILED (3 checks)
reword one acceptance-condition line              exit 1   S4 FAILED (4 checks)
drop one of the ten AC#2 replacements             exit 1   S4 FAILED (5 checks)
```

Packet re-validated against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`:
**0 schema errors**.

## Auditor findings addressed on this PR

| Finding | Action |
|---|---|
| P1 missing repo-bound Task Packet | added `task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT.json` |
| P1 no canonical embedded-audit proof | added schema-valid `PROOF.json` (status SKIPPED, truthful) + canonical `AUDITOR_REPORT.md` |
| P1 amendment audit session-ID mismatch | **producer error, corrected**: `019fe94f-…` -> `019fe93a-d8a9-7673-b69c-966e64b44e86` |
| P2 preflight ran against an empty diff | recorded above as a false green and re-run against the committed head |

The superseded pre-amendment acceptance branch `tp/DMX-SB-ADR-ACCEPTANCE-001` @ `19fa74faa9`
was inspected read-only and NOT modified, pushed, merged, rebased, or deleted.
