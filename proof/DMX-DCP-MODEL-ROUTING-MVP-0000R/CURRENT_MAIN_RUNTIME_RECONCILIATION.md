---
id: DCP_CURRENT_MAIN_RUNTIME_RECONCILIATION
title: DCP Current-Main Runtime and Toolchain Reconciliation
type: reference
owner: DMX-DCP-MODEL-ROUTING-MVP-0000R
date: '2026-07-26'
---

# DCP Current-Main Runtime and Toolchain Reconciliation

**Packet**: `DMX-DCP-MODEL-ROUTING-MVP-0000R` · series `DMX-DCP-MODEL-ROUTING-NEXT-TRANCHE-001`
**Subject SHA**: `9a52ecf4328f28756c3e87a2c351e60d46b805f6` (current `origin/main` at capture time)
**Scope**: Read-only evidence capture. No runtime, config, or forbidden-path edits were made. No merge or live execution is authorized by this document.

The prior 0000C–0000I evidence bundle was gathered in June 2026 and used `eb212dcaa73c407c271e0ddc60e38bdd2b7e4661` as its reference SHA. That SHA is **stale** — main has since absorbed the routing model, classifier, lane engine, provenance hardening, PAL model refresh, and PR Steward solo-owner work. This document supersedes those claims for anything that conflicts.

Every material statement below is labelled `OBSERVED`, `INFERRED`, `PROPOSED`, `UNKNOWN`, `CONFLICTING`, or `CLAIMED` per the packet's governing truth order. Full command output lives under `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/`.

## DCP components (`OBSERVED`)

13 source files under `src/dopemux/dcp/`: `__init__.py`, `control_snapshot.py`, `lane_engine.py`, `lane_model.py`, `proof_family.py`, `proof_pointer_reader.py`, `red_lane.py`, `red_lane_rules.py`, `red_lane_scanner.py`, `red_lane_taxonomy.py`, `routing_backend_policy.py`, `routing_classifier.py`, `routing_model.py`.

- `python -m compileall -q src/dopemux/dcp src/dopemux/commands` → **exit 0**, no output.
- `python -m pytest -q tests/unit/dcp tests/dcp/test_dcp_model_routing_0001_domain.py` → **exit 0**, 252 passed (dot-count, no verbose IDs; zero failures/errors/skips).
- **`UNKNOWN`**: `tests/dcp_extension/**`, `tests/contracts/test_openclaw_dcp_routing_contracts.py`, `tests/project_control_plane/test_dcp_extension_export.py`, `tests/test_dcp_surface_guard.py`, and `tests/test_dcp_denylist_nudge.py` all exist but sit outside this packet's exact two focused pytest paths and were not run.

## DCP CLI surface (`OBSERVED`)

`python -m dopemux.cli dcp --help` → exit 0. `dcp` is a registered subcommand group: "Read-only DCP routing projection (classify + backend policy recommend)." Two subcommands: `classify` and `recommend-backend`.

## PAL route and proxy disposition (`OBSERVED`)

The canonical PAL tool route is **`pal-stdio`** (exec-based MCP server, `docker exec -i mcp-pal-stdio /app/.venv/bin/python server.py`), not the HTTP server on `:3003`.

- `mcp_catalog.yaml` (both the repo root copy and `src/dopemux/mcp/default_catalog.yaml`) explicitly documents the HTTP wrapper (`mcp-pal`, `:3003`) as: *"health/lifecycle shim only — `/mcp`, `/sse`, `/messages` all 404. ... Use pal-stdio for PAL tools."*
- `pal_stdio_proxy.py` is classified **CANONICAL**: actively referenced by `mcp_catalog.yaml`, `compose.yml` (service `pal-stdio`, container `mcp-pal-stdio`), `opencode.jsonc`, `scripts/ensure_pal_stdio.sh`, `scripts/mcp_health_check.sh`, and `src/dopemux/mcp/fleet_catalog.py`.
- This packet's own required PAL chain confirms the route is live: `mcp__pal-stdio__analyze`, `__challenge`, and `__listmodels` all executed successfully during this packet's execution.

**Known limitation** (not re-tested by this packet): `scripts/ensure_pal_stdio.sh` and an in-repo diagnosis doc describe a known `model_context` import failure mode with a documented recovery of `docker restart mcp-pal-stdio`. This packet's own PAL calls succeeded, so the failure mode did not reproduce during this run, but it was not deliberately re-probed.

## OpenCode wiring (`OBSERVED`, static only)

`opencode debug config` → exit 0 (secrets redacted in proof). Resolved model: `anthropic/claude-sonnet-4-5` (small model `anthropic/claude-haiku-4-5`), default agent `build`. Declared MCP servers in the resolved config: `serena`, `dope-context`, `desktop-commander`, `gpt-researcher`, `pal-stdio`, `task-orchestrator`.

`bash scripts/opencode/verify-pal.sh` → exit 0. The script confirms `opencode.jsonc` exists, the PAL behavior guide exists, and PAL agents exist, but its own internal grep for the literal string `pal` in `opencode debug config` output did not match — the script treats this as a soft warning ("may still work"), not a failure. **This packet treats OpenCode↔PAL wiring as statically wired but not independently confirmed live** (no `opencode run` smoke test was executed — scope-out on model inference calls).

