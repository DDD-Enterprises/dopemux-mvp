# Security Weak Default Secrets Proof - 2026-05-31

## Scope

- Task Packet: `TP-SEC-WEAK-DEFAULT-SECRETS-001`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-security-weak-defaults`
- Branch: `fix/security-weak-default-secrets`
- Base commit: `69f17d066945a323f817557fc1d7a1e7d41a5a21`
- Repo remote: `https://github.com/DDD-Enterprises/dopemux-mvp.git`

## Authority Used

- Latest user prompt: item 5, replace weak `.env.example` defaults and add installer checks for placeholders/defaults.
- `AGENTS.md`: Task Packet, proof bundle, worktree, validation, and truthful finality requirements.
- Runtime/config evidence: `.env.example`, `install.sh`, `tests/scripts/test_install_sh_secrets.py`.

## Observed Evidence

- `.env.example` contained weak copied placeholders for:
  - `AGE_PASSWORD`
  - `REDIS_PASSWORD`
  - `QDRANT_API_KEY`
  - `ADHD_ENGINE_API_KEY`
  - `TASK_ORCHESTRATOR_API_KEY`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
- `install.sh` generated static local defaults:
  - `AGE_PASSWORD=dopemux_age_dev_password`
  - `TASK_ORCHESTRATOR_API_KEY=dev-key-456`
  - `ADHD_ENGINE_API_KEY=dev-key-123`
  - `LITELLM_DATABASE_URL` containing `dopemux_age_dev_password`
- Existing installer tests covered provider deferral and env precedence but did not reject placeholder/dev values.

## Changes

- `.env.example`
  - Replaced local weak placeholders with explicit `CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder` values.
  - Added `# REQUIRED: generate with: openssl rand -hex 32` comments above local sensitive keys.
  - Cleared provider placeholders for `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` so provider keys can be deferred instead of copied as fake values.
- `install.sh`
  - Added generated local defaults using Python `secrets.token_hex(32)`.
  - Tied the generated `LITELLM_DATABASE_URL` password to the resolved `AGE_PASSWORD`.
  - Added placeholder/dev-value detection for copied `.env` or shell values.
  - Emits a warning and treats placeholder/dev values as missing so installer policy can prompt, defer, or generate.
- `tests/scripts/test_install_sh_secrets.py`
  - Added coverage for placeholder rejection/regeneration.
  - Added coverage that `.env.example` uses invalid placeholders for local secrets.
- Task Packet/index/proof files added for auditability.

## Validation

### PASS

- `python -m json.tool task-packets/generated/TP-SEC-WEAK-DEFAULT-SECRETS-001.json >/dev/null`
- `python -m jsonschema -i task-packets/generated/TP-SEC-WEAK-DEFAULT-SECRETS-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/scripts/test_install_sh_secrets.py -q`
- `bash -n install.sh`
- `.env.example` placeholder assertion script:
  - no `your_secure_`, provider fake key placeholders, `dev-key-`, or lowercase `changeme`
  - required local secret comments and invalid placeholders present
- PAL codereview (`mcp__pal.codereview`, model `gpt-5-codex`, internal validation): no issues reported.
- `git diff --check`
- `pre-commit run --files .env.example install.sh tests/scripts/test_install_sh_secrets.py task-packets/INDEX.md task-packets/generated/TP-SEC-WEAK-DEFAULT-SECRETS-001.json claudedocs/security-weak-default-secrets-proof-2026-05-31.md`

### NOT_RUN

- Full installer execution against Docker services: not required for this commit-sized installer secret policy slice.
- Full repository test suite: not run; focused installer tests cover the changed behavior.

## Implementation Note

The first implementation attempt emitted placeholder warnings to stdout inside command substitution, causing the warning text to become the resolved env value. The focused test caught this. The warning now goes to stderr, preserving the empty resolved value and allowing regeneration.

## Precommit Status

- PASS: PAL codereview (`gpt-5-codex`, internal validation)
- PASS: `git diff --check`
- PASS: `pre-commit run --files ...`

## Commit / PR

- Commit SHA: pending
- PR URL: pending

## Residual Risk / Unknowns

- PR #748 also changes `.env.example` and `install.sh` for `LITELLM_MASTER_KEY`; this branch is based on `origin/main`, so a rebase/merge conflict is likely if #748 lands first.
- `REDIS_PASSWORD` and `QDRANT_API_KEY` remain template-only in this slice; runtime consumption was not broadened.
- Runtime code still has development fallback strings in non-installer modules; item 5 scoped the template and installer flow, not every service fallback.

## Rollback

Revert this branch commit or restore the touched files from `origin/main`:

- `.env.example`
- `install.sh`
- `tests/scripts/test_install_sh_secrets.py`
- `task-packets/INDEX.md`
- `task-packets/generated/TP-SEC-WEAK-DEFAULT-SECRETS-001.json`
- `claudedocs/security-weak-default-secrets-proof-2026-05-31.md`
