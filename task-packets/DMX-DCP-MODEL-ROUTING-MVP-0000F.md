# Task Packet: `DMX-DCP-MODEL-ROUTING-MVP-0000F` · DCP · Backend Runner Contract Dry-Run Matrix

════════════════════════════════════════════════════════════

## Objective

Prove which runners can produce controlled outputs with write controls, JSON emission, model capture, and diff capture. OpenCode must remain backend-only; all others are adapters.

**Runner**: Codex or Claude Code Sonnet
**Audit**: Gemini/AGY
**Mode**: no repo mutation

────────────────────────────────────────────────────────────

## Scope

### IN

* OpenCode
* Claude Code
* Codex
* Gemini CLI
* AGY / Antigravity
* Aider
* Copilot
* Jules
* shell/test runner
* GitHub/CI read-only

### OUT

* No model calls that mutate files
* No edits
* No PR creation
* No cloud agent tasks
* No GitHub writes

────────────────────────────────────────────────────────────

## Exact Commands

```bash
set -euo pipefail

for tool in opencode claude codex gemini aider gh; do
  echo "### $tool"
  command -v "$tool" || true
  "$tool" --version || true
  "$tool" --help > "/tmp/dmx_0000f_${tool}_help.txt" 2>&1 || true
done

gh auth status > /tmp/dmx_0000f_gh_auth_status.txt 2>&1 || true
```

────────────────────────────────────────────────────────────

## Required Artifacts

```
proof/DMX-DCP-MODEL-ROUTING-MVP-0000F/
  PROOF.json
  AUDIT.md
  COMMAND_LOG.md
  RUNNER_DRY_RUN_MATRIX.md
  BACKEND_ADAPTER_RISK_LEDGER.md
```

────────────────────────────────────────────────────────────

## Validation Gates

* Every runner classified
* No runner marked implementation-safe without write-control proof
* OpenCode remains backend-only
* Shell runner remains validation-only
* Cloud agents remain non-authoritative

────────────────────────────────────────────────────────────

## Stop Conditions

* Tool tries to initialize config with writes
* Tool asks to authenticate
* Tool triggers model execution
* Tool tries to create branch, PR, or patch

────────────────────────────────────────────────────────────

## Expected Output

A runner dry-run matrix that tells 0001 exactly which backends are safe for DCP v1 and which must remain adapters only.
