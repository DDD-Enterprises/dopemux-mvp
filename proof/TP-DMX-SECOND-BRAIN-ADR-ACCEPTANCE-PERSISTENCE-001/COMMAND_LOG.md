# COMMAND_LOG — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001

Executed 2026-08-14/15. Persists the operator's ten ACCEPT dispositions. Nothing here is
reconstructed from memory.

## S0 — re-verify the base, then read the constraints from source

```bash
git fetch origin --prune && git rev-parse origin/main
# -> 75b4cfc581786a53445e412bfc8e25a6e0fdb978  == MA08_MAIN_SHA, UNMOVED.
#    The Phase B MA-08 result therefore still binds and no delta addendum was needed.
```

The validator was read before anything was written, because two obvious ways to persist
acceptance would have turned its green gate red:

```bash
grep -nE "A34|A35|A36|A37|B05|B06|B07|FORBIDDEN_TRUTHY|PINNED" \
     scripts/governance/validate_second_brain_adr_contracts.py
grep -c "90-adr" scripts/governance/validate_second_brain_adr_contracts.py     # -> 0
```

Full analysis in `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/05_ACCEPTANCE_PERSISTENCE_CONSTRAINTS.md`.
The operative fact is the last line: the validator does not read `docs/90-adr/` at all, so
acceptance can be persisted there additively.

## S1 — generate the ten accepted records

```bash
python3 proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/generators/gen_accepted_adrs.py
# exit 0; ten files emitted, each verified after writing:
#   carried_body_is_candidate_substring  true
#   carries_amended_ac2                  true
#   carries_superseded_ac2               false
```

The generator refuses to run unless the candidate hash matches `e4b28946…`, the amended AC#2
appears exactly ten times, the pre-amendment wording appears nowhere, and the candidate is
still `CANDIDATE`. Those four guards are what stop the superseded attempt's wording from
reaching an accepted record.

Slug rule, applied to all ten without exception: lowercase, every run of non-alphanumerics
becomes one hyphen, trim. The superseded attempt hand-shortened ADR-SB-009's slug; one rule
removes that discretion.

```bash
pre-commit run --files docs/90-adr/adr-sb-*.md
# frontmatter guard, knowledge-graph schema, prohibited patterns, prelude <=100 tokens,
# markdown location, placement hygiene, filename hygiene, markdownlint: all Passed, first run
```

## S2 — index rows and acceptance records

```bash
python3 proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/generators/gen_acceptance_records.py
# first run:  index_rows_added 10, total 23
# second run: index_rows_added 0   <- idempotent, never double-appends
```

## S3 — prove it was additive, then freeze

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py --json
# PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE  94 checks  0 failed
# -- the same numbers as before persistence, which is the point

python3 -m pytest -q tests/governance/test_second_brain_adr_contracts.py     # 63/63, exit 0
```

Allowlist coverage and the read-only boundary were checked programmatically, not by eye:

```text
changed paths since MA08_MAIN_SHA   42
uncovered by any allowlist           0
read-only surfaces touched           0
```

The read-only set asserted against: the candidate document, `fo-01-repair-status.json`,
`traceability-matrix.json`, `FO01_RESOLUTION_RECEIPT.json`, `R2_AUDITOR_IDENTITY_RECONCILIATION.json`,
`schemas/second_brain/**`, `scripts/governance/validate_second_brain_adr_contracts.py`, and
`docs/03-reference/architecture/second-brain/authority/**`.

```bash
git commit    # -> 5f9f38acd465ea9a30df0a6251b6e4960704f5cc   (frozen persistence head)
```

## S4 — independent audit

The audit prompt is authored **after** the freeze so it names the head it audits.

**A first attempt was started and deliberately stopped ~30 seconds in.** Its prompt told the
auditor to diff the disposition worksheet against head `f7326b18397a4381df88ec4dc933eeb3f0011288`
— but the worksheet does not exist at that head. It was first committed at `fa48fcd201`,
because the operator's own sequence put the worksheet *after* the Phase B audit. Running an
audit against an instruction naming a head where the file does not exist is the same
stale-head defect this series has already paid a round for, so the round was killed rather
than allowed to produce findings from a false premise.

```bash
pkill -f sb-persist-audit          # stopped at 106 bytes of output, no verdict produced
```

The prompt was corrected to name `fa48fcd201`, and to state plainly that the worksheet was
never covered by the Phase B audit and must be treated as unaudited claims to check. The
round was then re-run from a fresh worktree:

```bash
git worktree add --detach /private/tmp/sb-persist-audit-r1 5f9f38acd4…
grok --cwd /private/tmp/sb-persist-audit-r1 -m grok-4.5 --always-approve \
     --max-turns 120 --output-format plain -p "$(cat …/AUDIT_PROMPT.md)"
```

`-m grok-4.5` pinned explicitly; the CLI default is `grok-4.6`, which the trusted
embedded-audit contract does not admit.

## Not run, and deliberately so

```text
git push / gh pr create / gh pr merge     NOT AUTHORIZED
Slice 0 or any implementation             NOT AUTHORIZED
denial fixtures                           FORBIDDEN by this packet
any edit to the candidate, the FO-01 records, the contracts, or the validator   FORBIDDEN
any edit to fo-01-repair-status.json to hide the staleness this persistence creates
                                          FORBIDDEN — declared instead
```
