# Macro Packet Series

## Series charter

- **PROPOSED:** Series ID: `UR-ROUTER-IMPL-001`.
- **PROPOSED:** Base branch: current reviewed `main` at packet creation, pinned by SHA in each child packet.
- **PROPOSED:** One dedicated worktree and branch per packet.
- **PROPOSED:** One primary implementer per packet. No subagent fanout in release-one packets.
- **PROPOSED:** Each packet is commit-sized, independently reviewable, and merges only after current proof and PR Steward readiness.
- **PROPOSED:** Packets 001 through 009 implement the first release. Packets 010 through 012 are future-gated and must not be issued merely because earlier packets merged.

## Mandatory packet envelope

The following fields and commands are incorporated into every repo-changing packet in this series.

### Common objective rule

- **PROPOSED:** The child packet objective states one externally testable outcome and the maximum state transition it can enable.

### Common scope OUT

- **PROPOSED:** No opportunistic cleanup.
- **PROPOSED:** No edits outside the packet allowlist.
- **PROPOSED:** No secrets, credential files, local transcripts, private session data, or generated virtual environments committed.
- **PROPOSED:** No new service/daemon, proxy manager, quota ledger, proof schema, handoff schema, execution engine, workflow engine, release gate, or revival of `services/task-router`.
- **PROPOSED:** No promotion of `src/dopemux/agent_orchestrator.py` or `services/agents/**` into authority.

### Common invariants

- **PROPOSED:** Existing Dopemux routing, Freeflow, LiteLLM, RTE, Task Orchestrator, dopetask, proof/handoff, and PR Steward flows remain usable when the Universal Router is disabled.
- **PROPOSED:** Runtime truth and current Git state outrank docs and proposals.
- **PROPOSED:** Unknown and conflicting evidence is preserved.
- **PROPOSED:** Prompt-requested controls are not represented as enforcement.
- **PROPOSED:** Environment failures never automatically promote model or cost tier.
- **PROPOSED:** Model-generated identity text is untrusted.
- **PROPOSED:** Tokens, plan credits, actual API cost, estimated cost, and runner overhead remain separate.
- **PROPOSED:** No completion claim without current proof, embedded audit, and PR Steward readiness when a PR exists.

### Common setup and baseline commands

The child packet sets `PACKET_ID` to its exact ID and executes:

```bash
export PACKET_ID="<EXACT_PACKET_ID>"
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export PROOF_DIR="out/proof/universal-router/${PACKET_ID}/${RUN_ID}"
mkdir -p "$PROOF_DIR"
git status --short --branch | tee "$PROOF_DIR/git-status-before.txt"
git rev-parse --show-toplevel | tee "$PROOF_DIR/repo-root.txt"
git rev-parse HEAD | tee "$PROOF_DIR/head-before.txt"
git branch --show-current | tee "$PROOF_DIR/branch.txt"
git worktree list --porcelain | tee "$PROOF_DIR/worktrees.txt"
test -f .dopetaskroot
test -f pyproject.toml
```

- **PROPOSED:** The executable child packet replaces `<EXACT_PACKET_ID>` before work begins. An unresolved placeholder is a stop condition.
- **PROPOSED:** The implementer verifies repo identity, dedicated worktree, expected branch, and a clean or explicitly documented baseline before modifying files.

### Common final evidence commands

```bash
git status --short --branch | tee "$PROOF_DIR/git-status-after.txt"
git diff --check | tee "$PROOF_DIR/git-diff-check.txt"
git diff --stat | tee "$PROOF_DIR/git-diff-stat.txt"
git diff --no-ext-diff | tee "$PROOF_DIR/git-diff.patch"
python -m compileall -q src/dopemux/universal_router
```

- **PROPOSED:** Every command's exit code is captured in `COMMAND_RESULTS.json`; stdout/stderr artifacts are listed in a proof manifest.
- **PROPOSED:** If the package does not yet exist in packet 001, the compile command runs after its allowed package file is created.

