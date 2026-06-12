---
id: DMX-DCP-MODEL-ROUTING-MVP-0000C
title: Dmx Dcp Model Routing Mvp 0000C
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-10'
last_review: '2026-06-10'
next_review: '2026-09-08'
prelude: Dmx Dcp Model Routing Mvp 0000C (explanation) for dopemux documentation and
  developer workflows.
---
# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000C` · DCP · Clean Origin/Main Evidence Refresh

════════════════════════════════════════════════════════════

## Objective

Prove what is true on clean `origin/main`, not the dirty DCP branch. This prevents the "current-branch soup wearing an origin/main nametag" problem that 0000/0000B suffered from.

**Runner**: Codex or Claude Code Sonnet
**Audit**: AGY/Sonnet or Claude Code Sonnet
**Mode**: read-only

────────────────────────────────────────────────────────────

## Scope

### IN

* Git identity on clean detached `origin/main`
* Clean worktree proof (`git status --short --branch`)
* `origin/main` SHA
* Routing policy presence (`config/ai/model-routing.policy.yaml`)
* Command help census (dopemux, dopetask)
* MCP inventory
* Slash/workflow/agent inventory
* Runner config inventory
* Model config inventory
* Red-lane seams
* Proof-shape samples
* Delta against 0000/0000B

### OUT

* No code changes
* No service startup
* No secret reads
* No route/model calls
* No workflow edits
* No merge tooling
* No writes outside proof artifacts

────────────────────────────────────────────────────────────

## Exact Commands

```bash
set -euo pipefail

mkdir -p /tmp/dmx-dcp-routing-origin-main
cd /tmp/dmx-dcp-routing-origin-main

git clone --no-checkout git@github.com:DDD-Enterprises/dopemux-mvp.git repo || \
git clone --no-checkout https://github.com/DDD-Enterprises/dopemux-mvp.git repo
cd repo
git fetch origin main
git checkout --detach origin/main

pwd
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short --branch

find . -maxdepth 4 -type f | sort > /tmp/dmx_0000c_files_max4.txt
find . -maxdepth 5 -type f \
  | grep -Ei 'mcp|workflow|slash|command|agent|opencode|codex|gemini|aider|claude|copilot|jules|routing|model' \
  | sort > /tmp/dmx_0000c_surface_special_files.txt

ls -la
ls -la .github/workflows || true
ls -la .claude || true
ls -la config/ai || true
ls -la schemas/dcp || true

git ls-tree -r --name-only HEAD \
  | grep -E 'model-routing|routing.yaml|litellm|mcp|workflow|agents|commands|dopetask|taskx|proof|dcp' \
  > /tmp/dmx_0000c_relevant_tree.txt

python - <<'PY'
from pathlib import Path
targets = [
    "config/ai/model-routing.policy.yaml",
    "litellm.config.yaml",
    "mcp-proxy-config.yaml",
    "mcp-proxy-config.json",
    "mcp-proxy-config.copilot.yaml",
    ".mcp.json",
    "scripts/dopetask",
    "scripts/taskx",
    ".github/workflows/gemini-review.yml",
    "scripts/batch_resolve_and_merge.py",
]
for t in targets:
    p = Path(t)
    print(f"{t}: {'PRESENT' if p.exists() else 'MISSING'}")
PY

uv run dopemux --help > /tmp/dmx_0000c_dopemux_help.txt 2>&1 || true
./scripts/dopetask --help > /tmp/dmx_0000c_dopetask_help.txt 2>&1 || true
```

────────────────────────────────────────────────────────────

## Required Artifacts

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0000C/
  PROOF.json
  AUDIT.md
  COMMAND_LOG.md
  ORIGIN_MAIN_SURFACE_CENSUS.md
  ORIGIN_MAIN_DELTA_VS_0000B.md
  ROUTING_POLICY_ORIGIN_MAIN_LEDGER.md
  RED_LANE_ORIGIN_MAIN_LEDGER.md
```

────────────────────────────────────────────────────────────

## Validation Gates

* `git status --short --branch` shows detached `origin/main` and clean
* `config/ai/model-routing.policy.yaml` status captured
* `.github/workflows/gemini-review.yml` status captured, not modified
* No secrets printed
* No services started
* No writes outside proof artifacts

────────────────────────────────────────────────────────────

## Stop Conditions

* Cannot create clean detached worktree
* `origin/main` cannot be fetched
* Any command would read secrets
* Any tool proposes writes

────────────────────────────────────────────────────────────

## Expected Output

A clean `origin/main` evidence bundle that can be used as the authoritative baseline for 0001 instead of the dirty DCP branch.
