# Audit — TP-DCP-MCP-RO-0002 (Architecture Doc And Multi Project Contract)

Auditor focus per packet `embedded_audit`. Verdict: **PASS_WITH_RISKS** (non-blocking; risks tracked below and in downstream packets).

## Deviation recorded: discovery inventory restored

`OBSERVED`: the prior commit on this branch (`78b04fb33`) shipped a script `generate_docs.py` that **overwrote** the canonical discovery artifact `READ_ONLY_SURFACE_INVENTORY.json` with a hardcoded 53-line stub (4 generic surfaces). The script body literally embeds the stub inventory and writes it over the file (verified by reading `generate_docs.py` before deletion).

Action taken:
- Restored the canonical 431-line artifact verbatim from the discovery commit: `git show 7c9ac6a45:docs/03-reference/dcp/chatgpt-mcp-readonly/READ_ONLY_SURFACE_INVENTORY.json` (artifact header: `packet_id: TP-DCP-MCP-RO-0001`, `head_sha: 9667f5e2d`). Line count 53 → 431.
- Deleted `generate_docs.py` (out of scope: packet forbids runtime code; the script re-clobbers on run and references a now-deleted temp path).
- All 7 prose docs rewritten as faithful transcriptions of the restored inventory + load-pack decisions (not net-new design). `TASK_ORCHESTRATOR_LOAD.md` retained (already complete).

`7c9ac6a45` lives on branch `dcp/chatgpt-mcp-readonly-discovery`; it is **not** an ancestor of `main`. This packet's PR therefore introduces the canonical inventory onto the 0002 branch — expected, since 0002 treats the inventory as a validated input.

## 1. Does the architecture accidentally make the facade an authority?

No. `ARCHITECTURE.md` §1 and the top-of-file authority note state the facade is an "evidence projection layer, not a canonical source" with "no write authority." §17 mandates every envelope carry `source_system` + `authority_label`; the facade is never labelled an authority. `RESPONSE_ENVELOPE_SCHEMA.md` carries `authority_label` on every payload.

## 2. Does any doc allow dopecon-bridge in Phase 1?

No. `ARCHITECTURE.md` §14, `TOOL_CONTRACT.md` §2, `SECURITY_MODEL.md` §6, and `DECISIONS.md` D4 all deny `dopecon-bridge /ddg/decisions`, citing the `OBSERVED` `PROXY` authority label and transport-confusion risk.

## 3. Does any doc allow generic search/fetch before source-label integrity is implemented?

No. `search_all` is denied across `ARCHITECTURE.md` §12/§15, `TOOL_CONTRACT.md` §2, `SECURITY_MODEL.md` §3, `DECISIONS.md` D5 (cites `READ_WITH_SIDE_EFFECT_RISK`: bridge + Redis). Generic search/fetch is explicitly deferred to Phase 2 (`ARCHITECTURE.md` §18, `DECISIONS.md` D3). Phase-1 dope-context hits are labelled `DERIVED` until exact-source fetch exists.

## 4. Does the registry design auto-expose initialized workspaces?

No. `MULTI_PROJECT_REGISTRY_CONTRACT.md` §2 makes eligibility-≠-exposure a core invariant: `dopemux init` is "eligibility, not consent"; exposure requires an explicit `enabled: true` registry entry. Absent an entry, a project does not exist to the facade (fail-closed). Validation rules (§4) reject unknown/disabled projects and path/symlink escapes.

## 5. Are the stop conditions strong enough?

Yes, with one tracked risk. The packet stop conditions ("working tree has unrelated changes", "docs location ambiguous", "a design doc requires a runtime fact not in 0001", "secret appears", "any runtime/service/config file would need editing") are honoured: only docs + INDEX + proof changed; no `src/`/`services/`/`docker/`/`compose` touched; no secrets; the one runtime fact gap (the `dopemux init` marker) is left `UNKNOWN` and routed to 0003 rather than invented.

## Residual risks (non-blocking)

- `CONFLICTING`/`PROPOSED`: the 8/7 phase-1 surface split is reconciled to the inventory `summary`, but the inventory has no per-surface `phase_1_recommended` flag — the identity of the 2 *deferred reads* (`/api/custom_data` + one of `/api/search`|`/api/decisions`) is inferred. Flagged inline in `ARCHITECTURE.md` §15 and `TOOL_CONTRACT.md` §2; resolved concretely in 0004/0005.
- `PROPOSED`: `RESPONSE_ENVELOPE_SCHEMA.md` introduces `OK` as the success status token (load pack only names `PARTIAL`/`BLOCKED`). Flagged inline; reconcile to implementation in 0004.
- `UNKNOWN`: `dopemux init` marker contract — deferred to 0003 (a packet dependency, not a gap in this packet).
- Untracked `run_checks.sh` (a prior-attempt artifact with absolute paths) is **excluded** from the commit; removed for workspace hygiene.
