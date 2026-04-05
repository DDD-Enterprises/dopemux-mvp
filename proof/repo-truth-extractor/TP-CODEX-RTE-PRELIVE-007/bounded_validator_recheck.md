# TP007 Bounded Validator Recheck

## Pre-Work Drift Classification

- In-scope for TP-007:
  - `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-007/*`
- Prior / unrelated tracked drift already present in worktree:
  - `compose.adhd-stack.yml`
  - `compose.yml`
  - `docker-compose.mcp-test.yml`
  - `docker-compose.smoke.yml`
  - `docker/compose.agents.yml`
  - `docker/compose.core.yml`
  - `docker/compose.pm.yml`
  - `docker/compose.research.yml`
  - `docker/compose.routing.yml`
  - `install.sh`
  - `mcp-proxy-config.copilot.yaml`
  - `mcp-proxy-config.json`
  - `mcp-proxy-config.yaml`
  - `scripts/deploy/deployment/start-mcp-servers.sh`
  - `scripts/dev/testing/validate-mcp-setup.sh`
  - `scripts/start-all-mcp-servers.sh`
  - `src/dopemux/mcp/instance_overlay.py`
  - `src/dopemux/mcp/registry.yaml`
- Unrelated untracked drift:
  - `.codex-tmp-doc-placement/`
  - `.codex-worktrees/`
  - `LIVE_LOG*.txt`
  - `llm-plans/*`
  - generated `reports/repo-truth-extractor/`

## Branch State

- Requested branch: `codex/rte-prelive-007-artifact-truth-revalidation`
- Observed current branch: `codex/canonical-compose-mcp`
- Attempt to create/switch requested branch failed:
  - `fatal: cannot lock ref ... Operation not permitted`
- This packet therefore proceeded on the current checkout and records branch creation failure as environment friction, not as repo truth about the bounded target.

## Canonical Command From Packet

```bash
python services/repo-truth-extractor/validate_pre_live_gate_v25.py --target-policy balanced_grok_openrouter --target-phases A --step A2 --allow-online-preflight
```

## Current Validator Truth

The current validator CLI no longer accepts `--step`.

Observed help output:

```text
validate_pre_live_gate_v25.py: error: unrecognized arguments: --step A2
```

Current parser surface supports:

- `--target-policy`
- `--target-phases`
- `--allow-online-preflight`

but not `--step`.

## Current Executed Validator Command

```bash
env XAI_API_KEY='<masked>' python services/repo-truth-extractor/validate_pre_live_gate_v25.py --target-policy balanced_grok_openrouter --target-phases A --allow-online-preflight
```

## Validator Verdict

- `verdict: NO_GO`
- `reason_codes: ["ONLINE_PREFLIGHT_FAILURE", "PAL_REQUIRED_UNAVAILABLE"]`
- output dir:
  - `reports/repo-truth-extractor/pre_live_gate_v25/pre_live_gate_v25_20260405T191013Z`

## Bounded-Target Drift Found

Current validator scope is no longer bounded to `A2`.

Observed in `VALIDATION_SCOPE.json`:

- required envs:
  - `OPENROUTER_API_KEY`
  - `XAI_API_KEY`
- required active OpenRouter routes were pulled in for phase `A`:
  - `openrouter:openai/gpt-5.3-codex:OPENROUTER_API_KEY`
  - `openrouter:openai/gpt-5.4:OPENROUTER_API_KEY`
- `A2` xAI routes are present, but validator scope also includes `A0`, `A1`, `A11`, `A12`, `A13`, and `A99`

## Blocking Conditions

- OpenRouter direct preflight returned `401 Unauthorized` for:
  - `openai/gpt-5.3-codex`
  - `openai/gpt-5.4`
- xAI preflight returned `200 OK` for:
  - `grok-4.20-beta-0309-reasoning`
  - `grok-4.20-beta-0309-non-reasoning`

## Recheck Result

- Validator truth is not intact for the previously bounded `A2` target.
- Current validator authority has drifted to phase-wide `A` route validation.
- Because current validator verdict is not `GO_NOW`, TP-007 does not attempt a live run.
