# Implementation Notes

## P0 package donor

Schema donor approach used: the frozen P0 identity/sharing contract was published as
design-only schemas and references without changing current runtime. The frozen external
implementation plan remains provenance/input evidence and is not published into the repo
by P0 (this packet publishes only the ADR, topology, falsification reference, and schemas).

## R1 bounded repair (P0-R1)

One bounded substantive repair within the existing packet (REPAIR_CLASS=ONE_BOUNDED_SUBSTANTIVE_REPAIR). No new packet, no recursion.

R1 repairs:
- P0-R1-01 R2 falsification binding: repository YAML frontmatter kept;
  post-frontmatter payload is byte-identical to R2 `04_FALSIFICATION_CONTRACT.md`;
  test hashes the frontmatter-stripped payload against the ratified digest.
  `REPO_DOC_FULL_FILE_HASH != R2_SUBJECT_HASH because repo frontmatter is required`;
  `R2_PAYLOAD_AFTER_FRONTMATTER_SHA256 = 84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb`;
  `R2_ARCHITECTURE_SEMANTICS_CHANGED = NO`.
- P0-R1-02 invalid repository plan location: `docs/superpowers/plans/...` file deleted and
  removed from packet allowlist/expected-files/mkdir instructions. No replacement repo path added.
- P0-R1-03 fleet-catalog-v2 closed schema vocabulary; legacy `scope`/`state_scope`/`port_policy`/
  `multi_project_singleton` rejected; negative fixtures prove garbage and legacy values rejected.
- P0-R1-04 service-topology enforces frozen R2 vocabulary: services_count=26, four ratified classes,
  CURRENT_CLASS/TARGET_CLASS/DISPOSITION closed; exact R2 topology JSON validates unmodified.
- P0-R1-05 ownership classification closed to OWNED/FOREIGN/AMBIGUOUS/UNKNOWN; non-OWNED forces
  mutation_eligible=false; OWNED+eligible requires registry+lease+probe+storage verified.
- P0-R1-06 service-lease-v2 fully specified to the frozen P0 fields; closed endpoint and
  owner_runtime_identity objects; scope conditions enforced; paths/hashes/labels not authority.
- P0-R1-07 runner-materialization-receipt fully specified (PROVENANCE_ONLY; digest fields 64 hex;
  strict_mode forbids UNKNOWN inherited surface).
- P0-R1-08 project-event-envelope fully specified to frozen contract; transport contract only.
- P0-R1-09 resolved-execution-identity fail-closed: mutable_routing_allowed required globally,
  UNKNOWN/CONFLICTING forces false, VERIFIED requires canonical fields, aliases closed
  role=EVIDENCE_ONLY, nested authority-shaped alias fields rejected.
- P0-R1-10 fresh independent L2 audit with full review bundle and schema-valid proof.
- P0-R1-11 CI rerun and PR metadata update.
- P0-R1-12 execution-gate timing disclosure.

## Execution-gate timing disclosure (P0-R1-12)

```text
INITIAL_EXECUTION_GATE_TIMING=PRE_AUTHORIZATION
CLASSIFICATION=GOVERNANCE_PROCESS_DEFECT
RUNTIME_OR_PRODUCTION_EFFECT=NONE_OBSERVED
MERGE_EFFECT=NONE
CURRENT_REPAIR_EXECUTION_AUTHORITY=EXPLICIT_OPERATOR_P0_AUTHORIZATION_NOW_PRESENT
RETROACTIVE_AUTHORIZATION_CLAIM=NO
```

The initial implementation/PR creation completed before the explicit
`AUTHORIZE_DMX_MCP_MULTIPROJECT_P0_EXECUTION=YES` declaration was supplied. This is recorded as a
governance process defect with no runtime or production effect and no merge effect. No history
rewrite. The existing branch is repaired under the now-present explicit operator P0 authorization.
