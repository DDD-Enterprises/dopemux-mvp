# COMMAND_LOG — TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001

Packet: `TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001`
Program: `SECOND_BRAIN`
Repository: `DDD-Enterprises/dopemux-mvp`
Mode: `ARCHITECTURE_ACCEPTANCE_EVIDENCE_REPAIR`
Risk lane: `L2`

Every command below was executed. Outputs are transcribed from the real run.

---

## S0 — Fresh identity and drift preflight

```bash
git fetch origin --prune
git rev-parse origin/main
git status --short
git remote get-url origin
```

```text
origin            = https://github.com/DDD-Enterprises/dopemux-mvp.git
EXECUTION_MAIN    = 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
ISSUE_BASELINE    = 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
DRIFT             = NONE (EXECUTION_MAIN == ISSUE_BASELINE_MAIN)
```

Delta since the AC#2 merge (`dc279256fedf63c9a799c8eeea249c0a7fd83d14`) is a single
unrelated commit, inspected for Second Brain overlap:

```bash
git log --oneline dc279256fedf63c9a799c8eeea249c0a7fd83d14..6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
git diff --name-only dc279256fedf63c9a799c8eeea249c0a7fd83d14 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
```

```text
6153bd4fb3 fix(mcp): fail-closed resolver provenance + gate required-tool-glob enforcement (F018/F019)

28 paths, all under:
  proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/**
  proof/pr_merge/embedded-audit/pr-1226/**
  src/dopemux/mcp/{gate.py,resolver.py}
  task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.{json,md}
  tests/mcp/{test_discovery_gate_strict.py,test_resolver.py}

docs/03-reference/architecture/second-brain/**   0 paths
schemas/second_brain/**                          0 paths
proof/TP-DMX-SECOND-BRAIN-*/**                   0 paths

CLASSIFICATION = UNRELATED_REPOSITORY_MOVEMENT
VERDICT        = no BLOCKED_NEW_SECOND_BRAIN_DRIFT
```

