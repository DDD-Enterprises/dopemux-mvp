# Runner Adapter Contract
schema_version: 1.0.0
status: PROPOSED
## Purpose
Define the minimum adapter contract for every runner DCP may route through. A runner is an execution surface, not an authority source. DCP owns policy, proof requirements, and release gates.
## Common identity fields
Every runner adapter MUST emit:
- `runner_id`
- `runner_type`
- `runner_version`
- `provider`
- `requested_model`
- `actual_model`
- `access_path`
- `session_id`
- `route_decision_id`
- `task_id`
- `started_at`
- `finished_at`
- `exit_status`
## Common evidence capture
Every runner adapter MUST capture:
- prompt body or prompt reference
- prompt hash
- response body or response reference
- response hash
- files read
- files changed
- tool calls
- command list
- command stdout/stderr references
- exit codes
- usage/cost when available
- actual model/provider
- errors/failures
- redaction report
- runner logs or transcript reference
## OpenClaw adapter
### Capabilities
- sessions
- tool execution
- shell execution
- file read/write
- provider routing
- OpenRouter provider parameters
- JSONL logs
- trajectory bundles
- diagnostics export
- MCP integration
### Forbidden capabilities unless explicitly allowed
- broad shell write access
- external network access on private/security tasks
- editing outside packet allowlist
- release judgment
- sole final audit of own run
### Required logs
- session JSONL transcript
- trajectory bundle ref
- tool event log
- model/provider usage
- diagnostics ref when failure occurs
### Write restrictions
- worktree must be declared
- allowlist must be enforced externally
- git status before/after must be captured externally or by wrapper
### Audit restrictions
OpenClaw may host an auditor agent, but DCP must verify provider, model, runner, and session independence.
## Codex adapter
### Capabilities
- code implementation
- patch generation
- shell/test execution where runner permits
- local or API-key-backed automation
- ChatGPT sign-in for local subscription-backed use where allowed
### Forbidden capabilities
- treating ChatGPT sign-in as shared programmable API capacity
- sole final audit of own implementation
- high-risk release judgment without independent audit
### Evidence capture
- auth mode: `api_key` or `chatgpt_sign_in`
- command transcript
- changed files
- git diff
- tests
- model identity
- proof capture if consumer-plan route used
## Claude Code adapter
### Capabilities
- repo navigation
- implementation
- multi-file edits
- tests
- local manual/semi-manual workflows
- API-key-backed automation where configured
### Forbidden capabilities
- final audit of same Claude Code implementation session
- shared backend use through consumer credentials
- security/release sole authority
### Evidence capture
- auth mode
- transcript ref
- changed files
- commands
- diff
- tests
- audit handoff ref
## Gemini / Antigravity adapter
### Capabilities
- long-context reasoning
- multimodal audit
- UI/design review
- challenger analysis
- API-key-backed automation where available
### Forbidden capabilities
- consumer Gemini CLI as production automation foundation
- preview model as sole R5/R6 authority
- release judgment without independent audit or human approval
### Evidence capture
- app/API/CLI path
- model stability status
- screenshots or multimodal inputs
- prompt/response hashes
- route proof
## OpenRouter generic route adapter
### Capabilities
- unified API
- provider pinning/order
- fallback
- max price
- data collection filtering
- ZDR filtering
- strict structured outputs on compatible models
### Forbidden capabilities
- OpenRouter free for private/secret/security/release/schema-authority lanes
- silent fallback that weakens policy
- using requested model as actual model without verification
### Evidence capture
- requested model
- actual returned model
- actual provider when available
- route profile
- provider settings
- fallback events
- usage/cost
- schema validation result
- router metadata when enabled
## Direct API route adapter
### Capabilities
- automation
- reproducible logs
- structured outputs
- high-trust lanes
- provider-native usage and cost capture
### Forbidden capabilities
- provider/model drift without logging
- schema-critical output without local validation
- release judgment without independent audit or human gate
### Evidence capture
- endpoint family
- requested/actual model
- request ID if available
- token usage
- cost
- prompt/response hash
- structured validation result
## Manual app route adapter
### Capabilities
- manual planning
- heavyweight reasoning
- critique
- design synthesis
- human-supervised review
### Forbidden capabilities
- machine authority without proof capture
- secrets/client/security data unless policy allows
- direct release approval from transcript alone
### Evidence capture
- transcript export or signed summary
- prompt/body hash where possible
- operator identity
- approval event if used
- redaction report
## Shell/local runner adapter
### Capabilities
- local commands
- tests
- linters
- git state capture
- artifact hashing
### Forbidden capabilities
- destructive commands without explicit approval
- secret exfiltration
- network writes unless authorized
### Evidence capture
- cwd
- command
- stdout/stderr
- exit code
- start/end time
- environment redaction summary
- file artifact refs

validation_notes: This is an adapter contract, not implementation code. It preserves runner/tool distinction and blocks self-certification.
