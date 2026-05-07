# OPEN_PR_COCKPIT_IMPACT_MATRIX — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

Cockpit-relevant open PRs only. Non-Cockpit open PRs are summarized in `OPEN_PR_AUDIT.md`.

| PR | Class | Runtime files | Tests | Packet JSON | INDEX.md | Proof | Blocks design pickup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #572 | OPEN_STACKED (governance artifact) | none | adds `test_merge_stack_artifacts.py` | adds MERGE-STACK-CONSOLIDATE-001 | edits | adds merge-stack proof tree | YES |
| #573 | OPEN_RELEVANT (runtime surface) | modifies pre-existing `runtime_contract.py` | modifies 2 pre-existing cockpit unit test files | adds RUNTIME-CONTRACT-FIDELITY-001 | edits | adds runtime-contract-fidelity proof tree | YES |

## Drift between #572 and #573

PR #572 was opened to audit the readiness of PRs 568–571 for stack consolidation. PR #573 was opened to repair runtime-contract gaps and introduces a new file under `src/dopemux/ui/cockpit/`. Neither PR references the other. The artifact in PR #572 therefore does **not** cover PR #573, even though both branches base on `pack/cockpit-pack-remediate-006-ia` and both attempt to feed downstream consolidation work.

**Consequence**: the merge-stack consolidation artifact in PR #572 cannot be treated as a complete readiness verdict for everything currently open against the pack branch. Any operator-initiated consolidation of pack into main must regenerate the consolidation artifact with PR #573 included, or PR #573 must land into pack first and PR #572 must be refreshed.

## Governance preservation per open PR

| PR | safe_for_claude_design | READY_FOR_CLAUDE_DESIGN | Claude Design upload | T4 remote mutation | Canonical writes | Runtime reclassification |
| --- | --- | --- | --- | --- | --- | --- |
| #572 | preserved as `NO` | `not approved` | none performed | none performed | none performed | none performed |
| #573 | preserved as `NO` | `not approved` | none performed | none performed | none performed | none performed |

## Non-actions

- no PR merges performed by this packet
- no PR retargets performed by this packet
- no PR edits performed by this packet
- no PR closes performed by this packet