Worktree created from the fresh baseline (not from the session's checked-out branch):

```bash
git worktree add -b tp/DMX-SB-ADR-CONTRACT-EVIDENCE-001 \
  /Users/hue/code/.worktrees/DMX-SB-ADR-CONTRACT-EVIDENCE-001 \
  6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
```

Frozen authority re-verified from repository bytes rather than carried from notes:

```bash
git show 6153bd4fb3:docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md | shasum -a 256
```

```text
e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c   == CANDIDATE_SHA256   PASS
375 lines
```

---

## S1 — Reproduce the current evidence gap

```bash
for t in LocalSpoolPort CustodyPort OpenLoopCandidate TaskProposal TaskPromotionRequest; do
  git grep -n -I "$t" -- .
done
git grep -n -I -i "project.identity.envelope" -- .
git grep -n -I -i "service.capability.receipt" -- .
ls schemas/
```

Emitted by the S1 generator (`proof/.../generators/gen_s1_s2.py`):

```text
S1: NO_SUFFICIENT_SECOND_BRAIN_MACHINE_CONTRACT_SET
    machine_contract_hits          = 0
    runtime_implementation_hits    = 0
    test_only_hits                 = 0
    prose_only_hits                = 29
    schemas/second_brain exists    = False
```

Every occurrence of every ADR-named type is narrative prose (`*.md`) or a free-form
explanatory string field inside a structured file (`traceability-matrix.json`
`semantic_relationship` / `decision_title`, `OPERATOR_DECISION_LEDGER.yaml` `title`).
Packet §3 excludes both from counting as machine contracts. `project identity envelope`
has **zero** hits in any form.

Artifact: `BASELINE_CONTRACT_INVENTORY.json`

---

## S2 — Freeze clause inventory BEFORE contract authoring

The denominator is derived from packet §5 mandatory coverage and bound to exact
fragments of the ratified candidate. Generation fails closed if any fragment is not a
verbatim substring of the candidate at `e4b28946…`.

```bash
python3 gen_s1_s2.py
```

```text
S2: 10 ADRs / 97 clauses
    ADR-SB-001:  6   sb_dec=['SB-DEC-001','SB-DEC-002','SB-DEC-027']
    ADR-SB-002:  8   sb_dec=['SB-DEC-003','SB-DEC-004','SB-DEC-005','SB-DEC-006']
    ADR-SB-003:  8   sb_dec=['SB-DEC-016','SB-DEC-017']
    ADR-SB-004:  7   sb_dec=['SB-DEC-010','SB-DEC-011','SB-DEC-012']
    ADR-SB-005:  9   sb_dec=['SB-DEC-018','SB-DEC-019']
    ADR-SB-006: 14   sb_dec=['SB-DEC-014','SB-DEC-015']
    ADR-SB-007: 11   sb_dec=['SB-DEC-019','SB-DEC-029']
    ADR-SB-008: 16   sb_dec=['SB-DEC-006','SB-DEC-007','SB-DEC-008','SB-DEC-030']
    ADR-SB-009:  8   sb_dec=['SB-DEC-009','SB-DEC-013','SB-DEC-022','SB-DEC-024']
    ADR-SB-010: 10   sb_dec=['SB-DEC-020','SB-DEC-021']
    total sb_dec references = 28          == SB_DEC_REFERENCE_COUNT   PASS
    SB-DEC-026 present in any ADR evidence list = False   (A_LEAVE_UNLINKED preserved)
```

**FROZEN DENOMINATOR**

```text
ADR_CLAUSE_INVENTORY.json
sha256 = f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288
clause_total = 97
```

This hash is frozen **in its own commit, before any contract artifact exists**. Git
history — not a self-asserted field — is what proves the freeze preceded authoring.
`ADR_CONTRACT_COVERAGE.json` must carry this exact value in `clause_inventory_sha256`,
and the deterministic validator enforces three-way agreement between the inventory
file's live hash, the coverage matrix's recorded hash, and every per-clause fragment
hash recomputed from the candidate.

---

## S3 — Author machine contracts

Generated from the frozen denominator, which is read and never re-derived — the
generator cannot widen or narrow the coverage denominator.

```bash
python3 gen_contracts.py
```

```text
S3: wrote 20 artifacts into schemas/second_brain/contracts/
    clause_inventory_sha256 = f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288
    clause_total            = 97
    coverage counts         = {'COVERED': 97, 'NOT_APPLICABLE_PROVEN': 0, 'MISSING': 0, 'AMBIGUOUS': 0}
```

Layer A: `adr-machine-contract.schema.json`, `interface-contract.schema.json`,
`ADR-SB-001..010.contract.json`. Layer B: `local-spool-port.contract.json`,
`custody-port.contract.json`, `open-loop-candidate.schema.json`,
`task-proposal.schema.json`, `task-promotion-request.schema.json`,
`project-identity-envelope.schema.json`, `service-capability-receipt.schema.json`.
Plus `ADR_CONTRACT_COVERAGE.json`.

`AMBIGUOUS` was never needed: no clause required an interpretation the candidate
does not state. `NOT_APPLICABLE_PROVEN` is used **zero** times — it is not a
shortcut taken anywhere in this packet.

---

## S4 — Deterministic validation and the false-green defence

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py
```

```text
checks: 113  failed: 0
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
FO01_STALE_RECORD_RECONCILED
```

A validator that only reports PASS on happy-path files proves nothing, so the
matrix runs the **real** validator against mutated repository copies:

```bash
python3 -m pytest -q tests/governance/test_second_brain_adr_contracts.py
```

```text
..............................................                           [100%]
46 passed
```

Matrix coverage against packet §9, with the guard each row exercises:

| §9 row | guard asserted |
|---|---|
| valid frozen contract set → PASS | exit 0, 113 checks, both groups PASS |
| delete one ADR contract | `A01-ten-adr-contracts-exist` |
| change candidate SHA binding | `A04-contracts-bind-candidate` |
| remove one coverage clause | `A08-every-clause-covered-once` |
| mark one clause MISSING | `A10-missing-zero` |
| point coverage at nonexistent rule | `A09-pointers-resolve` |
| corrupt one SB-DEC reference | `A07-sb-dec:ADR-SB-009` |
| change ADR status PROPOSED → ACCEPTED | `A16-ten-proposed`, `A18-no-accepted-token` |
| delete LocalSpoolPort contract | `A13-named-typed-artifacts-exist` |
| allow restricted spool without encryption | `S01-restricted-spool-requires-encryption` |
| give OpenLoopCandidate an assignee | `S02-open-loop-no-pm-properties` |
| enable TaskPromotionRequest by default | `S03-task-promotion-disabled` |
| allow UNKNOWN policy eligibility | `S04-unknown-eligibility-denies` |
| allow wrong-project write | `S05-envelope-denies-wrong-project` |
| raise UX visible queue max above 7 | `S06-visible-queue-max-7` |
| permit surprise write | `S07-no-surprise-writes` |
| claim denial fixtures implemented | `A15-no-denial-fixture-claim` + `A14` |

Beyond §9: mutated candidate document, coverage pointing at prose, rule
disagreeing with its clause, linking SB-DEC-026, deleting OpenLoopCandidate,
redefining the frozen denominator, forged source fragment, open-shaped
OpenLoopCandidate, dropped promotion proofs, confidential semantic indexing,
multi-project capture, >1 active capture project, non-zero searchable residual,
runtime-authority claim, port claiming implementation, Second Brain as authority
target, five FO-01 regressions, and four fail-closed cases (unparseable
contract, missing candidate, missing inventory, empty root, bad root → exit 2).

Two design points that make this matrix load-bearing rather than decorative:

1. **Each negative test asserts the specific guard responsible fires**, not
   merely `exit != 0`. Asserting only nonzero exit lets an unrelated check take
   the credit while the intended guard sits silently dead.
2. **Semantic mutations are applied consistently across inventory and
   contract.** Mutating one side only would trip the cross-file agreement guard
   and prove nothing about the semantic invariant. Mutating both sides is the
   real false-green attempt, and the hard-coded value invariants are what stop it.

One real defect was found and fixed by running this suite: the validator crashed
with an opaque traceback on a malformed clause node instead of reporting the
guard. It was still fail-closed (exit 2), but a crash discards the whole report,
so the affected passes were hardened to skip malformed nodes and still emit a
diagnostic.

---

## S5 — FO-01 stale-record reconciliation

Round-trip pre-check **for this specific file** before any mutation (a sibling
file in this tree does not round-trip, so one file's result licenses nothing
about another):

```text
round_trips_exactly = True
before sha256 = 0e0258e0dc3e524fc2a01e6b3f17875c3969d3266fd5e727c2ff03a84cf4fb3a
after  sha256 = bc2decd1eec9660c9889059cacf41e6ca3333f5cb809516dcb5b0b38e6c99687
```

Exact-string edits were used regardless, for minimality and auditability.

Group B of the validator failed 8/8 before the reconciliation and passes 8/8
after — the defect was reproduced by machine before it was repaired, not merely
asserted.

Semantic trap handled explicitly: `gates.adr_acceptance: "CLOSED"` means the
acceptance gate is **shut**, while §10's required "FO01 gate condition = CLOSED"
means the FO-01 **blocker** is closed. Opposite senses of one word. Neither
field was overloaded; eligibility went into separately named keys
(`fo01_gate_condition`, `adr_acceptance_gate_eligible`,
`other_adr_acceptance_conditions`) and the distinction is written into
`gate_field_semantics` in the file itself. `adr_acceptance_authorized` remains
`false` and `gates.adr_acceptance` remains `CLOSED`.

---

## S6 — Repository gates

```bash
git diff --check
```

```text
clean
```

```bash
python3 scripts/governance/validate_change_contract.py \
  --base 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac --head HEAD
```

```text
status=PASS
max_lane=L2
paths=29
```

The base is pinned to the frozen execution baseline; `--head` is deliberately
left unpinned, because pinning the head invalidates the step on every successor
commit — the exact recursion that commit-bound receipts exist to break. Both
endpoints are pinned only in recorded receipts, which describe a run that has
already happened.

```bash
python3 -c "<jsonschema validation of the packet against dopetask-canonical-spec.json>"
```

```text
S6 PASSED: task packet validates against dopetask-canonical-spec.json
```

First run of this gate FAILED with nine errors — `steps[].validation` must be an
array, not a string. Corrected and re-run.

```bash
pre-commit run --files $(git diff --name-only 6153bd4fb3 HEAD | tr '\n' ' ') \
  task-packets/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001.json
```

```text
18 hooks: 4 Passed / 14 Skipped
  Evidence-economy change-contract preflight ........ Passed
  Enforce markdown file locations for changed files . Passed
  Audit docs filename hygiene ....................... Passed
  Enforce repository root hygiene ................... Passed
```

The 14 skips were **verified, not assumed**: `trailing-whitespace`,
`end-of-file-fixer` and `markdownlint` are scoped by
`files: ^(docs/|task-packets/).*\.md$` and `check-yaml` by `^config/.*\.ya?ml$`;
this slice contains no matching file. pre-commit reports a hook with no matching
files as `Skipped` rather than omitting it, so a changed skip count is not by
itself a defect.

---

## S4 (continued) — a real false-green found by the producer, and closed

The §9 matrix passed 46/46, so I attacked the validator directly rather than
trusting that result. Group S pins ~37 of 97 clauses; the other ~60 have no pinned
semantic guard. The question is whether anything else stops them being weakened.

Attack: edit the inventory **and** the contract consistently, so cross-file
agreement still holds, and leave the cited source fragment untouched, so it remains
a genuine candidate substring with a matching hash.

```bash
# reroute ADR-SB-002-C01 canonical capture: Dope-Memory -> ConPort, on both sides
python3 scripts/governance/validate_second_brain_adr_contracts.py --repo-root /tmp/fg-probe
```

```text
checks: 113  failed: 0
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
```

**That is a real false-green.** The architecture decision "captured events go to
Dope-Memory" had been silently rerouted to a different canonical authority, and
every guard passed: the fragment check passed (fragment unchanged), the cross-file
agreement check passed (both sides edited), and `ConPort` is a legitimate member of
the closed authority set, so the A20 check passed too.

Fix — check **A21, value grounding**: for the rule classes where a silent swap does
the most damage, the machine value must itself appear in the decision text the
clause cites.

```text
AUTHORITY_TARGET / EQUALS    value must appear in the cited fragments
ENUM / SET_EQUALS            every member must appear
numeric bounds               digit or English number word must appear
```

Deliberately narrow: `SUPERSET_OF` is excluded because a contract may legitimately
normalise a term the prose abbreviates (`class` → `classification` in ADR-SB-006-C04),
and a grounding rule that is sometimes wrong is worse than none.

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py --repo-root /tmp/fg-probe --json
```

```text
result: FAIL | failed: 1
  A21-machine-values-grounded-in-cited-text
    ungrounded=["ADR-SB-002-C01: authority target 'ConPort' not in cited text"]
```

Six tests now cover this class, including `ADR-SB-009-C03` (max one active
automatic-capture project) and `ADR-SB-002-C07` (promotion receipt target), which
have **no** pinned Group-S guard and are caught by grounding alone.

Final: **114 checks / 0 failed; 52 adversarial tests / 0 failed.**

The lesson worth carrying: a green adversarial matrix proves the mutations you
thought of are caught. It says nothing about the ones you did not. The matrix had to
be attacked separately from the artifacts it guards.

---

## S7 — Independent audit: FAIL

Content head frozen at `7955ef33d7c0ab29daecbab966bc6a9497dc69ce` (C1).

Three audit routes failed before one worked. Each failure is recorded rather than
quietly retried:

| Route | Outcome |
|---|---|
| pal-stdio codereview / gemini-2.5-pro | `429 RESOURCE_EXHAUSTED`, `quota_limit_value: 0` |
| pal-stdio chat / gpt-5-pro | The pal MCP containers have **zero bind mounts** (`docker inspect ... .Mounts` is empty), so the server cannot read any host file; every `files[]` attachment resolved to nothing and the model kept asking for bytes it could never receive |
| opencode run / openrouter `~openai/gpt-latest` | Headless run auto-rejected its own bash permission request and terminated after 224 bytes with no verdict |

Working route — a throwaway detached worktree at C1, so the auditor could be granted
command approval with no possibility of touching the reviewed artifacts:

```bash
git worktree add --detach /private/tmp/sb-audit-c1 7955ef33d7c0ab29daecbab966bc6a9497dc69ce
grok --cwd /private/tmp/sb-audit-c1 --always-approve --max-turns 60 \
     --output-format plain -p "$(cat proof/.../AUDIT_PROMPT.md)"
```

```text
VERDICT: FAIL
BLOCKERS: 3
MUST_FIX: 5
```

The auditor independently detected that `AUDIT_PROMPT.md` names head `8a9b0ee53c`
while the tree it was given is `7955ef33d7` — a real discrepancy caused by the A21 fix
landing after the prompt was written. The prompt was **not** rewritten to match; it is
the artifact that was executed. The discrepancy is recorded in
`AUDIT_PROMPT_CUSTODY.json` instead.

### Producer re-verification of the blockers

Findings were re-derived from repository bytes rather than accepted on assertion.

```bash
grep -c "dopeTask" docs/.../second-brain-adr-candidates.md
```

```text
0        # B2 confirmed: `dopeTask` is in the task packet's own boundary list,
         # not in the ratified candidate. It should never have entered
         # AUTHORITY_TARGETS as a canonical write target.
```

```bash
# B3: drop PURGE from the deletion-operation set and Review from the UX set,
# consistently on both sides
python3 scripts/governance/validate_second_brain_adr_contracts.py --repo-root /tmp/fg-probe3
```

```text
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
         # B3 confirmed: A21's membership test is one-way. It rejects enum
         # WIDENING (a new member is not in the cited text) but accepts enum
         # SHRINKING, because every surviving member is still present.
```

```bash
# B1 residual: invert recall fusion to the explicitly REJECTED vector-first
# alternative, and flip the review default to auto-apply
python3 scripts/governance/validate_second_brain_adr_contracts.py --repo-root /tmp/fg-probe2
```

```text
checks: 114  failed: 0
         # B1 residual confirmed: A21 narrowed the bilateral-edit class but did
         # not close it. Normalised tokens (ORDERING lists, FAIL_CLOSED and
         # CONSTANT strings) cannot be grounded in prose, so ~75 of 97 clauses
         # have neither a Group-S pin nor A21 grounding.
```

**No finding is disputed.** The controlling verdict is FAIL, so the packet's terminal
state is `BLOCKED_INDEPENDENT_AUDIT`. Publication does not progress and the PR is not
marked ready.

### Stale-assertion sweep (class-level, not instance-level)

```bash
git grep -nE '\b113\b|\b46\b|FO01_STALE_RECONCILED' -- task-packets/... proof/...
```

Two stale assertions found in the committed packet — `113 checks` and `46/46`, both
superseded by the A21 fix, plus the token `FO01_STALE_RECONCILED` where the validator
actually emits `FO01_STALE_RECORD_RECONCILED`. All corrected in one pass; the packet
still validates against `dopetask-canonical-spec.json`. Classified
`NON_SUBSTANTIVE_RECORD_MAINTENANCE`: the corrected text asserts nothing the receipts
did not already record, and the packet JSON is not among the files the auditor read.

### Post-C1 mutation boundary

Everything committed after C1 is producer record *about* the audited content, never
audited content. Verified mechanically:

```bash
git diff 7955ef33d7c0ab29daecbab966bc6a9497dc69ce..HEAD --name-only
```

All paths fall under `proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/**` and
`task-packets/**`. Nothing under `schemas/`, `scripts/`, `tests/` or `docs/` moved, so
`C1_CONTENT_HEAD.txt` remains `7955ef33d7` and the audit binding stays valid. This is
what prevents an audit → commit → re-audit carousel.

---

## S6 (re-run) — embedded-audit representation gap

Once `PROOF.json` existed, the change-contract preflight and the pre-commit proof
hook began requiring a top-level `embedded_audit` block. Adding one truthfully is
impossible for this audit route, and the reason is worth recording precisely.

`schemas/proof/embedded_audit.schema.json` is strictly binary:

```text
status == SKIPPED   -> auditor_tool MUST be "none", auditor_model MUST be "unknown",
                       invocation null, exit_code null, skip_reason a string
status != SKIPPED   -> auditor_tool MUST NOT be "none", auditor_model MUST NOT be
                       "unknown", invocation a string, exit_code an integer,
                       skip_reason null
```

`auditor_tool` enumerates `[agy, antigravity, claude-code-cli, copilot-cli,
gemini-cli, pal-mcp-clink, none]` and `auditor_model` enumerates `[sonnet,
claude-sonnet-4.6, opus, gemini, gemini-3.1-pro-high, unknown]`. **Neither can name
the grok CLI that actually ran.** So the only two representable options are:

1. `status: SKIPPED` with `none`/`unknown` — falsely asserts no audit happened, which
   would hide a FAIL verdict behind an apparently un-audited packet. The worst
   available falsehood.
2. `status: FAIL` with a tool and model picked from the enum — fabricating an auditor
   identity, which packet §19 explicitly forbids.

Neither is truthful, so neither was used. The block records `status: "FAIL"` (true and
representable), keeps the honest fallback values for the two fields the schema cannot
express, and states the limitation in `skip_reason`. The gate consequently reports:

```text
status=FAIL
  - [error] proof_schema_fail: auditor_model 'unknown' should not be valid under
    {'const': 'unknown'}; auditor_tool 'none' should not be valid under
    {'const': 'none'}; skip_reason ... is not of type 'null'
```

**Three error strings, one cause.** Everything else in the block validates: the eight
findings were converted to the schema's `finding` object shape (`id`, `severity`,
`title`, `status`, `body`) and are accepted.