### Common embedded audit

- **OBSERVED:** UR-INV-003 did not prove AGY containment, structured output, identity, or telemetry sufficiently for a safe default invocation.
- **PROPOSED:** At child-packet lock time, use AGY/Sonnet only when a current certified capability snapshot provides an exact safe invocation.
- **PROPOSED:** Otherwise the default embedded auditor is Claude Code Sonnet in plan mode with no tools and no session persistence:

```bash
{
  printf '# Packet\n%s\n\n# Objective and acceptance criteria\n' "$PACKET_ID"
  cat "$PROOF_DIR/PACKET_SPEC.md"
  printf '\n# Git status before\n'
  cat "$PROOF_DIR/git-status-before.txt"
  printf '\n# Diff stat\n'
  cat "$PROOF_DIR/git-diff-stat.txt"
  printf '\n# Diff\n'
  cat "$PROOF_DIR/git-diff.patch"
  printf '\n# Validation summary\n'
  cat "$PROOF_DIR/VALIDATION_SUMMARY.md"
} > "$PROOF_DIR/EMBEDDED_AUDIT_INPUT.md"
claude --print --tools "" --no-session-persistence --permission-mode plan \
  --output-format json --model sonnet --effort high --max-budget-usd 5.00 -- \
  "$(cat "$PROOF_DIR/EMBEDDED_AUDIT_INPUT.md")" \
  > "$PROOF_DIR/EMBEDDED_AUDIT_RAW.json"
printf '%s\n' "$?" > "$PROOF_DIR/EMBEDDED_AUDIT_EXIT_CODE.txt"
```

- **PROPOSED:** Claude Code Opus uses the same command with `--model opus` only when Sonnet fails for capacity/depth and the packet permits premium audit.
- **PROPOSED:** Gemini CLI is an additional broad-context contradiction audit for packets 001, 005, 008, 010, and 012 when a current safe invocation is pinned.
- **PROPOSED:** The normalized audit record must include `auditor_tool`, `auditor_model`, `invocation`, `exit_code`, `auditor_verdict`, `auditor_findings`, `fixes_applied_from_audit`, `remaining_risks`, and `skip_reason`.
- **PROPOSED:** If no approved embedded auditor can run, the packet stops as `BLOCKED`; a skipped audit is not a pass.

### Common PR Steward requirement

- **OBSERVED:** The supplied evidence establishes PR Steward as required review intake/readiness but does not establish one canonical executable command or runtime location.
- **PROPOSED:** Every executable child packet must pin the current canonical PR Steward invocation before opening the PR. Failure to locate it is a stop condition, not permission to build a replacement.
- **PROPOSED:** When a PR exists, PR Steward must harvest metadata, changed files, commits/head SHA, reviews, review comments, threads, issue comments, bots, and checks, classify every item, and emit `MERGE_READINESS.json`.
- **PROPOSED:** `READY` requires current proof/head, current required checks, no unknown reviewer/bot, no unclassified item, no unresolved blocking thread, and diff inside the packet allowlist.

### Common rollback

- **PROPOSED:** Revert the packet commit or close the unmerged PR; do not rewrite shared history.
- **PROPOSED:** Remove only packet-created generated proof artifacts when repository policy permits. Preserve governance evidence required by retention policy.
- **PROPOSED:** Never delete or mutate prior Universal Router journal records as rollback.

### Common stop conditions

- **PROPOSED:** Repo/worktree/branch mismatch.
- **PROPOSED:** Dirty baseline not explicitly accepted.
- **PROPOSED:** Need to touch a file outside allowlist.
- **PROPOSED:** Runtime truth contradicts packet assumptions.
- **PROPOSED:** Required source contract or command is `UNKNOWN`.
- **PROPOSED:** Secret exposure or unsafe credential handling.
- **PROPOSED:** Validation, embedded audit, required checks, or PR Steward blocks.

---

