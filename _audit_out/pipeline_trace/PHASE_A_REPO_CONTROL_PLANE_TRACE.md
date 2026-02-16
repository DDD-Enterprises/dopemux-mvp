# Phase A: Repo Control Plane (Flash/Grok)

## Phase A goal
Extract Repo Control Plane surfaces that modulate behavior:
Instruction files (Claude/Codex/agents) and how they reference tools/services
MCP proxy/server configs and server definitions
Router/provider ladders (model selection, fallbacks)
Hooks (git hooks, taskx hooks, any scripts run implicitly)
Compose graphs and environment wiring
LiteLLM configs (routing, logging, spend, DBs)
TaskX integration surfaces in repo (.taskx*, pins, operator profiles, templates)
Implicit behavior triggers (scripts invoked by Makefile, CI, installer, start scripts)
All outputs must be mechanical evidence indices.

## Preferred model
Primary: Grok-code-fast-1
Fallback: Gemini Flash 3

## Hard rules
JSON only, ASCII only.
Every item includes path + line_range + excerpt (<= N lines as specified).
Do not infer intent. Do not label semantics. Do not decide “authoritative”.
Stable ordering.

## A0: Repo control inventory + partition plan (mandatory)
Outputs
REPO_CONTROL_INVENTORY.json
REPO_CONTROL_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.
TARGET ROOT: dopemux-mvp repo working tree.