This is the same representation gap recorded in the predecessor bundle
(`GROK_SCHEMA_REPRESENTATION_GAP.md`), except that the escape used there —
`auditor_tool: none` with a non-SKIPPED status — has since been closed by the
`allOf` conditionals. Repairing the schema is **explicitly out of scope**: packet §1
forbids embedded-audit platform repair. It is recorded here and left for the operator.

Note the direction of the error: the gate fails because the packet refuses to
overstate its audit. A packet that fabricated `auditor_tool: claude-code-cli` would
have passed this gate while lying about who audited it.

### Gate results at the final head

```text
git diff --check                          PASS
validate_second_brain_adr_contracts.py    PASS  (114 checks, 0 failed)
pytest tests/governance/...               PASS  (52 passed)
dopeTask packet schema validation         PASS
validate_change_contract.py               FAIL  (embedded-audit representation gap only)
pre-commit (changed slice)                FAIL  (same single cause, same file)
independent audit                         FAIL  (3 blockers, 5 must-fix) <- controlling
```

---

# ROUND 2 — operator-authorized denominator re-freeze and class-level repair

Round 1's terminal verdict was `BLOCKED_INDEPENDENT_AUDIT`. On 2026-08-12 the
operator authorized re-freezing the coverage denominator and repairing all three
blockers and all five must-fix classes in one wave, and required a fresh
independent audit at `PASS / 0 / 0`. The ruling is reproduced verbatim in
`DENOMINATOR_REFREEZE_RECEIPT.json`.