## LiteLLM and PAL container/health state (`OBSERVED`, snapshot only)

From `docker ps` at capture time (28 containers total; full list in `proof/docker-ps-summary.txt`):

| Container | Image | Status | Ports |
|---|---|---|---|
| `mcp-litellm` | `dopemux-litellm` | Up 51 min (healthy) | `0.0.0.0:4000->4000/tcp` |
| `litellm-db` | `postgres:16.6` | Up 51 min (healthy) | `0.0.0.0:2543->5432/tcp` |
| `mcp-pal` | `dopemux-pal` | Up 51 min (healthy) | `0.0.0.0:3003->3003/tcp` |
| `mcp-pal-stdio` | `dopemux-pal-stdio` | Up 51 min | (exec-based, no published port) |
| `pal-mcp-server` | `pal-mcp-server:latest` | Up 51 min (healthy) | (none published) |
| `pal-mcp-server-stale-20260721` | (untagged) | Up 51 min **(unhealthy)** | (none) |

`pal-mcp-server-stale-20260721`'s name and unhealthy status suggest a leaked/stale prior instance, consistent with a container-leak pattern noted in prior session history; this packet did not re-diagnose or prune it (out of scope — no container mutation authorized).

**Caveat**: All health verdicts above are Docker's own `HEALTHCHECK` result at snapshot time — this packet made no direct HTTP calls to `:3003` or `:4000` (scope-out on live network/inference calls beyond discovered static configuration).

## Runner CLI inventory (`OBSERVED`, no inference calls)

| Runner | Path | Version |
|---|---|---|
| codex | `/Users/hue/.local/share/mise/shims/codex` | codex-cli 0.145.0 |
| claude | `/Users/hue/.local/bin/claude` | 2.1.220 (Claude Code) |
| opencode | `/Users/hue/.opencode/bin/opencode` | 1.18.5 |
| gemini | `/opt/homebrew/bin/gemini` | 0.46.0 |
| agy | `/Users/hue/.local/bin/agy` | 1.1.7 |
| grok | `/Users/hue/.local/bin/grok` | grok 0.2.112 (9bbd559437aa) [stable] |

All six runners are present with resolvable versions. No paid inference calls were made for this inventory step.

## MCP registry state (`OBSERVED`)

`mcp_catalog.yaml` declares 15 top-level servers (sample: `pal`, `serena`, `dope-context`, `desktop-commander`, `gpt-researcher`). 28 live containers observed via `docker ps`. The DCP read-only facade's `route_manifest.py` exists at `services/dcp-readonly-facade/src/dcp_facade/route_manifest.py`, confirming the denylist-token source referenced by the repo's H2 Claude hook is a real, current module.

## Proof and handoff contract state (`OBSERVED`, one `CONFLICTING` note)

`docs/03-reference/governance/proof-bundle-schema.md`, `docs/03-reference/governance/handoff-contract.md`, and `schemas/proof/embedded_audit.schema.json` are all present and were used directly to construct this packet's own proof bundle without contradiction.

**`CONFLICTING`**: Both governance docs' frontmatter declare `next_review: 2026-06-15`, which is in the past relative to this packet's execution date (2026-07-26). This flags the *review date* as stale metadata — it is not a claim that the schema content itself is wrong; both schemas were applied successfully.

## PR Steward state (`OBSERVED`)

Current `origin/main` HEAD is PR #1131, *"feat(pr-steward): solo-owner exact-head security-release authorization"* (MERGED). PR Steward work is under active development at the tip of main (see also open PR #1133). This packet does not invoke PR Steward against its own branch inside this document — per packet mandate, `merge_readiness` for `DMX-DCP-MODEL-ROUTING-MVP-0000R` itself remains `BLOCKED_NOT_REQUESTED` until PR Steward inspects the actual pushed head.

## Unknowns

- Live HTTP health of `:3003` (mcp-pal) and `:4000` (mcp-litellm) was not independently re-probed.
- Whether the documented pal-stdio `model_context` import issue still reproduces on current main was not deliberately re-tested (this packet's own PAL calls happened to succeed).
- Pass/fail status of `tests/dcp_extension/**`, `tests/contracts/test_openclaw_dcp_routing_contracts.py`, `tests/project_control_plane/test_dcp_extension_export.py`, `tests/test_dcp_surface_guard.py`, `tests/test_dcp_denylist_nudge.py` — outside this packet's exact focused-test scope.
- Whether `opencode run "Use pal_listmodels..."` (verify-pal.sh's own recommended smoke test) currently succeeds.
- Origin and prunability of `pal-mcp-server-stale-20260721`.

## Contradictions

- See "Proof and handoff contract state" above: governance doc `next_review` dates are stale relative to execution date; no content-level contradiction found.

## Recommended next packet

`DMX-DCP-MODEL-ROUTING-MVP-0000S`, with candidate follow-ups: live HTTP health probes of `:3003`/`:4000` under explicit no-write authorization; running the remaining DCP-adjacent test suites; re-verifying the pal-stdio `model_context` issue against the current image; investigating `pal-mcp-server-stale-20260721`.
