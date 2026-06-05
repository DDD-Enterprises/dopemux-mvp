# 03 — Code Review · TP-DMX-ORCH-CS-P1

## Scope reviewed
`scripts/validate_dx_surface.py`, `.taskorchestrator/surface_manifest.json`,
`tests/orchestrator/test_dx_surface_manifest.py`, the inventory doc, the packet JSON.

## Correctness
- Manifest classifications match `MCP_TOOL_MANIFEST.json` `destructiveHint` for the 13 shared
  tools; `claim_item` documented as inferred (live v3 only). Verified against the extracted
  annotation table.
- Validator rules cover: (a) read command must use only read-only tools; (b) unknown tool;
  (c) orchestrator-tool drift vs manifest; (d) uncatalogued file; (e) stale manifest entry;
  (f) internal consistency (read_surface == read-class commands). All exercised by the run.
- Frontmatter parse uses PyYAML on the first `---`…`---` block — robust to the multi-line flow
  sequence used by `allowed-tools`. Non-orchestrator tools (Bash/Read/ConPort) are ignored;
  only `mcp__task-orchestrator__*` are checked, which correctly makes `implement` (composite)
  trivially conform with zero orchestrator tools.

## Design
- Manifest as **independent authority** (not generated from frontmatter) is the key property:
  it gives the validator something to violate. Confirmed by the bite test.
- `run_validation(root)` is pure (no print/exit) → testable against a tampered tmp copy without
  touching the real tree. `main()` wraps it with CLI/printing and an optional `--root`.

## Safety boundary
- Validator imports nothing that calls the MCP; only `json`, `pathlib`, `yaml`. Read-only.
- No existing command/config/ADR edited (additive-only diff confirmed via `git status`).

## Observations (non-blocking, deferred)
- `implement.md` uses legacy aliases (`mcp__zen__*`, `mcp__serena__*`) — pre-existing; noted in
  the inventory, fix out of scope.
- `dx-command-authoring.md` line 72 is stale re `claim_item` — noted; doc-fix deferred.
- Validator is advisory (gates committed files, not live MCP calls) — stated in the inventory's
  MetaMCP note. Wiring into CI/pre-commit deferred to a follow-up.

## Verdict
PASS — additive, read-only, internally consistent, enforced by a biting test.