## C0_REFREEZE — denominator only

The operator's freeze sequence forbids touching contracts or the validator in this
commit, so the census generator writes denominator artifacts and nothing else.

```bash
$ python3 gen_c0.py
clause_total       160  (was 97)
new_inventory_sha  b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439
added 63  removed 0  modified 86  unchanged 11
  ADR-SB-001    11
  ADR-SB-002    14
  ADR-SB-003    13
  ADR-SB-004    11
  ADR-SB-005    14
  ADR-SB-006    17
  ADR-SB-007    17
  ADR-SB-008    36
  ADR-SB-009    12
  ADR-SB-010    15
```

The generator fails closed before writing anything: every fragment must be a
verbatim substring of the candidate **and** fall inside its own ADR's Context /
Proposed decision / Consequences span, every closed set must equal the
tokenization of its verbatim `source_enumeration`, and the six omissions the
auditor named by hand are looked up by subject and must be present.

Two implementation notes worth recording because both were real defects caught in
the loop rather than in review:

- The generator originally read the superseded inventory from the worktree — the
  same path it writes. On a second run it therefore compared the new denominator
  against itself and reported `added 63 removed 63 modified 0`. It now reads the
  predecessor from `git show <freeze-commit>:<path>` and refuses to proceed unless
  that content hashes to the sha256 the operator's ruling names.
