# COMMAND_LOG — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002

Executed 2026-08-13. Every command below was run in this session; nothing is reconstructed
from memory or copied from a prior packet.

## S0 — resolve the actual current origin/main

```bash
git fetch origin --prune
git rev-parse origin/main
# -> 75b4cfc581786a53445e412bfc8e25a6e0fdb978   == operator-stated merge commit. MA08_MAIN_SHA pinned.

git worktree add --detach <scratchpad>/sb-phaseb-main 75b4cfc581786a53445e412bfc8e25a6e0fdb978
git -C <clean> status --porcelain      # -> empty
```

Custody hashes computed at that SHA (`shasum -a 256`) over the Second Brain authority
directory, the candidate document, the AC#2 amendment records, the traceability matrix,
the FO-01 status file and receipt, the frozen clause inventory, the re-freeze receipt, the
coverage index, and the validator. Recorded verbatim in `01_INPUT_CUSTODY.md`.

## S1 — contract family, verified from clean main

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py
python3 scripts/governance/validate_second_brain_adr_contracts.py --json
# exit 0
# result           PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
# checks           94 total, 0 failed   (coverage_group PASS, fo01_group PASS)
# trailing lines   PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE / FO01_STALE_RECORD_RECONCILED

python3 -m pytest -q tests/governance/test_second_brain_adr_contracts.py
# 63 collected, 63 passed, exit 0
```

Coverage was then **recomputed independently** rather than read from
`CONTRACT_COVERAGE_RECEIPT.json`, which is a producer-authored file:

```python
# from ADR_CLAUSE_INVENTORY.json and schemas/second_brain/contracts/ADR_CONTRACT_COVERAGE.json
inventory clause ids              160
coverage entries                  160
coverage_status_counts            {'COVERED': 160}
duplicate clause ids in coverage  []
in inventory, not covered         []
covered, not in inventory         []
per-ADR inventory counts vs per-ADR contract decision_clauses counts   agree for all 10
```

## S2 — fresh MA-08 drift recheck

```bash
git merge-base --is-ancestor 72af781e42… 75b4cfc581…      # exit 0
git rev-list --count 72af781e42…..75b4cfc581…             # 94
git diff --shortstat 72af781e42…..75b4cfc581…             # 823 files, +144356, -2636

# three-segment decomposition, counts must sum to 94
git rev-list --count 72af781e42…..33d6c353…               # 22   segment A
git rev-list --count 33d6c353…..cfa4927a88                # 5    segment B
git rev-list --count cfa4927a88..75b4cfc581…              # 67   segment C     (22+5+67 = 94)

git diff --shortstat cfa4927a88..75b4cfc581…              # 239 files, +37015, -1210
git diff --name-status cfa4927a88..75b4cfc581… | grep -vE $'\t(proof/|docs/|task-packets/)'
```

Segment C classification was computed programmatically and the class counts were asserted
to sum to the actual file count (239). A table that does not sum reads as full coverage
while hiding a class, so the sum is checked rather than eyeballed.

Hard-gate evidence, gathered rather than asserted:

```bash
# "fourth canonical DB?" — the one added top-level compose name, checked for section
grep -n "conport_supervision_state" compose.yml
# line 45 under `volumes:`; line 278 mounted at /var/lib/conport-supervision  -> a VOLUME, not a DB

# per-section counts, recomputed at BOTH ends after audit round 1 found the first count mislabelled
git show 72af781e42…:compose.yml   # services 24, volumes 15, networks 1   (all 2-space keys 40)
git show 75b4cfc581…:compose.yml   # services 24, volumes 16, networks 1   (all 2-space keys 41)
# the original "41 services at base and at head" was the ALL-KEYS sum, and was not equal at both ends.
# See 02_MA08_DRIFT_RECHECK.md "Repair after independent audit round 1 (MF-1)".

# "task-promotion route enabled?"
grep -rln "task-promotion-request\|task_promotion" src/ services/     # -> no matches

# segment C exclusions, each verified as zero rather than assumed
git diff --name-only cfa4927a88..75b4cfc581… -- compose.yml                        # 0
git diff --name-only cfa4927a88..75b4cfc581… -- config/ai/model-routing.policy.yaml # 0
git diff --name-only cfa4927a88..75b4cfc581… -- docs/90-adr/                        # 0
git diff --name-only cfa4927a88..75b4cfc581… -- docs/03-reference/architecture/second-brain/authority/  # 0

# segment A re-verification (not inherited)
git diff 72af781e42…..33d6c353… -- compose.yml | grep -E "^\+  [a-z0-9_-]+:"
git diff 72af781e42…..33d6c353… -- config/ai/model-routing.policy.yaml | grep "^+"
git diff 72af781e42…..33d6c353… -- services/dopecon-bridge/ | grep -E "^\+.*(@router|def )"
git diff cfa4927a88..75b4cfc581… -- src/dopemux/   # all four runtime files read in full
```

## S3 — freeze, then generate the audit prompt against the frozen head

```bash
git switch -c tp/DMX-SB-ADR-ACCEPTANCE-002        # cut from 75b4cfc581…
git add proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/ task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002.json
git diff --cached --check                          # clean
git commit                                         # -> 1939640e4d94159875543f1e0a22dba65032602f
git diff --name-only 75b4cfc581…..HEAD             # exactly the 4 packet files
git status --porcelain                             # empty
```

The prompt is authored **after** the freeze so it names the head it audits. A prompt
naming a stale head is a defect this series has already paid a round for.

## S4 — independent audit

```bash
git worktree add --detach /private/tmp/sb-accept-002-audit 1939640e4d…
git -C /private/tmp/sb-accept-002-audit diff --name-only 75b4cfc581…..HEAD   # the same 4 files

grok --cwd /private/tmp/sb-accept-002-audit -m grok-4.5 --always-approve \
     --max-turns 120 --output-format plain -p "$(cat …/AUDIT_PROMPT.md)"
```

`-m grok-4.5` is pinned explicitly. The CLI is 1.0.3 and its default has moved to
`grok-4.6`, which the trusted embedded-audit contract does not admit; an unpinned
invocation would have produced an unrepresentable audit.

Session metadata was snapshotted while the run was live rather than after it, because
`~/.grok` is mutable and the CLI has self-upgraded mid-task before:

```text
session id        019ffd2a-4777-7ac1-bc85-ff096f5479d6
current_model_id  grok-4.5          <- the pin took effect, confirmed from the runner's own record
head_commit       1939640e4d94159875543f1e0a22dba65032602f
cwd               /private/tmp/sb-accept-002-audit
reasoning_effort  high
runner            grok 1.0.3 (1a29d5bc12d4) [stable]
```

## S5 — worksheet and closure

See `04_ADR_DISPOSITION_WORKSHEET.md`, `PROOF.json`, `VALIDATION.json`, `HANDOFF.md`.

## Not run, and deliberately so

```text
git push                    NOT AUTHORIZED — branch stays local
gh pr create                NOT AUTHORIZED
gh pr merge                 NOT AUTHORIZED
any write under docs/03-reference/architecture/second-brain/**   FORBIDDEN this phase
any write under schemas/second_brain/**                          FORBIDDEN this phase
any write under proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001/**  FORBIDDEN — prior run's controlling bundle
any ADR disposition                                              OPERATOR_ONLY
```

Nothing was written to, checked out from, or rebased onto
`tp/DMX-SB-ADR-ACCEPTANCE-001` or its worktree. It was read once, read-only, to establish
that its ledger is the superseded attempt and not the controlling prior disposition.
