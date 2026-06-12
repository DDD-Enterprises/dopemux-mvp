# DMX-DCP-MODEL-ROUTING-MVP-0000 — SURFACE_CENSUS.md

## Summary Table

| Surface | Path | Type | Authority | Read/write posture | Evidence | Confidence | Notes |
|---------|------|------|-----------|--------------------|----------|------------|-------|
| Dopemux CLI | src/dopemux/cli.py | Python entrypoint | OBSERVED | Read + delegated write via subcommands | uv run --help (50+ commands) | HIGH | 50+ top-level commands; kernel/mcp/routing/workflow/memory subtrees |
| Dopetask wrapper | scripts/dopetask | Shell/Python CLI | OBSERVED | Read + TP lifecycle (mutating) | --help + doctor PASSED | HIGH | 20+ subcommands; compile/run/collect/gate/promote/commit/loop |
| DCP Schemas | schemas/dcp/ | JSON Schema | OBSERVED | Read-only (schema definitions) | ls + file reads | HIGH | 11 schemas: approval, chronicle, control, evidence, mutation_class, red_lane_* |
| Task Orchestrator | services/task-orchestrator/ | Python MCP server | OBSERVED | Read + write (claimed) | server.py + mcp-proxy-config | MEDIUM | 13-tool surface; workspace-scoped SQLite; write posture UNKNOWN |
| PR Steward | .github/workflows/pr-steward.yml + src/dopemux_pr_merge_specialist/ | Workflow + Python | OBSERVED | Write (forbidden) | workflow file + DCP test | HIGH | Explicitly forbidden in allowlist test |
| MCP Servers | compose.yml + .mcp.json + mcp-proxy-config.* | Docker + config | OBSERVED | Per-server (mixed) | registry.yaml + compose | HIGH | 22 services registered; conport/pal/serena/dope-context/exa/etc. |
| Slash Commands | .claude/commands/ + src/dopemux/commands/ | Markdown + Python | OBSERVED | Delegated | ls (52 + 27 files) | HIGH | 52 .md in .claude/commands; 27 modules in src/dopemux/commands |
| Workflows | .github/workflows/ | YAML | OBSERVED | CI automation | ls (18 files) | HIGH | ci-complete, pr-steward, gemini-*, security-*, embedded-audit |
| Hooks | .pre-commit-config.yaml + .githooks/ | YAML + shell | OBSERVED | Pre-commit gates | .pre-commit-config.yaml | HIGH | 8+ hooks: ruff, mypy, markdownlint, filename hygiene, pytest |
| CI Checks | .github/workflows/ + Makefile | YAML + make | OBSERVED | Quality gates | Makefile (50+ targets) | HIGH | test-*, lint, quality, docs-audit, pm-*, x-*, orchestrator |
| Model/Provider Configs | litellm.config.yaml + model_map_v2_tp008.yaml | YAML | OBSERVED | Read-only routing | file reads | HIGH | 14 models, fallbacks, alias_map; lane/step policy for D/C/A/B/G/H/Q/R/T/Z |
| Runner/Tool Configs | .mcp.json + mcp-proxy-config.* | JSON/YAML | OBSERVED | Read-only | file reads | HIGH | 3 native + 12+ wrapped servers |
| Agent Definitions | .github/agents/ + .claude/agents/ + .claude/personas/ | Markdown | OBSERVED | Read-only | ls (4 + 8 + 51 files) | HIGH | 4 GitHub agents; 8 Claude agents; 51 personas |
| Proof Bundles | proof/ + task-packets/ + out/ | JSON/MD | OBSERVED | Read-only artifacts | ls (231 + 95 + 11) | HIGH | DCP, pr_merge, rte-*, cockpit-*, TP-DCP-* |
| Service Boundaries | services/registry.yaml + compose.yml | YAML | OBSERVED | Infrastructure contracts | file reads | HIGH | 22 services with ports/health contracts |
| Red Lanes | src/dopemux_pr_merge_specialist/ + scripts/batch_resolve_and_merge.py | Python | OBSERVED | Mutation (forbidden) | DCP test + rg | HIGH | Explicitly listed in forbidden_prefixes |

**Total Surfaces Catalogued**: 16
**High Confidence**: 14
**Medium Confidence**: 1 (Task Orchestrator write posture)
**Unknowns Preserved**: 5 (see UNKNOWN_AND_CONFLICT_LEDGER.md)
