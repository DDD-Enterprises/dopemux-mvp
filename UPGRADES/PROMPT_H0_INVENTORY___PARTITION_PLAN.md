# PROMPT_H0_INVENTORY___PARTITION_PLAN
Goal: home control plane inventory + deterministic partitions (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
Inventory ONLY the following allowlisted home roots:
- ~/.dopemux/
- ~/.config/dopemux/
- ~/.config/taskx/
- ~/.config/litellm/
- ~/.config/mcp/

Then produce:
1) HOME_INDEX.json (inventory)
2) HOME_PARTITIONS.json (partition plan for Phase H)

## Hard rules
- Do not read outside allowlisted roots.
- Do not include file contents in outputs; inventory metadata only.
- Redact obvious secrets in filenames if present (rare). Do NOT print full paths to key files if they contain secrets in name; replace token-like segments with "[REDACTED]".
- Evidence required: HOMECTRL: <path> (for inventory items, evidence is the file path itself)
- Determinism: stable sorting.

## What counts as "control plane" in home
Priority include:
- dopemux configs, router configs, profile configs
- mcp server configs / tool configs
- litellm configs, spend db configs
- taskx user config, pins, profiles
- tmux helpers/layouts, workflow scripts
- sqlite db metadata (do NOT dump entire DBs; only filename + size + modified time)

Exclude:
- caches unless they are clearly used as state (e.g., *.sqlite, *.db, *.json caches referenced by config)
- logs unless referenced by config
- large binary blobs

## Output 1: HOME_INDEX.json
{
  "artifact": "HOME_INDEX",
  "generated_at": "<iso8601>",
  "roots": [
    {"root": "~/.dopemux", "scanned": true},
    {"root": "~/.config/dopemux", "scanned": true},
    {"root": "~/.config/taskx", "scanned": true},
    {"root": "~/.config/litellm", "scanned": true},
    {"root": "~/.config/mcp", "scanned": true}
  ],
  "files": [
    {
      "path": "<literal_path>",
      "rel_root": "~/.dopemux|~/.config/dopemux|~/.config/taskx|~/.config/litellm|~/.config/mcp",
      "ext": ".json|.yaml|.yml|.toml|.md|.sh|.sqlite|.db|.txt|unknown",
      "size": <int_bytes>,
      "mtime": "<iso8601>",
      "category_hint": "mcp|router|profiles|litellm|taskx|tmux|workflow|sqlite|other",
      "risk_hint": "HIGH|MED|LOW",
      "notes": ["..."]
    }
  ],
  "summary": {
    "file_count": <int>,
    "by_category": {"mcp": 0, "router": 0, "...": 0},
    "largest_files": [{"path": "...", "size": 0}]
  }
}

Risk hints:
- HIGH: keys/tokens likely (auth config, env dumps)
- MED: db files, sqlite, router configs
- LOW: docs, readmes, templates

## Output 2: HOME_PARTITIONS.json
Goal: chunk Phase H safely by topic to avoid context overflow.
{
  "artifact": "HOME_PARTITIONS",
  "generated_at": "<iso8601>",
  "rules": {
    "max_files_per_partition": 30,
    "max_total_chars_per_partition": 180000,
    "truncate_file_chars": 12000
  },
  "partitions": [
    {
      "id": "H_P1_MCP",
      "topic": "mcp servers/tools config",
      "include_globs": [
        "~/.dopemux/mcp_config.json",
        "~/.dopemux/mcp-tools/**",
        "~/.config/mcp/**"
      ],
      "include_paths": ["<resolved literals from HOME_INDEX>"],
      "exclude_globs": ["**/node_modules/**", "**/.cache/**"],
      "priority": 100,
      "rationale": "Needed for MCP->hooks migration and runtime behavior."
    },
    {
      "id": "H_P2_ROUTER",
      "topic": "router/provider ladders/profile routing",
      "include_globs": [
        "~/.dopemux/**router**",
        "~/.dopemux/**ladders**",
        "~/.config/dopemux/config.yaml",
        "~/.config/dopemux/dopemux.toml"
      ],
      "include_paths": [],
      "exclude_globs": [],
      "priority": 95,
      "rationale": "Local overrides of repo routing."
    },
    {
      "id": "H_P3_LITELLM",
      "topic": "litellm configs/spend db hints",
      "include_globs": [
        "~/.dopemux/litellm/**",
        "~/.config/litellm/**"
      ],
      "include_paths": [],
      "exclude_globs": [],
      "priority": 85,
      "rationale": "Provider routing + cost telemetry."
    },
    {
      "id": "H_P4_TASKX",
      "topic": "taskx user config/pins/profiles",
      "include_globs": ["~/.config/taskx/**"],
      "include_paths": [],
      "exclude_globs": [],
      "priority": 80,
      "rationale": "TaskX integration truth and portability."
    },
    {
      "id": "H_P5_TMUX_WORKFLOWS",
      "topic": "tmux/layout/workflow helpers",
      "include_globs": [
        "~/.dopemux/tmux-layout.sh",
        "~/.dopemux/**tmux**/**",
        "~/.dopemux/**workflow**/**",
        "~/.config/dopemux/**dashboard**"
      ],
      "include_paths": [],
      "exclude_globs": [],
      "priority": 70,
      "rationale": "Implicit workflows and startup flows."
    },
    {
      "id": "H_P6_SQLITE_STATE",
      "topic": "sqlite state db metadata",
      "include_globs": ["~/.dopemux/*.sqlite", "~/.dopemux/*.db", "~/.dopemux/**.sqlite", "~/.dopemux/**.db"],
      "include_paths": [],
      "exclude_globs": [],
      "priority": 65,
      "rationale": "Local state dependencies; do not dump contents."
    }
  ],
  "unknowns": [
    {"area": "home roots", "reason": "Some roots missing from input bundle"}
  ]
}

## Finish
Emit ONLY the two JSON artifacts.
No prose.
No markdown fences.