INCLUDE PATHS:
- .claude/**, .claude.json, .claude.json.template
- .dopemux/**, dopemux.toml, dopemux.rb
- .githooks/**, .git/hooks/** (if tracked), scripts/**, tools/**
- compose/**, compose.yml, docker-compose*.yml, docker/**, Dockerfile*
- AGENTS.md, CLAUDE.md, claude.md, README.md, QUICK_START.md, INSTALL.md
- litellm.config*, mcp-proxy-config*.y*ml/json, start-mcp-servers.sh
- .taskx/**, .taskx-pin, .taskxroot, .taskx_venv (just names)
- config/**, profiles/**, installers/**, install.sh, Makefile
- .github/** (workflow files)
- tmux-dopemux-orchestrator.yaml, .tmux.conf

OUTPUT 1: REPO_CONTROL_INVENTORY.json
For each included file:
- path
- size_bytes
- last_modified (if available)
- sha256 (if available)
- file_kind by extension (md|json|yaml|toml|sh|py|rb|other)
- first_nonempty_line (scan first 80 lines)
- contains_tokens[]: list of matched tokens from:
  ["mcp","litellm","router","provider","model","taskx","hook","compose","docker","tmux","agent","instruction","server","proxy","env","dotenv"]

OUTPUT 2: REPO_CONTROL_PARTITION_PLAN.json
Create deterministic partitions with explicit path lists:
A1_INSTRUCTIONS
A2_MCP_PROXY_AND_SERVERS
A3_ROUTER_PROVIDER_LADDERS
A4_HOOKS_AND_IMPLICIT_TRIGGERS
A5_COMPOSE_AND_SERVICE_GRAPH
A6_LITELLM_CONFIG_AND_LOGGING
A7_TASKX_REPO_SURFACE
A8_CI_AND_GATES

RULES:
- Partitioning is by path heuristics only.
- No interpretation.
- JSON only.

## A1: Instruction surfaces (priority treatment)
Outputs
REPO_INSTRUCTION_SURFACE.json
REPO_INSTRUCTION_REFERENCES.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE: Files likely to contain LLM instructions:
- .claude/**, AGENTS.md, CLAUDE.md, claude.md
- docs/**/custom-instructions/** (if present)
- docs/**/prompts*/** (if present)
- any file with "instruction" or "agent" in name from REPO_CONTROL_INVENTORY

TASK 1: REPO_INSTRUCTION_SURFACE.json
For each instruction-like block:
- path, line_range
- block_kind: markdown_section | yaml_block | json_block | plain_text
- excerpt <= 25 lines
- detected_directives[]: extract literal occurrences of:
  ["MUST","MUST NOT","NEVER","ALWAYS","STOP","Authority","Hierarchy","Invariants","No invention","Deterministic"]
- tool_mentions[]: literal tool/server names mentioned (e.g., "mcp", "filesystem", "memory", "conport", "serena", "dope-context", "taskx")

TASK 2: REPO_INSTRUCTION_REFERENCES.json
Extract explicit references to:
- file paths
- commands (lines starting with $, `make`, `docker`, `uv`, `python`, `node`, `taskx`)
- server configs (mcp, litellm, proxy)
For each reference:
- ref_kind: path|command|server|env|url
- value: literal string
- path, line_range, excerpt <= 6 lines

RULES:
- Do not interpret directives.
- JSON only.

## A2: MCP proxy + server definitions (repo)
Outputs
REPO_MCP_PROXY_SURFACE.json
REPO_MCP_SERVER_DEFS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- mcp-proxy-config*.yaml/json
- start-mcp-servers.sh
- docs/archive/mcp-servers/** (index only, do not infer)
- any compose files referencing mcp
- config files mentioning mcp in REPO_CONTROL_INVENTORY

TASK 1: REPO_MCP_PROXY_SURFACE.json
Extract:
- proxy config sections (servers, routes, env, auth, allowlists)
- path, line_range, excerpt <= 40 lines per section
Also emit:
- server_ids: literal keys/names if parseable

TASK 2: REPO_MCP_SERVER_DEFS.json
Extract server launch definitions:
- command + args
- env vars set for each server
- working dirs if specified
For each server:
- server_name
- command
- args[]
- env_kv[] (key only; redact values if sensitive)
- path, line_range, excerpt <= 20 lines

RULES:
- Redact secrets: if a value looks like key/token, output "***REDACTED***"
- JSON only.

## A3: Router + provider ladders (repo)
Outputs
REPO_ROUTER_SURFACE.json
REPO_PROVIDER_LADDER_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .claude.json, .claude/**, .dopemux/**, dopemux.toml
- any "router" configs, "provider" configs, "model" lists
- litellm.config* (also covered in A6 but extract routing bits here too)

TASK 1: REPO_ROUTER_SURFACE.json
Extract any configuration that appears to route requests:
- provider selection rules
- trust levels
- project allowlists
- model settings (name, reasoning effort)
For each block:
- path, line_range, excerpt <= 40 lines
- detected_keys[] (keys only)

TASK 2: REPO_PROVIDER_LADDER_HINTS.json
Extract literal ordered lists of providers/models/fallbacks:
- arrays or bullet lists of providers/models
- environment variables controlling provider
For each ladder:
- ladder_id
- ordered_items[] (literal strings)
- path, line_range, excerpt <= 20 lines

RULES:
- No claims about which is used at runtime.
- JSON only.

## A4: Hooks + implicit triggers (repo)
Outputs
REPO_HOOKS_SURFACE.json
REPO_IMPLICIT_BEHAVIOR_HINTS.json
REPO_BOOTSTRAP_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .githooks/**
- install.sh, installers/**, scripts/**, tools/**
- Makefile targets that call scripts
- .envrc, .env*, dopemux.rb (if it runs stuff)
- any "bootstrap", "start", "verify", "setup" scripts

TASK 1: REPO_HOOKS_SURFACE.json
Extract:
- hook files (pre-commit, post-checkout, post-merge, etc.)
- commands executed
For each hook:
- hook_name (filename)
- path, line_range, excerpt <= 40 lines

TASK 2: REPO_IMPLICIT_BEHAVIOR_HINTS.json
Extract command chains that can run implicitly:
- Makefile recipes
- installer scripts
- dev scripts that call other scripts
For each chain:
- chain_id
- steps[] (literal command lines)
- path, line_range, excerpt <= 30 lines

TASK 3: REPO_BOOTSTRAP_SURFACE.json
Extract "how the system starts":
- start scripts, compose up invocations, tmux layouts
For each:
- bootstrap_kind = compose|tmux|shell|python|node|other
- path, line_range, excerpt <= 40 lines

RULES:
- JSON only.
- No inference of purpose.

## A5: Compose + service graph (repo)
Outputs
REPO_COMPOSE_SERVICE_GRAPH.json
REPO_ENV_WIRING.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- compose.yml
- docker-compose*.yml
- compose/**

TASK 1: REPO_COMPOSE_SERVICE_GRAPH.json
Parse compose files and emit:
- services[]:
  - name
  - image/build (literal)
  - depends_on
  - ports
  - volumes
  - environment_keys[] (keys only; redact values)
  - command/entrypoint (literal)
  - networks
  - profiles
- file_sources[]: list of compose files used

TASK 2: REPO_ENV_WIRING.json
Extract:
- env files referenced
- environment variables used in compose as ${VAR}
Emit:
- var_name
- path, line_range, excerpt <= 6 lines
- used_in_service if parseable

RULES:
- JSON only.
- Redact suspicious values.

## A6: LiteLLM config + logging + spend DB surfaces (repo)
Outputs
REPO_LITELLM_SURFACE.json
REPO_LITELLM_DB_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- litellm.config
- litellm.config.yaml
- any file referencing "litellm"
- compose env for litellm
- docs about litellm (index only)

TASK 1: REPO_LITELLM_SURFACE.json
Extract:
- model definitions
- routers
- logging settings
- callbacks
- rate limits
- proxy settings
For each config block:
- path, line_range, excerpt <= 60 lines
- detected_keys[] (keys only)

TASK 2: REPO_LITELLM_DB_HINTS.json
Extract literal DB references:
- sqlite/postgres URLs
- file paths
- env vars for DB
For each:
- db_kind = sqlite|postgres|other|unknown
- path, line_range, excerpt <= 8 lines
- redacted_value if sensitive

RULES:
- JSON only.
- Redact values that look like credentials.

## A7: TaskX surfaces in repo (pinning, operator instructions, templates)
Outputs
REPO_TASKX_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .taskx/**
- .taskx-pin
- .taskxroot
- docs/task-packets/**
- any scripts invoking taskx

Extract:
- pin versions and roots
- operator profile files and compiled prompt outputs if present
- task packet templates and locations
- any CLI invocations of taskx in scripts/make/ci

For each item:
- item_kind = pin|root|profile|template|packet|invocation|output
- path, line_range, excerpt <= 40 lines
- detected_fields[] (keys only) if yaml/json

RULES:
- JSON only.

## A8: CI + gates (repo)
Outputs
REPO_CI_GATES_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .github/workflows/**
- .pre-commit-config.yaml
- pytest.ini, ruff/mypy configs
- scripts that look like CI gates

Extract:
- job steps that run tests/lint/format
- any artifact upload paths
- any environment requirements

For each gate:
- gate_kind = github_actions|precommit|pytest|ruff|mypy|other
- path, line_range, excerpt <= 60 lines
- commands[] (literal)

RULES:
- JSON only.

## A9: Merge + normalize + QA
Outputs
All normalized REPO_*.json in A_repo_control_plane/norm/
A_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS:
- all raw outputs from A0..A8

MERGE RULES:
- dedupe by (path, line_range, sha256(excerpt))
- stable sort by path then start line
- ensure each output has:
  - artifact_type
  - generated_at_local
  - inputs[] (file list)
  - items[]

QA OUTPUT: A_COVERAGE_REPORT.json
Include:
- expected_artifacts list
- present_artifacts list
- missing_artifacts list
- item_counts per artifact
- top_paths_by_items (top 25)
- redaction_count

JSON only.


# CONTEXT

## Repository Structure
.backup_location
.claude/AGENT_ARCHITECTURE.md
.claude/MULTI_LANGUAGE_SUPPORT.md
.claude/PRIMER.md
.claude/PROJECT_INSTRUCTIONS.md
.claude/README.md
.claude/SYNERGISTIC_WORKFLOWS.md
.claude/WORKTREE_MCP_SETUP.md
.claude/claude.md
.claude/claude_config.json
.claude/claude_config.json.bak_20260212_122329
.claude/claude_config.json.bak_20260212_160600
.claude/claude_config.json.bak_20260212_165708
.claude/claude_config.json.bak_20260212_165721
.claude/claude_config.json.bak_20260212_200248
.claude/claude_config.json.bak_20260212_200320
.claude/claude_config.json.bak_20260212_201250
.claude/claude_config.json.bak_20260212_201422
.claude/claude_config.json.bak_20260212_204028
.claude/claude_config.json.bak_20260212_204259
.claude/claude_config.json.bak_20260212_205246
.claude/claude_config.json.bak_20260212_210009
.claude/claude_config.json.disabled
.claude/commands/doc-pull.md
.claude/commands/dx/implement.md
.claude/context.md
.claude/docs/GLOBAL_MCP_CONFIGURATION.md
.claude/docs/MCP_DesktopCommander.md
.claude/hooks/check_energy.sh
.claude/hooks/log_progress.sh
.claude/hooks/prompt_analyzer.py
.claude/hooks/save_context.sh
.claude/llm.md
.claude/llms.md
.claude/mcp-system.md
.claude/modules/_index.md
.claude/modules/cognitive-plane/serena-lsp.md
.claude/modules/coordination/authority-matrix.md
.claude/modules/coordination/integration-bridge.md
.claude/modules/shared/event-patterns.md
.claude/personas/backend-architect-dopemux.md
.claude/personas/devops-architect-dopemux.md
.claude/personas/frontend-architect-dopemux.md
.claude/personas/general-purpose-dopemux.md
.claude/personas/learning-guide-dopemux.md
.claude/personas/performance-engineer-dopemux.md
.claude/personas/python-expert-dopemux.md
.claude/personas/quality-engineer-dopemux.md
.claude/personas/security-engineer-dopemux.md
.claude/personas/socratic-mentor-dopemux.md
.claude/personas/statusline-setup-dopemux.md
.claude/personas/system-architect-dopemux.md
.claude/personas/technical-writer-dopemux.md
.claude/plans/silly-riding-curry.md
.claude/prompts/DEEP_COMPONENT_RESEARCH_PROMPT.md
.claude/session.md
.claude/sessions/2025-09-26-gpt-researcher-integration.md
.claude/sessions/current-status.md
.claude/settings.json
.claude/settings.local.json
.claude/statusline.sh
.claude/task-master-mcp-config.json
.claude/workflows/QUICK_REFERENCE.md
.claude/workflows/WORKFLOW_AUTOMATION.md
.claude/workflows/templates/bug-fix.md
.claude/workflows/templates/feature-implementation.md
.claude.json
.claude.json.template
.dockerignore
.dopemux/Dopemux-Architectural-Hardening-Template.md
.dopemux/active_profile
.dopemux/capture_audit.log
.dopemux/chronicle.sqlite
.dopemux/claude-code-router/A/.claude-code-router/.claude.json
.dopemux/config.yaml
.dopemux/context.db
.dopemux/dope-brainz-router/A/.claude.json
.dopemux/dope-brainz-router/A/.dope-brainz-router/.claude-code-router.pid
.dopemux/dope-brainz-router/A/.dope-brainz-router/api.key
.dopemux/dope-brainz-router/A/.dope-brainz-router/config.json
.dopemux/dope-brainz-router/A/.dope-brainz-router/logs/ccr-20260208183133.log
.dopemux/dope-brainz-router/A/.dope-brainz-router/logs/ccr-20260208183323.log
.dopemux/dope-brainz-router/A/.dope-brainz-router/logs/ccr-20260208183512.log
.dopemux/dope-brainz-router/A/.dope-brainz-router/logs/ccr-20260208183512.log.txt
.dopemux/dope-brainz-router/A/.dope-brainz-router/logs/ccr-20260209000000_1.log
.dopemux/dope-brainz-router/A/.dope-brainz-router/logs/ccr-20260215083645.log
.dopemux/dope-brainz-router/A/dope-brainz-router.log
.dopemux/env/current.env
.dopemux/env/current.sh
.dopemux/env/instance_A.env
.dopemux/env/instance_A.sh
.dopemux/instances_cache.json
.dopemux/litellm/A/litellm.config.yaml
.dopemux/litellm/A/master.key
.dopemux/sessions/20250121_204500_multi_instance_complete.json
.dopemux/sessions/session-1c6be768-2270-4c71-bf25-5b9845bb58a2.json
.env
.env.example
.env.smoke
.envrc
.githooks/pre-commit
.github/copilot-instructions.md
.github/instructions/codacy.instructions.md
.github/workflows/ci-complete.yml
.github/workflows/docs.yml
.github/workflows/repo-identity.yml
.github/workflows/security-review.yml
.gitignore
.lychee.toml
.markdownlint.jsonc
.pre-commit-config.yaml
.repo_id
.ruff_cache/.gitignore
.ruff_cache/0.14.13/10015026113523046369
.ruff_cache/0.14.13/10029985470555385662
.ruff_cache/0.14.13/10051954397201316011
.ruff_cache/0.14.13/10054084736895669161
.ruff_cache/0.14.13/10066754833764357255
.ruff_cache/0.14.13/10104644839742613171
.ruff_cache/0.14.13/1010512270611485289
.ruff_cache/0.14.13/10114521260190478345
.ruff_cache/0.14.13/10116466528626382734
.ruff_cache/0.14.13/10125917453056507056
.ruff_cache/0.14.13/1013631458116353172
.ruff_cache/0.14.13/1014461155227095486
.ruff_cache/0.14.13/10146175404349167492
.ruff_cache/0.14.13/10149319943678339564
.ruff_cache/0.14.13/10152994697331146308
.ruff_cache/0.14.13/10153475475804954307
.ruff_cache/0.14.13/1015911393910833128
.ruff_cache/0.14.13/1017042109844050052
.ruff_cache/0.14.13/10183988722012698941
.ruff_cache/0.14.13/10195163805822719719
.ruff_cache/0.14.13/10199093538716236569
.ruff_cache/0.14.13/10202591049149652901
.ruff_cache/0.14.13/10208802784522299851
.ruff_cache/0.14.13/10215135970646926970
.ruff_cache/0.14.13/10245208071279798087
.ruff_cache/0.14.13/10245996387102556782
.ruff_cache/0.14.13/1025394831281662644
.ruff_cache/0.14.13/10261292076043670345
.ruff_cache/0.14.13/10285453021862776611
.ruff_cache/0.14.13/1029003800390818376
.ruff_cache/0.14.13/10296297502525539257
.ruff_cache/0.14.13/10303251723059884698
.ruff_cache/0.14.13/10325001068055382414
.ruff_cache/0.14.13/10327236765842620314
.ruff_cache/0.14.13/10328714390989268160
.ruff_cache/0.14.13/10338815562795291326
.ruff_cache/0.14.13/10339858563385931771
.ruff_cache/0.14.13/10349324940935318786
.ruff_cache/0.14.13/10356118698156626858
.ruff_cache/0.14.13/10362985209574819849
.ruff_cache/0.14.13/10372852065209199097
.ruff_cache/0.14.13/10375623478262810002
.ruff_cache/0.14.13/10380871739095260130
.ruff_cache/0.14.13/10383413308932090781
.ruff_cache/0.14.13/10392234419471507141
.ruff_cache/0.14.13/10401862133502386774
.ruff_cache/0.14.13/10414349703377698177
.ruff_cache/0.14.13/10420405244008301611
.ruff_cache/0.14.13/10437368985793867426
.ruff_cache/0.14.13/10438204245703471795
.ruff_cache/0.14.13/10442576971563078753
.ruff_cache/0.14.13/10453907251018274640
.ruff_cache/0.14.13/10471753094602263372
.ruff_cache/0.14.13/1048146036982182156
.ruff_cache/0.14.13/10485568124291911567
.ruff_cache/0.14.13/10486180457784195570
.ruff_cache/0.14.13/10489077092238616301
.ruff_cache/0.14.13/10510822874879191485
.ruff_cache/0.14.13/10517571931235731912
.ruff_cache/0.14.13/10543025046133573899
.ruff_cache/0.14.13/10543108917262476018
.ruff_cache/0.14.13/10549898595897559924
.ruff_cache/0.14.13/10563872452780859059
.ruff_cache/0.14.13/10580626756546198675
.ruff_cache/0.14.13/10605649578120846794
.ruff_cache/0.14.13/10633542491249513413
.ruff_cache/0.14.13/10641880626665339798
.ruff_cache/0.14.13/10658051364923194072
.ruff_cache/0.14.13/10676699571111903440
.ruff_cache/0.14.13/10699258730844125500
.ruff_cache/0.14.13/10701532979952851748
.ruff_cache/0.14.13/10707284717994446483
.ruff_cache/0.14.13/10729782393661477967
.ruff_cache/0.14.13/10748163030345879851
.ruff_cache/0.14.13/10759571376952287256
.ruff_cache/0.14.13/10767557034765662504
.ruff_cache/0.14.13/10769906964686157101
.ruff_cache/0.14.13/10772776190810124018
.ruff_cache/0.14.13/10793082401962887817
.ruff_cache/0.14.13/10800710528006704182
.ruff_cache/0.14.13/10813828173527630549
.ruff_cache/0.14.13/1081673694829915714
.ruff_cache/0.14.13/10842159061241377072
.ruff_cache/0.14.13/10843656062924662929
.ruff_cache/0.14.13/1087833158320053979
.ruff_cache/0.14.13/10901784989860686927
.ruff_cache/0.14.13/10911747091041025960
.ruff_cache/0.14.13/1091840460977695988
.ruff_cache/0.14.13/10930721949291399430
.ruff_cache/0.14.13/10941103060507479495
.ruff_cache/0.14.13/10951055842320742055
.ruff_cache/0.14.13/10955085905574649071
.ruff_cache/0.14.13/10959601565206805913
.ruff_cache/0.14.13/10965404382103580136
.ruff_cache/0.14.13/10974262087782136419
.ruff_cache/0.14.13/10980650376610128350
.ruff_cache/0.14.13/11005229594472725101
.ruff_cache/0.14.13/11009423072080869617
.ruff_cache/0.14.13/11041381193987214467
.ruff_cache/0.14.13/11050455439789751935
.ruff_cache/0.14.13/11064952102061685846
.ruff_cache/0.14.13/1108233318667510937
.ruff_cache/0.14.13/1108255942351757007
.ruff_cache/0.14.13/11091579114892567855
.ruff_cache/0.14.13/11121771866905417486
.ruff_cache/0.14.13/11144681078396286076
.ruff_cache/0.14.13/11166751755060828593
.ruff_cache/0.14.13/11171327411532311493
.ruff_cache/0.14.13/11185586244177328465
.ruff_cache/0.14.13/11193585643451663232
.ruff_cache/0.14.13/11224314764847377478
.ruff_cache/0.14.13/11227742598421544315
.ruff_cache/0.14.13/11229043785070267879
.ruff_cache/0.14.13/11247732812104920925
.ruff_cache/0.14.13/11251541112953730904
.ruff_cache/0.14.13/11271111616259084912
.ruff_cache/0.14.13/11277091977747410754
.ruff_cache/0.14.13/11279811357006151746
.ruff_cache/0.14.13/11309817774566519631
.ruff_cache/0.14.13/11316812800466428853
.ruff_cache/0.14.13/11320554598154983923
.ruff_cache/0.14.13/11334023956873209636
.ruff_cache/0.14.13/113517211149659154
.ruff_cache/0.14.13/11361222868178373707
.ruff_cache/0.14.13/1136990397688507723
.ruff_cache/0.14.13/11377331882455130092
.ruff_cache/0.14.13/11380001817051148143
.ruff_cache/0.14.13/1138383973536905821
.ruff_cache/0.14.13/11384455689918546136
.ruff_cache/0.14.13/11422691157484986294
.ruff_cache/0.14.13/11438840964637069243
.ruff_cache/0.14.13/11438856800920789581
.ruff_cache/0.14.13/11443675764503638644
.ruff_cache/0.14.13/11449252382409793812
.ruff_cache/0.14.13/11471945285634124503
.ruff_cache/0.14.13/11478977463589573613
.ruff_cache/0.14.13/11488719093916415691
.ruff_cache/0.14.13/11489125936348936093
.ruff_cache/0.14.13/11497824262627297059
.ruff_cache/0.14.13/11507585459021560594
.ruff_cache/0.14.13/11554761571619595015
.ruff_cache/0.14.13/11555559449330867756
.ruff_cache/0.14.13/11567943439733032136
.ruff_cache/0.14.13/11578006594876754539
.ruff_cache/0.14.13/11604881524554867786
.ruff_cache/0.14.13/11606716600805937225
.ruff_cache/0.14.13/11629568788316704153
.ruff_cache/0.14.13/11631137098850343193
.ruff_cache/0.14.13/11642931127132066062
.ruff_cache/0.14.13/11653654818984043772
.ruff_cache/0.14.13/11661258255750235685
.ruff_cache/0.14.13/11678067418433965484
.ruff_cache/0.14.13/11708582547641387328
.ruff_cache/0.14.13/11710339611432712412
.ruff_cache/0.14.13/11716721977573576504
.ruff_cache/0.14.13/11735540120845666853
.ruff_cache/0.14.13/1174396051075796477
.ruff_cache/0.14.13/11750249520943372304
.ruff_cache/0.14.13/11804094154260025766
.ruff_cache/0.14.13/11806316116598369951
.ruff_cache/0.14.13/11832145691393271847
.ruff_cache/0.14.13/11840821531467914934
.ruff_cache/0.14.13/11854834873330216152
.ruff_cache/0.14.13/11878204354808192275
.ruff_cache/0.14.13/1194553866283065176
.ruff_cache/0.14.13/119486643348517022
.ruff_cache/0.14.13/11955673129690985112
.ruff_cache/0.14.13/11963516860916528838
.ruff_cache/0.14.13/11969839953277598700
.ruff_cache/0.14.13/11971069677419559077
.ruff_cache/0.14.13/12040794311901184633
.ruff_cache/0.14.13/12055737931282127242
.ruff_cache/0.14.13/12059760573525307923
.ruff_cache/0.14.13/12090795796809204447
.ruff_cache/0.14.13/12091967600511230922
.ruff_cache/0.14.13/12094154320742695062
.ruff_cache/0.14.13/12098963309385077966
.ruff_cache/0.14.13/12102725013096271232
.ruff_cache/0.14.13/12103618546223945048
.ruff_cache/0.14.13/12109178103928906621
.ruff_cache/0.14.13/12119565041861666294
.ruff_cache/0.14.13/12126610220319419857
.ruff_cache/0.14.13/12127744460624718468
.ruff_cache/0.14.13/12153902339901077774
.ruff_cache/0.14.13/1218945181631065021
.ruff_cache/0.14.13/12200827917334414925
.ruff_cache/0.14.13/12204593842113101454
.ruff_cache/0.14.13/12212133344122895304
.ruff_cache/0.14.13/12229254324559800164
.ruff_cache/0.14.13/12262250874651581196
.ruff_cache/0.14.13/123007652230651924
.ruff_cache/0.14.13/12304534893554316571
.ruff_cache/0.14.13/12324932477950754445
.ruff_cache/0.14.13/12338486668695777189
.ruff_cache/0.14.13/12368284858130607469
.ruff_cache/0.14.13/12394607511247242651
.ruff_cache/0.14.13/12419866275337903956
.ruff_cache/0.14.13/12420133552879725013
.ruff_cache/0.14.13/12423150218394654315
.ruff_cache/0.14.13/12426418852869096517
.ruff_cache/0.14.13/12427959794502832448
.ruff_cache/0.14.13/12453832655087155126
.ruff_cache/0.14.13/12458203094399832606
.ruff_cache/0.14.13/12484210867128054936
.ruff_cache/0.14.13/12486295747426636784
.ruff_cache/0.14.13/12503093965034010021
.ruff_cache/0.14.13/12533720771983687328
.ruff_cache/0.14.13/12539037426771399550
.ruff_cache/0.14.13/12548718368045971726
.ruff_cache/0.14.13/12599824418621243907
.ruff_cache/0.14.13/12601178533820076428
.ruff_cache/0.14.13/1260400723768402052
.ruff_cache/0.14.13/12614308704801337015
.ruff_cache/0.14.13/12651049449894929209
.ruff_cache/0.14.13/12679253050845999514
.ruff_cache/0.14.13/12679277162759250061
.ruff_cache/0.14.13/12687953578093553329
.ruff_cache/0.14.13/12726467998870762926
.ruff_cache/0.14.13/12728072801065876441
.ruff_cache/0.14.13/12784595215756703946
.ruff_cache/0.14.13/12787103680001766611
.ruff_cache/0.14.13/12787149949078397796
.ruff_cache/0.14.13/12795160805377499115
.ruff_cache/0.14.13/12805206787472704272
.ruff_cache/0.14.13/12808041921309288032
.ruff_cache/0.14.13/12808671744592116537
.ruff_cache/0.14.13/12851371990123552661
.ruff_cache/0.14.13/12864875271122454566
.ruff_cache/0.14.13/12865792168975589603
.ruff_cache/0.14.13/12867540163914126251
.ruff_cache/0.14.13/12878460828275063634
.ruff_cache/0.14.13/12921391192249391332
.ruff_cache/0.14.13/12923429511143110071
.ruff_cache/0.14.13/12926615439498884272
.ruff_cache/0.14.13/12942743290937161516
.ruff_cache/0.14.13/1295089113464239067
.ruff_cache/0.14.13/12952604424594183522
.ruff_cache/0.14.13/1295536311481614862
.ruff_cache/0.14.13/1296823447479841928
.ruff_cache/0.14.13/12972506960174356764
.ruff_cache/0.14.13/12977024546629754717
.ruff_cache/0.14.13/13042200589319650670
.ruff_cache/0.14.13/13085471687481783561
.ruff_cache/0.14.13/13085981809513067872
.ruff_cache/0.14.13/13095323571949184132
.ruff_cache/0.14.13/13096118212713719284
.ruff_cache/0.14.13/13104542115270092363
.ruff_cache/0.14.13/13124137439377495584
.ruff_cache/0.14.13/13126920063473333114
.ruff_cache/0.14.13/13143313943558645213
.ruff_cache/0.14.13/13158598095161190394
.ruff_cache/0.14.13/13164095577655984109
.ruff_cache/0.14.13/13184022194710767997
.ruff_cache/0.14.13/13206572779102375119
.ruff_cache/0.14.13/13229214142811532090
.ruff_cache/0.14.13/1323022222090618963
.ruff_cache/0.14.13/1323353535570007740
.ruff_cache/0.14.13/13240598418128422930
.ruff_cache/0.14.13/1324731459344692871
.ruff_cache/0.14.13/13256513001404582296
.ruff_cache/0.14.13/13283852903268141579
.ruff_cache/0.14.13/13288426764374807438
.ruff_cache/0.14.13/13293335018006985693
.ruff_cache/0.14.13/13298730588760195257
.ruff_cache/0.14.13/13309953644077246367
.ruff_cache/0.14.13/13320965610831343738
.ruff_cache/0.14.13/13327886675250538987
.ruff_cache/0.14.13/13335276970455198093
.ruff_cache/0.14.13/13340586293297351939
.ruff_cache/0.14.13/13352899087883475887
.ruff_cache/0.14.13/13354417253000473359
.ruff_cache/0.14.13/13355776136519876613
.ruff_cache/0.14.13/1336095299258016478
.ruff_cache/0.14.13/13409814336879941110
.ruff_cache/0.14.13/13419914332930821904
.ruff_cache/0.14.13/13425448014097617706
.ruff_cache/0.14.13/13429157109599358462
.ruff_cache/0.14.13/13433024085111575756
.ruff_cache/0.14.13/13433940127284785801
.ruff_cache/0.14.13/13477533809397061696
.ruff_cache/0.14.13/13484638960870678166
.ruff_cache/0.14.13/13485569610676065505
.ruff_cache/0.14.13/13492517574285429596
.ruff_cache/0.14.13/1349992607470139956
.ruff_cache/0.14.13/13531868384775145769
.ruff_cache/0.14.13/13584883521586285637
.ruff_cache/0.14.13/13591605200240140520
.ruff_cache/0.14.13/13603790444279786845
.ruff_cache/0.14.13/13624229651482821368
.ruff_cache/0.14.13/13661586450825486145
.ruff_cache/0.14.13/13694910788277048540
.ruff_cache/0.14.13/13703594077465315906
.ruff_cache/0.14.13/13705072824730138071
.ruff_cache/0.14.13/13711875109244597524
.ruff_cache/0.14.13/13717301768282848907
.ruff_cache/0.14.13/13741147179188681766
.ruff_cache/0.14.13/13745199294060501388
.ruff_cache/0.14.13/13758676671855433846
.ruff_cache/0.14.13/13763922291121293713
.ruff_cache/0.14.13/13768303146976066181
.ruff_cache/0.14.13/13774347575517970944
.ruff_cache/0.14.13/13787392533483315349
.ruff_cache/0.14.13/13831313287568061658
.ruff_cache/0.14.13/13834600143267448869
.ruff_cache/0.14.13/13846690617926730738
.ruff_cache/0.14.13/13856969050188567227
.ruff_cache/0.14.13/13913154206681301879
.ruff_cache/0.14.13/13918591600836989938
.ruff_cache/0.14.13/1393066952981618049
.ruff_cache/0.14.13/13933143085776737792
.ruff_cache/0.14.13/13937570743327056053
.ruff_cache/0.14.13/13940386354351845619
.ruff_cache/0.14.13/13943904245355278192
.ruff_cache/0.14.13/14004073653976546768
.ruff_cache/0.14.13/14005664158642787616
.ruff_cache/0.14.13/14017116574281410695
.ruff_cache/0.14.13/14049197089134949629
.ruff_cache/0.14.13/14057671767750962771
.ruff_cache/0.14.13/14066723896086712218
.ruff_cache/0.14.13/14103196190296156038
.ruff_cache/0.14.13/14106794923779939243
.ruff_cache/0.14.13/14117962977392080041
.ruff_cache/0.14.13/1412581595356071635
.ruff_cache/0.14.13/14129833290215422799
.ruff_cache/0.14.13/1413192111687597956
.ruff_cache/0.14.13/14135644840922382442
.ruff_cache/0.14.13/14155877416691774842
.ruff_cache/0.14.13/14164216189755634862
.ruff_cache/0.14.13/1420745634364935406
.ruff_cache/0.14.13/14240633806491740037
.ruff_cache/0.14.13/14250544822308595539
.ruff_cache/0.14.13/14259072706948956420
.ruff_cache/0.14.13/14274541959778316483
.ruff_cache/0.14.13/14291705206587639904
.ruff_cache/0.14.13/14295620052470722527
.ruff_cache/0.14.13/14312270406153191288
.ruff_cache/0.14.13/14313578982721909677
.ruff_cache/0.14.13/14327473677567817300
.ruff_cache/0.14.13/14336428022197672292
.ruff_cache/0.14.13/14336731688440773110
.ruff_cache/0.14.13/14347688449711043256
.ruff_cache/0.14.13/14364904605872220391
.ruff_cache/0.14.13/14370689156191736815
.ruff_cache/0.14.13/1437432610453699626
.ruff_cache/0.14.13/14380710570682326764
.ruff_cache/0.14.13/14398062258560525931
.ruff_cache/0.14.13/14416647077222648383
.ruff_cache/0.14.13/14417046140797341355
.ruff_cache/0.14.13/14417233993310236409
.ruff_cache/0.14.13/14428833502249409465
.ruff_cache/0.14.13/14432576712704453171
.ruff_cache/0.14.13/14441620892298786075
.ruff_cache/0.14.13/1444225779232804619
.ruff_cache/0.14.13/14486806932947838346
.ruff_cache/0.14.13/14494742046306846238
.ruff_cache/0.14.13/14506800309327115337
.ruff_cache/0.14.13/1450816656380393086
.ruff_cache/0.14.13/14555461969296079077
.ruff_cache/0.14.13/14573401010075648171
.ruff_cache/0.14.13/14604264385001236342
.ruff_cache/0.14.13/14621061401213470222
.ruff_cache/0.14.13/14629476020667284014
.ruff_cache/0.14.13/14640954822595524658
.ruff_cache/0.14.13/14665126678660511915
.ruff_cache/0.14.13/14691347121470408651
.ruff_cache/0.14.13/14697410802546230503
.ruff_cache/0.14.13/14763746883479113728
.ruff_cache/0.14.13/14786089135751434936
.ruff_cache/0.14.13/14799435546045920394
.ruff_cache/0.14.13/14813137901038061918
.ruff_cache/0.14.13/14815812501281779061
.ruff_cache/0.14.13/14820882458244151519
.ruff_cache/0.14.13/14822310332859102813
.ruff_cache/0.14.13/14835775779519639860
.ruff_cache/0.14.13/14836970923519017913
.ruff_cache/0.14.13/14863471117454127788
.ruff_cache/0.14.13/148638286509048636
.ruff_cache/0.14.13/14883774257840816713
.ruff_cache/0.14.13/14892182674846574967
.ruff_cache/0.14.13/14899055976996921911
.ruff_cache/0.14.13/14950640152125073883
.ruff_cache/0.14.13/14954583319818621074
.ruff_cache/0.14.13/14955465937010299125
.ruff_cache/0.14.13/14958751801986896907
.ruff_cache/0.14.13/14965397066392158665
.ruff_cache/0.14.13/14965837855355710971
.ruff_cache/0.14.13/14972037798290224906
... (12997 more files)

## Key Configuration Files
File: .github/workflows/ci-complete.yml
```
name: 🚀 Complete CI Pipeline (ADHD-Optimized)

on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true  # ADHD-friendly: cancel outdated runs

jobs:
  # ADHD chunk #1: Code quality (fast feedback)
  code-quality:
    name: "💅 Code Quality & Linting"
    runs-on: ubuntu-latest
    timeout-minutes: 10  # Quick feedback loop

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 📦 Install pre-commit & deps
        run: |
          pip install pre-commit
          pre-commit install --install-hooks

      - name: 🧹 Enforce repo root hygiene
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin "${{ github.base_ref }}" --depth=1
            CHANGED_FILES="$(git diff --name-only "origin/${{ github.base_ref }}"...HEAD)"
          else
            BEFORE="${{ github.event.before }}"
            if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
              CHANGED_FILES="$(git ls-files)"
            else
              CHANGED_FILES="$(git diff --name-only "$BEFORE" "${{ github.sha }}")"
            fi
          fi

          if [ -z "$CHANGED_FILES" ]; then
            echo "No changed files to validate for root hygiene."
            exit 0
          fi

          echo "$CHANGED_FILES" | xargs -r python scripts/check_root_hygiene.py --quiet

      - name: 🔍 Run pre-commit (code quality)
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin "${{ github.base_ref }}" --depth=1
            pre-commit run --from-ref "origin/${{ github.base_ref }}" --to-ref HEAD
          else
            BEFORE="${{ github.event.before }}"
            if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
              pre-commit run --all-files
            else
              pre-commit run --from-ref "$BEFORE" --to-ref "${{ github.sha }}"
            fi
          fi
        env:
          SKIP: docs-graph-validator  # Temporarily skip graph validator (pre-existing validation issues)

      - name: 🎯 ADHD-Friendly Summary
        if: always()
        run: |
          echo "## 💅 Code Quality Check" >> $GITHUB_STEP_SUMMARY
          if [ $? -eq 0 ]; then
            echo "✅ **Code looks great!** Ready for the next step." >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ **Code quality items found** - Check the details above." >> $GITHUB_STEP_SUMMARY
            echo "_Focus on the most important fixes first._" >> $GITHUB_STEP_SUMMARY
          fi

  # ADHD chunk #2: Security (takes longer, separate job)
  security:
    name: "🔒 Security Review"
    runs-on: ubuntu-latest
    timeout-minutes: 25  # 25-minute focus session

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 2

      - name: 🛡️ AI-Powered Security Analysis
        uses: anthropics/claude-code-security-review@main
        with:
          comment-pr: true
          claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
          custom-security-scan-instructions: .github/security-scan-instructions.txt
          false-positive-filtering-instructions: .github/security-filtering-instructions.txt
          claudecode-timeout: "20"

      - name: 🎯 Gentle Security Summary
        if: always() && github.event_name == 'pull_request'
        run: |
          echo "## 🔒 Security Check Complete" >> $GITHUB_STEP_SUMMARY
          echo "AI-powered analysis finished! Check PR comments for details." >> $GITHUB_STEP_SUMMARY
          echo "_Remember: Security is about progress, not perfection._" >> $GITHUB_STEP_SUMMARY

  # ADHD chunk #3: Documentation (link checking)
  docs:
    name: "📚 Documentation Check"
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5

      - name: 🔗 Check links (lychee)
        uses: lycheeverse/lychee-action@v2  # Security: Fixed code injection vulnerability in v1
        with:
          args: --config .lychee.toml docs/**/*.md README.md
          fail: false

      - name: 📖 Documentation Summary
        if: always()
        run: |
          echo "## 📚 Documentation Check" >> $GITHUB_STEP_SUMMARY
          echo "Link checking completed! Your docs are being kept current." >> $GITHUB_STEP_SUMMARY

  tests:
    name: "🧪 Unit Tests"
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5

      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: 📦 Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .[dev]

      - name: ✅ Verify TaskX wiring
        run: |
          test -f .taskx-pin
          grep -q '^commit=' .taskx-pin
          test -f .taskxroot
          test -d .taskx_venv
          test -x .taskx_venv/bin/taskx

      - name: 🧠 TaskX doctor
        run: |
          scripts/taskx doctor --timestamp-mode deterministic

      - name: ▶️ Run Pytest (unit suite)
        run: |
          pytest tests/unit --maxfail=1 --disable-warnings --no-cov

      - name: 🧪 Installer Smoke Tests (core + full stacks)
        run: |
          cd /home/runner/work/${{ github.event.repository.name }}/${{ github.event.repository.name }}
          ./test_installer_basic.sh

      - name: 📈 Upload coverage artifact
        if: success()
        uses: actions/upload-artifact@v5
        with:
          name: unit-test-coverage
          path: |
            coverage.xml
            htmlcov

  # Final summary for ADHD-friendly overview
  ci-summary:
    name: "📊 CI Pipeline Summary"
    runs-on: ubuntu-latest
    needs: [code-quality, security, docs, tests]
    if: always()

    steps:
      - name: 🎉 ADHD-Optimized Results Summary
        run: |
          echo "## 🚀 Dopemux CI Pipeline Complete" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          # Code Quality Status
          if [ "${{ needs.code-quality.result }}" == "success" ]; then
            echo "✅ **Code Quality:** Passing - Code is clean and consistent!" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ **Code Quality:** Needs attention - Small fixes needed" >> $GITHUB_STEP_SUMMARY
          fi

          # Security Status
          if [ "${{ needs.security.result }}" == "success" ]; then
            echo "✅ **Security:** Clear - Memory systems are secure!" >> $GITHUB_STEP_SUMMARY
          else
            echo "🔒 **Security:** Review needed - Check findings above" >> $GITHUB_STEP_SUMMARY
          fi

          # Documentation Status
          if [ "${{ needs.docs.result }}" == "success" ]; then
            echo "✅ **Documentation:** Links working - Docs are current!" >> $GITHUB_STEP_SUMMARY
          else
            echo "📝 **Documentation:** Links need fixing - Minor updates needed" >> $GITHUB_STEP_SUMMARY
          fi

          # Tests Status
          if [ "${{ needs.tests.result }}" == "success" ]; then
            echo "✅ **Unit Tests:** Passing - Core workflow stable!" >> $GITHUB_STEP_SUMMARY
          else
            echo "🧪 **Unit Tests:** Failing - Fix regressions before merge" >> $GITHUB_STEP_SUMMARY
          fi

          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### 💡 ADHD-Friendly Next Steps" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          if [ "${{ needs.code-quality.result }}" == "success" ] && [ "${{ needs.security.result }}" == "success" ] && [ "${{ needs.docs.result }}" == "success" ] && [ "${{ needs.tests.result }}" == "success" ]; then
            echo "**🎉 Excellent work!** All checks passed. Ready to merge when you are!" >> $GITHUB_STEP_SUMMARY
            echo "_Take a well-deserved break - you've earned it._" >> $GITHUB_STEP_SUMMARY
          else
            echo "**📋 Focus areas:** Address the items above one at a time." >> $GITHUB_STEP_SUMMARY
            echo "**⏰ Tip:** Use 25-minute Pomodoro sessions for fixes." >> $GITHUB_STEP_SUMMARY
            echo "**🤝 Need help?** Ask in the PR discussion!" >> $GITHUB_STEP_SUMMARY
          fi

          echo "" >> $GITHUB_STEP_SUMMARY
          echo "---" >> $GITHUB_STEP_SUMMARY
          echo "*Powered by Dopemux ADHD-optimized CI/CD*" >> $GITHUB_STEP_SUMMARY

