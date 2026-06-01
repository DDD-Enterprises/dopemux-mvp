---
id: START-HERE
title: Start Here
type: tutorial
owner: '@hu3mann'
last_review: '2026-05-31'
next_review: '2026-08-29'
author: '@hu3mann'
date: '2026-02-05'
prelude: Start Here (tutorial) for dopemux documentation and developer workflows.
---
# Start Here

Use this page as the first-touch path for a local Dopemux checkout. It is a
short orientation, not a replacement for runtime truth: code, compose wiring,
tests, and active entrypoints still outrank this document.

Dopemux is an operator control workspace for split-authority development
systems. It coordinates startup, routing, MCP/service surfaces, execution
handoff, PM metadata, structured context, chronicle memory, retrieval, bridge
transport, operator support, and repo audit without claiming one system owns
all of those lanes.

## First Local Run

Prerequisites:

- Python 3.11 or newer.
- Docker with `docker compose`.
- `uv` for Python dependency management.
- Claude Code installed and available to open from this repository checkout.
- Provider API keys for any provider-backed services you choose to run.

Clone and enter the repo:

```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp
```

Run the installer:

```bash
./install.sh
```

The installer is the repo's first-touch setup path. For unattended or stack
specific options, see [INSTALL.md](../../INSTALL.md).

Load the shell integration that the installer wrote, or open a new terminal:

```bash
# zsh
source ~/.zshrc

# bash
source ~/.bashrc
```

Start the operator CLI:

```bash
dopemux start
```

`dopemux start` is the operator cockpit entrypoint. It handles the local
startup path for Dopemux operator work; use the explicit compose flow in
[Quick Start](../../QUICK_START.md) when you need to start and inspect the
compose-backed service stack directly.

Open Claude Code from this checkout after startup so it reads the repository
Claude/MCP configuration for the current working directory. In Claude Code, use
`/mcp` to inspect which MCP servers are visible for the active session.

## Optional Smoke Checks

If you started the compose-backed services, check the observed default health
ports:

```bash
curl -fsS http://localhost:3016/health  # dopecon-bridge
curl -fsS http://localhost:3004/health  # ConPort HTTP
curl -fsS http://localhost:3010/health  # dope-context
curl -fsS http://localhost:3020/health  # dope-memory
curl -fsS http://localhost:8000/health  # task-orchestrator
curl -fsS http://localhost:3025/health  # ADHD Engine
```

These ports are defaults from the tracked compose and registry configuration.
Local `.env` overrides can change them.

## Authority Notes

- `dopemux` owns operator startup, routing, and coordination.
- `dopetask` owns execution after handoff through `scripts/dopetask`.
- Leantime owns passive PM metadata.
- task-orchestrator owns workflow-significant transitions.
- ConPort owns structured decisions, progress, and context.
- dope-memory owns chronicle receipts.
- dope-context owns derived code/docs retrieval.
- dopecon-bridge is bridge/proxy/event transport only.
- ADHD Engine is operator support only.
- Repo Truth Extractor emits evidence artifacts; runtime/source truth still
  wins.

## If You Get Stuck

- Installer failure: run `./install.sh --verify` and read the reported blocker.
- Missing Docker network: follow [Quick Start](../../QUICK_START.md) to create
  `dopemux-network`.
- Port conflict: inspect `.env`, existing containers, and local processes
  before changing docs or code.
- MCP missing in Claude Code: confirm Claude Code was opened from this checkout
  and run `/mcp`.

## Next Reading

- [Quick Start](../../QUICK_START.md)
- [Tutorial Quickstart](quickstart.md)
- [Developer Onboarding](../02-how-to/developer-onboarding.md)
- [Architecture](../../ARCHITECTURE.md)
- [System Boundaries](../03-reference/systems/system-boundaries.md)
