# Independent Final Audit — TP-DMX-CONTROL-TOWER-SUPERVISOR-KIT-001

**Repo**: DDD-Enterprises/dopemux-mvp
**Base**: 6a728f74c0311967f83213513308f97613e3f28d
**Head**: 648475216f2ffab9b249de6502294c124890f090
**Lane**: L2 (per change-contract tool; see F6 caveat)
**Auditor**: independent Claude review, no tool use, diff-only

## Scope

This audit covers 25 changed files: doc/pointer edits in `.claude/*`, `.github/copilot-instructions.md`, and `AGENTS.md`; a new `.control-tower/` local supervisor kit (CLI, contracts, prompts, schemas, templates, config); a `.pre-commit-config.yaml` carve-out; a `root_hygiene_policy.json` allowlist addition; and the governing Task Packet JSON. No service activation, no CI/workflow changes, no runtime service wiring changes, and no observable secret material in the diff.

## Authority preservation

All `AGENTS.md`, `.claude/*`, and `.github/copilot-instructions.md` edits are additive banner/pointer insertions bracketed by clear markers (`CONTROL_TOWER_ENTRY_*`, `CONTROL_TOWER_MANAGED_*`, `CONTROL_TOWER_REPO_*`); no existing governance text is deleted or rewritten in this diff, and the new text explicitly subordinates itself to repository authority and live runtime/GitHub truth. The `.claude/llm.md`/`llms.md` edits remove stale hardcoded model names (`gemini-2.5-flash`, `o3`, etc.) in favor of 'current validated packet routing decision' language, which is a net improvement in doc/reality alignment rather than a regression.

## Correctness / tooling findings

Five MEDIUM findings were identified (F1-F5), none of which bypass an operator-only gate, expose credentials, or defeat the existing canonical proof/audit chain — the diff contains no git-mutating commands (no push/commit/merge/checkout -b) in `ct`, and the audit-required check for L2/L3 route records is correctly enforced independent of the flawed `schema_version` check:

- **F1**: the shipped `route_decision.schema.json`/`return_packet.schema.json` are not actually invoked by `ct`; validation is hand-rolled and diverges from the schema (e.g., no `const`/enum enforcement), so schema-conformance claims are not backed by code.
- **F2**: `return-pack` accepts empty `reason`/`decision-needed`, weakening the architecture-return escalation contract.
- **F3**: `runner-inventory` unconditionally shells out to `agy models` when present, a possible provider-side call folded into routine bootstrap.
- **F4**: `verify-zip` only checks ZIP CRC/readability, not the embedded manifest hashes — a narrower guarantee than the name implies.
- **F5**: new AGENTS.md sections layer a routing-decision obligation onto the file without visibly reconciling it against the existing 14-step canonical lifecycle in §4.

Two LOW findings (F6 lane-classification confirmation, F7 unused `defaults.json`) and two INFO items (F8 secret-scan heuristics, F9 unverifiable byte-identical provenance claim) round out the picture; none are blocking on their own.

## Prior review claims

The prior (adOps) review's P1/P2 claims were independently re-derived from the diff itself rather than taken on faith: the `schema_version` gap (P1) is real but does not itself bypass the audit-requirement check (recharacterized here as MEDIUM, not a security bypass); the empty return-packet fields (P2), `agy models` side effect (P2), and weak `verify-zip` (P2) claims are all corroborated by direct code reading. The fsmonitor-noise claim (P2) was not independently reproducible from static diff review and is not carried forward as a finding here. No prior finding is treated as resolved or accepted; that determination belongs to the operator.

## Verdict

**PASS_WITH_RISKS.** No BLOCKING or HIGH-severity finding was identified: the diff does not expose credentials, does not bypass any operator-only gate (merge/force-push/history-rewrite/branch-protection/credentials/production/migration/publish-activate/security-risk-acceptance), and explicitly preserves existing canonical governance and audit requirements while adding local advisory tooling. However, five MEDIUM findings (F1-F5) around the new tool's self-validation/verification claims and the scope of a governance-file addition are unresolved and should be evidenced or fixed — or explicitly risk-accepted by the operator — before this is treated as fully clean. Full integration/CI is NOT_RUN; the smoke evidence was executed in an out-of-tree fixture directory, not this repository's own CI, and does not substitute for it.