```

File: .github/workflows/docs.yml
```
name: docs
on: [push, pull_request]
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install pre-commit
      - run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            git fetch origin "${{ github.base_ref }}" --depth=1
            pre-commit run --from-ref "origin/${{ github.base_ref }}" --to-ref HEAD
          else
            BEFORE="${{ github.event.before }}"
            if [ -z "$BEFORE" ] || [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
              pre-commit run --all-files
            else
              pre-commit run --from-ref "$BEFORE" --to-ref "${{ github.sha }}"
            fi
          fi
        env:
          SKIP: docs-graph-validator  # Temporarily skip graph validator (pre-existing validation issues)
      - name: Broken-link check (lychee)
        uses: lycheeverse/lychee-action@v2  # Security: Fixed code injection vulnerability in v1
        with:
          args: --config .lychee.toml docs/**/*.md
          fail: false

```

File: .github/workflows/repo-identity.yml
```
name: Repo Identity Check

on: [push, pull_request]

jobs:
  identity-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify Repo Identity
        run: |
          test -f .repo_id
          grep "^project=dopemux-mvp$" .repo_id

```

File: .github/workflows/security-review.yml
```
name: 🔒 Security Review with Claude Code

permissions:
  pull-requests: write  # Needed for PR comments
  contents: read
  issues: write         # For issue tracking

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]