## UR-TP-001: Universal Router contracts

### Objective

- **PROPOSED:** Define strict, versioned Universal Router-owned contracts and typed refs to existing contracts without enabling a CLI or execution.

### Scope IN

- **PROPOSED:** Dataclasses/Pydantic-style models, enums, validation, schemas, fixtures, and contract tests.

### Scope OUT

- **PROPOSED:** CLI registration, SQLite, runtime adapters, provider calls, runner calls, policy promotion.

### Files allowed

```text
src/dopemux/universal_router/__init__.py
src/dopemux/universal_router/models.py
schemas/universal-router/*.json
tests/universal_router/test_models.py
tests/universal_router/fixtures/contracts/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-001"
python -m json.tool schemas/universal-router/route-policy.schema.json >/dev/null
python -m pytest -q tests/universal_router/test_models.py
python -m pytest -q tests/universal_router -k 'contract or model'
```

### Validation gates

- **PROPOSED:** All required contracts exist; authority-bearing objects reject undeclared fields; invalid and conflicting fixtures behave as specified; proof/handoff/PR readiness remain refs.

### Proof requirements

- **PROPOSED:** Schema inventory, generated/handwritten schema comparison, test outputs, Git evidence, normalized embedded audit, and authority-boundary review.

### Rollback

- **PROPOSED:** Revert the contract commit; no state migration exists.

### Packet-specific stop conditions

- **PROPOSED:** Stop if current canonical proof/handoff contracts cannot be referenced without copying or if one required decision record cannot be kept distinct.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default plus Gemini contradiction audit when safely available. PR Steward `READY` required.

---

## UR-TP-002: Read-only CLI and deterministic engine

### Objective

- **PROPOSED:** Add in-process `dopemux route explain|recommend|inspect|validate` that returns deterministic fixture/policy-backed advice and cannot execute.

### Scope IN

- **PROPOSED:** CLI group, engine skeleton, policy loader, rendering, JSON output, unit and CLI tests.

### Scope OUT

- **PROPOSED:** Journal, external snapshots, subsystem adapters, network/subprocess calls, operator acceptance.

### Files allowed

```text
src/dopemux/universal_router/__init__.py
src/dopemux/universal_router/engine.py
src/dopemux/universal_router/policy.py
src/dopemux/universal_router/cli.py
src/dopemux/cli.py
config/universal-router/policies/ur-policy-0.1.0.yaml
config/universal-router/active-policy.json
tests/universal_router/test_cli.py
tests/universal_router/test_engine.py
tests/universal_router/test_policy.py
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-002"
python -m pytest -q tests/universal_router/test_policy.py
python -m pytest -q tests/universal_router/test_engine.py
python -m pytest -q tests/universal_router/test_cli.py
python -m dopemux.cli route --help
python -m dopemux.cli route validate policy --json
```

### Validation gates

- **PROPOSED:** No imports of subprocess/provider SDKs in the package; frozen inputs yield identical decision hashes; list output follows operator contract; invalid policy blocks recommend.

### Proof requirements

- **PROPOSED:** CLI transcripts for all four commands, deterministic replay hashes, import/static side-effect check, tests, Git evidence, and embedded audit.

### Rollback

- **PROPOSED:** Revert CLI registration/package changes and active pointer; existing `dopemux routing` is unaffected.

### Packet-specific stop conditions

- **PROPOSED:** Stop if CLI noun conflicts with active commands or any route can enter handoff/execution states.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default. PR Steward `READY` required.

---

## UR-TP-003: Append-only decision journal

### Objective

- **PROPOSED:** Add workspace-local append-only SQLite for Universal Router decisions, imports, corrections, and later acceptance events.

### Scope IN

- **PROPOSED:** Schema, migrations, locking, triggers, replay, redaction hooks, journal inspection tests.

### Scope OUT

- **PROPOSED:** Upstream-state replication, quota state, RTE runs, proof bodies, approvals, execution.

