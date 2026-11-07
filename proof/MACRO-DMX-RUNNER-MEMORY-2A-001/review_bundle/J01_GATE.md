# MACRO-DMX-RUNNER-MEMORY-2A-001 — J01-GATE Record

**Recorded**: 2026-10-31 by the team lead (Control Tower supervisor session). Authority: NONE.

## W00 return, as checked by the team lead

| Item | Value |
|---|---|
| Child status | READY_FOR_AUDIT |
| Evidence file | `W00_FINDINGS.md`, sha256 `4baa2184923bf0522d2ebb930c09d3e9eb394920c5ac4451f69f2ad0c4d1f117`, 743 lines |
| Counters (completion notice) | 1,117,647 ms elapsed; 411,169 subagent tokens; 120 tool uses (caps 150 min / 1,800,000 / 350) |
| advisor_calls | 0 (child-reported; not structurally verified from its transcript) |
| observed_model | UNKNOWN (requested `claude-sonnet-5-5`; no runtime receipt) |
| Write scope | only `W00_FINDINGS.md` new; `task-packets/MACRO-DMX-RUNNER-MEMORY-2A-001/` was the team lead's pre-existing untracked package (the literal "equals exactly" verify wording could not account for it) |
| GATE_TABLE | parses; `workstream_go` W01 NO_GO, W02 NO_GO, W03 GO, W04 GO_REDUCED, W05 NO_GO, W06 GO_REDUCED, W07 GO_REDUCED, W08 GO_REDUCED |
| Secret scan | clean |

Team-lead spot checks of the two decisive claims (independent of the child):

- `src/dopemux/dcp/red_lane_rules.py:85-86` forbids `services/working-memory-assistant/.*` and `docker/mcp-servers-source/conport/.*` (DCP-RED-MERGE-SEAM-0001). **Confirmed.**
- `gh release list -R jpicklyk/task-orchestrator`: latest `v3.16.0` (2026-10-02); `git/matching-refs/tags/v4` returns 0 refs. **Confirmed**: no upstream 4.0.0 release or tag.

## Gate decision

J01-GATE condition: dispatch a workstream only if its verdict is GO or GO_REDUCED **and** no `design_changes` entry lists it. The 16 `design_changes` entries together name W01-W08, so **every build workstream is held**. Nothing is dispatched. Per the macro, the supervisor issues a revision (R2) after operator rulings; R2 needs its own authorization.

## Rulings R2 needs from the operator

1. **DCP red lane** (W01, W02, W08's ConPort client): an operator-approved narrow carve-out in the ADR-224/226 pattern, or an operator decision to run those workstreams on a non-Claude runner with the PR Steward `dcp_boundary` approval recorded.
2. **Task orchestrator 4.0.0** (W05, and the gate check in W06): upstream has not released it, and 4.0 removes every 3.x tool this repo's `/dx:*` commands, hooks, manifests and policy tables call. Either move the orchestrator out of Wave 2A (memory identity ships first) or hold Wave 2A for upstream.
3. **G2 scope** (W08, W01): file-level and Redis writers (`capture_client.py`, `native_hooks.py`, `eventbus_consumer.py`) have no HTTP route to authenticate, and about 15 in-repo ConPort REST writers sit outside W08's allowlist. Either re-word G2 to verified identity on HTTP writes (local writers recorded as self-asserted internal principals) and widen the ConPort-client work, or route those writers through HTTP.

The other design changes (token-file shapes, compose override in `docker_runtime.py`, the bridge handshake, ConPort's larger write surface and missing instance columns, the CI-run dope-memory test, catalog details, the cutover scan's exclusions, worktrees without `.envrc.dopemux-mcp`) are supervisor-level and will be folded into R2 and a design revision.
