TOOL_ACCESS=FULL
CUSTODY=MATCH  head=2b453caad13f19758923fee026cf69b52b7f0064
VERDICT=FAIL
POINTS:
  1: UPHELD — NUL-safe diff parsed 670 deletions. All under docs/04-explanation/history/sourceFiles/, all end ` (1).md`; each base deleted blob sha256 matched HEAD base-named twin; exceptions=0.
  2: UPHELD — HEAD retains exactly 9 ` (1).md` files in that directory; each lacks a base-named twin at HEAD; retained exceptions=0.
  3: UPHELD — `git grep -n -F -f` over 1340 deleted path/basename patterns at HEAD, excluding proof/, audit_inputs/, reports/, extraction/, claudedocs/, returned exit 1 and hits=0.
  4: DISPUTED — `dopemux mcp doctor` sidecar scope upheld: .mcp.json has conport/dope-memory/task-orchestrator, doctor builds service list from .mcp.json/defaults (src/dopemux/mcp/doctor.py:360, src/dopemux/mcp/runtime_state.py:312). `dopemux health` MCP-only Docker filter upheld (src/dopemux/health.py:268). `start-all --verify` forwarding upheld and scripts/start-all.sh absent (src/dopemux/commands/mcp_commands.py:411). But smoke claim false: docs say smoke gate covers `enabled_in_smoke` services (docker/.claude/claude.md:84, scripts/.claude/claude.md:45), while tools/smoke_runtime_gate.py hardcodes only conport/dopecon-bridge/task-orchestrator (tools/smoke_runtime_gate.py:111). services/registry.yaml has 7 enabled_in_smoke services out of 21: postgres, qdrant, dopecon-bridge, conport-http, task-orchestrator, dope-memory, adhd-engine.
  5: UPHELD — proof/.gitattributes contains only `**/auditor_scratch/** -whitespace`; `git check-attr whitespace` shows actual auditor_scratch unset, PROOF.json/proof/.gitattributes/.github path unspecified. `git diff --check` exited 0. config/repo_hygiene/root_hygiene_policy.json and .pre-commit-config.yaml unchanged.
  6: UPHELD — Changed paths limited to three docs, proof/.gitattributes, and 670 duplicate deletions. No AGENTS.md, governance doctrine, schemas, src, or tests changed. Added hunks show no secrets, absolute machine paths, or machine-specific ids.
FINDINGS:
  - id: F-01
    severity: HIGH
    blocking: true
    title: Smoke runtime gate scope claim is false
    body: Changed docs claim `scripts/smoke_up.sh`/`tools/smoke_runtime_gate.py` covers `enabled_in_smoke` services, but the runtime gate never reads services/registry.yaml and hardcodes `['conport', 'dopecon-bridge', 'task-orchestrator']` (tools/smoke_runtime_gate.py:111). Registry truth has 7 enabled smoke services out of 21, including postgres, qdrant, dope-memory, and adhd-engine (services/registry.yaml:22, services/registry.yaml:49, services/registry.yaml:174, services/registry.yaml:183). This makes the health-tool scope documentation materially false.
REMAINING_RISKS:
  - `tools/ports_health_audit.py --mode runtime` source appears to iterate all registry services by default and probe runtime health/status, but I did not run it because it writes reports/ under the worktree. Its existence further complicates the broad “no full-stack health” wording, though it does not appear to be an enforcing gate from source inspection.