jobs:
  security-review:
    name: "🤖 Claude Code Security Analysis"
    runs-on: ubuntu-latest
    timeout-minutes: 25  # ADHD-optimized: 25-minute chunks

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v5
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
          fetch-depth: 2  # Get enough history for diff analysis

      - name: 🔐 ADHD-Optimized Security Review
        uses: anthropics/claude-code-security-review@main
        with:
          comment-pr: true
          claude-api-key: ${{ secrets.CLAUDE_API_KEY }}
          upload-results: true

          # ADHD-optimized timeout (25-minute focus sessions)
          claudecode-timeout: "20"

          # Use latest Claude model for best analysis
          claude-model: "claude-opus-4-1-20250805"

          # Custom instructions for memory/intelligence systems
          custom-security-scan-instructions: .github/security-scan-instructions.txt
          false-positive-filtering-instructions: .github/security-filtering-instructions.txt

          # Exclude test directories and generated files to reduce noise
          exclude-directories: "tests,__pycache__,node_modules,.git,docker/leantime/data"

          # Run on every commit for comprehensive coverage
          run-every-commit: false

  # ADHD-friendly summary for non-technical stakeholders
  security-summary:
    name: "📊 ADHD-Friendly Security Summary"
    runs-on: ubuntu-latest
    needs: security-review
    if: always() && github.event_name == 'pull_request'

    steps:
      - name: 🎯 Generate gentle security report
        run: |
          echo "🧠 **ADHD-Friendly Security Check Complete**" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          if [ "${{ needs.security-review.result }}" == "success" ]; then
            echo "✅ **Great news!** Your code changes look secure." >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "**What this means:**" >> $GITHUB_STEP_SUMMARY
            echo "- No high-severity security issues detected" >> $GITHUB_STEP_SUMMARY
            echo "- Memory system components are safe" >> $GITHUB_STEP_SUMMARY
            echo "- Ready for merge when tests pass!" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ **Security items need attention**" >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
            echo "**Next steps:**" >> $GITHUB_STEP_SUMMARY
            echo "1. Check the detailed findings in the PR comments above" >> $GITHUB_STEP_SUMMARY
            echo "2. Address high-priority items first (marked 🔴)" >> $GITHUB_STEP_SUMMARY
            echo "3. Ask for help if anything is unclear" >> $GITHUB_STEP_SUMMARY
          fi

          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**💡 Remember:** Small, focused security fixes work best!" >> $GITHUB_STEP_SUMMARY
          echo "_Take breaks and tackle one issue at a time._" >> $GITHUB_STEP_SUMMARY
