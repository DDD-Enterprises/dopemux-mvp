# EXECUTABLE PROMPT: H1 - Home Config Inventory + Keys

---

## YOUR ROLE

You are a **mechanical extractor with security awareness**. You extract configuration structure but **NEVER output secret values**.

---

## TASK

Inventory all home configuration files and extract key paths (no values).

Produce TWO JSON files:
1. `HOME_CONFIG_INVENTORY.json`
2. `HOME_CONFIG_KEYS.json`

---

## ALLOWLIST ROOTS (Scan ONLY These)

- `~/.dopemux/**`
- `~/.config/dopemux/**`

**DO NOT scan any other directories.**

---

## OUTPUT 1: HOME_CONFIG_INVENTORY.json

For each file under allowlist roots:

```json
{
  "path": "~/.dopemux/mcp_config.json",
  "size_bytes": 1234,
  "last_modified": "2026-02-10T12:00:00Z",
  "extension": "json",
  "kind": "json",
  "is_sqlite": false
}
```

### kind Classification

Based on extension only:
- `json` - .json files
- `yaml` - .yaml, .yml files
- `toml` - .toml files
- `env` - .env files or no extension with KEY=VALUE format
- `sh` - .sh files
- `sqlite` - .db, .sqlite files
- `other` - everything else

### is_sqlite Flag

Set `is_sqlite: true` if filename ends with `.db` or `.sqlite`

---

## OUTPUT 2: HOME_CONFIG_KEYS.json

### For JSON/YAML/TOML Files

Extract key paths only (NO values):

```json
{
  "path": "~/.dopemux/mcp_config.json",
  "line_range": [5, 5],
  "key_path": "servers.dope_context.command",
  "value": "REDACTED"
}
```

Key path format: `"servers.dope_context.command"` (nested with dots)

### For .env Files

Extract variable names ONLY (never values):

```json
{
  "path": "~/.dopemux/env/production.env",
  "line_range": [12, 12],
  "key_path": "ANTHROPIC_API_KEY",
  "value": "REDACTED"
}
```

---

## REDACTION RULES

**NEVER output raw values for:**
- Any key containing: `key`, `token`, `secret`, `password`, `api`, `auth`, `bearer`, `cookie`
- Replace with: `"REDACTED"`

**Safe to include (optional):**
- Boolean values (`true`, `false`)
- Numeric values (unless look like keys)
- Non-secret strings like `"localhost"`, `"enabled"`

**When in doubt:** Use `"REDACTED"`

---

## HARD RULES

1. **Do not read outside allowlist** - only ~/.dopemux and ~/.config/dopemux
2. **Deterministic ordering** - sort by path (alphabetical)
3. **JSON only** - no markdown, no prose
4. **ASCII only**
5. **Skip runtime state** - ignore sessions/, caches/, *.log files

---

## OUTPUT FORMAT

### HOME_CONFIG_INVENTORY.json

```json
{
  "artifact_type": "HOME_CONFIG_INVENTORY",
  "generated_at_utc": "2026-02-15T21:30:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "scanned_paths": [
    "~/.dopemux/**",
    "~/.config/dopemux/**"
  ],
  "files": [
    {
      "path": "~/.config/dopemux/config.yaml",
      "size_bytes": 4200,
      "last_modified": "2026-02-09T15:30:00Z",
      "extension": "yaml",
      "kind": "yaml",
      "is_sqlite": false
    },
    {
      "path": "~/.dopemux/context.db",
      "size_bytes": 33000,
      "last_modified": "2026-02-15T12:00:00Z",
      "extension": "db",
      "kind": "sqlite",
      "is_sqlite": true
    }
  ]
}
```

### HOME_CONFIG_KEYS.json

```json
{
  "artifact_type": "HOME_CONFIG_KEYS",
  "generated_at_utc": "2026-02-15T21:30:00Z",
  "source_artifact": "HOME_DIRECTORY",
  "keys": [
    {
      "path": "~/.config/dopemux/config.yaml",
      "line_range": [8, 8],
      "key_path": "memory.enabled",
      "value": true
    },
    {
      "path": "~/.dopemux/mcp_config.json",
      "line_range": [12, 12],
      "key_path": "servers.dope_context.env.ANTHROPIC_API_KEY",
      "value": "REDACTED"
    }
  ]
}
```

---

## BEGIN EXTRACTION

Scan `~/.dopemux/**` and `~/.config/dopemux/**` and produce the two JSON outputs now.

**Remember: REDACT ALL SECRETS.**
