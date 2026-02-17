# PROMPT_H0 — HOME inventory + partition plan (SAFE MODE)

ROLE: Forensic extractor. Safety-first. Evidence-only. No invention.
MODEL: Gemini Flash (fast scanner).

GOAL:
Build HOME_INDEX.json and HOME_PARTITIONS.json for safe home control-plane scanning.
Home scope must be restricted to:
- ~/.dopemux/**
- ~/.config/dopemux/**
- ~/.config/taskx/**
- ~/.config/litellm/**
- ~/.config/mcp/**

HARD RULES (SAFE MODE):
1) Never output secrets. Redact any values that look like:
   - API keys, bearer tokens, private keys, session cookies
   - OAuth tokens, JWTs, passwords, DSNs with credentials
   Replace value with: "__REDACTED__"
2) Do not traverse outside the allowlist roots above.
3) Ignore noise + heavy dirs:
   - ~/.cache, ~/Library, ~/Downloads, ~/Documents, ~/Desktop, ~/Pictures, ~/Music
   - node_modules, .git, dist, build, tmp, logs (unless within allowlist and clearly relevant)
4) Prefer metadata over full contents. For each file, capture:
   - path, size, mtime, extension, and a small SAFE excerpt (max 40 lines) ONLY if it contains config keys (not secrets).
5) If a file is SQLite: do not dump raw rows. Only identify it as sqlite and list filename/size/mtime.

OUTPUTS (write valid JSON, no markdown fences):
A) HOME_INDEX.json
{
  "artifact": "HOME_INDEX",
  "generated_at": "<iso8601>",
  "roots": ["~/.dopemux", "~/.config/dopemux", "~/.config/taskx", "~/.config/litellm", "~/.config/mcp"],
  "files": [
    {
      "path": "<absolute>",
      "rel_root": "<which root>",
      "kind": "config|script|sqlite|cache|unknown",
      "ext": ".json|.yaml|.toml|.sh|.db|...",
      "size": <int>,
      "mtime": <epoch_seconds>,
      "signals": ["router","mcp","litellm","taskx","profiles","tmux","hooks","env","sqlite","unknown"],
      "safe_excerpt": "<optional short excerpt with sensitive values redacted>"
    }
  ],
  "stats": { "file_count": <int>, "total_bytes": <int> }
}

B) HOME_PARTITIONS.json
{
  "artifact": "HOME_PARTITIONS",
  "generated_at": "<iso8601>",
  "partitions": [
    { "id": "H_P1_MCP", "include_globs": ["**/mcp*.json","**/mcp/**/*.json","**/mcp/**/*.yaml","**/mcp/**/*.yml"], "notes": "MCP client/server configs" },
    { "id": "H_P2_ROUTER", "include_globs": ["**/*router*.*","**/*provider*.*","**/*ladder*.*"], "notes": "routing/provider ladder hints" },
    { "id": "H_P3_LITELLM", "include_globs": ["**/litellm*.*","**/*proxy*.*","**/*spend*.*"], "notes": "litellm configs + spend/log hints" },
    { "id": "H_P4_PROFILES", "include_globs": ["**/profiles/**/*.*","**/*profile*.*","**/*persona*.*"], "notes": "profiles + operator configs" },
    { "id": "H_P5_TMUX_WORKFLOWS", "include_globs": ["**/*.tmux*","**/*tmux*.*","**/*layout*.*"], "notes": "tmux helpers/workflows" },
    { "id": "H_P6_SQLITE_STATE", "include_globs": ["**/*.sqlite","**/*.db","**/*.sqlite3"], "notes": "state DBs (metadata only)" },
    { "id": "H_P9_MISC", "include_globs": ["**/*.*"], "notes": "catchall, only if not matched above" }
  ],
  "exclusions": ["**/Library/**","**/Downloads/**","**/.cache/**","**/node_modules/**","**/.git/**"],
  "redaction_policy": { "redact_patterns": ["api_key","token","secret","password","Authorization","Bearer","OPENAI","ANTHROPIC","GEMINI","XAI"], "replacement": "__REDACTED__" }
}