### Files allowed

```text
src/dopemux/universal_router/journal.py
src/dopemux/universal_router/models.py
src/dopemux/universal_router/cli.py
tests/universal_router/test_journal.py
tests/universal_router/fixtures/journal/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-003"
python -m pytest -q tests/universal_router/test_journal.py
python -m pytest -q tests/universal_router/test_cli.py -k inspect
python -m pytest -q tests/universal_router -k 'journal or replay or migration'
```

### Validation gates

- **PROPOSED:** Update/delete abort; foreign keys and WAL enabled; concurrent append conflict is deterministic; migration failure preserves prior DB; replay order and hash are stable.

### Proof requirements

- **PROPOSED:** SQLite schema dump, trigger tests, concurrency output, migration/rollback fixture output, replay hash, Git evidence, and audit.

### Rollback

- **PROPOSED:** Revert code. Preserve or archive created journal; do not mutate records.

### Packet-specific stop conditions

- **PROPOSED:** Stop if state design starts owning another subsystem's data or requires distributed transactions.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default. PR Steward `READY` required.

---

## UR-TP-004: Capability and health snapshot ingestion

### Objective

- **PROPOSED:** Validate, import, expire, and inspect capability/provider-health snapshots without invoking runners or providers.

### Scope IN

- **PROPOSED:** Snapshot models, import paths, TTL policy, invalidation, environment scoping, fixtures.

### Scope OUT

- **PROPOSED:** Live provider probes, authentication, provider dispatch, route execution.

### Files allowed

```text
src/dopemux/universal_router/snapshots.py
src/dopemux/universal_router/models.py
src/dopemux/universal_router/policy.py
src/dopemux/universal_router/cli.py
tests/universal_router/test_snapshots.py
tests/universal_router/fixtures/snapshots/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-004"
python -m pytest -q tests/universal_router/test_snapshots.py
python -m pytest -q tests/universal_router -k 'stale or environment_blocked or capability'
python -m dopemux.cli route validate snapshots --json
```

### Validation gates

- **PROPOSED:** Source/hash/time/TTL/environment required; copied or stale snapshots cannot appear fresh; sandbox denial differs from provider outage; unknown containment remains unknown.

### Proof requirements

- **PROPOSED:** Fixture matrix, expiry/invalidation outputs, environment-failure decision diffs, Git evidence, and audit.

### Rollback

- **PROPOSED:** Revert ingestion code; imported journal events remain historical and become unreadable only through versioned compatibility behavior, never deletion.

### Packet-specific stop conditions

- **PROPOSED:** Stop if a safe acquisition artifact cannot be distinguished from local configuration containing secrets.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default. PR Steward `READY` required.

---

## UR-TP-005: Existing-subsystem read adapters

### Objective

- **PROPOSED:** Add non-mutating adapters for DCP, Freeflow, LiteLLM, RTE, proof, handoff, audit, and PR Steward refs.

### Scope IN

- **PROPOSED:** Artifact/file/API-read normalization where current runtime proves a stable read surface, adapter versions, failure mapping, contract tests.

### Scope OUT

- **PROPOSED:** Freeflow mutation, proxy management, RTE invocation, workflow writes, handoff submission, proof generation, PR readiness computation.

### Files allowed

```text
src/dopemux/universal_router/adapters.py
src/dopemux/universal_router/models.py
src/dopemux/universal_router/engine.py
tests/universal_router/test_adapters.py
tests/universal_router/fixtures/adapters/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-005"
python -m pytest -q tests/universal_router/test_adapters.py
python -m pytest -q tests/universal_router -k 'dcp or freeflow or litellm or rte or proof or handoff or steward'
python -m pytest -q tests/universal_router -k 'read_only or no_mutation or authority'
```

### Validation gates

- **PROPOSED:** Every adapter identifies source authority, read methods, unavailable fields, freshness, environment, and version; mutation attempts are absent or rejected; proxy observation is not attestation.

