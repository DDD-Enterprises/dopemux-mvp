# EXECUTABLE PROMPT: E - Env Vars + Config Loaders + Secrets Risk

---

## YOUR ROLE

You are a **mechanical extractor with security awareness**. Extract environment variable usage, config loading patterns, and secrets-risk locations. **NEVER output actual secret values.**

---

## TASK

Scan the provided files and produce THREE JSON files:
1. `ENV_VARS.json`
2. `CONFIG_LOADERS.json`
3. `SECRETS_RISK_LOCATIONS.json`

---

## OUTPUT 1: ENV_VARS.json

Find all environment variable references.

```json
{
  "path": "src/dopemux/config.py",
  "line_range": [25, 25],
  "domain": "code_env",
  "kind": "env_var",
  "name": "ANTHROPIC_API_KEY",
  "access_pattern": "os.getenv",
  "default_value": "REDACTED",
  "required": true,
  "excerpt": "ANTHROPIC_API_KEY = os.getenv(\"ANTHROPIC_API_KEY\")"
}
```

### Patterns to Match

| Pattern                                      | access_pattern |
| -------------------------------------------- | -------------- |
| `os.getenv("X")` / `os.getenv("X", default)` | `os.getenv`    |
| `os.environ["X"]` / `os.environ.get("X")`    | `os.environ`   |
| `env.str("X")` / `config("X")`               | `env_lib`      |
| `.env` file entries: `KEY=value`             | `dotenv`       |

### REDACTION

- If the default value contains: `key`, `token`, `secret`, `password`, `api`, `auth` → set `"default_value": "REDACTED"`
- Safe defaults: `localhost`, `8000`, `true`, `false`, `INFO` → include literally

---

## OUTPUT 2: CONFIG_LOADERS.json

Find code that loads configuration files.

```json
{
  "path": "src/dopemux/config.py",
  "line_range": [10, 12],
  "domain": "code_env",
  "kind": "config_loader",
  "name": "load_dotenv",
  "loader_type": "dotenv",
  "loaded_file": ".env",
  "symbol": "load_dotenv",
  "excerpt": "from dotenv import load_dotenv\nload_dotenv()"
}
```

### loader_type

- `dotenv` — `load_dotenv()` / `dotenv_values()`
- `toml` — `toml.load()` / `tomllib.load()`
- `yaml` — `yaml.safe_load()` / `yaml.load()`
- `json` — `json.load()` for config files
- `ini` — `configparser`

---

## OUTPUT 3: SECRETS_RISK_LOCATIONS.json

Find patterns where secrets or sensitive data might be exposed.

```json
{
  "path": "services/chronicle/main.py",
  "line_range": [88, 88],
  "domain": "risk_secrets",
  "kind": "secrets_risk",
  "name": "env_dump_in_log",
  "risk_type": "logging_exposure",
  "matched_pattern": "logger.info(f\"Config: {os.environ}\")",
  "severity_hint": "high",
  "excerpt": "logger.info(f\"Config: {os.environ}\")"
}
```

### Patterns to Scan

| risk_type               | What to Match                                                   |
| ----------------------- | --------------------------------------------------------------- |
| `logging_exposure`      | `print(os.environ)`, `logger.*(.*key.*\|.*secret.*\|.*token.*)` |
| `payload_dump`          | `print(request.body)`, `logger.*(payload\|body\|content)`       |
| `credential_in_string`  | Hardcoded strings matching API key patterns (32+ hex chars)     |
| `unredacted_transcript` | Writing raw LLM prompts/responses to files without redaction    |
| `env_in_response`       | Returning env vars in HTTP responses                            |

### severity_hint

- `high` — credentials could leak to logs/output
- `medium` — payload data could leak
- `low` — potential but unlikely exposure

---

## REDACTION RULES

**NEVER include in output:**
- Actual API keys, tokens, passwords
- Replace with `"REDACTED"` if found inline

**Safe to include:**
- Variable names (`ANTHROPIC_API_KEY`)
- Pattern descriptions (`os.getenv(...)`)
- Non-secret defaults (`localhost`, `8000`)

---

## HARD RULES

1. **No inference** — match literal patterns only
2. **JSON only** — no markdown, no prose
3. **ASCII only**
4. **Deterministic sorting** — by path, then line_range
5. **path + line_range required** on every item
6. **REDACT all secrets** — when in doubt, REDACT

---

## OUTPUT FORMAT

Each file wrapper:

```json
{
  "artifact_type": "ENV_VARS",
  "generated_at_utc": "2026-02-15T22:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```

---

## BEGIN EXTRACTION

Process the provided context files and produce the three JSON outputs now.

**Remember: REDACT ALL SECRETS.**
