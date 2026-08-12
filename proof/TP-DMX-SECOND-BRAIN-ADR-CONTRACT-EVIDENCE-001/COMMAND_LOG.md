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
