# TP-DMX-PR-STEWARD-001 Embedded Audit Report

## Verdict

PASS_WITH_RISKS

## Auditor Route

Supervisor-approved one-time fallback:

```text
GitHub Copilot CLI with Claude Sonnet 4.6
```

Compliant invocation used:

```bash
copilot --model claude-sonnet-4.6 \
  --no-custom-instructions \
  --disable-builtin-mcps \
  --stream off \
  --available-tools=__none__ \
  -p "$(cat proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md)"
```

Exit code: `0`.

Tool boundary: `--available-tools=__none__` caused Copilot CLI to print a disabled-tools list and no tools executed. The CLI also printed `Unknown tool name in the tool allowlist: "none"` because the placeholder is not a real tool; this was used deliberately to leave no usable tool available to the model.

## Earlier Failed / Non-Authoritative Attempts

| Tool | Model | Invocation | Exit Code | Result |
| --- | --- | --- | ---: | --- |
| AGY / Antigravity | unknown | `agy --help` | 0 | Help proved `--print` / `--prompt`, but did not prove a Sonnet model-selection flag. |
| Claude Code CLI | auth | `claude auth status` | 1 | CLI reported `loggedIn: false`; no repo context was sent through Claude. |
| Claude Code CLI | sonnet | `claude --print ... --model sonnet --permission-mode plan` | 1 | CLI reported `Not logged in`; audit did not run. |
| Claude Code CLI | opus | `claude --print ... --model opus --permission-mode plan --tools "" --no-session-persistence` | 1 | CLI reported `Not logged in`; audit did not run. |
| Gemini CLI | auth | `gemini --prompt "Auth availability check only. Respond OK." --approval-mode plan --skip-trust --output-format text` | 0 / internal 130 | CLI opened an interactive authentication prompt. The prompt was declined/cancelled; no repo context was sent. |
| AGY / Antigravity | unknown | `agy --print-timeout 2m --print ...` | 1 | Sandbox blocked local log creation and localhost bind. Escalation to run outside sandbox was rejected or not approved because it would expose repo context to an external AI CLI. |
| Copilot CLI | claude-sonnet-4.6 | `copilot ... --available-tools "" ...` | 0 | Non-authoritative because the empty available-tools filter still exposed read-only tools. Result was consistent with `PASS_WITH_RISKS`, but this report uses the later no-tools run as authoritative. |

## Evidence Reviewed

- Bounded audit input at `proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md`.
- Diff stat and changed file list.
- Review bundle manifest summary.
- Proof validation summary.
- No-mutation boundary evidence.
- Key changed file list and fixture coverage summary.

## Findings

| Severity | Finding | Evidence | Required Action |
| --- | --- | --- | --- |
| INFO | No GitHub mutation path identified in bounded evidence. | Audit input static scan summary and workflow permission summary. | None. |
| INFO | Runtime remains check-only and artifacts report `mutation_performed: false`. | Audit input no-mutation evidence and fixture artifact summaries. | None. |
| INFO | Advisory workflow is read-only and exits successfully to avoid a pending-check branch-protection race. | `.github/workflows/pr-steward.yml` summary in audit input. | None. |
| INFO | Unknown reviewers, unresolved threads, failed checks, pending checks in strict mode, draft PRs, incomplete harvest/auth, and skipped audit are covered by fixtures. | Fixture coverage summary in audit input. | None. |
| LOW | Live GitHub smoke remains blocked by invalid local `gh` auth. | Proof and manifest blockers. | No code change; requires valid GitHub auth in live environments. |
| LOW | Review bundle artifacts are generated from offline fixture smoke, not a successful live PR harvest. | Manifest excluded-artifacts section and proof live-smoke note. | Acceptable for v1 check-only runtime; live readiness remains fail-closed until auth/proof linkage is valid. |
| LOW | Static known-reviewer list will block new reviewers/bots until classified. | `known_reviewers.json` is intentionally bounded. | Maintain allowlist in follow-up packets. |

## Required Fixes

None blocking after this report is copied into proof and `embedded_audit.status` is updated to `PASS_WITH_RISKS`.

## Nonblocking Risks

- Live harvest cannot complete locally until `gh` auth is repaired.
- Live `READY` remains intentionally hard to reach unless proof/head-SHA linkage is present and current.
- Copilot no-tools audit was bounded to summarized evidence rather than full unrestricted repo inspection.

## Supervisor Escalation

Required: no

Reason: The fallback auditor returned `PASS_WITH_RISKS`, with only nonblocking risks and commit readiness `READY` after audit-status bookkeeping.

## Commit Readiness

READY
