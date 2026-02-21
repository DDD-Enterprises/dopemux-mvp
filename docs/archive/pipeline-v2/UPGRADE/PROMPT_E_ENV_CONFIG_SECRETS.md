---
id: PROMPT_E_ENV_CONFIG_SECRETS
title: Prompt E Env Config Secrets
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt E Env Config Secrets (explanation) for dopemux documentation and developer
  workflows.
---
# Prompt E (v2): Env + config loaders + secrets-risk locations

**Outputs:** `ENV_VARS.json`, `CONFIG_LOADERS.json`, `SECRETS_RISK_LOCATIONS.json`

---

## TASK

Produce THREE JSON files: `ENV_VARS.json`, `CONFIG_LOADERS.json`, `SECRETS_RISK_LOCATIONS.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE.

## ENV_VARS.json

- Extract all env var names used via `os.getenv`/`os.environ` and config libraries.
- Emit items:
  - `domain=code_env`
  - `kind=env_var`
  - `name=<ENV_VAR_NAME>`
  - `strings` include default value if present (as string).

## CONFIG_LOADERS.json

- Find code that loads config files: dotenv, toml, yaml, json.
- Emit items:
  - `domain=code_env`
  - `kind=config_loader`
  - `name=<loaded filename or loader function>`
  - `strings` include file extensions and paths mentioned.

## SECRETS_RISK_LOCATIONS.json

- Find patterns where secrets or raw payloads might be logged or written:
  - printing env
  - dumping request bodies
  - writing raw transcripts/prompts
- Emit items:
  - `domain=risk_secrets`
  - `kind=risk`
  - `name=<pattern label>`
  - `strings` include the matched token (e.g., `"print(os.environ"` or `"logger.info(payload)"`)

## RULES

- Never output secret values.
- Universal schema, deterministic sorting.