- The tokenizer must try `", and "` before `","`, or `"Archive, Forget, and Purge"`
  yields `["Archive", "Forget", "and Purge"]`.

```bash
$ git commit   # 3e0d89815c
$ git show --stat --name-only 3e0d89815c | grep -c '^schemas/'
0
```

Zero contract files in the freeze commit. That is the ordering evidence; a hash
recorded next to the artifacts would prove nothing.

## Contract regeneration

```bash
$ python3 gen_contracts2.py
inventory sha256  b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439
clauses           160
artifacts written 20
```

Every property name, enum member and const string in the seven Layer B artifacts
is bound in `x-grounding` to a clause and a verbatim candidate phrase, and the
generator refuses to emit a binding whose phrase is not a substring of that
clause's fragments. Several names therefore read as candidate prose rather than as
conventional API names — `leantime_plus_task_orchestrator_proof` instead of
`leantime_proof_ref` — which is the point: each one is traceable to the sentence
that authorises it.

What was deleted, and why it was invention:

```text
LocalSpoolPort.operations   admit / append / flush / expire / participate_in_purge
CustodyPort.operations      put / verify_integrity / residual_scan /
                            backup_eligibility / tombstone
OpenLoopCandidate           candidate_id, project_id, detected_at,
                            source_event_ref, summary, confidence,
                            evidence_refs, canonicality, loop_state enum
TaskProposal                proposal_id, proposed_at, title, rationale,
                            proposal_state enum, a PM-forbid list MA-06 does
                            not place on proposals
TaskPromotionRequest        request_id, requested_at, disposition enum,
                            approved_digest_sha256
ProjectIdentityEnvelope     envelope_id, registry_ref, issued_at, expires_at,
                            CURRENT_DIRECTORY as a rejected identity source
ServiceCapabilityReceipt    service, resolved_identity, capabilities,
                            issued_at, expires_at, freshness_state enum,
                            unknown_capability_disposition
```

