---
id: DMX-DCP-MODEL-ROUTING-MVP-0000E
title: Dmx Dcp Model Routing Mvp 0000E
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-10'
last_review: '2026-06-10'
next_review: '2026-09-08'
prelude: Dmx Dcp Model Routing Mvp 0000E (explanation) for dopemux documentation and
  developer workflows.
---
# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000E` · DCP · Routing Runtime Health + PAL Inventory Probe

════════════════════════════════════════════════════════════

## Objective

Verify the current health of routing services, capture model inventory through approved mechanisms, and explicitly distinguish `CONFIGURED_MODEL`, `CALLABLE_MODEL`, `PAL_OBSERVED_MODEL`, `RUNNER_COMPATIBLE_MODEL`, and `UNKNOWN`.

**Runner**: Human-supervised shell + Claude/Codex
**Audit**: Claude/Gemini
**Mode**: diagnostic only, no config mutation

────────────────────────────────────────────────────────────

## Scope

### IN

* `dopemux routing status`
* `dopemux routing doctor`
* `dopemux routing config`
* LiteLLM health endpoint (no secrets)
* PAL MCP listmodels (only if already approved and safe)
* No-op smoke tests for non-sensitive models (if explicitly allowed)

### OUT

* No `repair-aliases --apply`
* No editing `~/.dopemux/routing.yaml`
* No reading `routing.env`
* No secrets
* No expensive model calls
* No production route changes

────────────────────────────────────────────────────────────

## Exact Commands

```bash
set -euo pipefail

pwd
git status --short --branch

dopemux routing status > /tmp/dmx_0000e_routing_status.txt 2>&1 || true
dopemux routing doctor > /tmp/dmx_0000e_routing_doctor.txt 2>&1 || true
dopemux routing config > /tmp/dmx_0000e_routing_config_redacted.txt 2>&1 || true

python - <<'PY'
from pathlib import Path
for p in [
    Path.home() / ".dopemux" / "routing.yaml",
    Path.home() / ".dopemux" / "routing.env",
]:
    print(f"{p}: {'PRESENT' if p.exists() else 'MISSING'}")
PY

curl -sS -m 3 http://127.0.0.1:4000/health > /tmp/dmx_0000e_litellm_health_public.txt 2>&1 || true
```

────────────────────────────────────────────────────────────

## Required Artifacts

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0000E/
  PROOF.json
  AUDIT.md
  COMMAND_LOG.md
  ROUTING_RUNTIME_HEALTH_LEDGER.md
  PAL_MODEL_INVENTORY_LEDGER.md
  MODEL_STATUS_CLASSIFICATION.csv
```

────────────────────────────────────────────────────────────

## Validation Gates

* LiteLLM state classified as `HEALTHY`, `UNHEALTHY`, or `UNKNOWN`
* Stale alias state captured
* PAL inventory either captured or explicitly remains `BLOCKED_OR_UNAVAILABLE`
* No model slot lock unless callable evidence exists

────────────────────────────────────────────────────────────

## Stop Conditions

* Tool asks to read secrets
* Tool asks to apply alias repair
* MCP model listing requires service startup outside approval
* Any live call risks cost or data leakage

────────────────────────────────────────────────────────────

## Expected Output

A clear health and model inventory ledger that tells 0001 exactly which models are configured vs callable vs unknown.
