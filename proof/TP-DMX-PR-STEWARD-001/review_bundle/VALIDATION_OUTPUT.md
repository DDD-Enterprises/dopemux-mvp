# Validation Output

| Command | Exit Code | Result |
| --- | ---: | --- |
| `python -m json.tool task-packets/generated/TP-DMX-PR-STEWARD-001.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/merge_readiness.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/review_item_ledger.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/thread_dispositions.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/ci_triage.schema.json` | 0 | PASS |
| `python -m json.tool schemas/pr_steward/pr_state_snapshot.schema.json` | 0 | PASS |
| `python -m json.tool schemas/proof/embedded_audit.schema.json` | 0 | PASS |
| task packet validation against `dopetask-canonical-spec.json` | 0 | PASS |
| `python -m compileall -q tools tests` | 0 | PASS |
| `pytest -q tests/pr_steward` | 0 | PASS, 5 passed |
| `python -m tools.pr_steward.intake --help` | 0 | PASS |
| `scripts/pr-steward --help` | 0 | PASS |
| fixture smoke `ready_all_green` | 0 | PASS, emitted READY |
| JSON parse of copied fixture artifacts | 0 | PASS |
| optional live smoke for PR #704 | 0 via `|| true` | PASS_WITH_RISKS, emitted BLOCKED due invalid `gh` auth |
| `git diff --check` | 0 | PASS |
| `pre-commit run --files $(git diff --name-only) || true` | 0 | PASS |
| `copilot --model claude-sonnet-4.6 --no-custom-instructions --disable-builtin-mcps --stream off --available-tools=__none__ -p "$(cat proof/TP-DMX-PR-STEWARD-001/COPILOT_AUDIT_INPUT.md)"` | 0 | PASS_WITH_RISKS |

## Embedded Audit Attempts

| Tool | Exit Code | Result |
| --- | ---: | --- |
| `claude auth status` | 1 | NOT_RUN, CLI reported `loggedIn: false`; no repo context sent |
| `claude --print ... --model sonnet --permission-mode plan` | 1 | NOT_RUN, CLI not logged in |
| `claude --print ... --model opus --permission-mode plan --tools "" --no-session-persistence` | 1 | NOT_RUN, CLI not logged in |
| `gemini --prompt "Auth availability check only. Respond OK." --approval-mode plan --skip-trust --output-format text` | 0 / internal 130 | NOT_RUN, opened interactive browser auth; cancelled without repo context |
| `gemini --prompt ... --approval-mode plan --skip-trust --output-format text` | n/a | NOT_RUN, prior audit attempt opened interactive browser auth |
| `agy --print-timeout 2m --print ...` | 1 | NOT_RUN, sandbox blocked log/bind; external escalation not approved |
| `copilot ... --available-tools "" ...` | 0 | NOT_AUTHORITATIVE, read-only tools were still exposed |
| `copilot ... --available-tools=__none__ ...` | 0 | PASS_WITH_RISKS, tools disabled and no tool execution output |
