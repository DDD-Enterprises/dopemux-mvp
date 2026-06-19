Below are the Codex recon packs to feed the final GPT-5.5 Pro prompt series.

Use these as read-only / evidence-only packets. No commits unless explicitly stated. No runtime implementation. No “agent theatre in a little velvet cape.” 🦇

These packs line up with the final prompt suite:

PACK 1 — DCP runner recon: OpenCode / Grok Build / runners
PACK 2 — combined orchestration evidence pack
PACK 3 — Secure MCP read-only facade discovery
PACK 4 — ECC external component harvest
PACK 5 — final GPT-5.5 attachment assembler

Source grounding:

* ECC intake must start with read-only harvest and no ECC install/run/import; only Macro Packets 0 and 1 are ready before audit.
* Secure MCP facade discovery is explicitly a Codex discovery/documentation packet, not implementation or tunnel wiring.
* The final runner prompt stream requires a dcp-runner-recon bundle containing GIT_RECON, OPEN_CODE_RECON, GROK_BUILD_RECON, DOPMUX_RECON, DOPETASK_RECON, MCP_RECON, and related files.
* The Secure MCP architecture requires a local read-only evidence router, not raw “all MCP tools” exposure.

⸻

PACK 1 — Codex Runner Recon

# Codex Recon Pack — TP-DMX-DCP-RUNNER-RECON-001
## Title
DCP Runner Recon: OpenCode, Grok Build, Codex, Claude, Gemini, AGY, Aider, Dopemux, Dopetask, MCP
## Objective
Collect a repo-grounded runner/runtime evidence bundle for GPT-5.5 Pro to evaluate the DCP Multi-Model Routing & Execution Plane.
This packet produces:
```text
audit_inputs/dcp-runner-recon/GIT_RECON.txt
audit_inputs/dcp-runner-recon/OPEN_CODE_RECON.txt
audit_inputs/dcp-runner-recon/GROK_BUILD_RECON.txt
audit_inputs/dcp-runner-recon/ENV_PRESENCE_REDACTED.txt
audit_inputs/dcp-runner-recon/DOPMUX_RECON.txt
audit_inputs/dcp-runner-recon/DOPETASK_RECON.txt
audit_inputs/dcp-runner-recon/MCP_RECON.txt
audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt
audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt
audit_inputs/dcp-runner-recon/RECON_SUMMARY.md
audit_inputs/dcp-runner-recon/RECON_FINDINGS.json

Mode

READ_ONLY_PLUS_EVIDENCE_FILES

Authority posture

Codex is the recon executor only.

Codex must not:

* implement architecture
* edit runtime/source/config outside audit_inputs/dcp-runner-recon/
* commit
* push
* open PR
* run external install scripts
* start services
* expose secrets

Scope IN

* repo identity
* git branch/head/status
* runner CLI availability
* runner versions/help/config presence
* OpenCode config and local state inventory
* Grok Build / grok availability and help/config
* Codex/Claude/Gemini/Aider/AGY presence if locally detectable
* Dopemux CLI availability/help
* Dopetask availability/help/doctor
* MCP config inventory
* repo surface inventory
* redacted env presence only

Scope OUT

* no code changes
* no dependency installs
* no MCP tool calls
* no Docker service starts
* no package manager commands
* no .env contents
* no credential reads
* no auth token display
* no runner implementation
* no proof schema implementation

Invariants

1. Runtime evidence outranks docs.
2. If a runner binary is missing, record UNAVAILABLE, do not install it.
3. If a runner exists but auth/config is unclear, record UNKNOWN, do not read secrets.
4. OpenCode and Grok Build are backend candidates, not authority.
5. Grok Build local config must be inspected only for non-secret metadata.
6. Environment checks must be redacted.
7. All commands and exit codes must be captured.
8. Failures are evidence.

Allowed files

Only:

audit_inputs/dcp-runner-recon/**

Forbidden files

Everything else.

Especially:

src/**
services/**
docker/**
.github/**
.claude/**
.opencode/**
config/**
compose.yml
pyproject.toml
scripts/**
.env*

You may read files, but not modify them.

Exact commands

Run from repo root.

set -u
OUT="audit_inputs/dcp-runner-recon"
mkdir -p "$OUT"
run() {
  name="$1"; shift
  {
    echo "## command: $*"
    echo "## cwd: $(pwd)"
    echo "## started_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    "$@"
    code=$?
    echo
    echo "## exit_code: $code"
    echo "## ended_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    return 0
  } > "$OUT/${name}.txt" 2>&1
}

1. Git / repo recon

{
  echo "# GIT_RECON"
  pwd
  git rev-parse --show-toplevel
  git remote -v
  git branch --show-current
  git rev-parse HEAD
  git status --short --branch
  git worktree list
  git diff --stat
  git diff --name-only
} > "$OUT/GIT_RECON.txt" 2>&1

2. OpenCode recon

{
  echo "# OPEN_CODE_RECON"
  echo "## binary"
  command -v opencode || true
  opencode --version 2>/dev/null || true
  opencode --help 2>/dev/null || true
  echo
  echo "## project config"
  find . -maxdepth 4 -type f $begin:math:text$ \-name \'opencode\.json\' \-o \-name \'opencode\.jsonc\' \-o \-path \'\.\/\.opencode\/\*\' $end:math:text$ | sort 2>/dev/null || true
  echo
  echo "## safe snippets"
  sed -n '1,220p' opencode.jsonc 2>/dev/null || true
  sed -n '1,220p' opencode.json 2>/dev/null || true
  echo
  echo "## commands/agents"
  find .opencode -maxdepth 4 -type f -print -exec sed -n '1,120p' {} \; 2>/dev/null || true
  echo
  echo "## local config presence only"
  find "$HOME/.config/opencode" -maxdepth 3 -type f 2>/dev/null | sed "s|$HOME|~|g" | sort || true
} > "$OUT/OPEN_CODE_RECON.txt" 2>&1

Do not print OpenCode auth/token files.

3. Grok Build recon

{
  echo "# GROK_BUILD_RECON"
  echo "## binaries"
  command -v grok || true
  command -v grok-build || true
  echo
  echo "## versions"
  grok --version 2>/dev/null || true
  grok-build --version 2>/dev/null || true
  echo
  echo "## help"
  grok --help 2>/dev/null || true
  grok agent --help 2>/dev/null || true
  grok mcp --help 2>/dev/null || true
  grok model --help 2>/dev/null || true
  grok export --help 2>/dev/null || true
  grok-build --help 2>/dev/null || true
  echo
  echo "## config presence redacted"
  find "$HOME/.grok" -maxdepth 3 -type f 2>/dev/null | sed "s|$HOME|~|g" | sort || true
  echo
  echo "## config non-secret preview"
  if [ -f "$HOME/.grok/config.toml" ]; then
    sed -E 's/(key|token|secret|password|api_key).*/\1 = "[REDACTED]"/Ig' "$HOME/.grok/config.toml" | sed -n '1,220p'
  fi
  echo
  echo "## model/cache presence"
  find "$HOME/.grok" -maxdepth 4 -type f 2>/dev/null \
    | grep -Ei 'model|cache|config|mcp|plugin|skill' \
    | sed "s|$HOME|~|g" \
    | sort || true
} > "$OUT/GROK_BUILD_RECON.txt" 2>&1

4. Redacted env presence

{
  echo "# ENV_PRESENCE_REDACTED"
  env | grep -Ei 'OPENAI|ANTHROPIC|GEMINI|GROK|XAI|OPENROUTER|CODEX|CLAUDE' \
    | sed -E 's/(=).*/=$begin:math:display$REDACTED\_PRESENT$end:math:display$/' || true
} > "$OUT/ENV_PRESENCE_REDACTED.txt" 2>&1

5. Dopemux recon

{
  echo "# DOPMUX_RECON"
  command -v dopemux || true
  dopemux --help 2>&1 || true
  dopemux kernel --help 2>&1 || true
  dopemux mcp --help 2>&1 || true
  dopemux routing --help 2>&1 || true
  dopemux health --help 2>&1 || true
  dopemux workflow --help 2>&1 || true
  dopemux memory --help 2>&1 || true
  dopemux extractor --help 2>&1 || true
  dopemux tmux --help 2>&1 || true
  echo
  echo "## source snippets"
  sed -n '1,220p' pyproject.toml 2>/dev/null || true
  sed -n '1,240p' src/dopemux/cli.py 2>/dev/null || true
  sed -n '1,240p' src/dopemux/commands/kernel_commands.py 2>/dev/null || true
} > "$OUT/DOPMUX_RECON.txt" 2>&1

6. Dopetask recon

{
  echo "# DOPETASK_RECON"
  ls -la .dopetaskroot .dopetask-pin scripts/dopetask scripts/taskx 2>/dev/null || true
  cat .dopetask-pin 2>/dev/null || true
  sed -n '1,260p' scripts/dopetask 2>/dev/null || true
  sed -n '1,220p' scripts/taskx 2>/dev/null || true
  echo
  echo "## help"
  ./scripts/dopetask --help 2>&1 || true
  ./scripts/dopetask doctor 2>&1 || true
  ./scripts/dopetask dopemux --help 2>&1 || true
  ./scripts/dopetask compile-tasks --help 2>&1 || true
  ./scripts/dopetask run-task --help 2>&1 || true
  ./scripts/dopetask collect-evidence --help 2>&1 || true
  ./scripts/dopetask gate-allowlist --help 2>&1 || true
  ./scripts/dopetask promote-run --help 2>&1 || true
  ./scripts/dopetask commit-run --help 2>&1 || true
  ./scripts/dopetask spec-feedback --help 2>&1 || true
  ./scripts/dopetask loop --help 2>&1 || true
  ./scripts/dopetask tp --help 2>&1 || true
} > "$OUT/DOPETASK_RECON.txt" 2>&1

7. MCP recon

{
  echo "# MCP_RECON"
  echo "## config files"
  find . -maxdepth 5 -type f $begin:math:text$ \\
    \-name \'\.mcp\.json\' \-o \\
    \-name \'mcp\*\.json\' \-o \\
    \-name \'mcp\*\.yaml\' \-o \\
    \-name \'\*mcp\*\' \\
  $end:math:text$ | sort
  echo
  echo "## runtime/tool declarations"
  rg -n "FastMCP|@mcp|mcp\.tool|Server\(|register_tool|tool\(|tools/list|jsonrpc|stdio|sse|streamable|/mcp" \
    src services docker config .claude .github compose.yml pyproject.toml -S 2>/dev/null || true
  echo
  echo "## known DCP tool names"
  rg -n "index_workspace|search_code|docs_search|mem\.upsert|mem\.search|graph\.link|graph\.neighbors|assess_risk|get_cognitive_state|assess_task_complexity|analyze_dependencies|batch_tasks|decompose_task|get_workflow_status" \
    src services docker config docs -S 2>/dev/null || true
} > "$OUT/MCP_RECON.txt" 2>&1

8. Repo surface recon

{
  echo "# REPO_SURFACE_RECON"
  echo "## files maxdepth 4"
  find . -maxdepth 4 -type f | sort
  echo
  echo "## runner/model/routing surfaces"
  find . -maxdepth 6 -type f \( \
    -name '*model*' -o \
    -name '*routing*' -o \
    -name '*router*' -o \
    -name '*runner*' -o \
    -name '*opencode*' -o \
    -name '*grok*' -o \
    -name '*codex*' -o \
    -name '*claude*' -o \
    -name '*gemini*' \
  \) | sort
  echo
  echo "## workflows/agents/commands"
  find .claude .github .codex .vibe .Jules config task-packets docs -maxdepth 6 -type f 2>/dev/null | sort
  echo
  echo "## grep"
  rg -n "opencode|grok|grok-build|codex|claude|gemini|antigravity|AGY|aider|openrouter|model-route|runner|routing|DCP|PR Steward|red-lane|proof" \
    .claude .github .codex config docs src services scripts task-packets tests 2>/dev/null -S || true
} > "$OUT/REPO_SURFACE_RECON.txt" 2>&1

9. Final verification

{
  echo "# FINAL_VERIFICATION"
  date -u +"generated_at_utc=%Y-%m-%dT%H:%M:%SZ"
  git status --short --branch
  find "$OUT" -maxdepth 2 -type f | sort
  echo
  echo "## secret scan of recon outputs"
  rg -n "sk-[A-Za-z0-9_-]+|OPENAI_API_KEY=|ANTHROPIC_API_KEY=|GEMINI_API_KEY=|GROK_API_KEY=|XAI_API_KEY=|TOKEN=|SECRET=|PASSWORD=|Bearer " "$OUT" -S || true
} > "$OUT/FINAL_VERIFICATION.txt" 2>&1

Required summaries

Create RECON_FINDINGS.json:

{
  "packet_id": "TP-DMX-DCP-RUNNER-RECON-001",
  "status": "COMPLETE_OR_BLOCKED",
  "repo": "DDD-Enterprises/dopemux-mvp",
  "branch": "",
  "head_sha": "",
  "generated_at_utc": "",
  "runners": {
    "opencode": {
      "availability": "OBSERVED|UNAVAILABLE|UNKNOWN",
      "version": null,
      "config_present": false,
      "notes": []
    },
    "grok_build": {
      "availability": "OBSERVED|UNAVAILABLE|UNKNOWN",
      "binary": "grok|grok-build|null",
      "version": null,
      "auth_state": "OBSERVED|UNKNOWN|MISSING",
      "mcp_configured": "OBSERVED|UNKNOWN|NONE",
      "permission_risk": []
    },
    "codex": {},
    "claude_code": {},
    "gemini_cli": {},
    "agy": {},
    "aider": {}
  },
  "dopemux": {
    "cli_available": "OBSERVED|UNAVAILABLE|UNKNOWN",
    "help_status": "PASS|FAIL|UNKNOWN"
  },
  "dopetask": {
    "available": "OBSERVED|UNAVAILABLE|UNKNOWN",
    "doctor": "PASS|FAIL|UNKNOWN"
  },
  "mcp": {
    "configs_observed": [],
    "liveness": "NOT_TESTED"
  },
  "security": {
    "secret_scan_status": "PASS|REDACTIONS_REQUIRED|BLOCKED",
    "notes": []
  },
  "unknowns": [],
  "conflicts": []
}

Create RECON_SUMMARY.md:

# DCP Runner Recon Summary
## Verdict
READY_FOR_GPT55 / READY_WITH_GAPS / BLOCKED
## Repo State
## Runner Findings
## Dopemux / Dopetask Findings
## MCP Findings
## Security / Secret Redaction
## Highest Risk Unknowns
## Attach These Files to GPT-5.5 Pro

Acceptance criteria

* All required recon files exist.
* No secrets are present in outputs.
* Missing runners are recorded as missing, not installed.
* All command failures are preserved.
* RECON_FINDINGS.json is valid JSON.
* RECON_SUMMARY.md is complete enough for GPT-5.5 Pro.

Validation

python -m json.tool audit_inputs/dcp-runner-recon/RECON_FINDINGS.json >/dev/null
find audit_inputs/dcp-runner-recon -maxdepth 1 -type f | sort
git status --short --branch

Stop conditions

Stop if:

* repo identity is not DDD-Enterprises/dopemux-mvp
* command would expose secrets
* command requires installing/running external code
* output contains unredacted secrets
* any non-audit_inputs/dcp-runner-recon/** file is modified

Final response

Return:

# TP-DMX-DCP-RUNNER-RECON-001 Result
## Status
COMPLETE / COMPLETE_WITH_GAPS / BLOCKED
## Output directory
## Files created
## Command failures
## Secret scan
## Top 10 observed facts
## Top 10 unknowns/conflicts
## Recommended GPT-5.5 attachments
---
# PACK 2 — Combined Orchestration Evidence Pack
```markdown
# Codex Recon Pack — TP-DMX-AIORCH-EVIDENCE-001
## Title
Multi-Model Orchestration Evidence Pack
## Objective
Collect a sanitized repo-grounded evidence pack for GPT-5.5 Pro to evaluate the end-to-end Dopemux / dopetask / DCP multi-model routing, execution, proof, MCP, connector, and workflow architecture.
This is broader than runner recon. It collects authority, runtime entrypoints, service boundaries, workflows, proof contracts, tests, drift, and safety evidence.
## Mode
```text
READ_ONLY_PLUS_EVIDENCE_FILES

Output directory

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="audit_inputs/multi_model_orchestration_evidence/$RUN_ID"
mkdir -p "$OUT"/{commands,inventory,snippets,configs,tests,proof,review}

Scope IN

* repo identity and state
* file/surface inventory
* Dopemux CLI evidence
* Dopetask runtime evidence
* runtime entrypoint snippets
* MCP inventory
* slash/agent/workflow inventory
* services/compose/registry
* model/routing config surfaces
* task packet / PAL / proof / handoff contracts
* tests/CI
* drift/contradiction hunt
* secret redaction report
* final evidence index

Scope OUT

* no source edits
* no config edits
* no docs edits outside evidence dir
* no commits
* no PR
* no service start/stop
* no Dopetask execution
* no MCP tool invocation
* no dependency install
* no live writes

Invariants

* Runtime evidence outranks docs.
* Generated extraction artifacts never outrank runtime.
* dopemux is operator CLI/startup/routing/MCP coordination unless runtime says otherwise.
* dopetask is external execution runtime.
* task-orchestrator workflow views/transitions are not universal PM truth.
* dopecon-bridge is adapter/proxy/event transport only.
* UNKNOWN stays UNKNOWN.
* Contradictions are preserved.
* No raw secrets.

Allowed files

Only:

audit_inputs/multi_model_orchestration_evidence/<RUN_ID>/**

Redaction rules

Before final handoff, scan the evidence directory for:

OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
GROK_API_KEY
XAI_API_KEY
TOKEN=
SECRET=
PASSWORD=
Bearer
api_key
private_key
client_secret
sk-

If found, redact or stop.

Command capture helper

Use:

run_cmd() {
  local name="$1"
  shift
  local file="$OUT/commands/${name}.txt"
  {
    echo "## command: $*"
    echo "## cwd: $(pwd)"
    echo "## started_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo
    "$@"
    local code=$?
    echo
    echo "## exit_code: $code"
    echo "## ended_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    return 0
  } > "$file" 2>&1
}

Append every command to:

$OUT/COMMAND_LEDGER.md

Exact collection plan

Step 1 — repo identity

pwd > "$OUT/commands/pwd.txt" 2>&1
git rev-parse --show-toplevel > "$OUT/commands/git_root.txt" 2>&1
git rev-parse HEAD > "$OUT/commands/git_head.txt" 2>&1
git branch --show-current > "$OUT/commands/git_branch.txt" 2>&1
git remote -v > "$OUT/commands/git_remotes.txt" 2>&1
git status --short > "$OUT/commands/git_status_short.txt" 2>&1
git worktree list > "$OUT/commands/git_worktree_list.txt" 2>&1
git diff --stat > "$OUT/commands/git_diff_stat.txt" 2>&1
git diff --name-only > "$OUT/commands/git_diff_name_only.txt" 2>&1

Write inventory/REPO_STATE.md.

Step 2 — file/surface inventory

find . -maxdepth 4 -type f | sort > "$OUT/commands/find_files_max4.txt" 2>&1
find . -maxdepth 6 -type f $begin:math:text$ \\
  \-name \'\*mcp\*\' \-o \\
  \-name \'\*workflow\*\' \-o \\
  \-name \'\*slash\*\' \-o \\
  \-name \'\*command\*\' \-o \\
  \-name \'\*agent\*\' \-o \\
  \-name \'\*router\*\' \-o \\
  \-name \'\*routing\*\' \\
$end:math:text$ | sort > "$OUT/commands/find_surfaces.txt" 2>&1
find . -maxdepth 5 -type f $begin:math:text$ \\
  \-path \'\.\/\.github\/\*\' \-o \\
  \-path \'\.\/\.claude\/\*\' \-o \\
  \-path \'\.\/\.codex\/\*\' \-o \\
  \-path \'\.\/\.vibe\/\*\' \-o \\
  \-path \'\.\/\.Jules\/\*\' \\
$end:math:text$ | sort > "$OUT/commands/find_agent_workflow_dirs.txt" 2>&1

Write inventory/FILE_SURFACE_INVENTORY.md.

Step 3 — Dopemux CLI

{
  command -v dopemux || true
  dopemux --help 2>&1 || true
  dopemux kernel --help 2>&1 || true
  dopemux mcp --help 2>&1 || true
  dopemux routing --help 2>&1 || true
  dopemux health --help 2>&1 || true
  dopemux workflow --help 2>&1 || true
  dopemux memory --help 2>&1 || true
  dopemux extractor --help 2>&1 || true
  dopemux tmux --help 2>&1 || true
} > "$OUT/commands/dopemux_help.txt" 2>&1

Write inventory/DOPEMUX_CLI_SURFACES.md.

Step 4 — Dopetask runtime

{
  ls -la scripts/dopetask scripts/taskx .dopetaskroot .dopetask-pin 2>/dev/null || true
  sed -n '1,260p' scripts/dopetask 2>/dev/null || true
  sed -n '1,220p' scripts/taskx 2>/dev/null || true
  cat .dopetask-pin 2>/dev/null || true
  ./scripts/dopetask --help 2>&1 || true
  ./scripts/dopetask doctor 2>&1 || true
  ./scripts/dopetask dopemux --help 2>&1 || true
  ./scripts/dopetask compile-tasks --help 2>&1 || true
  ./scripts/dopetask run-task --help 2>&1 || true
  ./scripts/dopetask collect-evidence --help 2>&1 || true
  ./scripts/dopetask gate-allowlist --help 2>&1 || true
  ./scripts/dopetask promote-run --help 2>&1 || true
  ./scripts/dopetask commit-run --help 2>&1 || true
  ./scripts/dopetask spec-feedback --help 2>&1 || true
  ./scripts/dopetask loop --help 2>&1 || true
  ./scripts/dopetask tp --help 2>&1 || true
} > "$OUT/commands/dopetask_help.txt" 2>&1

Write inventory/DOPETASK_RUNTIME_SURFACES.md.

Step 5 — runtime snippets

Capture snippets to snippets/RUNTIME_ENTRYPOINT_SNIPPETS.md:

for f in \
  pyproject.toml \
  src/dopemux/cli.py \
  src/dopemux/commands/kernel_commands.py \
  scripts/taskx \
  scripts/dopetask \
  services/task-orchestrator/app/main.py \
  services/task-orchestrator/mcp_stdio.py \
  services/dope-context/src/mcp/server.py \
  services/working-memory-assistant/dope_memory_main.py \
  services/dopecon-bridge/dopecon_bridge/routes.py \
  services/adhd_engine/main.py \
  services/repo-truth-extractor/run_extraction_v5.py
do
  {
    echo "## $f"
    if [ -f "$f" ]; then sed -n '1,260p' "$f"; else echo "MISSING"; fi
    echo
  } >> "$OUT/snippets/RUNTIME_ENTRYPOINT_SNIPPETS.md"
done

Step 6 — MCP inventory

{
  find . -maxdepth 5 -type f $begin:math:text$ \\
    \-name \'\.mcp\.json\' \-o \\
    \-name \'mcp\*\.json\' \-o \\
    \-name \'mcp\*\.yaml\' \-o \\
    \-name \'\*mcp\*\' \\
  $end:math:text$ | sort
  rg -n "FastMCP|@mcp|mcp\.tool|Server\(|register_tool|tool\(" src services docker config .claude .github -S 2>/dev/null || true
  rg -n "index_workspace|search_code|docs_search|mem\.upsert|mem\.search|graph\.link|graph\.neighbors|assess_risk|get_cognitive_state|assess_task_complexity|analyze_dependencies|batch_tasks|decompose_task|get_workflow_status" src services docker config -S 2>/dev/null || true
} > "$OUT/commands/mcp_inventory_raw.txt" 2>&1

Write inventory/MCP_SERVER_TOOL_INVENTORY.md.

Step 7 — slash / agent / workflow inventory

{
  find .claude .github .codex .vibe .Jules config task-packets docs -maxdepth 6 -type f 2>/dev/null | sort
  rg -n "^---|description:|name:|tools:|model:|handoffs:|slash|command|workflow|agent|codex|claude|gemini|jules|opencode|grok|openrouter" \
    .claude .github .codex .vibe .Jules config task-packets docs src services 2>/dev/null -S || true
  find .github/workflows -maxdepth 2 -type f -print -exec sed -n '1,240p' {} \; 2>/dev/null
} > "$OUT/commands/slash_agent_workflow_raw.txt" 2>&1

Write inventory/SLASH_AGENT_WORKFLOW_INVENTORY.md.

Step 8 — services / compose / registry

{
  find . -maxdepth 4 -type f \( \
    -name 'compose*.yml' -o \
    -name 'docker-compose*.yml' -o \
    -name 'registry.yaml' -o \
    -name 'Dockerfile*' \
  \) | sort
  docker compose ps 2>&1 || true
  docker compose config --services 2>&1 || true
  docker compose config --profiles 2>&1 || true
  sed -n '1,280p' compose.yml 2>/dev/null || true
  sed -n '1,280p' services/registry.yaml 2>/dev/null || true
} > "$OUT/commands/service_compose_raw.txt" 2>&1

Write inventory/SERVICE_COMPOSE_PORT_MAP.md.

Step 9 — routing/model config surfaces

{
  find . -maxdepth 4 -type f $begin:math:text$ \\
    \-name \'\*model\*\' \-o \\
    \-name \'\*routing\*\' \-o \\
    \-name \'\*router\*\' \-o \\
    \-name \'\*litellm\*\' \-o \\
    \-name \'\*openrouter\*\' \-o \\
    \-name \'\*claude\*\' \-o \\
    \-name \'\*codex\*\' \-o \\
    \-name \'\*gemini\*\' \-o \\
    \-name \'\*grok\*\' \\
  $end:math:text$ | sort
  rg -n "model|provider|route|routing|litellm|openrouter|claude|codex|gemini|grok|xai|opus|sonnet|haiku|gpt|5\.5" . src services config docs task-packets 2>/dev/null -S || true
} > "$OUT/commands/routing_model_raw.txt" 2>&1

Write inventory/ROUTING_MODEL_CONFIG_SURFACES.md.

Step 10 — contracts

{
  sed -n '1,260p' dopetask-cannonical-spec.json 2>/dev/null || true
  sed -n '1,260p' PAL_EXECUTION_RULES.md 2>/dev/null || true
  sed -n '1,320p' PAL_CHAINING_DOCTRINE.md 2>/dev/null || true
  sed -n '1,260p' PAL_PACKET_TEMPLATE.md 2>/dev/null || true
  sed -n '1,260p' task-packets/TEMPLATE_TASK_PACKET.md 2>/dev/null || true
  find proof task-packets audit_inputs audit_prep extraction repo-truth-pack -maxdepth 6 -type f $begin:math:text$ \\
    \-name \'\*PROOF\*\' \-o \\
    \-name \'\*proof\*\' \-o \\
    \-name \'\*HANDOFF\*\' \-o \\
    \-name \'\*handoff\*\' \-o \\
    \-name \'\*READINESS\*\' \-o \\
    \-name \'\*MERGE\*\' \-o \\
    \-name \'\*\.json\' \\
  $end:math:text$ | sort 2>/dev/null
} > "$OUT/commands/proof_contracts_raw.txt" 2>&1

Write inventory/PROOF_PACKET_CONTRACTS.md.

Step 11 — tests / CI

{
  find .github/workflows -maxdepth 2 -type f -print -exec sed -n '1,260p' {} \; 2>/dev/null
  find tests -maxdepth 4 -type f | sort 2>/dev/null
  python -m compileall -q src services
  echo "compileall_exit=$?"
  python -m pytest -q
  echo "pytest_exit=$?"
} > "$OUT/tests/TEST_AND_CI_EVIDENCE.md" 2>&1

If pytest fails, also run targeted tests and append output.

Step 12 — drift / contradictions

rg -n "TODO|FIXME|UNKNOWN|drift|legacy|deprecated|TaskX|dopetask|taskx|plan.yaml|execute|validate|LIVE_WRITE_READY|bridge.*authority|not authority|canonical|unsupported|conflict|contradiction" \
  RULES.md PROJECT.md ARCHITECTURE.md PM_PLANE.md SERVICE_CATALOG.md TRUTH_*.md SYSTEM_*.md AGENTS.md docs src services scripts tests -S \
  > "$OUT/review/DRIFT_CONTRADICTION_LEDGER.md" 2>&1 || true

Step 13 — secret redaction report

{
  echo "# Secret Redaction Report"
  echo
  rg -n "OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|GROK_API_KEY|XAI_API_KEY|TOKEN=|SECRET=|PASSWORD=|Bearer |api_key|private_key|client_secret|sk-[A-Za-z0-9_-]+" "$OUT" -S || true
} > "$OUT/review/SECRET_REDACTION_REPORT.md"

If unredacted secrets remain, stop.

Step 14 — evidence index

Create:

$OUT/EVIDENCE_INDEX.md
$OUT/ATTACH_TO_GPT55_PRO.md
$OUT/MISSING_INPUTS_FOR_GPT55_PRO.md

Step 15 — optional zip

cd audit_inputs/multi_model_orchestration_evidence
zip -r "${RUN_ID}.zip" "$RUN_ID"

Acceptance criteria

* evidence index exists
* command ledger exists
* all inventory markdown exists
* secret report exists
* no unredacted secrets
* failures are preserved
* no files outside $OUT modified

Final response

# TP-DMX-AIORCH-EVIDENCE-001 Result
## Status
EVIDENCE_READY / EVIDENCE_READY_WITH_GAPS / BLOCKED
## RUN_ID
## Evidence directory
## Archive path
## Command failures
## Secret redaction status
## Top observed authority facts
## Top UNKNOWN / CONFLICTING items
## Exact attach list for GPT-5.5 Pro
---
# PACK 3 — Secure MCP Read-Only Facade Discovery
```markdown
# Codex Recon Pack — TP-DCP-MCP-RO-0001
## Title
Read-Only MCP Evidence Facade Discovery
## Objective
Produce an evidence-backed discovery pack for a ChatGPT-accessible, Secure MCP Tunnel-compatible, read-only Dopemux evidence facade.
This is discovery and documentation only. It is not implementation, not tunnel setup, and not local MCP exposure.
## Mission
Inspect the repo and classify existing evidence surfaces for a future local MCP facade exposing read-only access to:
- proof bundles and proof artifacts
- repo state and branch/status
- dope-memory chronicle/replay/recap surfaces
- ConPort decisions/context/progress/custom-data reads
- dope-context code/docs retrieval
- task-orchestrator read-only workflow/status surfaces
- repo-truth-extractor outputs
- safe health/info/status surfaces
## Mode
```text
READ_ONLY_PLUS_DOCS_AND_PROOF

Truth order

1. Runtime code/config/compose/tests/active entrypoints.
2. TRUTH_*.md and repo-truth artifacts.
3. canonical docs.
4. system docs.
5. PAL/proof/handoff contracts.
6. current external docs.
7. inference.

Security rules

Do not:

* run tunnel-client
* create OpenAI connector config
* start Docker services
* invoke local MCP tools unless already proven safe
* run write routes
* call POST/PUT/DELETE mutation routes
* run task packets
* expose secrets
* expose raw local paths unnecessarily
* implement the facade

Allowed files

Only:

docs/03-reference/dcp/chatgpt-mcp-readonly/README.md
docs/03-reference/dcp/chatgpt-mcp-readonly/RUNTIME_SURFACE_INVENTORY.md
docs/03-reference/dcp/chatgpt-mcp-readonly/READ_ONLY_SURFACE_INVENTORY.json
docs/03-reference/dcp/chatgpt-mcp-readonly/PROOF_BUNDLE_AND_EVIDENCE_SOURCES.md
docs/03-reference/dcp/chatgpt-mcp-readonly/AUTHORITY_AND_RISK_REGISTER.md
docs/03-reference/dcp/chatgpt-mcp-readonly/PROPOSED_FACADE_TOOLS.md
docs/03-reference/dcp/chatgpt-mcp-readonly/DCP_THREAD_HANDOFF.md
proof/TP-DCP-MCP-RO-0001/PROOF.json
proof/TP-DCP-MCP-RO-0001/COMMAND_LOG.md
proof/TP-DCP-MCP-RO-0001/AUDIT.md

Required commands

Capture command, output, and exit code in proof/TP-DCP-MCP-RO-0001/COMMAND_LOG.md.

Initial state

pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short --branch

Repo shape

git ls-files | sed -n '1,240p'
find . -maxdepth 3 -type f $begin:math:text$ \\
  \-name \'compose\*\.yml\' \-o \\
  \-name \'compose\*\.yaml\' \-o \\
  \-name \'services\.yaml\' \-o \\
  \-name \'registry\.yaml\' \-o \\
  \-name \'pyproject\.toml\' \-o \\
  \-name \'AGENTS\.md\' \-o \\
  \-name \'RULES\.md\' \-o \\
  \-name \'PROJECT\.md\' \-o \\
  \-name \'ARCHITECTURE\.md\' \-o \\
  \-name \'PM\_PLANE\.md\' \-o \\
  \-name \'SERVICE\_CATALOG\.md\' \\
$end:math:text$ | sort

MCP / route discovery

rg -n "FastMCP|@mcp\.tool|mcp\.tool|tools/list|list_tools|MCP|stdio|sse|streamable|/mcp|JSON-RPC|jsonrpc|server.py|mcp_stdio|SseServerTransport|StreamableHTTP" \
  src services docker compose.yml services/registry.yaml pyproject.toml 2>/dev/null || true
rg -n "FastAPI|APIRouter|@app\.(get|post|put|delete|patch)|@router\.(get|post|put|delete|patch)|WebSocket|/health|/info|/status|/metrics" \
  src services docker compose.yml services/registry.yaml 2>/dev/null || true
rg -n "proof|PROOF|proof bundle|PROOF_PACK|bundle|handoff|chain_of_custody|authoritative_artifacts|validation_state|manifest" . 2>/dev/null || true

Secret-pattern inventory, filenames only

rg -l "OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|TOKEN=|PASSWORD=|SECRET=|sk-[A-Za-z0-9_-]+" . 2>/dev/null || true

Targeted inspections

rg -n "dope-memory|dope_memory|chronicle|memory_search|memory_recap|memory_replay|memory_store|memory_correct" services src docs 2>/dev/null || true
rg -n "conport|decision|progress|custom_data|workspace_context|workspace-summary|workspace-relationships" services src docker docs 2>/dev/null || true
rg -n "dope-context|index_workspace|search_code|docs_search|search_all|get_index_status|fetch|DocumentSearch" services src docker docs 2>/dev/null || true
rg -n "task-orchestrator|workflow|blockers|queue|transition|coordination|mcp_stdio" services src docker docs 2>/dev/null || true
rg -n "repo-truth-extractor|run_extraction_v5|PROOF_PACK|COVERAGE_ROLLUP|RUN_DASHBOARD|FAILURE_INDEX" services src docs extraction 2>/dev/null || true
rg -n "dopecon-bridge|/kg/|/ddg/|/route/pm|SAFE_PM|WORKFLOW_SIGNIFICANT|fail closed|fail-closed" services src docs 2>/dev/null || true

Required artifact: READ_ONLY_SURFACE_INVENTORY.json

Create valid JSON:

{
  "packet_id": "TP-DCP-MCP-RO-0001",
  "repo": "DDD-Enterprises/dopemux-mvp",
  "head_sha": "",
  "generated_at_utc": "",
  "summary": {
    "total_surfaces": 0,
    "confirmed_read_only": 0,
    "read_with_side_effect_risk": 0,
    "mutating": 0,
    "unknown": 0,
    "recommended_for_phase_1": 0,
    "deny_for_phase_1": 0
  },
  "surfaces": [],
  "red_lane_findings": [],
  "unresolved_questions": []
}

Each surfaces[] item must include:

{
  "surface_id": "",
  "system": "",
  "authority_domain": "",
  "transport": "",
  "entrypoint_path": "",
  "handler_path": "",
  "port_or_command": "",
  "tool_or_route": "",
  "method": "",
  "operation_kind": "",
  "read_only_classification": "CONFIRMED_READ_ONLY | READ_WITH_SIDE_EFFECT_RISK | MUTATING | UNKNOWN",
  "authority_label": "CANONICAL | OPERATIONAL | DERIVED | PROXY | MIRROR | UNKNOWN",
  "chatgpt_tunnel_suitability": "ALLOW | ALLOW_AFTER_WRAPPER | DENY | UNKNOWN",
  "facade_recommendation": "",
  "security_notes": [],
  "evidence": [],
  "remaining_unknowns": []
}

Required artifact: RUNTIME_SURFACE_INVENTORY.md

Include:

1. Executive summary.
2. Commands used.
3. MCP surfaces.
4. HTTP surfaces.
5. CLI/filesystem proof surfaces.
6. Findings by system:
    * dopemux
    * dopetask
    * task-orchestrator
    * ConPort
    * dope-memory
    * dope-context
    * dopecon-bridge
    * ADHD Engine
    * Repo Truth Extractor
    * proof/governance artifacts
7. Read-only classification table.
8. Authority labels.
9. Drift/contradictions.
10. Phase-1 allowlist.
11. Explicit denylist.
12. Remaining unknowns.

Required artifact: PROOF_BUNDLE_AND_EVIDENCE_SOURCES.md

Map proof/evidence sources:

* proof schemas/contracts
* proof directories
* repo-truth-extractor outputs
* extraction outputs
* handoff bundles
* task packet index/templates
* PR Steward/readiness artifacts
* chronicle/proof-relevant memory outputs

Required artifact: AUTHORITY_AND_RISK_REGISTER.md

Include:

* Secure MCP Tunnel threat model
* prompt-injection risk
* bridge/proxy authority confusion
* side-effect reads
* secret exposure
* stale proof/stale branch risk
* mutable ConPort/progress/custom-data risk
* dope-memory versus ConPort distinction
* task-orchestrator read views versus transitions
* minimum safe phase-1 constraints
* implementation stop conditions

Required artifact: PROPOSED_FACADE_TOOLS.md

Include two versions:

Version A — minimal search/fetch

Only as Phase 2 unless authority labels/provenance are strict.

Version B — Dopemux-specific evidence tools

At minimum propose:

list_projects
get_project_capabilities
get_repo_state_snapshot
list_proof_bundles
fetch_proof_bundle
search_decisions
search_progress
search_chronicle
replay_chronicle_session
search_code_docs
get_index_status
get_workflow_status_snapshot

For each:

* purpose
* input schema
* output schema
* source system
* authority label
* allowed backends
* denied backends/routes
* side-effect policy
* redaction policy
* freshness behavior
* DCP usefulness
* Phase-1 suitability

Required artifact: DCP_THREAD_HANDOFF.md

Include:

1. One-paragraph summary.
2. What Codex inspected.
3. Confirmed safe phase-1 surfaces.
4. Denied/unsafe surfaces.
5. Unknowns requiring GPT-5.5 design decision.
6. Recommended facade architecture in 8–12 bullets.
7. Proposed next GPT-5.5 Pro design prompt inputs.
8. Artifact list produced.
9. “Do not do this” warning section.

Required artifact: PROOF.json

Create:

proof/TP-DCP-MCP-RO-0001/PROOF.json

Use status:

COMPLETE
PARTIAL
BLOCKED

Include:

* packet id
* repo
* branch
* head sha
* scope flags
* authoritative artifacts
* supporting artifacts
* command list
* validation state
* surface counts
* risk summary
* chain of custody

Embedded audit

If AGY / Google Antigravity with Sonnet is available, run it as embedded auditor.

If unavailable, write AUDIT.md with:

auditor_tool
auditor_model
invocation
exit_code
auditor_verdict: PASS / PASS_WITH_RISKS / FAIL / NEEDS_SUPERVISOR / SKIPPED
auditor_findings
fixes_applied_from_audit
remaining_risks
skip_reason

Audit must challenge:

* read-only classifications
* authority labels
* bridge/proxy confusion
* mutable-but-read-looking routes
* proof freshness assumptions
* secret exposure
* whether proposed Phase-1 tools are too broad

Validation

python -m json.tool docs/03-reference/dcp/chatgpt-mcp-readonly/READ_ONLY_SURFACE_INVENTORY.json >/tmp/read_only_surface_inventory.validated.json
python -m json.tool proof/TP-DCP-MCP-RO-0001/PROOF.json >/tmp/tp_dcp_mcp_ro_0001_proof.validated.json
git diff --stat
git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0001
git status --short --branch

Commit plan

If validation passes and only allowed files changed:

git add docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0001
git commit -m "docs(dcp): inventory chatgpt readonly mcp evidence facade"

Do not push. Do not open PR.

Stop conditions

Stop if:

* repo identity wrong
* unrelated uncommitted changes
* secret risk
* classification requires mutating tool
* runtime behavior cannot classify route
* JSON inventory/proof invalid
* generated artifacts require runtime/source/config/test changes

Final response

# TP-DCP-MCP-RO-0001 Result
## Status
COMPLETE / PARTIAL / BLOCKED
## Branch / head
## Files created
## Phase-1 allowlist
## Denied / unsafe surfaces
## Remaining UNKNOWNs
## Validation commands
## Diff stat
## Commit hash or commit-ready status
---
# PACK 4 — ECC External Component Harvest
```markdown
# Codex Recon Pack — MP-DMX-ECC-000
## Title
External Repo Intake: Read-Only ECC Evidence Harvest
## Objective
Create a static, read-only evidence bundle for auditing `https://github.com/affaan-m/ECC` against Dopemux / DCP architecture and authority boundaries.
This packet creates:
```text
/tmp/ecc-dopemux-audit/ECC_HEAD.txt
/tmp/ecc-dopemux-audit/ECC_REMOTES.txt
/tmp/ecc-dopemux-audit/ECC_STATUS.txt
/tmp/ecc-dopemux-audit/ECC_FILE_LIST.txt
/tmp/ecc-dopemux-audit/ECC_FIND_MAX4.txt
/tmp/ecc-dopemux-audit/ECC_STRUCTURE_SUMMARY.md
/tmp/ecc-dopemux-audit/ECC_KEYWORD_HITS.txt
/tmp/ecc-dopemux-audit/ECC_SUSPICIOUS_TEXT_HITS.txt
/tmp/ecc-dopemux-audit/ECC_EXEC_SECRET_RISK_HITS.txt
/tmp/ecc-dopemux-audit/ECC_AUDIT_EVIDENCE_INDEX.md
/tmp/ecc-dopemux-audit/EVIDENCE_BUNDLE_FILE_LIST.txt
/tmp/ecc-dopemux-audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz

Mode

READ_ONLY_EXTERNAL_REPO_HARVEST

Scope IN

* clone ECC into /tmp
* record commit/remotes/status/file tree
* copy selected docs/source into evidence folder
* run static text/security scans
* create evidence index
* archive evidence bundle

Scope OUT

* no Dopemux repo edits
* no ECC install
* no ECC hooks
* no ECC dashboard
* no ECC agents
* no ECC MCP configs
* no npm install
* no npx
* no pnpm
* no bun
* no lifecycle scripts
* no network after clone unless explicitly approved
* no secrets loading

Invariants

* ECC is untrusted supply-chain input.
* Do not execute ECC code.
* Do not source ECC shell scripts.
* Do not import ECC packages.
* Do not copy ECC code into Dopemux.
* Preserve suspicious findings.
* Pin exact commit SHA.
* If a command would execute ECC, skip it and report.

Allowed locations

Only:

/tmp/ecc-dopemux-audit/**

Exact commands

set -euo pipefail
rm -rf /tmp/ecc-dopemux-audit
mkdir -p /tmp/ecc-dopemux-audit
cd /tmp/ecc-dopemux-audit
git clone --depth 1 https://github.com/affaan-m/ECC.git
cd ECC
git rev-parse HEAD > /tmp/ecc-dopemux-audit/ECC_HEAD.txt
git remote -v > /tmp/ecc-dopemux-audit/ECC_REMOTES.txt
git status --short > /tmp/ecc-dopemux-audit/ECC_STATUS.txt
git ls-tree -r --name-only HEAD > /tmp/ecc-dopemux-audit/ECC_FILE_LIST.txt
find . -maxdepth 4 -type f | sort > /tmp/ecc-dopemux-audit/ECC_FIND_MAX4.txt

Structure summary

{
  echo "## root"
  find . -maxdepth 1 $begin:math:text$ \-type f \-o \-type d $end:math:text$ | sort
  echo
  echo "## key dirs"
  for d in agents .agents commands hooks scripts manifests schemas mcp-configs rules skills docs .claude-plugin .codex .cursor .gemini .opencode .zed ecc2; do
    if [ -e "$d" ]; then
      echo "### $d"
      find "$d" -maxdepth 3 -type f | sort | head -200
      echo
    fi
  done
} > /tmp/ecc-dopemux-audit/ECC_STRUCTURE_SUMMARY.md

Copy selected files

for f in \
  README.md \
  package.json \
  LICENSE \
  COMMANDS-QUICK-REF.md \
  docs/SELECTIVE-INSTALL-DESIGN.md \
  docs/SELECTIVE-INSTALL-ARCHITECTURE.md \
  the-security-guide.md \
  manifests/install-modules.json \
  manifests/install-profiles.json \
  schemas/install-modules.schema.json \
  schemas/install-profiles.schema.json \
  schemas/install-state.schema.json
do
  if [ -f "$f" ]; then
    mkdir -p "/tmp/ecc-dopemux-audit/evidence/$(dirname "$f")"
    cp "$f" "/tmp/ecc-dopemux-audit/evidence/$f"
  fi
done

Keyword scan

rg -n "install-state|install-plan|install-apply|doctor|repair|uninstall|manifest|profile|hooks-runtime|AgentShield|security|MCP|mcp|worktree|tmux|orchestrat|model-route|harness-audit|quality-gate|session|memory|learning|skill" . \
  --glob '!node_modules/**' \
  --glob '!.git/**' \
  > /tmp/ecc-dopemux-audit/ECC_KEYWORD_HITS.txt || true

Suspicious text scan

rg -nP '[\x{200B}\x{200C}\x{200D}\x{2060}\x{FEFF}\x{202A}-\x{202E}]|<!--|<script|data:text/html|base64,' . \
  --glob '!node_modules/**' \
  --glob '!.git/**' \
  > /tmp/ecc-dopemux-audit/ECC_SUSPICIOUS_TEXT_HITS.txt || true

Exec / secret risk scan

rg -n "curl .*bash|wget .*bash|rm -rf|sudo|chmod \+x|ANTHROPIC_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|token|secret|password|Bash\(|shell|exec|spawn|child_process" . \
  --glob '!node_modules/**' \
  --glob '!.git/**' \
  > /tmp/ecc-dopemux-audit/ECC_EXEC_SECRET_RISK_HITS.txt || true

Evidence index

cat > /tmp/ecc-dopemux-audit/ECC_AUDIT_EVIDENCE_INDEX.md <<'EOF'
# ECC Audit Evidence Index
## Repo
- URL: https://github.com/affaan-m/ECC
- Commit SHA: TODO paste ECC_HEAD.txt
- Harvest mode: read-only static inspection
- Dopemux mutation: none
## Commands Run
TODO paste commands and exit codes.
## Evidence Files
TODO list files under /tmp/ecc-dopemux-audit/evidence.
## Candidate Areas
TODO summarize observed candidate areas only.
## Security / Intake Concerns
TODO summarize suspicious text, executable, secret, hook, MCP, and install risks.
## Skipped Commands
TODO list skipped commands and reason.
## UNKNOWNs
TODO list unresolved facts.
EOF

Fill the TODOs from collected files before final.

Archive

cd /tmp/ecc-dopemux-audit
find . -maxdepth 5 -type f | sort > EVIDENCE_BUNDLE_FILE_LIST.txt
tar -czf ECC_DOPMUX_AUDIT_EVIDENCE.tgz \
  ECC_HEAD.txt \
  ECC_REMOTES.txt \
  ECC_STATUS.txt \
  ECC_FILE_LIST.txt \
  ECC_FIND_MAX4.txt \
  ECC_STRUCTURE_SUMMARY.md \
  ECC_KEYWORD_HITS.txt \
  ECC_SUSPICIOUS_TEXT_HITS.txt \
  ECC_EXEC_SECRET_RISK_HITS.txt \
  ECC_AUDIT_EVIDENCE_INDEX.md \
  EVIDENCE_BUNDLE_FILE_LIST.txt \
  evidence

Validation

test -s /tmp/ecc-dopemux-audit/ECC_HEAD.txt
test -s /tmp/ecc-dopemux-audit/ECC_FILE_LIST.txt
test -s /tmp/ecc-dopemux-audit/ECC_AUDIT_EVIDENCE_INDEX.md
test -s /tmp/ecc-dopemux-audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz
tar -tzf /tmp/ecc-dopemux-audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz | head -50

Acceptance criteria

* ECC commit SHA recorded.
* Evidence bundle exists.
* Static scans exist even if empty.
* No ECC code executed.
* No Dopemux files modified.
* Evidence index is usable for GPT-5.5 Pro.

Stop conditions

Stop if:

* clone fails
* repo path is not affaan-m/ECC
* command would execute ECC code
* scan reveals obvious secrets that should not be pasted into ChatGPT
* evidence cannot be pinned to commit SHA

Rollback

rm -rf /tmp/ecc-dopemux-audit

Final response

# MP-DMX-ECC-000 Result
## Status
COMPLETE / BLOCKED
## ECC commit SHA
## Evidence bundle path
## Files created
## Top keyword findings
## Top suspicious/security findings
## Commands skipped
## Stop conditions triggered
## Recommended GPT-5.5 attachments
---
# PACK 5 — GPT-5.5 Attachment Assembler
```markdown
# Codex Recon Pack — TP-DMX-GPT55-ATTACHMENT-ASSEMBLER-001
## Title
Assemble Final GPT-5.5 Pro Input Bundle
## Objective
Create a single attachment manifest and optional zip bundle for the final GPT-5.5 Pro prompt series.
This packet does not inspect architecture. It packages evidence and records missing files.
## Mode
```text
READ_ONLY_PLUS_ARCHIVE

Scope IN

Collect references to:

* runner recon bundle
* orchestration evidence pack
* Secure MCP facade discovery
* ECC harvest bundle
* repo truth/governance docs
* model/runner ledgers
* DCP synthesis docs
* DCP routing evidence
* PR evidence if present

Scope OUT

* no source edits
* no docs edits outside audit_inputs/final_gpt55_bundle/
* no runtime commands except file listing and archive
* no secret-bearing files
* no .env
* no full compose config

Allowed files

Only:

audit_inputs/final_gpt55_bundle/**

Exact commands

set -euo pipefail
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="audit_inputs/final_gpt55_bundle/$RUN_ID"
mkdir -p "$OUT"
cat > "$OUT/ATTACHMENT_MANIFEST.md" <<'EOF'
# Final GPT-5.5 Pro Attachment Manifest
## Required runtime recon
- audit_inputs/dcp-runner-recon/GIT_RECON.txt
- audit_inputs/dcp-runner-recon/OPEN_CODE_RECON.txt
- audit_inputs/dcp-runner-recon/GROK_BUILD_RECON.txt
- audit_inputs/dcp-runner-recon/ENV_PRESENCE_REDACTED.txt
- audit_inputs/dcp-runner-recon/DOPMUX_RECON.txt
- audit_inputs/dcp-runner-recon/DOPETASK_RECON.txt
- audit_inputs/dcp-runner-recon/MCP_RECON.txt
- audit_inputs/dcp-runner-recon/REPO_SURFACE_RECON.txt
- audit_inputs/dcp-runner-recon/FINAL_VERIFICATION.txt
- audit_inputs/dcp-runner-recon/RECON_SUMMARY.md
- audit_inputs/dcp-runner-recon/RECON_FINDINGS.json
## Required orchestration evidence
- latest audit_inputs/multi_model_orchestration_evidence/<RUN_ID>.zip
## Required Secure MCP evidence
- docs/03-reference/dcp/chatgpt-mcp-readonly/**
- proof/TP-DCP-MCP-RO-0001/**
## Required ECC evidence
- /tmp/ecc-dopemux-audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz
- /tmp/ecc-dopemux-audit/ECC_AUDIT_EVIDENCE_INDEX.md
- /tmp/ecc-dopemux-audit/ECC_HEAD.txt
## Required governance docs
- RULES.md
- PROJECT.md
- ARCHITECTURE.md
- SYSTEM_BOUNDARIES.md or 04_system-boundaries.md
- PM_PLANE.md
- SERVICE_CATALOG.md
- TRUTH_*.md
- SYSTEM_*.md
- AGENTS.md
- PAL_*.md
- proof/handoff/adapter contracts
- dopetask-cannonical-spec.json
## Required model / runner ledgers
- MODEL_PROVIDER_CAPABILITY_LEDGER.md
- RUNNER_CLI_INTEGRATION_LEDGER.md
- OPENROUTER_CODING_MODEL_EXPANSION.md
## Existing DCP synthesis
- DCP_5_5_SYNTHESIS_INPUT_PACK.md
- DCP_ARCHITECTURE_SYNTHESIS_GPT55.md
- DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md
- DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md
- DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md
- DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md
- DCP_BUILD_RECON.md
- DCP_BUILD_RECON.json
EOF

File existence report

{
  echo "# Attachment Existence Report"
  echo
  date -u +"generated_at_utc=%Y-%m-%dT%H:%M:%SZ"
  echo
  while IFS= read -r line; do
    case "$line" in
      "- "*)
        p="${line#- }"
        if ls $p >/dev/null 2>&1; then
          echo "PRESENT: $p"
        else
          echo "MISSING: $p"
        fi
        ;;
    esac
  done < "$OUT/ATTACHMENT_MANIFEST.md"
} > "$OUT/ATTACHMENT_EXISTENCE_REPORT.md"

Secret risk report

{
  echo "# Secret Risk Report"
  echo
  echo "No file contents scanned here unless copied into bundle."
  echo "Do not attach .env, raw credentials, tunnel secrets, local auth stores, or interpolated compose config."
} > "$OUT/SECRET_RISK_REPORT.md"

Optional copy lightweight manifest only

Do not copy huge files by default. Create a bundle containing the manifest/reports:

cd audit_inputs/final_gpt55_bundle
zip -r "$RUN_ID-final-gpt55-manifest.zip" "$RUN_ID"

Acceptance criteria

* manifest created
* existence report created
* missing inputs listed
* no secrets copied
* final zip contains only manifest metadata unless operator explicitly asks for full bundle

Final response

# TP-DMX-GPT55-ATTACHMENT-ASSEMBLER-001 Result
## Status
COMPLETE / COMPLETE_WITH_MISSING_INPUTS / BLOCKED
## Manifest path
## Zip path
## Missing blocking inputs
## Missing non-blocking inputs
## Attach order
---
## Recommended execution order
```text
1. TP-DMX-DCP-RUNNER-RECON-001
2. TP-DMX-AIORCH-EVIDENCE-001
3. TP-DCP-MCP-RO-0001
4. MP-DMX-ECC-000
5. TP-DMX-GPT55-ATTACHMENT-ASSEMBLER-001
6. GPT-5.5 Pro Prompt 1

Tool routing

Codex:
  runner recon, evidence pack, attachment assembler
Codex or Claude Sonnet:
  Secure MCP discovery
  ECC harvest
Claude Opus / GPT-5.5 Pro:
  synthesis and adversarial review
Do not use OpenCode/Grok/Grok Build for recon until their runner proof and safety posture are known.

One-line launch commands

Codex, run TP-DMX-DCP-RUNNER-RECON-001 exactly. Evidence-only, no source edits, no installs, no secrets.
Codex, run TP-DMX-AIORCH-EVIDENCE-001 exactly. Evidence-only, write only under audit_inputs/multi_model_orchestration_evidence.
Codex, run TP-DCP-MCP-RO-0001 exactly. Discovery/docs/proof only, no tunnel, no MCP tool calls, no implementation.
Codex, run MP-DMX-ECC-000 exactly. Clone ECC to /tmp, read-only static harvest, no install/run/import.
Codex, run TP-DMX-GPT55-ATTACHMENT-ASSEMBLER-001 exactly. Manifest only, no secret files, no giant copy unless asked.