### Proof requirements

- **PROPOSED:** Adapter matrix, imports/call-path inspection, no-mutation tests, source fixtures/hashes, Git evidence, Claude audit, and Gemini contradiction audit when safely available.

### Rollback

- **PROPOSED:** Disable/revert individual adapters. Engine treats their data as unavailable without changing upstream systems.

### Packet-specific stop conditions

- **PROPOSED:** Stop any adapter whose only path is a write, a secret-bearing config, or a proxy/derived view presented as canonical.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet plus Gemini contradiction audit when safely available. PR Steward `READY` required.

---

## UR-TP-006: Codex advisory adapter

### Objective

- **PROPOSED:** Normalize current Codex capabilities and build non-executing Codex `ExecutionRecommendation` records.

### Scope IN

- **PROPOSED:** Model/reasoning/config mapping, JSONL/schema/sandbox/ephemeral capability fields, usage normalization, containment declaration, fixtures.

### Scope OUT

- **PROPOSED:** Running Codex, OAuth/API-key handling, file editing, proof claims, credit inference, actual-model attestation.

### Files allowed

```text
src/dopemux/universal_router/adapters.py
src/dopemux/universal_router/models.py
src/dopemux/universal_router/engine.py
tests/universal_router/test_codex_advisory_adapter.py
tests/universal_router/fixtures/codex/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-006"
python -m pytest -q tests/universal_router/test_codex_advisory_adapter.py
python -m pytest -q tests/universal_router -k 'identity or usage or credits or containment'
python -m dopemux.cli route recommend --fixture tests/universal_router/fixtures/codex/contained_read.json --json
```

### Validation gates

- **PROPOSED:** `model_response_claim` remains untrusted; `attested_actual_model` remains unknown; usage source/confidence preserved; no cost/credit fabrication; no invocation path exists.

### Proof requirements

- **PROPOSED:** Mapping table to UR-INV-003 evidence, negative fixtures, recommendation transcript, Git evidence, and audit.

### Rollback

- **PROPOSED:** Revert/disable Codex adapter; generic candidates remain available only when supported by other snapshots.

### Packet-specific stop conditions

- **PROPOSED:** Stop if local Codex version/current help materially conflicts with the supplied probe and safe reacquisition is not authorized.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default. PR Steward `READY` required.

---

## UR-TP-007: Proof and governance references

### Objective

- **PROPOSED:** Validate and attach canonical proof, handoff, validation, audit, human approval, dopetask, and PR Steward refs without copying their schemas.

### Scope IN

- **PROPOSED:** Ref resolution, hashes, head/decision linkage, freshness, rendering, broken/stale/conflict fixtures.

### Scope OUT

- **PROPOSED:** Proof generation, handoff creation, approval mutation, audit execution, PR readiness calculation.

### Files allowed

```text
src/dopemux/universal_router/models.py
src/dopemux/universal_router/adapters.py
src/dopemux/universal_router/engine.py
src/dopemux/universal_router/cli.py
tests/universal_router/test_governance_refs.py
tests/universal_router/fixtures/governance_refs/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-007"
python -m pytest -q tests/universal_router/test_governance_refs.py
python -m pytest -q tests/universal_router -k 'stale_proof or head_sha or audit_ref or handoff_ref or steward'
python -m dopemux.cli route inspect --fixture tests/universal_router/fixtures/governance_refs/stale_head.json --json
```

### Validation gates

- **PROPOSED:** Stale/current-head mismatch blocks dependent claims; skipped audit is not pass; approval scope/expiry preserved; upstream status is never remapped.

### Proof requirements

- **PROPOSED:** Ref-resolution matrix, stale/head tests, canonical schema source refs, Git evidence, and audit.

### Rollback

- **PROPOSED:** Revert ref adapters; no upstream record changes.

### Packet-specific stop conditions

- **PROPOSED:** Stop if canonical contract provenance is unresolved or the implementation would normalize away a status/posture distinction.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default. PR Steward `READY` required.

