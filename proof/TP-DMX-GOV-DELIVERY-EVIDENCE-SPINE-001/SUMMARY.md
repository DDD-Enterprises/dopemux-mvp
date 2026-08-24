# TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001 — Proof Summary

```text
PACKET_ID=TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001
RISK_LANE=L2_MATERIAL
BASE_SHA=d40e43dd70307d2c000a4efd581be7c11248728c
CONTENT_HEAD=8c309d764a55896c3363bd803404f64d4e277185
CONTENT_TREE=89bec5999f8ba750851225484f99489c9ffa0d9b
CHANGED_FILES=21
DIFF=4817 insertions, 0 deletions

VALIDATION_STATUS=PASS
GOV_AUD_F1=PASS
AUDIT_VERDICT=NOT_RUN
PR_STEWARD_READINESS=NOT_RUN
PROOF_ONLY_EQUIVALENCE=NOT_REQUIRED
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO
```

These four are recorded separately and are never collapsed into a single PASS:
`VALIDATION_STATUS`, `AUDIT_VERDICT`, `PR_STEWARD_READINESS`, `MERGE_AUTHORITY`.

## What landed

Seven versioned schemas, six pure Python modules, six test modules, a contract
document and the packet JSON. The change is **purely additive** — 4817
insertions and zero deletions — and the package imports **stdlib only**, so no
existing owner's behaviour or test suite is implicated.

## GOV-AUD-F1 — the blocking acceptance requirement

The independent architecture audit's attack: a proof bundle's known-risks,
unknowns and evidence-ref list live *inside* an allowed proof-only path and are
consumed downstream by PR Steward and the operator merge card, so hand-editing
them passes every path and digest conjunct while laundering a governance change
past re-audit. A path allowlist is necessary but not sufficient.

The evaluator answers this in two parts. Classification is **total and
fail-closed** — a broad governance substring net over the full dotted path
first, a tight exact-name inert allowlist over the leaf second, and anything
remaining is `UNKNOWN` and rejected. Governance fields are then compared as a
**path-independent aggregate**, so byte-identical relocation passes while
semantic drift fails regardless of which file carries it.

All eight verbatim conjuncts from architecture section 08 are implemented. All
ten mandatory negative fixtures and three mandatory positive fixtures are present
and passing.

### A HIGH-severity defect was found and fixed before freeze

Adversarial probing during the PAL codereview workflow found a real bypass of
this very requirement. `aggregate_fields` had synthesised a disambiguation key
`field#document` that shared a namespace with real field names, making it
**forgeable**:

```text
audited   = {"A": {"known_risks": ["R1"]}, "B": {"known_risks": ["R2"]}}
successor = {"A": {"known_risks": ["R1"], "known_risks#B": ["R2"]},
             "B": {"known_risks": ["R1"]}}
```

Both produced an identical aggregate and the evaluator returned **PASS** — while
document B had silently dropped risk R2. That is the F1 laundering channel
reopened by a crafted field name, and hand-editing the bundle is precisely the F1
threat model.

Fixed by replacing the synthesised namespace with a per-field **sorted multiset**
of values, so a dropped value changes the multiset and no crafted name can
restore it. Five regression fixtures cover the forgery; the mandated relocation
fixture still passes.

Eighteen adversarial probes were run in total. One bypassed — the forgery above,
now fixed. The other seventeen fail closed.

## Source-fidelity corrections

Two divergences from the architecture package were found by reading the source
directly and corrected before freeze:

1. Added the eighth conjunct `raw_diff_contains_no_substantive_source_change`,
   which section 08 states explicitly but the implementation had only implied.
2. Reordered posture precedence so `BLOCKED` outranks `DECISION_REQUIRED`, per
   section 02's stated reduction. The initial implementation had them inverted.

## Custody: a contamination incident, contained

Two research subagents spawned by this session wrote implementation files into
the worktree despite explicit read-only extraction instructions. They were
detected mid-session, identified via `ListAgents` (both still running at eleven
minutes for sub-minute tasks, with implementation intent in their final output),
and stopped.

**Nothing was ever committed from the contaminated state.** The entire content
head was rebuilt single-author from the clean base after deleting every
contaminated file. A residue check returns zero occurrences of the rejected fork
signatures (`require_known_consumer`, `NOT_INDEPENDENT`, permissive `v[0-9]+`
schema_version patterns, `gate_ledger_id`), and all seven schemas use fail-closed
`const` schema versions — the fork design had weakened these to a permissive
regex that would have *accepted* unknown major versions, the opposite of what
packet §8.1 requires.

This is recorded in full deliberately: an auditor inspecting session artifacts
could otherwise encounter traces, and their omission would read as concealment.

## Authorized scope deviation

`tests/unit/governed_delivery/__init__.py` is not on the packet's §6 allowlist but
was **operator-authorized** after the packet's `PATH_REMAP_REQUIRED` stop was
surfaced. Without it, the mandated `test_models.py` collides with the existing
`tests/repository_planner/test_models.py` and breaks collection for the entire
repository suite — verified empirically. It is an empty test-infrastructure file
matching existing repo convention.

## What is NOT established

- **`AUDIT_VERDICT=NOT_RUN`.** Content is frozen and ready for one independent L2
  audit. The implementer has not and must not self-audit. The auditor route
  identity is an operator input.
- **PAL expert-model validation is `NOT_RUN`.** All three configured providers
  failed — gpt-5-pro (no credits), gemini-2.5-pro (region quota 0), grok-4.5
  (could not access the changeset). The adversarial findings above are
  self-derived and independently unvalidated. This is recorded as NOT_RUN and is
  never collapsed into PASS.
- **`PR_STEWARD_READINESS=NOT_RUN`**, **`MERGE_AUTHORIZED=NO`**,
  **`ACTIVATION_AUTHORIZED=NO`**.

## Remaining risks

The classification tables are checked-in data needing deliberate extension as
real bundles introduce new field names; the failure mode is a false rejection,
never a laundered change. Content *exchanged* between two documents that both
remain in the bundle preserves the path-independent aggregate and passes — a
documented boundary following necessarily from the relocation fixture the packet
mandates. A leaf literally named `checksum` is inert, as that same fixture set
requires. `GOV-AUD-F2` and `GOV-AUD-F3` are deferred by the packet to G2 and are
untouched here.

## Next action

`OPERATOR_MERGE_DECISION` is **not** yet reachable. The next step is an
independent L2 final content audit against the frozen head above.
