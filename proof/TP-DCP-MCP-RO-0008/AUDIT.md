# TP-DCP-MCP-RO-0008 — Embedded Audit

**Verdict: PASS_WITH_RISKS** (non-blocking). Final hardening packet. Self-audit by
the implementing agent against the packet invariants and STOP-IFs.

## 1. Scope conformance

- Allowlist only: `services/dcp-readonly-facade/**` + `docs/03-reference/dcp/chatgpt-mcp-readonly/**` + `proof/TP-DCP-MCP-RO-0008/**`. No `services/{dope-context,dopecon-bridge,task-orchestrator,working-memory-assistant}/**`, no `docker/**`, no `.env*`, no `.dopemux/**`.
- Diff: 5 source/doc files (`envelope.py`, `tools.py`, `test_packet_0008.py`, `RESPONSE_ENVELOPE_SCHEMA.md`, `ARCHITECTURE.md`) + proof bundle.

## 2. Invariants — evidence

| Invariant | Evidence | Verdict |
| --- | --- | --- |
| Denied routes remain denied | `test_no_mutating_route_strings_in_executable_paths`, `test_no_mutating_http_verbs_in_facade_source`, `test_denied_and_allowed_routes_stay_disjoint` + existing `test_route_denylist`/`test_packet_0006` | PASS |
| Cross-project evidence cannot leak | `test_list_proof_bundles_never_leaks_other_project`, `test_fetch_other_projects_bundle_id_is_blocked`, `test_symlink_from_one_project_into_another_is_blocked`, `test_resolve_binds_only_the_requested_project`, `test_isolation_holds_both_directions` | PASS |
| All outputs include envelope | `untrusted` added to `ENVELOPE_FIELDS`; `test_envelope_has_all_canonical_fields` (existing) + `test_untrusted_is_always_present_on_every_envelope_shape` | PASS |
| Untrusted retrieved content is marked untrusted | **Implemented** `untrusted` flag (fail-closed default True; facade-authored=False). `test_build_envelope_defaults_untrusted_true`, `test_facade_authored_tools_are_trusted`, `test_retrieved_content_tools_are_untrusted` | PASS |
| Prompt-injection wrapping | `test_injection_content_is_confined_to_data_and_marked_untrusted`, `test_injection_in_proof_bundle_content_is_inert` — injection text confined to `data`, marked untrusted, never elevated to facade-authored fields, not acted on | PASS |
| Secret redaction tested | `test_secrets_and_paths_redacted_in_backend_payload` (sk-/ghp_/AKIA/Bearer/KEY=VALUE/abs-path) + existing `test_redaction` | PASS |
| No arbitrary path/URL/port/backend | resolver/proofs containment unchanged; caller supplies only `project_id` + typed params (existing tests + isolation tests) | PASS |
| Stale proof detectable | `test_stale_proof_emits_warning`, `test_fresh_proof_has_no_stale_warning` | PASS |
| No writes / no shell | `test_no_filesystem_write_ops_in_facade_source`, `test_no_shell_or_eval_in_facade_source`, `test_gitstate_only_runs_read_only_git_verbs` + `NO_WRITE_REVIEW.md` | PASS |
| PR proof current to head SHA | PROOF.json head_sha recorded at commit time | PASS |

## 3. STOP-IF review

None triggered: no denylist weakened (additive `untrusted` field only); no write path discovered (gitstate is read-only git, fixed argv); cross-project isolation holds both directions; redaction holds; stale-proof detectable; embedded audit verdict is PASS_WITH_RISKS (not FAIL/NEEDS_SUPERVISOR).

## 4. Contract change — `untrusted` envelope field

The envelope is a contract-sensitive surface. The change is **additive and fail-closed**: a new `untrusted` boolean (default `True`) plus a doc update (`RESPONSE_ENVELOPE_SCHEMA.md` §6, `ARCHITECTURE.md` §7). Canonical writer (`envelope.build_envelope`) and all callers (`tools.py`) updated together; the only consumers are the MCP tool surface (returns the dict) and the tests — all in-tree and updated. Backward-compatible: all 108 pre-existing tests pass unchanged.

## 5. Findings

| ID | Severity | Status | Note |
| --- | --- | --- | --- |
| F-0008-LOW-1 | LOW | ACCEPTED_RISK | `untrusted` is an advisory marker: it signals the client (ChatGPT) to treat `data` as inert, but cannot force the client to honor it. Defence-in-depth: content is also structurally confined to `data` (never merged into facade-authored fields), so the marker + structural separation together are the control. |
| F-0008-LOW-2 | LOW | ACCEPTED_RISK | dope-context tools remain Phase-1 BLOCKED (MCP JSON-RPC transport not bridged); injection/redaction for that path is therefore exercised against the ConPort/dope-memory/proof surfaces, not dope-context (which returns no data in Phase 1). Carried from TP-0006. |
| F-0008-INFO-1 | INFO | ACCEPTED_RISK | Pre-existing pyright `str|None` narrowing notes on backend-call args in `tools.py` are unchanged by this packet (the `if missing: return blocked` guard narrows at runtime). Out of scope; not introduced here. |

## 6. Validation buckets

- **PASS:** full facade suite 130 passed, 1 skipped (exit 0); `compileall` exit 0; no-write hazard scan classified (all benign); secret scan no real secrets; diff allowlist-only.
- **NOT_RUN:** live backend integration (suite mocks all HTTP; opt-in `DCP_FACADE_LIVE_TESTS=1` not run — by design); live tunnel/connector (out of scope, TP-0007 manual checklist).
- **FAIL:** none.
