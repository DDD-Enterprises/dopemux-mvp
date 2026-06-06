# Evidence & Proof Flow

How capsule executions establish truth, generate proof bundles, and what makes a proof valid or rejectable.

---

## Evidence Priority Order

Evidence is ranked by observability. Higher-ranked sources outrank lower-ranked ones. Never launder a lower-ranked source into a claim that requires a higher-ranked one.

1. **Runtime code (observed)** — highest authority. What the process actually does at execution time. Requires a running process, verified output, or confirmed test execution.
2. **Config files (observed)** — `.env`, `settings.json`, `docker-compose.yml` overrides, `pyproject.toml`. Read directly from disk; observable without running the system.
3. **Tests and fixtures (observed)** — test source + passing exit code. A test that does not run is NOT evidence. `NOT_RUN` must be declared, not collapsed into `PASS`.
4. **Compose.yml and Dockerfiles (compose-wiring, NOT runtime-verified)** — express deployment intent. Confirm image wiring, port bindings, and service graph topology. Do not treat a compose file as proof that a process is running.
5. **Docs under `docs/03-reference/` (advisory)** — architectural intent, design decisions, and reference material. Superseded by runtime code when they conflict.
6. **`claudedocs/` artifacts — INFERRED / advisory only, never primary source** — transcripts, audit reports, session summaries. May be stale, session-scoped, or written by a model with partial context. Never cite as a proof source without a matching runtime or config observation.
7. **Session memory — INFERRED / advisory only, never primary source** — lowest authority. MEMORY.md and ConPort active context are orientation aids, not evidence.

---

## Proof Bundle Requirements

Every capsule execution must produce a proof bundle before transitioning to `review` state. No proof = no review = no merge.

```
proof/TP-DMX-*/
  PROOF.json     # structured proof object
  SUMMARY.md     # human-readable summary
```

The `proof/` directory is the ONLY system the proof-generation step may write to. All other writes during proof generation = stop condition violation.

---

## PROOF.json Required Fields

A PROOF.json missing any of the following is considered **incomplete** and must be rejected by PR Steward:

- `packet_id` — task-orchestrator item ID for this capsule
- `head_sha` — git SHA at time of proof generation
- `branch` — branch name where proof was generated
- `worktree_path` — absolute path to the worktree used
- `files_changed` — array of file paths modified by this capsule
- `validations` — array of `{name, status: PASS|FAIL|NOT_RUN, evidence}` objects; every test/check must appear; `NOT_RUN` is a valid status and must be declared explicitly
- `pal_codereview_status` — `PASS`, `FAIL`, `SKIPPED`, or `NEEDS_SUPERVISOR`; never omit
- `precommit_status` — `PASS`, `FAIL`, or `NOT_RUN`
- `residual_risks` — array of known risks not addressed by this capsule
- `unknowns` — array of unresolved questions; use the string `"none"` only when genuinely empty
- `stop_conditions_met` — array of stop conditions that fired (may be empty array)
- `cleanup_status` — `CLEAN`, `PENDING`, or `DEFERRED`

---

## Model Routing Receipt

The proof bundle must include the model(s) used per stage. This is not optional.

```json
"model_routing_receipt": {
  "analysis":     "gemini-2.5-pro",
  "planning":     "gpt-5",
  "implementation": "claude-sonnet-4-6",
  "codereview":   "gpt-5",
  "precommit":    "claude-sonnet-4-6"
}
```

**Rejection rule**: A cheap-read or fast model (e.g., `gemini-flash`, `gpt-5-mini`) used for architecture decisions or PAL codereview = **proof rejection**. Model routing must match the stage's criticality tier as defined in `model-routing.md`.

---

## Audit Receipt

Every capsule proof must include the PAL clink external audit receipt:

```json
"audit_receipt": {
  "tool":       "pal/clink",
  "auditor_model": "gpt-5",
  "status":     "PASS_WITH_RISKS | PASS | FAIL",
  "cost_usd":   0.628,
  "receipt_id": "<external-receipt-id>"
}
```

**Rejection rule**: Self-audit by the implementing model = **immediate proof rejection**. The auditor must be an external tool invocation (PAL clink or equivalent) operating independently of the implementer's session. An audit marked `SKIPPED` is equivalent to `FAILED` for proof purposes.

---

## Stale-Proof Detection

A proof bundle is **stale** if the `head_sha` recorded in `PROOF.json` does not match the current tip of the target branch at the time of merge review.

PR Steward must:

1. Fetch `head_sha` from `PROOF.json`
2. Compare against `git rev-parse origin/main` (or the PR's target branch tip)
3. If mismatch: emit `STALE_PROOF` flag and block `MERGE_READINESS: READY`

A stale proof requires re-running the validation suite on the updated HEAD and generating a new `PROOF.json`. Partial re-validation is not acceptable.

---

## No-Write Confirmation

Proof generation is a **read-and-write-to-proof-only** operation. The proof generation step must not:

- Write to `src/`, `tests/`, `scripts/`, `docs/`, or `schemas/`
- Invoke any queue drain or batch merge script
- Call any external API with side effects
- Modify ConPort records outside the capsule's own progress entry
- Commit to git (the orchestrator or human does this after proof review)

Any write outside `proof/TP-DMX-<id>/` during proof generation = immediate stop condition.

---

## Evidence Caveat

> **All component statuses in this build series reflect static analysis only.**
>
> `runtime_process_verified: false` on all entries.
>
> Compose-wiring (`docker-compose.yml`, `Dockerfile`) indicates deployment intent and image topology — it does not confirm that any process is running, healthy, or accepting connections. No live service call has been made. No port has been probed. All service-level verdicts are derived from source inspection and compose graph analysis, not from observed runtime behavior.
>
> Any proof that asserts a service is "running" based solely on compose-file presence is mis-classified and must be downgraded to `INFERRED`.
