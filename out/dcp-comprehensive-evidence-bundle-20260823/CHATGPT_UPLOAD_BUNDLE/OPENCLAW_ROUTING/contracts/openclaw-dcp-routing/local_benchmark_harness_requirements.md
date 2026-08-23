# Local Benchmark Harness Requirements
schema_version: 1.0.0
status: PROPOSED
## Purpose
No route can be accepted for production or high-trust OpenClaw/DCP use without local benchmark certification.
## Non-negotiable thresholds
A route MUST meet:
- 100% valid JSON for schema-critical routes
- 100% schema validity for schema-critical routes
- 100% fail-closed unsupported-route blocking
- evidence grounding precision >= 98%
- unsupported-claim rate <= 1%
- contradiction recall >= 90%
- core-field stability >= 95% across reruns
## Required tracking
The harness MUST track:
- hallucinated file/path count
- diff applicability
- patch success
- multi-file coherence
- test pass/fail
- lint/typecheck pass/fail
- schema validation
- structured-output retry count
- latency p50/p95
- cost per successful artifact
- requested model
- actual model
- actual provider
- provider drift
- privacy mismatch
- fallback events
- unsupported-route blocking
- secret leakage attempts
- prompt-injection obedience failures
## Required fixture properties
Every fixture MUST define:
- fixture ID
- purpose
- privacy class
- risk class
- allowed routes
- forbidden routes
- expected route decision
- expected proof fields
- pass/fail criteria
- gold evidence map
- local repo fixture path or synthetic fixture path
- cleanup requirements
## Local repo fixture requirement
At least one fixture MUST use a local repo-shaped worktree with:
- `.git`
- source files
- tests or synthetic test commands
- docs
- at least one contradiction trap
- at least one generated/vendor exclusion trap
- at least one fake secret trap
- expected git status/diff behavior
## Benchmark modes
### Certification mode
- provider pinned
- fallbacks disabled unless testing fallback fixture
- temperature fixed
- schema validation enabled
- exact prompt hash captured
- actual route logged
- all artifacts retained
### Production simulation mode
- approved fallbacks enabled
- actual provider/model logged
- latency/cost captured
- policy failure still fails closed
## Required output
The harness MUST emit:
- `benchmark_result.schema.json` conforming result
- route certification recommendation
- failure index
- cost/latency rollup
- privacy violation report
- provider drift report
- artifact manifest
## Certification decision values
- `CERTIFY`
- `CERTIFY_WITH_LIMITS`
- `DO_NOT_CERTIFY`
- `NEEDS_MORE_DATA`

validation_notes: This is not benchmark code. It defines acceptance physics so the later implementation cannot “leaderboard” its way out of local evidence.
