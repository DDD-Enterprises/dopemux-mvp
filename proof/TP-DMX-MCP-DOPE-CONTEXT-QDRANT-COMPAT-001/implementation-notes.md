# Implementation notes

## Change

- Removed unused `SearchRequest` import from `dense_search.py`.
- Added subprocess-isolated real-Qdrant-SDK import regression.
- Preserved dependency policy, lockfile, Compose, Dockerfile, provider execution, foreign services, and Task Orchestrator.

## Content identity

- Base: `c7bc2fb479d7386825df73e028acdce723ee3388`
- Content commit: `8d88cc3e7f0fea65c5d5b878c3813a5a81eff356`
- Content tree: `8e06364d311371224aa4b3c74fc007bff446e86c`
- Packet/RTK-normalized diff SHA-256: `5dee0a6410608cdf310c1370941a778c8ccd3d5755ef1a438aef09b705ea7ad9`
- Raw Git patch SHA-256: `665dacc300b00b4c88b78f1efcc962ac2295f05f40493392d72b2bea7ae1e64c`

## Verification

- Focused locked SDK: `13 passed, 1 skipped`.
- Focused Qdrant 1.19.0: `13 passed, 1 skipped`.
- Full service suite: `116 passed, 2 skipped, 1 xfailed`.
- Changed-file pre-commit, diff check, changed-contract, packet schema, and Gitleaks: PASS.
- Image build/import: PASS.
- Runtime health/MCP/workspace: PASS after bounded mount correction.
- Independent AGY/Claude final audit: `PASS_WITH_RISKS`.

## Deviations and corrections

- First focused-test invocation omitted packet-required `PYTHONPATH`; result was invocation FAIL, then exact command passed.
- First dope-context recreation used worktree-relative data/log binds. Only dope-context was recreated again with primary project directory and `--no-build`; final binds match original.
- Auditor raw diff hash exposed RTK normalization domain mismatch. Both hashes retained; no packet rewrite or re-audit.

## Remaining risk

- Diff hash domain ambiguity HIGH/OPEN.
- A1/A2/A3 exact separate source text `UNKNOWN`.
- Credential equality and provider-attested model identity `UNKNOWN`.
- PR, CI, and PR Steward `NOT_RUN` until publication step.
