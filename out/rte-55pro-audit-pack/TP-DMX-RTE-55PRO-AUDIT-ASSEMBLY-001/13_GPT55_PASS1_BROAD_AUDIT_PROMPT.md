# GPT-5.5 Pro Pass 1 Broad Audit Prompt

You are starting Pass 1 of a multi-pass deep audit of Dopemux Repo Truth Extractor (RTE). Do not implement. Do not infer repo facts without uploaded source evidence. Preserve OBSERVED, INFERRED, UNKNOWN, CONFLICTING, and CLAIMED labels.

Use the uploaded files in this order:
1. Project instructions and authority docs.
2. RTE runtime and CLI files.
3. Promptset/model/proof/test files.
4. Prior audit/proof/remediation artifacts.
5. Generated audit-pack navigation files.

Audit RTE end to end across:
- runtime architecture and authority boundaries
- prescan/corpus/source hygiene
- prompts and promptset authority
- UX/UI/operator journey
- model/provider routing, escalation, fallback, comparison, and batch handling
- sidefill, enrichment, repair, retry, and resume
- structured outputs and schema enforcement
- proof artifacts, dashboards, manifests, logs, coverage, and validation gates
- determinism, idempotency, safety, secret handling, and test posture

Required output:

1. Executive verdict: GO, CONDITIONAL_GO, NO_GO, or UNKNOWN. Include the exact scope of the verdict.
2. Findings by severity: CRITICAL, HIGH, MEDIUM, LOW, INFO. Each finding must include claim label, evidence path/function/line where possible, impact, and remediation direction.
3. Findings by axis, using the audit axes above.
4. Evidence ledger: table of every important file/path used and what it proves.
5. Unknowns/conflicts: preserve contradictions between runtime, docs, proofs, and generated artifacts.
6. Opus/Gemini crosswalk: map prior findings/remediations to current source evidence; do not fabricate missing Opus findings.
7. Remediation roadmap: ordered, commit-sized slices with recommended task-packet IDs under series `DMX-RTE-55PRO-AUDIT`.
8. Candidate task packet series: include title, scope, allowlist, validation, and risk for each candidate.
9. Deep Research questions: external/current facts only, especially provider structured-output behavior and audit pipeline best practices.
10. Codex addendum requests: list missing files, line excerpts, command outputs, or proof artifacts needed for the next pass.

Rules:
- Do not ask Deep Research to inspect repo runtime.
- Do not hide uncertainty.
- Do not claim tests passed unless the uploaded proof or command output proves it.
- Do not treat generated audit-pack files as source authority.
