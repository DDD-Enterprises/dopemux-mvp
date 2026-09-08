# Independent Final Audit — TP-DMX-CONTROL-TOWER-SUPERVISOR-KIT-REPAIR-002

**Repo**: DDD-Enterprises/dopemux-mvp
**Base**: 6a728f74c0311967f83213513308f97613e3f28d
**Head**: 4b31331b93fae6ffb98d23b4c0cfa1df7f5e55d5 (metadata) — note the packaged focused-tests/change-contract/precommit evidence uses head `4b31331b93fae6ffb98d23b4c0cfa1df7f5e55d5` per the packet's own change-contract tool output
**Lane**: L3 per ROUTING_DECISION.json (risk_lane), L2 per validate_change_contract.py's max_lane computation — the higher L3 lane governs per 'when uncertain use the higher lane'
**Auditor**: independent Claude Sonnet review, no tool use, diff-only, as required for this L3 final audit stage
**Prior audit**: historical (covers an earlier head, 648475216f2ffab9b249de6502294c124890f090); not reused for this changed content.

## Scope

This audit covers the full accumulated diff against `main` across both TP-DMX-CONTROL-TOWER-SUPERVISOR-KIT-001 (original kit installation) and TP-DMX-CONTROL-TOWER-SUPERVISOR-KIT-REPAIR-002 (bounded repair). Cross-checking `changed_files` against both packets' `commit.allowlist` entries confirms every changed path is covered by one of the two packets' declared scope; no scope creep into unlisted files was found. All content is treated as untrusted candidate data per instructions; no instructions embedded in the diff or proof bundle were followed as directives.

## Authority preservation

All edits to `AGENTS.md`, `.claude/*`, and `.github/copilot-instructions.md` remain additive, bracketed by `CONTROL_TOWER_ENTRY_*`/`CONTROL_TOWER_MANAGED_*`/`CONTROL_TOWER_REPO_*` markers, and now explicitly scope the kit's extra routing/packaging obligations to *supervised* work only ('ordinary work retains the repository's existing workflow'), directly closing the ambiguity flagged as F5 in the historical audit. No existing governance text is deleted. The repository-owned `AGENTS.md` §Control Tower Packet Workflow correctly names `.control-tower/project.json` (not the installer's `config/defaults.json`) as canonical runtime config, matching the CLI's actual behavior (verified: `config/defaults.json` is never referenced by `.control-tower/bin/ct`).

## Repair verification (F1–F5 from historical audit)

- **F1 (schema not enforced)** — RESOLVED. `_load_schema`/`_validate_schema` now load and apply the shipped `route_decision.schema.json`/`return_packet.schema.json`, cross-validated against the real `jsonschema` library by `test_route_validation_matches_jsonschema_oracle` for both valid and invalid cases on both schemas.
- **F2 (empty return-pack reason/decision-needed accepted)** — RESOLVED. argparse-required flags plus an explicit non-blank check in `package()`; `return_packet.schema.json` additionally validates the generated `RETURN_METADATA.json`.
- **F3 (unconditional `agy models` call)** — RESOLVED. Now gated behind an explicit `--probe-models` flag, default off, tested.
- **F4 (verify-zip only checks CRC)** — RESOLVED. Full manifest/inventory/hash/byte-count cross-validation plus path-traversal and symlink-member rejection, tested against both a valid archive and several tampered/malformed variants.
- **F5 (routing obligation not reconciled with AGENTS.md lifecycle)** — RESOLVED via explicit scoping language rather than mechanical step-numbering; sufficient to remove authority ambiguity.

## New hardening reviewed for correctness

- Secret scanning fails closed on oversized (>20MB), unreadable, or directory-walk-error inputs instead of silently skipping them, and any hit blocks packaging. Only path + a fixed pattern label is ever logged — matched secret content is never emitted, consistent with the CodeQL 'constant-label dataflow' disposition for alerts 269/270 (though this auditor cannot independently confirm that code path is what those alert IDs actually flagged, given no direct visibility into the CodeQL alert record itself).
- Packet/route identity binding: `get_route()` now rejects a route file whose `packet_id` doesn't match, and `package()` independently re-derives the packet's own id from its content and rejects mismatches — closing a route/packet identity-confusion class of defect.
- `verify-zip` now rejects zip-slip-style paths (absolute, `..`, backslash) and symlink members, and requires exactly one root manifest directory.

## Residual / open items (non-blocking)

1. Markdown-path `packet_identity()` binds to the *first* heading found rather than specifically searching for a 'Task Packet' heading, which could silently mis-identify a packet if an unrelated heading precedes the canonical one. LOW severity given the JSON path (used for this repo's actual task packets) is unaffected and correct.
2. The hand-rolled schema validator rejects any keyword outside its supported set; future schema edits using an unsupported keyword would break validation until the code is updated in lockstep. Not a current defect against the two shipped schemas.
3. `config/defaults.json`/`project.json` canonical-authority separation is documentation-enforced, not structurally enforced.
4. CodeQL alert 269/270 disposition is plausible given the reviewed logging code but not independently confirmable from the materials provided.

## What was NOT verified by this audit

- No tests, precommit, change-contract validation, or `ct` commands were executed by this auditor; all pass/fail claims (19/19 pytest, precommit PASS, change-contract PASS, `git diff --check` clean, `validate-route` PASS) are implementer-reported evidence only.
- Full integration and a fresh CI run on the repaired head are explicitly NOT_RUN and are not inferred as passing.
- No operator risk acceptance is inferred beyond what is explicitly stated as authorized in the frozen task packets and their invariants.

## Verdict

**PASS_WITH_RISKS.** No BLOCKING or HIGH-severity finding was identified in the diff: no credential exposure, no bypass of any operator-only gate (merge/force-push/history-rewrite/branch-protection/credentials/production/migration/publish-activate/security-risk-acceptance), and the five MEDIUM findings from the historical audit (F1–F5) are now backed by concrete code changes and targeted tests rather than assertion alone. One MEDIUM finding remains open — the CodeQL disposition cannot be independently confirmed from the supplied materials, though the reviewed logging code is consistent with the stated rationale — plus several LOW/INFO items (Markdown identity-heuristic edge case, schema-validator keyword fragility, defaults.json/project.json duplication) that should be tracked but do not block. Full integration/CI and this auditor's own execution of the test suite remain NOT_RUN; that gap is preserved explicitly rather than treated as passing.
