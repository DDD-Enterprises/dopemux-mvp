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

## Round 2 — PR #826 review feedback addressed

1. **P1 (codex) — packet schema conformance.** Verified against repo truth: nearly all existing packets (`TP-DCP-0001`, `DMX-COCKPIT-PM-TEXTUAL`, all `generated/*`) conform to `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (`additionalProperties:false`); only the 7 DCP-MCP-RO packets deviated. **Fixed**: converted all 7 (`TP-DCP-MCP-RO-0002..0008.json`) to the canonical schema (`id/project/target/repo_binding/series/commit/pr/steps` + `invariants/depends_on/execution/pal_chain`). Rich content preserved — `scope.out`/`stop_conditions`/`forbidden_files` folded into `invariants`; `plan`/`exact_commands`/`validation_gates`/`proof_requirements` folded into `steps`. All 7 now pass `jsonschema.validate`. `series.parent_tp_id` chains 0001→…→0007; `final_packet:true` on 0008; `execution.agent:"codex"`.
2. **P2 (codex) — `get_index_status` not in inventory.** Correct: the inventory only carries dope-context `search_code`/`docs_search`/`search_all`. **Fixed**: `TOOL_CONTRACT.md` §1c now labels `get_index_status` source as `PROPOSED (load-pack 0006 scope; not in inventory)` with a ⚠️ note requiring it be added to the inventory with `OBSERVED` evidence (or deferred) before 0006 exposes it. `search_code_docs` and `get_workflow_status_snapshot` remain `OBSERVED` (their surfaces are inventoried).
3. **P2 (codex) — proof SHA vs reviewed commit.** The reviewed `d2820cea…` is GitHub's ephemeral PR merge ref, not a branch commit; `PROOF.json.head_sha` tracks the actual branch tip and is re-synced after each commit. Non-blocking, partially intrinsic to recording a SHA inside a committed file.
4. **CI fixes.** `docs-frontmatter-guard` added required frontmatter to the 7 packet `.md` stubs + `TASK_ORCHESTRATOR_LOAD.md`; `markdownlint` MD055 on `task-packets/INDEX.md` fixed (blank line before the section divider). All pre-commit hooks pass locally on the staged set.

## Round 3 — further PR #826 review feedback

5. **P2 (codex) — RO-0005/0008 write-hazard grep too broad.** Bare `POST` matched the side-effect-free read routes `/tools/memory_search` and `/tools/memory_replay_session`. **Fixed**: dropped bare `POST` from RO-0005/0008 (kept `PUT|PATCH|DELETE` + named mutating tokens; RO-0004 keeps bare `POST` — its invariant forbids all backend HTTP).
6. **P2 (codex) — COMMAND_LOG lacked final clean snapshot.** **Fixed**: appended a final post-commit snapshot (clean `git status`, head SHA, `git diff --stat <base>..HEAD`).
7. **P2 (codex) — `/workflow/state` missing from contract.** Verified `OBSERVED`: `GET /api/projects/{project_id}/workflow/state` (`services/task-orchestrator/app/api/project_workflow.py:385`, returns snapshot + `allowed_transitions`), already called by `src/dopemux/pm/adapters/orchestrator.py:48`, but absent from the 0001 inventory. **Fixed (deferred)**: documented as `UNCLASSIFIED`/deferred in `TOOL_CONTRACT.md` §1c + `ARCHITECTURE.md` §13/§20 — 0006 must inventory+classify it before exposing `get_workflow_status_snapshot` with `/state`. Not re-authoring 0001's inventory in this docs packet.