---

## UR-TP-008: Shadow evaluation and certification harness

### Objective

- **PROPOSED:** Build historical replay, hard-negative fixtures, metrics, and advisory certification artifacts without affecting execution.

### Scope IN

- **PROPOSED:** Corpus schema, redaction, gold labels, replay, metrics, decision diff, certification report, CI checks.

### Scope OUT

- **PROPOSED:** Provider benchmarks not exposed by vendors, live execution, automatic policy promotion, storing raw secrets/client data.

### Files allowed

```text
schemas/universal-router/evaluation-report.schema.json
scripts/dev/benchmarks/universal_router/**
tests/universal_router/test_evaluation.py
tests/universal_router/fixtures/evaluation/**
docs/03-reference/governance/universal-router-evaluation.md
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-008"
python -m json.tool schemas/universal-router/evaluation-report.schema.json >/dev/null
python -m pytest -q tests/universal_router/test_evaluation.py
python scripts/dev/benchmarks/universal_router/replay.py --corpus tests/universal_router/fixtures/evaluation/corpus.jsonl --policy config/universal-router/active-policy.json --output "$PROOF_DIR/evaluation"
python scripts/dev/benchmarks/universal_router/validate_report.py "$PROOF_DIR/evaluation/EVALUATION_REPORT.json"
```

### Validation gates

- **PROPOSED:** Corpus redaction passes; metric definitions/version captured; hard constraints 100%; deterministic replay 100%; unavailable measurements remain unavailable; no severe failure.

### Proof requirements

- **PROPOSED:** Corpus manifest/hashes, report, per-task refs, defects/corrections, commands/exits, Git evidence, Claude audit, and Gemini contradiction audit when safely available.

### Rollback

- **PROPOSED:** Revert harness/docs. Preserve evaluation evidence according to proof retention; no route behavior changes unless a separate policy PR is promoted.

### Packet-specific stop conditions

- **PROPOSED:** Stop on data leakage, unlabeled gold disagreement, metric manipulation, severe failure, or corpus contamination.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet plus Gemini contradiction audit when safely available. Independent audit required before certification. PR Steward `READY` required.

---

## UR-TP-009: Manual operator acceptance

### Objective

- **PROPOSED:** Record explicit accept, alternate, reject, and correction events while leaving execution manual and external.

### Scope IN

- **PROPOSED:** CLI actions, acceptance/correction records, expiry/scope, journal linkage, metrics.

### Scope OUT

- **PROPOSED:** Dopetask handoff submission, runner/provider invocation, workflow transition, policy promotion.

### Files allowed

```text
src/dopemux/universal_router/cli.py
src/dopemux/universal_router/engine.py
src/dopemux/universal_router/journal.py
src/dopemux/universal_router/models.py
tests/universal_router/test_operator_acceptance.py
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-009"
python -m pytest -q tests/universal_router/test_operator_acceptance.py
python -m pytest -q tests/universal_router -k 'accept or reject or correction or override'
python -m dopemux.cli route recommend --fixture tests/universal_router/fixtures/evaluation/cheap_read.json --json
python -m dopemux.cli route inspect --latest --json
```

### Validation gates

- **PROPOSED:** No implicit acceptance; original decision immutable; acceptance bound to exact decision hash; hard invariants cannot be overridden; no execution imports/calls.

### Proof requirements

- **PROPOSED:** CLI transcripts, journal event sequence, negative override tests, Git evidence, and audit.

### Rollback

- **PROPOSED:** Revert acceptance UI/logic. Historical events remain append-only and ignored by older code if necessary.

### Packet-specific stop conditions

- **PROPOSED:** Stop if acceptance has a side effect outside the router journal or if identity of the approving human cannot be represented by an external ref.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet default. PR Steward `READY` required.

---

## UR-TP-010: First bounded execution adapter, future-gated

### Issuance preconditions

