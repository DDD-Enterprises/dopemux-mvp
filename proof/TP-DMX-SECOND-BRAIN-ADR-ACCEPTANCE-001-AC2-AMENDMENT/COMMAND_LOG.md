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
#   ^^^ SUPERSEDED — INCOMPLETE COVERAGE FOR ITS OWN SLICE. See the commit-bound receipts below.
#   This run is preserved as historical evidence of what was actually executed at the time.
#   It is NOT deleted or back-dated. It predates commit 48098c8178, which added two L2
#   authority-metadata records, so its "same single L2 authority path" claim understates
#   the authority surface of the final slice.

pre-commit run --from-ref origin/main --to-ref HEAD   # 18 hooks, all Passed, no files modified
#   ^^^ ACCURATE FOR ITS OWN SLICE, SUPERSEDED FOR FULL-SLICE COVERAGE.
#   Like the paths=11 preflight above, this ran before the later commits and therefore
#   covers fewer paths than the final slice. It is preserved, not rewritten. For the
#   full 19-path slice see PRE-COMMIT RECEIPT below. (Hook counts differ between the
#   two runs because pre-commit only executes hooks whose file filters match the paths
#   in range; a different slice legitimately runs a different number of hooks.)
git diff --check                                       # clean
python3 scripts/audit/validate_audit_proof.py proof/.../PROOF.json   # 1/1 PASS (SKIPPED, truthful)
```

### Preflight re-run at `764f1644d1` — supersedes the `paths=11` record above

> Retitled later. This section was originally headed *"Final-slice re-run — supersedes the
> `paths=11` record above"*. Only the title changed; the run recorded below is untouched, and it
> reproduces exactly at the commit now named in the title. The word *final* was the defect — see
> **Commit-bound preflight receipt** below.

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

### Commit-bound preflight receipt — target head `e10a79a32d`

Raised by automated PR review (chatgpt-codex-connector, P2, `COMMAND_LOG.md:78`) and confirmed:
the `paths=16` record above no longer covered the slice, because the round-4 commit `e10a79a32d`
added three audit-prompt custody artifacts. That is the same defect the `paths=16` record was
itself written to fix.

The cause is structural, not arithmetic. A receipt that calls itself *final* is invalidated by any
successor commit that adds a file, so replacing one number with another would only reproduce the
defect at the next commit. Receipts are therefore **bound to a named commit** from here on and
claim nothing about successors. The superseded records are kept in place rather than overwritten:
`paths=11` (pre-`48098c8178`) and `paths=16` (at `764f1644d1`) each remain accurate for the head
that carried them, and `paths=16` was re-confirmed by re-running the validator with `--head
764f1644d1`.

```text
COMMIT-BOUND PREFLIGHT RECEIPT

VALIDATED_TARGET_HEAD = e10a79a32db1f200cd36d75d6fb04a25fce12e30
BASE                  = 3e8fcc1c70c5b859dd651a1cd33c85eab837c93e   (origin/main at time of run)
STATUS                = PASS
MAX_LANE              = L2
MODEL_AUDIT_REQUIRED  = True
PATHS                 = 19
L2_AUTHORITY_PATHS    = 3

This result describes the PR slice at target head e10a79a32d. It supersedes earlier path-count
receipts for coverage of that target, but does not claim to be an immutable "final" result for
all future successor commits.
```

Command as run, with both endpoints pinned so it reproduces regardless of where `origin/main`
later moves (byte-identical to the same run expressed as `--base origin/main --head HEAD`):

```bash
python3 scripts/governance/validate_change_contract.py \
  --base 3e8fcc1c70c5b859dd651a1cd33c85eab837c93e \
  --head e10a79a32db1f200cd36d75d6fb04a25fce12e30 --format text
```

Verbatim result:

```text
status=PASS
max_lane=L2
model_audit_required=True
proof_only=False
paths=19
  [L2] docs/03-reference/architecture/second-brain/adr-candidates/ADR_CANDIDATE_AMENDMENT_HEAD.json
  [L2] docs/03-reference/architecture/second-brain/adr-candidates/ac2-acceptance-condition-amendment.json
  [L2] docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AC2_AMENDMENT_RECEIPT.json
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDITOR_REPORT.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDITOR_REPORT_AMENDMENT.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDITOR_REPORT_PR1214.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDIT_PROMPT_AMENDMENT.md
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDIT_PROMPT_CUSTODY.json
  [L0] proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/AUDIT_PROMPT_PR1214.md
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

**Successor commit.** The repair that adds this receipt modifies exactly two files —
`COMMAND_LOG.md` and `AUDIT_PROMPT_CUSTODY.json`. Both are already members of the 19-path set
above, so the successor commit changes bytes without changing path identities: `paths` stays 19,
`max_lane` stays L2, `model_audit_required` stays true. What this receipt measures is path-set
membership at a named commit, not the bytes of the files in it — which is what stops it
self-invalidating. The re-run at the successor head is reported on the PR review thread rather
than committed, so that recording the record does not itself require another record.

