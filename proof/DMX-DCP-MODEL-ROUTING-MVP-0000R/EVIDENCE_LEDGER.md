# Evidence Ledger — DMX-DCP-MODEL-ROUTING-MVP-0000R

Every claim in `CURRENT_MAIN_RUNTIME_RECONCILIATION.{md,json}` traced to its source command/artifact and confidence label.

| Claim | Label | Source command | Artifact | Confidence |
|---|---|---|---|---|
| Subject SHA = `9a52ecf432...` | OBSERVED | `git rev-parse HEAD` / `git rev-parse origin/main` | (preflight output, this transcript) | certain |
| Packet's authoring-time SHA (`eb212dca...`) is stale | OBSERVED | packet metadata vs. current HEAD comparison | packet frontmatter + preflight | certain |
| 13 DCP source files under `src/dopemux/dcp/` | OBSERVED | `find src/dopemux/dcp -maxdepth 2 -type f` | `inventory.txt` | certain |
| DCP compileall clean | OBSERVED | `python -m compileall -q src/dopemux/dcp src/dopemux/commands` | `compileall.log` (empty), `compileall.exit`=0 | certain |
| 252 focused DCP tests pass, zero failures | OBSERVED | `python -m pytest -q tests/unit/dcp tests/dcp/test_dcp_model_routing_0001_domain.py` | `pytest.log`, `pytest.exit`=0 | certain |
| Additional DCP-adjacent test dirs exist but were not run | OBSERVED (existence) / UNKNOWN (pass state) | `find tests -type f -path '*dcp*'` | `inventory.txt` | certain (existence), none (pass/fail) |
| `dcp` CLI group exists with `classify`/`recommend-backend` | OBSERVED | `python -m dopemux.cli dcp --help` | `dcp-help.txt`, exit 0 | certain |
| `mcp-pal` (HTTP :3003) is a health/lifecycle shim only, not functional MCP endpoint | OBSERVED (documentation claim, not independently re-probed via HTTP) | `grep` reference scan | `reference-scan.txt` lines citing `mcp_catalog.yaml:57,75` | high (repo self-documents this; not independently HTTP-verified this run) |
| `pal-stdio` is the canonical PAL tool route | OBSERVED | grep reference scan + this session's own successful `mcp__pal-stdio__*` tool calls | `reference-scan.txt`; this session's tool-call transcript (analyze/challenge/listmodels all succeeded) | certain |
| `pal_stdio_proxy.py` classified CANONICAL | OBSERVED | grep reference scan across `mcp_catalog.yaml`, `compose.yml`, `opencode.jsonc`, `scripts/ensure_pal_stdio.sh`, `scripts/mcp_health_check.sh`, `src/dopemux/mcp/fleet_catalog.py` | `reference-scan.txt` | certain (reference density); the packet's own classification rubric (canonical/legacy/experimental/unused) is an implementer judgment applied to that evidence, labeled OBSERVED-derived |
| OpenCode resolved model = `anthropic/claude-sonnet-4-5`; MCP servers declared: serena, dope-context, desktop-commander, gpt-researcher, pal-stdio, task-orchestrator | OBSERVED | `opencode debug config` | `opencode-resolved-config.txt` (redacted), exit 0 | certain |
| `verify-pal.sh` passes with a soft warning on the literal-string `pal` check | OBSERVED | `bash scripts/opencode/verify-pal.sh` | `verify-pal.log`, exit 0 | certain |
| OpenCode↔PAL wiring is static-only confirmed, not live-confirmed | INFERRED (from the above two rows — no `opencode run` smoke test was executed) | n/a | n/a | medium |
| `mcp-litellm` container healthy, port 4000 | OBSERVED (Docker's own HEALTHCHECK verdict, not independently HTTP-probed) | `docker ps --format '{{json .}}'` | `docker-ps-summary.txt`, `docker-ps.jsonl` | high |
| `mcp-pal`, `mcp-pal-stdio`, `pal-mcp-server` containers up; `pal-mcp-server-stale-20260721` unhealthy | OBSERVED | `docker ps --format '{{json .}}'` | `docker-ps-summary.txt` | certain (container state); INFERRED that the stale name indicates a leaked instance (medium confidence, not re-diagnosed) |
| 6/6 runner CLIs (codex, claude, opencode, gemini, agy, grok) present with versions | OBSERVED | `command -v` + `--version` loop, no inference calls | `runner-cli-inventory.txt` | certain |
| `mcp_catalog.yaml` declares 15 top-level servers | OBSERVED | Python YAML parse of `mcp_catalog.yaml` | (this transcript; not persisted as a separate artifact beyond the count) | certain |
| `route_manifest.py` exists at `services/dcp-readonly-facade/src/dcp_facade/route_manifest.py` | OBSERVED | `find . -iname 'route_manifest*'` | (this transcript) | certain |
| Proof-bundle schema / handoff contract / embedded-audit schema all present and usable | OBSERVED | direct file reads | `docs/03-reference/governance/proof-bundle-schema.md`, `handoff-contract.md`, `schemas/proof/embedded_audit.schema.json` | certain |
| Governance doc `next_review` dates (2026-06-15) are stale relative to execution date (2026-07-26) | OBSERVED / CONFLICTING (metadata only) | frontmatter read | same files as above | certain |
| Current `origin/main` HEAD is PR #1131 (pr-steward solo-owner work), MERGED | OBSERVED | `git log -1 --oneline origin/main` + `gh pr list` | (this transcript), `gh-pr-open-all.json` | certain |
| No PR exists yet for this packet's branch; branch not yet pushed | OBSERVED | `gh pr list --head ...`, `git ls-remote origin ...` | `gh-pr-this-branch.json` (empty array) | certain |
| No secret values present in any proof artifact | OBSERVED (post-redaction verification) | regex secret-pattern scan across `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/` | this transcript ("NO RAW SECRET PATTERNS FOUND") | certain |

## Evidence NOT collected (explicit non-claims)

- No HTTP probe of `:3003`, `:4000`, or any other MCP/service port was performed. Any "healthy" statement above is Docker's own `HEALTHCHECK` verdict, not this packet's independent verification.
- No `opencode run` invocation was made (scope-out: no model inference calls).
- The four DCP-adjacent test directories/files outside the packet's exact focused-test scope were not executed; their pass/fail state is `UNKNOWN`, not assumed passing.
- `pal-mcp-server-stale-20260721` was observed but not inspected further (no `docker inspect`, no logs pulled, no prune attempted — out of scope, would be a mutation).