- **PROPOSED:** Do not issue until release-one advisory certification, manual-acceptance evidence, a new execution ADR, explicit human approval, current runner capability/identity/containment evidence, and selected adapter certification plan exist.

### Objective

- **PROPOSED:** Enable one Codex execution adapter for a narrowly defined low-risk packet class through accepted dopetask handoff or an explicitly approved boundary, with no parallel adapter.

### Scope IN

- **PROPOSED:** Codex request construction, wrapper-enforced worktree/file/command/network controls, cancellation, idempotency, result normalization, proof refs, and bounded trial tests.

### Scope OUT

- **PROPOSED:** Other runners, subagent fanout, R5/R6 tasks, automatic selection, workflow/release authority, quota ledger duplication.

### Files allowed

```text
src/dopemux/universal_router/runner_adapters/__init__.py
src/dopemux/universal_router/runner_adapters/codex.py
src/dopemux/universal_router/models.py
src/dopemux/universal_router/engine.py
src/dopemux/universal_router/adapters.py
tests/universal_router/test_codex_execution_adapter.py
tests/universal_router/fixtures/codex_execution/**
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-010"
python -m pytest -q tests/universal_router/test_codex_execution_adapter.py
python -m pytest -q tests/universal_router -k 'allowlist or cancellation or idempotency or containment or proof'
python -m pytest -q tests/universal_router -k 'environment_failure and not premium'
```

- **UNKNOWN:** The exact live Codex invocation cannot be safely frozen from the carried evidence because current auth, actual-model attestation, plan-credit telemetry, and target-environment containment are unresolved.
- **PROPOSED:** The executable child packet must pin the exact invocation after a fresh approved capability packet. Absence is a hard stop.

### Validation gates

- **PROPOSED:** Zero allowlist escape, no unauthorized network/write, current proof, successful rollback, exact failure classification, and no environment-driven premium escalation.

### Proof requirements

- **PROPOSED:** Fresh capability/identity/containment certification, synthetic and bounded-live outputs, full Git/command evidence, independent containment audit, Claude embedded audit, Gemini contradiction audit, and PR Steward readiness.

### Rollback

- **PROPOSED:** Disable adapter-specific kill switch, revert policy enablement/code, cancel active bounded run, and preserve proof/journal history.

### Packet-specific stop conditions

- **PROPOSED:** Stop on identity conflict for pinned task, missing exact invocation, secret exposure, unauthorized action, stale certification, proof gap, or any need for a second adapter.

### Embedded audit and PR readiness

- **PROPOSED:** Embedded audit plus separate independent audit required. PR Steward `READY` required.

---

## UR-TP-011: Bounded escalation and demotion, future-gated

### Issuance preconditions

- **PROPOSED:** At least 25 accepted low-risk executions for the first adapter, zero severe failures, current certifications, and new supervisor approval.

### Objective

- **PROPOSED:** Add deterministic attempt budgets for validation-driven reasoning/model escalation, equivalent-route fallback, and safe demotion.

### Scope IN

- **PROPOSED:** Attempt graph, escalation records, budgets, stop rules, environment-failure lane, cost/credit/identity guards, fixtures.

### Scope OUT

- **PROPOSED:** Automatic policy promotion, unrestricted retries, cross-adapter fanout, security/release tasks.

### Files allowed

```text
src/dopemux/universal_router/engine.py
src/dopemux/universal_router/policy.py
src/dopemux/universal_router/models.py
src/dopemux/universal_router/journal.py
tests/universal_router/test_escalation.py
tests/universal_router/fixtures/escalation/**
config/universal-router/policies/ur-policy-<approved-version>.yaml
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-011"
python -m pytest -q tests/universal_router/test_escalation.py
python -m pytest -q tests/universal_router -k 'retry_budget or demotion or escalation or environment_failure'
python -m pytest -q tests/universal_router -k 'cost_ceiling or credits_unknown or identity_conflict'
```

### Validation gates