### Commit-bound pre-commit receipt — target head `27ba49b4fd`

Raised by automated PR review (chatgpt-codex-connector, P2, `COMMAND_LOG.md:57`) and confirmed:
the only pre-commit receipt in this log predates the later commits and therefore covers fewer
paths than the final slice. The hooks *were* run on the full slice; what was missing was the
record, not the run. It is recorded here against the head it actually names.

```text
PRE-COMMIT RECEIPT

BASE          = 3e8fcc1c70c5b859dd651a1cd33c85eab837c93e
TARGET_HEAD   = 27ba49b4fd0fa44aed90c31b790807ad66a1f4a6
PATH_SET      = 19
RESULT        = PASS
HOOKS         = 18 evaluated / 14 Passed / 4 Skipped (no files to check) / 0 Failed
FILES_MODIFIED = none

This receipt proves the full 19-path PR slice at the named target head. It does not claim
immutable finality for later successor commits.
```

Command as run, both endpoints pinned:

```bash
pre-commit run --from-ref 3e8fcc1c70c5b859dd651a1cd33c85eab837c93e \
               --to-ref 27ba49b4fd0fa44aed90c31b790807ad66a1f4a6
```

Eighteen hooks were evaluated: 14 reported `Passed`, 4 reported `Skipped (no files to check)`,
none Failed, and the tree was unchanged afterwards. The earlier `18 hooks, all Passed` record is
not contradicted — `pre-commit` evaluates only the hooks whose file filters match the paths in
range, and reports a hook with no matching files as `Skipped` rather than omitting it, so the same
18 hooks can legitimately tally differently across two different slices.

Re-verification at the successor head is reported on the PR review thread rather than committed,
for the same reason as the preflight receipt above: recording the record would itself require
another record.

### Class-closing repair — records bound to things that move or disappear

Round 6 of automated review raised four P2 findings which, on inspection, are one defect family:
**validation machinery depending on moving refs, on commits that do not survive a squash merge, or
on a non-root identity marker.** A sweep on that axis found two further instances the review had
not named. All are repaired together rather than one per round.

| Site | Was | Now |
|---|---|---|
| `repo_binding.repo_marker` | `dopetask-canonical-spec.json` — exists only under `docs/03-reference/spec/dopetask/`, so with `require_identity_match: true` it cannot identify the repository from its root | `.dopetaskroot`, the documented per-repo root marker (`docs/03-reference/fast-dev-os/template-task-packet.md:44`) |
| `S1` | asserted `origin/main` resolves to `cfa4927a…` — false as soon as main advanced | binds `FO01_REPAIR_BASE = cfa4927a883b469c06f37343c18e6582f23d1443` directly; the fetch is retained as freshness only and no value is asserted for `origin/main` |
| `S5.validation[0]` | audit binding stated against content head `cc2f49ccad…` | binding established by candidate-byte equality, plus a new executable check over committed bytes; `cc2f49ccad…` reclassified as a historical identifier |
| `S8.commands[2]` | `git diff cc2f49ccad…..HEAD` — unreachable after squash merge, fails with `unknown revision` rather than verifying anything | executable verifier over committed bytes (candidate hash, both authority records, ADR statuses, SB-DEC-026) |
| **`S7.commands` (not raised by review)** | `--base origin/main` in both the preflight and the pre-commit command — the packet-side twin of the two receipt defects above | pinned to `S7_BASE = 9dce8ffaec489f486d0356d300f0e8ea5aefa3d2` |
| **`commit.verify` (not raised by review)** | the same two moving-base forms, second occurrence in the same file | pinned to the same frozen execution base |

`--head HEAD` is deliberately **not** pinned anywhere in the packet's executable steps. The moving
input was the base; pinning the head instead would mean every successor commit invalidates the
step, which is the recursion the commit-bound receipts exist to stop. Both endpoints are pinned
only in *recorded receipts*, which describe a run that already happened.

Two identifiers are retained as historical metadata and are no longer execution dependencies:
`cc2f49ccad3d7c39d6b9f0a9fb044616069585a7` (content head of the historical Grok audit) and the
superseded acceptance attempt `19fa74faa9`. Neither needs to be reachable for any step to run.

Post-repair class check on the packet:

```text
grep -n 'origin/main' <packet>   -> 2 hits, both prose explaining why it is NOT an input
grep -n 'cc2f49cc'    <packet>   -> 2 hits, both labelled HISTORICAL IDENTIFIER
executable commands referencing a moving ref or a squash-unreachable commit: 0
schema validation against docs/03-reference/spec/dopetask/dopetask-canonical-spec.json: 0 errors
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
