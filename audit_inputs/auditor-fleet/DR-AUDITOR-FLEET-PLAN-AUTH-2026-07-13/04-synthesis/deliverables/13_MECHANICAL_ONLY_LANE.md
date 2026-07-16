# Mechanical-Only Lane

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `13_MECHANICAL_ONLY_LANE.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Status

`OBSERVED` Mechanical validation is the only currently observed usable execution lane.

`PROPOSED` Treat it as a first-class audit route with a strict authority registry, not as a warm-up act before a model.

## Worker profile

- Credential-free disposable worker.
- Network `NONE` by default.
- Read-only repository or diff mount.
- No package installation.
- No hooks, build scripts, test discovery, or imports with side effects.
- Version-pinned validator binaries.
- Explicit command allowlist.
- Captured argv, cwd, binary version, stdout, stderr, exit code, start/end time, and file/diff digests.
- Worker destroyed after one request.

## Accepted validator inventory

| Validator | Observed command class | Authority limit | Lane status |
|---|---|---|---|
| Repository identity | Git remote/rev-parse/status | Checkout identity and state only | Allowed |
| Task-packet schema | Draft 7 JSON validation | Structure only, not runtime truth | Allowed where schema is present |
| Embedded-audit proof schema | Existing validation script | Embedded-audit object validity only | Allowed after path and version verification |
| Probe-bundle validator | Bundle shape, hashes, secret patterns | Probe evidence contract only | Allowed for relevant bundle |
| JSON parse | Python standard library | Syntax only | Allowed |
| Diff hygiene | `git diff --check` | Whitespace errors in compared tracked diff | Allowed |
| PR Steward static contract inspection | `sed`/`rg` over tracked docs/source | Inventory only, no intake execution | Allowed as evidence collection |
| Pre-commit | Hook runner | Potential mutation and dependency install | Excluded from offline lane |

## Additional validator admission rule

`PROPOSED` A validator enters the lane only after its profile records:

- exact binary/version/hash;
- complete argv;
- expected input class;
- mutation behavior;
- network behavior;
- deterministic exit meanings;
- output schema;
- authority limit;
- known false-positive and false-negative boundaries;
- cleanup behavior.

Any unknown mutation or network behavior blocks admission.

## Mechanical-only closure policy

A PR may use mechanical-only closure only when all are true:

1. Every changed file is in a certified non-executable allowlist.
2. No protected category is touched.
3. No executable-bit, symlink, submodule, binary, or generated shipping artifact change exists.
4. No dependency, CI, build, container, infrastructure, schema, auth, secret, persistence, release, or provenance path changes.
5. Required ownership and status evidence is present.
6. Diff and request are complete and exact-head bound.
7. All required validators pass.
8. A human accepts that the validator authority is sufficient for this change class.

`PROPOSED` Additive tests may eventually receive a low-risk lane, but they are not automatically mechanical-only. Test deletion, assertion weakening, fixture semantics, snapshot acceptance, and test-selection changes require semantic review.

## Mechanical result envelope

The result records:

- request and exact-head identifiers;
- validator profile IDs and hashes;
- command receipts;
- per-validator result and authority statement;
- aggregate status;
- skipped checks and reasons;
- proof artifacts and hashes;
- explicit statement that semantic correctness beyond the validators is not established.

## Aggregate result semantics

| State | Meaning |
|---|---|
| `PASS_WITHIN_AUTHORITY` | Every required validator passed; only bounded claims are allowed |
| `FAIL_VALIDATION` | At least one validator found a deterministic violation |
| `BLOCKED_UNSUPPORTED_CHANGE` | Diff falls outside mechanical-only policy |
| `ENVIRONMENT_FAILURE` | Validator could not run reliably |
| `INCOMPLETE_EVIDENCE` | Required input or proof missing |

No state is equivalent to merge approval.

## Excluded paths

`REJECTED`

- Aggregate Dopemux CLI preflight path with observed import-time network fetch.
- `uv` or package-manager commands that create environments or install dependencies.
- Pre-commit in the offline lane unless a future profile proves no mutation and no install.
- Builds, tests, linters, or scanners that execute candidate code without a separate disposable execution profile.
- Any command whose authority or side effects are unknown.

## Future extension

`PROPOSED` Candidate-code mechanical tests can be added only as a separate worker class, still credential-free, preferably in a disposable VM, with explicit network and resource policy. They must never run under a plan-authenticated adapter account.