- **PROPOSED:** No loops; default budgets enforced; environment failures never increase tier; demotion preserves every hard control; Freeflow admission remains separate.

### Proof requirements

- **PROPOSED:** Fifty-scenario trial report, attempt graphs, decision diffs, cost/identity/containment evidence, Git evidence, embedded and independent audits.

### Rollback

- **PROPOSED:** Revert to single-attempt policy and disable escalation feature flag; preserve attempt history.

### Packet-specific stop conditions

- **PROPOSED:** Stop on loop, repeated identical failure, guard weakening, cost breach, unknown identity where required, or unexplained escalation spike.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Sonnet or Opus based on depth, independent audit, and PR Steward `READY` required.

---

## UR-TP-012: Narrow automatic route selection, future-gated

### Issuance preconditions

- **PROPOSED:** At least 100 certified executions for the exact low-risk lane/route tuple, zero severe failures, current policy/adapter/identity/containment certifications, explicit human promotion approval, and a new ADR confirming scope.

### Objective

- **PROPOSED:** Permit automatic selection of one certified low-risk route while retaining separate execution acceptance and all subsystem authorities.

### Scope IN

- **PROPOSED:** One lane, one active certified policy version, kill switch, monitoring, revocation, shadow comparator, and explicit execution boundary.

### Scope OUT

- **PROPOSED:** R5/R6, subagent fanout, automatic policy promotion, automatic release, workflow mutation, broad multi-runner selection.

### Files allowed

```text
src/dopemux/universal_router/engine.py
src/dopemux/universal_router/policy.py
src/dopemux/universal_router/cli.py
config/universal-router/active-policy.json
config/universal-router/policies/ur-policy-<approved-version>.yaml
tests/universal_router/test_automatic_lane.py
tests/universal_router/fixtures/automatic_lane/**
docs/03-reference/governance/universal-router-automatic-lane.md
```

### Exact packet commands

```bash
export PACKET_ID="UR-TP-012"
python -m pytest -q tests/universal_router/test_automatic_lane.py
python -m pytest -q tests/universal_router -k 'kill_switch or revocation or shadow or automatic_lane'
python -m pytest -q tests/universal_router -k 'security or release or authority' --maxfail=1
python scripts/dev/benchmarks/universal_router/replay.py --corpus tests/universal_router/fixtures/evaluation/corpus.jsonl --policy config/universal-router/active-policy.json --output "$PROOF_DIR/automatic-lane-replay"
```

### Validation gates

- **PROPOSED:** Only the approved lane auto-selects; execution remains separately accepted; all out-of-lane cases remain advisory; kill switch and rollback tested; zero severe failures.

### Proof requirements

- **PROPOSED:** Exact certification refs, 100-execution evidence, independent audit, human approval, policy diff/replay, monitoring/revocation test, Git evidence, Claude audit, Gemini contradiction audit, and PR Steward `READY`.

### Rollback

- **PROPOSED:** Activate kill switch, revert active policy pointer to prior certified advisory policy, and preserve decisions/attempts.

### Packet-specific stop conditions

- **PROPOSED:** Stop on any red-lane reachability, execution coupling, stale certification, provider drift, override spike, failed required check, stale proof, unknown reviewer/bot, or PR Steward block.

### Embedded audit and PR readiness

- **PROPOSED:** Claude Opus or current approved high-depth auditor plus independent provider/human review. Gemini contradiction audit when safely available. PR Steward `READY` required.

## Series-level completion

- **PROPOSED:** First release is complete only after UR-TP-001 through UR-TP-009 satisfy their gates and advisory certification is independently accepted.
- **PROPOSED:** UR-TP-010 through UR-TP-012 remain `NOT_ISSUED` until their explicit preconditions are evidenced.
- **PROPOSED:** The final proof index lists every packet, branch, commit, PR, head SHA, audit verdict, PR Steward readiness, and residual risk without claiming that merge alone proves correctness.
