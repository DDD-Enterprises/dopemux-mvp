# RTE Deep Audit Stage 8: System Boundaries & Dependencies

## Trace of Cross-Plane Dependencies
- **RTE → Project Root:** Uses `.dopetaskroot` to resolve absolute paths for deterministic scanning.
- **RTE → Governance Plane:** Consumes `config/pricing.yaml` to enforce spend caps. This is a **Canonical** dependency.
- **RTE → Service Plane:** Consumes `services/registry.yaml` as the authoritative list of service identities to scan. This is an **Operational** dependency.
- **CLI → RTE:** `src/dopemux` uses `subprocess` to launch the runner, maintaining a process-level boundary.

## Boundary Overreach Analysis
- **Code Isolation:** No direct imports from `dope_context`, `dope_memory`, or `task_orchestrator` were found in the RTE library. The system maintains strict process-level isolation.
- **Write Boundaries:** RTE only writes to its dedicated `extraction/repo-truth-extractor/` directory. It does NOT attempt to modify `src/` or `config/` files directly.

## Authority Confusion Risks
- **Upgrades Alias:** The `dopemux upgrades` command name is misleading. It suggests a mutation of runtime code/state, but it only performs extraction. This is a "Semantic Overreach" risk.
- **Derived-Surface Confusion:** Artifacts like `REPO_MCP_SERVER_DEFS.json` are derived truth. If an operator mistakes these for the actual `mcp-proxy-config.yaml`, they might attempt to debug the system using the wrong authority.

## Verdict
System boundaries are **Strongly Enforced at the Process Level**. The primary risk is "Operator Semantic Confusion" caused by misleading command aliases (upgrades) and the existence of multiple truth-derived artifacts that mirror canonical configurations.