`CURRENT_DIRECTORY` is the instructive one: it is verbatim candidate text, but only
from ADR-SB-009's *rejected alternatives*. The accepted Context sentence enumerates
exactly three sources. That is what check A23 now exists to catch generally.

## Validator

```bash
$ python3 scripts/governance/validate_second_brain_adr_contracts.py
  checks: 94  failed: 0
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
FO01_STALE_RECORD_RECONCILED
```

Two crashes were found by the adversarial suite and fixed, both of the same class
as a defect fixed in round 1: an exception discards the whole report, so a
mutation surfaces as an opaque exit 2 instead of as the finding it is.

- A coverage pointer aimed at prose resolves to a string; `rule.get(...)` then
  raised `AttributeError`.
- A clause removed from the inventory but still listed in the coverage matrix
  raised `KeyError`.

Both are now reported as findings.

## Adversarial suite and the operator's false-green matrix

```bash
$ python3 -m pytest tests/governance/test_second_brain_adr_contracts.py -q
...............................................................          [100%]
63 passed
```

```bash
$ python3 gen_false_green.py
  FAILED_AS_INTENDED         inventory + contract bilateral change
  FAILED_AS_INTENDED         authority-first -> vector-first
  FAILED_AS_INTENDED         DEFER/NO MUTATION -> auto-apply
  FAILED_AS_INTENDED         drop PURGE from a closed set
  FAILED_AS_INTENDED         drop Review from UX operations
  FAILED_AS_INTENDED         add dopeTask as canonical authority
  FAILED_AS_INTENDED         add cloud_offload to CustodyPort
  FAILED_AS_INTENDED         invent unsupported schema enum/property
  FAILED_AS_INTENDED         remove each newly-added MUST_FIX-1 denominator clause
  FAILED_AS_INTENDED         alter FO-01 receipt-derived field
  FAILED_AS_INTENDED         test_m09b_removed_clause_survives_a_repin
  CONTROL_PASSES             test_repinned_pristine_still_passes

all_rows_held: True
```