```

File: .pre-commit-config.yaml
```
repos:
  # Knowledge Graph Documentation Enforcement
  - repo: local
    hooks:
      # Frontmatter validation (enable existing)
      - id: docs-frontmatter-guard
        name: Validate YAML frontmatter in docs
        entry: python scripts/docs_frontmatter_guard.py --fix
        language: system
        files: ^docs/.*\.md$

      # Graph schema validation
      - id: docs-graph-validator
        name: Validate documentation against knowledge graph schema
        entry: python scripts/docs_validator.py
        language: system
        files: ^docs/.*\.md$
        exclude: ^docs/archive/
        pass_filenames: true

      # Prohibited file pattern check
      - id: docs-prohibited-patterns
        name: Block prohibited documentation patterns (NOTES, TODO, TEMP, etc.)
        entry: bash -c
        args:
          - |
            set -e
            prohibited_found=false
            # Evaluate only the changed docs files passed by pre-commit.
            for file in "$@"; do
              case "$file" in
                docs/*)
                  base="$(basename "$file")"
                  case "$base" in
                    TEMPLATE_*.md)
                      continue
                      ;;
                    NOTES*.md|TODO*.md|TEMP*.md|*temp*.md|*scratch*.md)
                      echo "❌ Found prohibited file pattern in changed file:"
                      echo "  $file"
                      prohibited_found=true
                      ;;
                  esac
                  ;;
              esac
            done
            if [ "$prohibited_found" = true ]; then
              echo "Use structured workflow: RFC->ADR->arc42 for documentation"
              exit 1
            fi
            echo "✅ No prohibited patterns found in changed docs"
          - --
        language: system
        files: ^docs/.*\.md$
        pass_filenames: true

      # Prelude token count validation for embeddings
      - id: docs-prelude-tokens
        name: Validate prelude ≤100 tokens for efficient embeddings
        entry: python -c
        args:
          - |
            import sys, yaml, os
            errors = []
            for file in sys.argv[1:]:
                if not file.endswith('.md'): continue
                try:
                    with open(file, 'r') as f: content = f.read()
                    if not content.startswith('---'): continue
                    end = content.find('\n---\n', 4)
                    if end == -1: continue
                    fm = yaml.safe_load(content[4:end])
                    prelude = fm.get('prelude', '')
                    if prelude:
                        tokens = int(len(prelude.split()) * 1.3)
                        if tokens > 100:
                            errors.append(f'{file}: prelude ~{tokens} tokens (max 100)')
                except Exception as e:
                    errors.append(f'{file}: error - {e}')
            if errors:
                print('❌ Prelude token errors:')
                for error in errors: print(f'  {error}')
                sys.exit(1)
            print('✅ All preludes within token limit')
        language: system
        files: ^docs/.*\.md$
        pass_filenames: true

      # Markdown file location enforcement
      - id: markdown-location-guard
        name: Enforce markdown file locations for changed files
        entry: bash -c
        args:
          - |
            set -e
            violations_found=false

            for file in "$@"; do
              if [[ "$file" != *.md ]]; then continue; fi

              normalized="./${file#./}"

              # Canonical docs locations
              if [[ "$normalized" =~ ^\./(docs/) ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(reports/|quarantine/) ]]; then continue; fi
              if [[ "$normalized" =~ /(SYSTEM_ARCHIVE|archive|ARCHIVE)/ ]]; then continue; fi

              # Config/state and tooling docs
              if [[ "$normalized" =~ /\.claude/ ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(\.conport/|conport_export/) ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(\.github/) ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(examples/) ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(tests/resources/) ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(src/dopemux/templates/) ]]; then continue; fi
              if [[ "$normalized" =~ /\.pytest_cache/ ]]; then continue; fi


              # Root project docs and common standards docs anywhere
              if [[ "$normalized" =~ ^\./[A-Z][A-Z_0-9-]*\.md$ ]]; then continue; fi
              if [[ "$normalized" =~ /(README|CHANGELOG|CONTRIBUTING|LICENSE|CODE_OF_CONDUCT|SECURITY)\.md$ ]]; then continue; fi

              # Service/container docs and research
              if [[ "$normalized" =~ ^\./(services|docker)/[^/]+/(docs|research|intelligence|archive|migrations)/ ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(services|docker)/[^/]+/[A-Z_0-9-]+\.md$ ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(docker/mcp-servers/pal/) ]]; then continue; fi
              if [[ "$normalized" =~ ^\./(docker/mcp-servers/)[A-Z_0-9-]+\.md$ ]]; then continue; fi

              # Scripts documentation
              if [[ "$normalized" =~ ^\./(scripts/)[A-Z_0-9-]+\.md$ ]]; then continue; fi

              echo "❌ $file"
              violations_found=true
            done

            if [ "$violations_found" = true ]; then
              echo ""
              echo "Move misplaced .md files to docs/ or see plan.md for cleanup strategy"
              exit 1
            fi
            echo "✅ All markdown files in approved locations"
          - --
        language: system
        files: \.md$
        pass_filenames: true

      # Repo root hygiene enforcement
      - id: root-hygiene
        name: Enforce repository root hygiene (no random root files)
        entry: python scripts/check_root_hygiene.py
        language: system
        files: .*
        pass_filenames: true
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.41.0
    hooks:
      - id: markdownlint
        args: ["--config", ".markdownlint.jsonc"]
        files: ^docs/.*\.md$
        exclude: node_modules/

  # Lychee link checking handled by separate GitHub Action (docs job)
  # - repo: https://github.com/lycheeverse/lychee
  #   rev: v0.15.1
  #   hooks:
  #     - id: lychee
  #       args: ["--config", ".lychee.toml", "--no-progress", "docs/**/*.md"]

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
        files: ^docs/.*\.md$
      - id: end-of-file-fixer
        files: ^docs/.*\.md$
      - id: check-yaml
        files: ^config/.*\.ya?ml$

