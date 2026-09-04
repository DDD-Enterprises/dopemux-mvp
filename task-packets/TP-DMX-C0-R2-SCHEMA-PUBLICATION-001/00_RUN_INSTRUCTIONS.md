# TP-DMX-C0-R2-SCHEMA-PUBLICATION-001 — Deterministic C0-R2 schema publication

## Current observed state at issuance

```text
C0_R2_SOURCE_SHA256=a9d51a5b19170589cff38fee951fd611436e65711af4a8bbfcff4084ab884c19

PR_1283_HEAD=bc7d96d539dac82c23caf67850742196dcc550c5
PR_1283_STATE=OPEN
PR_1283_MERGED=NO
PR_1283_MERGEABLE=YES

OBSERVED_MAIN=04be55535d1582c304cf31a02923fb9c521ab547

DISPATCHABLE_NOW=NO
```

These PR/main facts are volatile and MUST be reharvested at execution.

## Hard admission

Do not touch the repository until BOTH are true:

```text
1. C0-R2 exact operator ratification record is signed and custody-verified.
2. PR #1283 is merged and current main is reharvested after that merge.
```

If either is false:

```text
STOP
REPOSITORY_MUTATION=0
```

## Publication source

Use the exact frozen C0-R2 package:

```text
TP-UAG-C0-DCP-UAG-DOPETASK-AUTHORITY-INTERFACE-FREEZE-001-R2
SHA256=a9d51a5b19170589cff38fee951fd611436e65711af4a8bbfcff4084ab884c19
```

Source schema files:

- `schemas/common_defs.schema.json`
- `schemas/dcp_route_authorization.schema.json`
- `schemas/uag_transport_request.schema.json`
- `schemas/uag_transport_result.schema.json`
- `schemas/model_transport_receipt.schema.json`
- `schemas/tool_intent.schema.json`
- `schemas/macro_execution_authority_ref_v2.schema.json`
- `schemas/dopetask_governed_execution_profile.schema.json`
- `schemas/governed_execution_receipt.schema.json`
- `schemas/uag_compatibility_certification.schema.json`

The repair/freeze package may place the schema directory under its subject root. Resolve source paths from its manifest rather than guessing.

## Destination

Canonical repository destination:

```text
dopemux-mvp/schemas/dcp/
```

plus deterministic registration in:

```text
schemas/dcp/manifest.json
```

Do not publish dopeTask mirrors in this packet.

## Lane

```text
L0_DETERMINISTIC
MODEL_AUDIT=NOT_REQUIRED
```

This L0 classification is valid only while:
- schema bytes are exact copies;
- manifest change is registration-only;
- no `$id`, `$ref`, authority, schema meaning, runtime wiring, loader semantics, or version semantics change.

Any semantic deviation escalates and STOPS this packet.

## Required final return

```text
FINAL_STATUS=
C0_R2_RATIFICATION=
PR1283_MERGED=
PR1283_MERGE_COMMIT=
POST_MERGE_MAIN_SHA=
POST_MERGE_MAIN_TREE=

SOURCE_SCHEMA_COUNT=10
PUBLISHED_SCHEMA_COUNT=
BYTE_IDENTICAL_COUNT=
CONFLICTING_DESTINATIONS=
MANIFEST_ONLY_SEMANTIC_CHANGE=NO

DRAFT7_VALIDATION=
REF_CLOSURE=
FOCUSED_TESTS=
COMPLETE_RELEVANT_SUITE=
PRECOMMIT=
DIFF_CHECK=
SECRET_SCAN=

PR_NUMBER=
PR_HEAD=

MODEL_AUDIT=NOT_REQUIRED
IMPLEMENTATION_AUTHORIZED=NO
RUNTIME_INTEGRATION_AUTHORIZED=NO
DOPETASK_RELEASE_AUTHORIZED=NO
PIN_UPDATE_AUTHORIZED=NO
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO

NEXT_GATE=
```