Each row asserts a **named** guard, not merely a nonzero exit, so an unrelated
parse error cannot take credit. Rows 9 and 10 are loops over all 63 added clauses
and all 39 projected FO-01 fields respectively — the operator's matrix says
"each", so nothing is sampled and nothing is capped.

Half the rows run in **repinned** mode: the test rewrites `FROZEN_INVENTORY_SHA256`
inside a copy of the validator *and* the supersession receipt, so the freeze no
longer objects and only the semantic guards can catch the mutation. Without that
mode the pin would absorb every mutation and the S-group pins could be dead code
without anyone noticing — which is close to how BLOCKER 1 survived round 1.
`test_repinned_pristine_still_passes` is the control: an unmutated repin must
still pass, or every repinned row would be failing for the wrong reason.

## Round-2 gate results at the final head

Re-executed against the round-2 tree, not carried forward from round 1.

```text
git diff --check                          PASS
validate_second_brain_adr_contracts.py    PASS  (94 checks, 0 failed)
pytest tests/governance/...               PASS  (63 passed)
FALSE_GREEN_MATRIX                        PASS  (10/10 rows failed as intended)
dopeTask packet schema validation         PASS  (after round-2 counts applied)
validate_change_contract.py               FAIL  (embedded-audit representation gap only)
pre-commit (changed slice)                FAIL  (same single cause, same file)
independent audit                         PENDING <- controlling
```

