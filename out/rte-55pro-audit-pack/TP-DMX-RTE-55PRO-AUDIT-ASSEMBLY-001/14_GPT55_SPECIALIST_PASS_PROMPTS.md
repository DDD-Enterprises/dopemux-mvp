# GPT-5.5 Specialist Pass Prompts

## Runtime Architecture Audit

Audit RTE runtime architecture and authority boundaries. Trace `dopemux rte` CLI wiring, v5/v4/v3 layering, direct runners, pre-live gate, output roots, and helper modules. Produce findings by severity, evidence ledger, unknowns, and commit-sized remediation slices. Do not implement.

## Prescan And Inventory Audit

Audit prescan, corpus walking, source inclusion/exclusion, generated/proof/secret-bearing file handling, duplicate detection, enrichment, provider catalog, cost estimation, and routing-plan generation. Verify source authority and failure modes from uploaded files only. Output severity findings, evidence, and targeted test gaps.

## Prompt, Model, And Escalation Audit

Audit promptset loading, prompt registries, v4/generated/v3 prompt authority, schema alignment, model maps, provider routing, fallback ladders, comparison lanes, and escalation gates. Mark external provider facts as EXTERNAL_NEEDED unless a Deep Research brief is supplied.

## Sidefill, Enrichment, And Repair Audit

Audit sidefill/enrichment/repair/retry/resume paths. Focus on provenance, lossy repair marking, hallucination boundaries, schema repair, failure classification, duplicate emissions, idempotency, and proof visibility. Separate OBSERVED runtime behavior from INFERRED intent.

## Proof, Artifact, And Schema Audit

Audit `PROOF_PACK.json`, `COVERAGE_ROLLUP.json`, `RUN_DASHBOARD.json`, `STEP_METRICS.json`, `FAILURE_INDEX.json`, manifests, logs, normalized outputs, preflight/doctor/status outputs, and proof contract alignment. Identify schema gaps, ordering instability, overclaiming, and missing tests.

## UX/UI Operator Audit

Audit the operator journey: preflight, doctor, prescan, phase run, status monitoring, coverage/report review, failure handling, proof review, resume/retry, and legacy command confusion. Produce UX risks grounded in CLI/runtime evidence and propose minimal operator-facing improvements.

## Determinism, Security, And Test Audit

Audit deterministic ordering, stable serialization, idempotency, replay safety, secret handling, prompt injection risks, cost abort behavior, provider-key handling, test coverage, and validation posture. Identify high-risk untested branches and safe validation commands.

## Final Synthesis And Triage Audit

Synthesize all prior passes. Deduplicate findings, rank by risk, produce final GO/CONDITIONAL_GO/NO_GO/UNKNOWN verdict, map findings to candidate task packets, and list exact Codex addendum requests. Preserve unresolved conflicts.
