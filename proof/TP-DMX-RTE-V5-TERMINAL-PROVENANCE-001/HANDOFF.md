# Handoff — TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001

## Decision

Repair the canonical v5 execution authority first, per the original packet's scope. **Complete.**

## Evidence

- Content head (C1): `67f22b4829b0e3e98ba59fcb609f42c5af213ffc`
- Execution base: `6626aa9a58dd82e62226cfca63498cc3f711bb75`
- Proof head: this bundle's final commit
- Branch: `tp/DMX-RTE-V5-TERMINAL-PROVENANCE-001` (not pushed)

## Changed files

See `CHANGED_FILES.txt` — 9 files, all within Task Packet Section 5.

## Finding dispositions

```
RTE_W1_001                                  = REPAIRED_AND_VERIFIED
RTE_W1_006_V5_TERMINAL                      = REPAIRED_AND_VERIFIED
RTE_W1_006_V3_LEGACY                        = DEFERRED_LEGACY_RESIDUAL
RTE_W1_006_ORIGINAL_SUBMISSION_PROVENANCE   = DEFERRED_RESIDUAL
RTE_W1_010                                  = REPAIRED_AND_VERIFIED
```

## Terminal exit behavior matrix

| Scenario | Exit code |
|---|---|
| Phase execution completes, `run_status == RUN_STATUS_OK` | 0 |
| `run_status` FAIL/BLOCKED/COST_ABORTED/unrecognized | non-zero |
| Missing/unreadable coverage rollup | non-zero |
| `--batch-retrieve` reports `success=True` | 0 |
| `--batch-retrieve` reports `success=False` (any material failure) | non-zero |
| `--doctor` (persist=True) with proven identity | 0 or 1 per gate/duplicate/provider-fail checks (unchanged) |
| `--doctor` (persist=True) with unproven identity | 1, no evidence written |
| `--doctor` (persist=False) | unaffected by the identity gate |

## Batch outcome matrix

See `BatchRetrievalIntegrationOutcome` reason codes: `retriever_module_unavailable`, `provider_credential_unavailable`, `event_store_unavailable`, `retrieval_failed`, `all_integrations_failed`, `partial_failure` (all `success=False`); `no_terminal_batches_yet`, `idempotent_replay_only`, `fully_integrated` (all `success=True`).

## Source identity behavior

`get_git_sha()` unchanged (best-effort, never raises). `required_execution_source_identity()` is the fail-closed layer: raises `SourceIdentityUnprovenError` unless the result is a plausible 40/64-char lowercase hex string. Gated before: (1) the main phase-execution loop, (2) `run_doctor_full`'s `persist=True` write block, (3) `validate_pre_live_gate_v25.py`'s `run_gate()` via the new `SOURCE_IDENTITY_UNPROVEN` blocker. **Not** gated (disclosed residual, non-blocking): `write_run_manifest`/`write_runner_identity` (called before the phase-loop gate; the run is still correctly marked `FAILED` afterward on identity failure) and the `--preset` confidence-ramp certification write (its payload does not embed `git_sha` for this call path).

## Tests

Focused / batch / cert / full-suite: all PASS. See `VALIDATION.json` for exact commands and results.

## Pre-commit / secret scan

PASS on both substantive commits (repo's `repo_preflight` hook). No secrets in new code/tests.

## #1136 / #1183 overlap and carry-forward

Both COMPATIBLE, not superseded, carry-forward-required, no conflict. Full detail in `OPEN_PR_CARRY_FORWARD.md`.

## Implementer identity

Claude Code, `developer` subagent (in-process Agent tool), model inherited from session (Sonnet 5). Self-repair of the `--doctor` gap performed by the orchestrating session itself, same family/model.

## Controlling auditor identity/verdict

`grok-cli` / requested `grok-4.5`, API-reported `grok-4.5-build` (xAI). **PASS_WITH_RISKS**, 5 explicit non-blocking risks (see `AUDITOR_REPORT.md`). Genuinely independent of both the implementer (Claude/Anthropic) and the supporting reviewer (GPT-5-pro/OpenAI).

## Proof paths

`proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/{PROOF.json, VALIDATION.json, MANIFEST.json, COMMAND_LOG.md, CHANGED_FILES.txt, HANDOFF.md, AUDITOR_REPORT.md, OPEN_PR_CARRY_FORWARD.md, GROK_AUDIT_PROMPT.md, GROK_AUDIT_OUTPUT.json, scratch_notes.md}`

## Conflicts / UNKNOWN / NOT_RUN

- `task_packet_schema`: NOT_RUN — the canonical `dopetask-canonical-spec.json`'s `execution.agent` enum (`{gemini, codex, vibe, shell}`) has no entry that truthfully represents a Claude Code subagent implementer. Left honest rather than mislabeled; `task-packets/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001.json` exists as an informational, unvalidated companion.
- `adjacent_rte_cli_smoke`: not separately isolated as a narrower subset; superseded by the full relevant-suite run, which already covers `services/repo-truth-extractor/tests` in its entirety.

## Risks (from the controlling audit, all non-blocking)

See `AUDITOR_REPORT.md` R1–R5. Summary: `RUN_MANIFEST.json`/`RUNNER_IDENTITY.json` can transiently contain `git_sha:"UNKNOWN"` before the run is marked `FAILED`; the `--preset` confidence-ramp path isn't identity-gated (but its certification payload doesn't embed `git_sha` for that path); some new tests are structural/source-order guards rather than full runtime e2e.

## Rollback

Not pushed. Delete local branch/worktree to fully undo; no remote or shared state touched.

## Governing gate

Packet §22 pre-push gate: all items PASS except `task_packet_schema` (NOT_RUN, explained above) and the two items explicitly marked superseded/not-separately-run. §25 stop conditions: none triggered that weren't already resolved (the schema-representation stop conditions for both the audit tool and the task-packet agent field were resolved by finding/using the correct non-mislabeling route rather than forcing through).

## Next action / requested from operator

Publication (PR creation, mark-ready, merge) is **not authorized** by this packet under any circumstance (§27: "Publication is not authorized. If later separately authorized..."). This packet's disposition is:

```
PASS_WITH_RISKS_READY_FOR_PROOF_CLOSURE
```

Awaiting explicit separate authorization for: (a) whether to open a draft PR per §27, and (b) whether to pursue the recommended non-blocking follow-on (moving `required_execution_source_identity()` earlier than `write_run_manifest`/`write_runner_identity`).

## Evidence required for next verdict

None outstanding for this packet's own scope. A future PR-publication decision would need: explicit "AUTHORIZE PUBLICATION" instruction, plus a fresh drift refresh of `origin/main`/#1136/#1183 at that time per §23/§25.
