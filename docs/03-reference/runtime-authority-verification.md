---
id: runtime_authority_verification
title: Runtime Authority Verification
type: reference
owner: '@hu3mann'
date: '2026-04-30'
prelude: Static runtime authority verification harness for Dopemux entrypoints, ports,
  wrappers, and known drift.
author: '@hu3mann'
last_review: '2026-04-30'
next_review: '2026-07-29'
---
# Runtime Authority Verification

## Purpose

`scripts/verify_runtime_authority.py` checks the static authority manifest at
`config/runtime_authority_manifest.json`.

The verifier supports runtime truth review. It does not replace runtime
execution, container startup, health probes, integration tests, or generated
artifact inspection.

## What Static Mode Checks

- Required runtime pointer files exist.
- Registry and compose port declarations match the manifest.
- Wrapper files still delegate to their expected targets.
- Forbidden legacy targets are not referenced from declared active launch files.
- Known drift is reported as expected conflict instead of silently normalized.

Static mode does not perform external network I/O and does not mutate
production state. When `repo_identity.require_identity_match` is enabled in the
manifest, the verifier may still invoke local `git` commands such as
`git remote get-url origin` to inspect repository identity. In that mode,
operators need `git` available and an `origin` remote configured in the
checkout, or they should disable the identity-match requirement in the
manifest for non-git environments.

## Authority Boundaries

Runtime code, config, and tests outrank generated docs. Generated and derived
truth docs are useful evidence, but the verifier intentionally checks active
code/config surfaces first.

Bridge, proxy, retrieval, and mirror services are not promoted to PM-plane
authority by this manifest:

- DopeconBridge remains an adapter/proxy/router layer.
- Dope-Context remains a retrieval/search surface.
- Dope-Memory remains a durable memory sink and mirror receipt surface, not PM
  status authority.
- ConPort conflict is reported rather than resolved because source-level and
  deployed runtime pointers still diverge.

## Commands

```bash
python3 -m json.tool config/runtime_authority_manifest.json
python3 -m pytest -q tests/unit/test_runtime_authority_manifest.py
python3 scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static
```

## Failure Handling

Unexpected missing required files are errors and produce a nonzero exit.

Expected conflicts are warnings. They mean the repo still contains known drift,
not that the verifier accepted the drift as resolved runtime truth.

If an `UNKNOWN` surface is added to the manifest, keep its validation advisory
and avoid asserting runtime authority until code/config evidence proves it.

## Proof Expectations

For manifest-only changes, proof requires JSON parsing and the unit test above.

For verifier logic changes, proof requires the unit test and a direct static
verifier invocation against the checked-in manifest.

For runtime entrypoint, port, or wrapper changes, static verification is only the
first proof layer. Follow it with the narrow runtime check for the touched
surface, such as a container start, service health check, CLI invocation, or
artifact-generation flow.