```

File: docker-compose.dev.yml
```
version: '3.9'

name: dopemux-dev

networks:
  dopemux-network:
    driver: bridge

volumes:
  pg_age_data:
  redis_data:
  qdrant_data:

services:
  # ========================================
  # INFRASTRUCTURE
  # ========================================

  # PostgreSQL with AGE extension
  postgres:
    image: apache/age:release_PG16_1.6.0
    container_name: dopemux-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: dopemux_age
      POSTGRES_PASSWORD: dopemux_age_dev_password
      POSTGRES_DB: dopemux_knowledge_graph
    volumes:
      - pg_age_data:/var/lib/postgresql/data
      - ./docker/postgres/01-init-age.sql:/docker-entrypoint-initdb.d/01-init-age.sql
    ports:
      - "5432:5432"
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dopemux_age -d dopemux_knowledge_graph || exit 1"]
      timeout: 5s
      retries: 10
      interval: 10s
      start_period: 20s

  # Redis - Events and caching
  redis:
    image: redis:7-alpine
    container_name: dopemux-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - dopemux-network
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Qdrant - Vector database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: dopemux-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - dopemux-network
    environment:
      QDRANT_API_KEY: ${QDRANT_API_KEY:-dev-key}

  # ========================================
  # BACKEND SERVICES
  # ========================================

  # Backend API (Python)
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dopemux-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://dopemux_age:dopemux_age_dev_password@postgres:5432/dopemux_knowledge_graph
      REDIS_URL: redis://redis:6379
      QDRANT_URL: http://qdrant:6333
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    volumes:
      # Hot reload for development
      - ./src:/app/src
      - ./config:/app/config
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ========================================
  # FRONTEND
  # ========================================

  # Frontend (Next.js)
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: dopemux-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NODE_ENV: development
    volumes:
      # Hot reload for Next.js development
      - ./pages:/app/pages
      - ./components:/app/components
      - ./src:/app/src
      - ./public:/app/public
      - ./styles:/app/styles
    depends_on:
      - backend
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

  # ========================================
  # OPTIONAL: Development Tools
  # ========================================

  # Redis UI (optional)
  redis-ui:
    image: redislabs/redisinsight:latest
    container_name: dopemux-redis-ui
    restart: unless-stopped
    ports:
      - "8001:5540"
    depends_on:
      - redis
    networks:
      - dopemux-network

```

File: docker-compose.mcp-test.yml
```
# Minimal MCP Stack for Testing
version: '3.8'

networks:
  mcp-test-network:
    driver: bridge