The change-contract and pre-commit failures name one hook and one cause:

```text
proof-embedded-audit-schema
  - auditor_model: 'unknown' should not be valid under {'const': 'unknown'}
  - auditor_tool: 'none' should not be valid under {'const': 'none'}
  - skip_reason: '...' is not of type 'null'
```

Three error strings, one cause, unchanged from round 1: the schema is strictly
binary, and its enums cannot name the auditor that actually ran. Packet §1 places
embedded-audit platform repair out of lane and the operator's round-2
authorization did not add it, so the gap is recorded and the gate is left red.
A PASS from the independent audit will not turn these two gates green.

Note the direction of the failure: the gate fails because the bundle refuses to
overstate its audit. A bundle claiming `auditor_tool: claude-code-cli` would pass
this gate while lying about who audited it.

The `Skipped` pre-commit hooks are scoped by file filter to `docs/*.md` and
similar paths this slice does not touch. Those are the hook config's own filters,
not suppressed failures.

## What is deliberately NOT claimed

The round-1 audit artifacts — `AUDITOR_REPORT.md`, `AUDIT_PROMPT.md`,
`AUDIT_PROMPT_CUSTODY.json` — are untouched. They are the controlling evidence for
why round 2 was required, and the operator directed that they stay as written.
Round-2 audit artifacts take new filenames rather than overwriting them.

`PROOF.json`'s `embedded_audit` block still records the round-1 run, because that
is the last embedded audit that actually happened; `independent_audit.round_2` is
`PENDING`. Rewriting the block to look current would claim an audit of this head
that has not been performed.