services:
  # Infrastructure
  postgres:
    image: postgres:16-alpine
    container_name: test-postgres
    environment:
      - POSTGRES_USER=dopemux_age
      - POSTGRES_PASSWORD=dopemux_age_dev_password
      - POSTGRES_DB=dopemux_knowledge_graph
    ports:
      - "5433:5432"
    networks:
      - mcp-test-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dopemux_age"]
      interval: 10s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: test-redis
    ports:
      - "6380:6379"
    networks:
      - mcp-test-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  qdrant:
    image: qdrant/qdrant:latest
    container_name: test-qdrant
    ports:
      - "6335:6333"
    networks:
      - mcp-test-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:6333 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Conport MCP Server
  conport:
    build:
      context: ./docker/mcp-servers/conport
      dockerfile: Dockerfile
    container_name: test-mcp-conport
    environment:
      - MCP_SERVER_PORT=3004
      - AGE_HOST=postgres
      - AGE_PORT=5432
      - AGE_PASSWORD=dopemux_age_dev_password
    ports:
      - "3004:3004"
    networks:
      - mcp-test-network
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3004/health || exit 0"]
      interval: 30s
      timeout: 10s
      retries: 3

```

File: docker-compose.monitoring.yml
```
# ⚠️ DEPRECATED - Use compose.yml instead
# This file is kept for reference only. The canonical compose file is now compose.yml at repo root.
# Monitoring services can be added to compose.yml if needed.
# See: compose.yml

version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: dopemux-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./services/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./services/monitoring/alerting_rules.yml:/etc/prometheus/alerting_rules.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    networks:
      - dopemux-monitoring

  grafana:
    image: grafana/grafana:10.1.0
    container_name: dopemux-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=dopemux_admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3000
      - GF_INSTALL_PLUGINS=
    volumes:
      - grafana-data:/var/lib/grafana
      - ./services/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./services/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    networks:
      - dopemux-monitoring
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: dopemux-alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./services/monitoring/alertmanager.yml:/etc/alertmanager/config.yml:ro
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    networks:
      - dopemux-monitoring

volumes:
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
  alertmanager-data:
    driver: local

networks:
  dopemux-monitoring:
    driver: bridge

```

File: docker-compose.prod.yml
```
version: '3.9'

name: dopemux-prod

networks:
  dopemux-network:
    driver: bridge

volumes:
  pg_age_data:
  redis_data:
  qdrant_data:

services:
  # ========================================
  # INFRASTRUCTURE
  # ========================================

  postgres:
    image: apache/age:release_PG16_1.6.0
    restart: always
    environment:
      POSTGRES_USER: dopemux_age
      POSTGRES_PASSWORD: ${AGE_PASSWORD}
      POSTGRES_DB: dopemux_knowledge_graph
    volumes:
      - pg_age_data:/var/lib/postgresql/data
      - ./docker/postgres/01-init-age.sql:/docker-entrypoint-initdb.d/01-init-age.sql
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dopemux_age -d dopemux_knowledge_graph || exit 1"]
      timeout: 5s
      retries: 10
      interval: 10s
      start_period: 20s
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /run
      - /tmp

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    networks:
      - dopemux-network
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    security_opt:
      - no-new-privileges:true

  qdrant:
    image: qdrant/qdrant:latest
    restart: always
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - dopemux-network
    environment:
      QDRANT_API_KEY: ${QDRANT_API_KEY}
    security_opt:
      - no-new-privileges:true

  # ========================================
  # APPLICATION SERVICES
  # ========================================

  backend:
    image: dopemux-backend:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://dopemux_age:${AGE_PASSWORD}@postgres:5432/dopemux_knowledge_graph
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      QDRANT_URL: http://qdrant:6333
      QDRANT_API_KEY: ${QDRANT_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      ENVIRONMENT: production
      LOG_LEVEL: info
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    image: dopemux-frontend:latest
    restart: always
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: ${FRONTEND_API_URL:-http://localhost:8000}
      NODE_ENV: production
    depends_on:
      - backend
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

```

File: docker-compose.smoke.yml
```
# Dopemux Smoke Stack - Minimal test environment
# Ports and configuration driven by .env.smoke (generated from services/registry.yaml)
#
# Usage:
#   1. Generate .env.smoke: python tools/generate_smoke_env.py
#   2. Build and start: docker compose -f docker-compose.smoke.yml up -d --build
#   3. Validate: python tools/ports_health_audit.py --mode runtime --services conport,dopecon-bridge,task-orchestrator
#   4. Stop: docker compose -f docker-compose.smoke.yml down

version: '3.8'

networks:
  dopemux-smoke-network:
    driver: bridge

volumes:
  smoke_pg_data:
  smoke_redis_data:
  smoke_qdrant_data:
  dope_memory_data:




services:
  # Infrastructure: PostgreSQL with AGE extension
  postgres:
    image: apache/age:release_PG16_1.6.0
    container_name: smoke-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=dopemux_age
      - POSTGRES_PASSWORD=dopemux_age_dev_password
      - POSTGRES_DB=dopemux_knowledge_graph
    volumes:
      - smoke_pg_data:/var/lib/postgresql/data
      - ./docker/postgres/01-init-age.sql:/docker-entrypoint-initdb.d/01-init-age.sql
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    networks:
      - dopemux-smoke-network
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U dopemux_age -d dopemux_knowledge_graph" ]
      timeout: 5s
      retries: 10
      interval: 10s

  # Infrastructure: Redis
  redis:
    image: redis:7-alpine
    container_name: smoke-redis
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    networks:
      dopemux-smoke-network:
        aliases:
          - redis
          - smoke-redis
    healthcheck:
      test: [ "CMD", "redis-cli", "ping" ]
      interval: 10s
      timeout: 3s
      retries: 3

  # Infrastructure: Qdrant vector database
  qdrant:
    image: qdrant/qdrant:latest
    container_name: smoke-qdrant
    restart: unless-stopped
    ports:
      - "${QDRANT_PORT:-6333}:6333"
      - "${QDRANT_GRPC_PORT:-6341}:6334"
    volumes:
      - smoke_qdrant_data:/qdrant/storage
    networks:
      - dopemux-smoke-network

  # MCP: ConPort knowledge graph server
  conport:
    build:
      context: .
      dockerfile: services/conport/Dockerfile
    container_name: smoke-conport
    restart: unless-stopped
    environment:
      - PORT=${CONPORT_CONTAINER_PORT:-3004}
      - DATABASE_URL=postgresql://dopemux_age:dopemux_age_dev_password@postgres:5432/dopemux_knowledge_graph
      - POSTGRES_USER=dopemux_age
      - POSTGRES_PASSWORD=dopemux_age_dev_password
      - POSTGRES_DB=dopemux_knowledge_graph
      - REDIS_URL=redis://redis:6379
    ports:
      - "${CONPORT_PORT:-3004}:${CONPORT_CONTAINER_PORT:-3004}"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - dopemux-smoke-network
    healthcheck:
      test: [ "CMD-SHELL", "curl -f http://localhost:${CONPORT_CONTAINER_PORT:-3004}/health || exit 1" ]
      timeout: 10s
      retries: 3
      interval: 30s

  # Coordination: DopeconBridge event routing
  dopecon-bridge:
    build:
      context: services/dopecon-bridge
      dockerfile: Dockerfile
    container_name: smoke-dopecon-bridge
    restart: unless-stopped
    environment:
      - DOPECON_BRIDGE_PORT=${DOPECON_BRIDGE_CONTAINER_PORT:-3016}
      - CONPORT_URL=http://conport:${CONPORT_CONTAINER_PORT:-3004}
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql+asyncpg://dopemux_age:dopemux_age_dev_password@postgres:5432/dopemux_knowledge_graph
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    ports:
      - "${DOPECON_BRIDGE_PORT:-3016}:${DOPECON_BRIDGE_CONTAINER_PORT:-3016}"
    depends_on:
      - conport
      - redis
      - postgres
    networks:
      - dopemux-smoke-network
    volumes:
      - ./services/dopecon-bridge:/app
    healthcheck:
      test: [ "CMD-SHELL", "curl -f http://localhost:${DOPECON_BRIDGE_CONTAINER_PORT:-3016}/health || exit 1" ]
      timeout: 5s
      retries: 3
      interval: 30s

  # Cognitive: Task Orchestrator
  task-orchestrator:
    build:
      context: services/task-orchestrator
      dockerfile: Dockerfile
    container_name: smoke-task-orchestrator
    command: uvicorn app.main:app --host 0.0.0.0 --port 3014
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKSPACE_ID=/workspace
      - CONPORT_URL=http://conport:${CONPORT_CONTAINER_PORT:-3004}
      - DOPECON_BRIDGE_URL=http://dopecon-bridge:${DOPECON_BRIDGE_CONTAINER_PORT:-3016}
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - TASK_ORCHESTRATOR_API_KEY=dev-smoke-test-key
      - PORT=${TASK_ORCHESTRATOR_CONTAINER_PORT:-8000}
    ports:
      - "${TASK_ORCHESTRATOR_PORT:-8000}:${TASK_ORCHESTRATOR_CONTAINER_PORT:-8000}"
    depends_on:
      - redis
      - conport
      - dopecon-bridge
    networks:
      - dopemux-smoke-network
    volumes:
      - ./services/task-orchestrator:/app
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:${TASK_ORCHESTRATOR_CONTAINER_PORT:-8000}/health" ]
      timeout: 10s
      retries: 3
      interval: 30s

  # MCP: Dope-Memory temporal chronicle service
  dope-memory:
    build:
      context: services/working-memory-assistant
      dockerfile: Dockerfile.dope-memory
    container_name: smoke-dope-memory
    restart: unless-stopped
    environment:
      - PORT=${DOPE_MEMORY_CONTAINER_PORT:-3020}
      - DOPE_MEMORY_PORT=${DOPE_MEMORY_CONTAINER_PORT:-3020}
      - DOPE_MEMORY_WORKSPACE_ID=dopemux
      - DOPE_MEMORY_INSTANCE_ID=smoke
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - ENVIRONMENT=smoke
      - ENABLE_EVENTBUS=true
      - REDIS_URL=redis://redis:6379
    ports:
      - "${DOPE_MEMORY_PORT:-3020}:${DOPE_MEMORY_CONTAINER_PORT:-3020}"
    depends_on:
      - redis
    networks:
      - dopemux-smoke-network
    volumes:
      - dope_memory_data:/home/dopememory/.dope-memory
    healthcheck:
      test: [ "CMD-SHELL", "curl -f http://localhost:${DOPE_MEMORY_CONTAINER_PORT:-3020}/health || exit 1" ]
      timeout: 5s
      retries: 3
      interval: 30s

```

File: docker-compose.unified.yml
```
# ⚠️ DEPRECATED - Use compose.yml instead
# This file is kept for reference only. The canonical compose file is now compose.yml at repo root.
# See: compose.yml
#
# Dopemux Unified Docker Compose
# Simplified version for quick setup - includes core services only

version: '3.8'

networks:
  dopemux-network:
    driver: bridge

volumes:
  pg_age_data:
  redis_data:
  qdrant_data:

services:
  # PostgreSQL with AGE extension for graph database
  postgres:
    image: postgres:16-alpine
    container_name: dopemux-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=dopemux_age
      - POSTGRES_PASSWORD=dopemux_age_dev_password
      - POSTGRES_DB=dopemux_knowledge_graph
    volumes:
      - pg_age_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dopemux_age -d dopemux_knowledge_graph"]
      timeout: 5s
      retries: 10
      interval: 10s

  # Redis for caching and events
  redis:
    image: redis:7-alpine
    container_name: dopemux-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Qdrant vector database for semantic search
  qdrant:
    image: qdrant/qdrant:latest
    container_name: dopemux-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - dopemux-network

  # DopeconBridge - Central coordination layer (formerly Integration Bridge)
  dopecon-bridge:
    image: dopemux/dopecon-bridge:latest
    container_name: dopecon-bridge-unified
    ports:
      - "3016:3016"
    environment:
      - DOPECON_BRIDGE_PORT=3016
      - CONPORT_URL=http://conport:3004
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - dopemux-unified-network
    depends_on:
      - conport
      - redis
    restart: unless-stopped

  # ConPort - Knowledge Graph & Context Management
  conport:
    build:
      context: ./docker/mcp-servers/conport
      dockerfile: Dockerfile
    container_name: mcp-conport
    restart: unless-stopped
    environment:
      - MCP_SERVER_PORT=3004
      - DATABASE_URL=postgresql://dopemux_age:dopemux_age_dev_password@postgres:5432/dopemux_knowledge_graph
      - REDIS_URL=redis://redis:6379
    ports:
      - "3004:3004"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3004/health || exit 0"]
      timeout: 10s
      retries: 3
      interval: 30s

  # ADHD Engine - Real-time ADHD Accommodation Service
  adhd-engine:
    build:
      context: ./services/adhd_engine/services/adhd_engine
      dockerfile: Dockerfile
    container_name: dopemux-adhd-engine
    restart: unless-stopped
    ports:
      - "8095:8095"
    environment:
      - API_PORT=8095
      - HOST=0.0.0.0
      - ADHD_ENGINE_API_KEY=dev-key-123
      - REDIS_URL=redis://redis:6379
      - CONPORT_URL=http://conport:3004
      - DOPECON_BRIDGE_URL=http://dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097
    depends_on:
      redis:
        condition: service_healthy
      conport:
        condition: service_healthy
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8095/health || exit 1"]
      timeout: 10s
      retries: 3
      interval: 30s

  # Task Orchestrator - ADHD Task Coordination
  task-orchestrator:
    build:
      context: ./services/task-orchestrator
      dockerfile: Dockerfile
    container_name: dopemux-task-orchestrator
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKSPACE_ID=/Users/hue/code/dopemux-mvp
      - CONPORT_URL=http://conport:3004
      - DOPECON_BRIDGE_URL=http://dopecon-bridge:3016
      - DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane
      - TASK_ORCHESTRATOR_API_KEY=dev-key-456
    ports:
      - "8000:8000"
    depends_on:
      redis:
        condition: service_healthy
      conport:
        condition: service_healthy
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      timeout: 10s
      retries: 3
      interval: 30s

```

File: litellm.config.yaml
```
# Placeholder - LiteLLM will use database configuration
model_list: []

```

File: mcp-proxy-config.yaml
```
# MCP Proxy Configuration
# Multi-workspace support: Services can accept workspace_path parameter

mcp_servers:
  mas-sequential-thinking:
    command: ["docker", "exec", "-i", "mcp-mas-sequential-thinking", "mcp-server-mas-sequential-thinking"]
    port: 8001
    supports_workspace: false  # Legacy service

  exa:
    command: ["docker", "exec", "-i", "mcp-exa", "python", "server.py"]
    port: 8003
    supports_workspace: false  # Search service (global)

  pal:
    command: ["docker", "exec", "-i", "mcp-pal", "python", "-m", "pal_mcp_server"]
    port: 8004
    supports_workspace: true   # Multi-workspace aware
    workspace_param: "workspace_path"  # Parameter name for workspace

  serena:
    command: ["docker", "exec", "-i", "mcp-serena", "python", "server.py"]
    port: 8005
    supports_workspace: true   # Multi-workspace aware
    workspace_param: "workspace_path"  # Parameter name for workspace

  leantime-bridge:
    command: ["docker", "exec", "-i", "mcp-leantime-bridge", "python", "-m", "leantime_bridge.http_server"]
    port: 3015
    supports_workspace: true   # Multi-workspace aware
    workspace_param: "workspace_id"  # Parameter name for workspace

# Workspace routing configuration
workspace:
  # Auto-detect workspace from environment
  auto_detect: true
  
  # Environment variables to check (in order)
  env_vars:
    - DOPEMUX_WORKSPACE_ID
    - DEFAULT_WORKSPACE_PATH
    - PWD
  
  # Pass workspace to all compatible services
  pass_to_services: true
  
  # Workspace parameter name (default)
  default_param_name: "workspace_path"

```

File: package.json
```
{
  "name": "dopemux-ui",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "@radix-ui/react-accordion": "^1.2.0",
    "@radix-ui/react-progress": "^1.1.0",
    "@radix-ui/react-radio-group": "^1.2.0",
    "@radix-ui/react-slot": "^1.1.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.451.0",
    "next": "14.2.5",
    "next-themes": "^0.3.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "sonner": "^1.5.0",
    "swr": "^2.2.5",
    "tailwind-merge": "^2.5.4",
    "tailwindcss-animate": "^1.0.7",
    "typescript": "^5.6.2"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.4.20",
    "eslint": "^8",
    "eslint-config-next": "14.2.5",
    "postcss": "^8",
    "tailwindcss": "^3.4.10"
  }
}
```

File: pyproject.toml
```
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dopemux"
version = "0.1.0"
description = "ADHD-optimized development platform that wraps Claude Code with custom configurations"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Dopemux Team", email = "team@dopemux.dev"},
]
keywords = ["adhd", "development", "ai", "claude", "productivity"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Tools",
    "Topic :: Scientific/Engineering :: Human Machine Interfaces",
]

dependencies = [
    "click>=8.0.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",
    "textual>=0.54.0",
    "requests>=2.28.0",
    "aiohttp>=3.12.0",
    "watchdog>=3.0.0",
    "python-dateutil>=2.8.0",
    "python-dotenv>=1.0.0",
    "sqlite-utils>=3.30.0",
    "psutil>=5.9.0",
    "pydantic>=2.0.0",
    "toml>=0.10.0",
    "docker>=7.0.0",
    "litellm>=1.0.0",
    # Document processing dependencies
    "chardet>=5.0.0",
    "pymilvus>=2.3.0",
    "voyageai>=0.2.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "scikit-learn>=1.3.0",
    "pandas>=2.0.0",
    "markdown>=3.4.0",
    "python-docx>=0.8.11",
    "pdfplumber>=0.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[project.urls]
Homepage = "https://github.com/dopemux/dopemux-mvp"
Repository = "https://github.com/dopemux/dopemux-mvp"
Issues = "https://github.com/dopemux/dopemux-mvp/issues"
Documentation = "https://docs.dopemux.dev"

[project.scripts]
dopemux = "dopemux.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["dopemux"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]

```

File: src/dopemux/cli.py (Imports Only)
```
import os
import logging
import sys
import time
import shutil
import socket
import signal
import tempfile
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence
import warnings
import logging
import click
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from . import __version__
from .claude_tools.cli import register_commands
from .console import console
from .adhd import AttentionMonitor, ContextManager, TaskDecomposer
from .claude import ClaudeConfigurator, ClaudeLauncher
from .dope_brainz_router import (
from .config import ConfigManager
from .health import HealthChecker
from .instance_manager import InstanceManager, detect_instances_sync, detect_orphaned_instances_sync
from .litellm_proxy import (
from .profile_manager import ProfileManager
from .profile_models import ProfileValidationError
from .claude_config import ClaudeConfig, ClaudeConfigError
from .profile_parser import ProfileParser
from .protection_interceptor import check_and_protect_main, consume_last_created_worktree
from .project_init import init_project
import subprocess
from subprocess import CalledProcessError
from urllib.parse import urlparse
import yaml
from .mobile import mobile as mobile_commands
from .mobile.hooks import mobile_task_notification
from .mobile.runtime import update_tmux_mobile_indicator
from .tmux import tmux as tmux_commands
from .roles.catalog import (
from .memory.capture_client import CaptureError, emit_capture_event
from .claude_tools.cli import register_commands
```
