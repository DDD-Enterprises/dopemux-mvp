# Security Compose LiteLLM + Localhost Proof - 2026-05-31

## Scope

- Task Packet: `TP-SEC-COMPOSE-LITELLM-LOCALHOST-001`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-security-compose`
- Branch: `fix/security-litellm-key-compose`
- Base commit: `69f17d066945a323f817557fc1d7a1e7d41a5a21`
- Repo remote: `https://github.com/DDD-Enterprises/dopemux-mvp.git`

## Authority Used

- Latest user prompt: implement remaining beta work sequentially; combine items 3 and 4 if cleaner.
- `AGENTS.md`: Task Packet, proof bundle, worktree, validation, and truthful finality requirements.
- `.claude/claude.md` and `.claude/modules/shared/governance-principles.md`: inspect-first and validation bucket doctrine.
- Runtime/config evidence: `compose.yml`, `.env.example`, `install.sh`, service entrypoints under `services/` and `docker/`.

## Observed Evidence

- `grep -n "LITELLM_MASTER_KEY\|Authorization.*Bearer" compose.yml` on the base showed a redacted hardcoded bearer placeholder in the LiteLLM healthcheck, not an unredacted secret value.
- `grep -n "0\.0\.0\.0" compose.yml` showed `MCP_SERVER_HOST`, `HOST`, and `WEBHOOK_RECEIVER_HOST` values using `0.0.0.0`.
- Runtime inspection showed Docker-published container services generally must listen on the container interface. Changing those container-internal binds to `127.0.0.1` risks making host-published ports unreachable.

## Changes

- `compose.yml`
  - Added `LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}` to the LiteLLM environment.
  - Replaced the hardcoded LiteLLM healthcheck bearer with `Authorization: Bearer $${LITELLM_MASTER_KEY}`.
  - Restricted `adhd-engine`, `leantime-bridge`, and `webhook-receiver` host port publication to `127.0.0.1`.
  - Documented retained container-internal `0.0.0.0` binds as intentional Docker reachability requirements.
- `.env.example`
  - Added `LITELLM_MASTER_KEY` with a non-real placeholder and generation comment.
- `install.sh`
  - Added `LITELLM_MASTER_KEY` to full-stack env collection.
  - Marked it sensitive and local-defaultable.
  - Generates a 32-byte hex secret via Python `secrets.token_hex(32)` when using the installer default.
- `task-packets/INDEX.md`
  - Added the active Task Packet entry.
- `task-packets/generated/TP-SEC-COMPOSE-LITELLM-LOCALHOST-001.json`
  - Added the scoped Task Packet for this slice.

## Validation

### PASS

- `python -m json.tool task-packets/generated/TP-SEC-COMPOSE-LITELLM-LOCALHOST-001.json >/dev/null`
- `python -m jsonschema -i task-packets/generated/TP-SEC-COMPOSE-LITELLM-LOCALHOST-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `grep -n "LITELLM_MASTER_KEY\|Authorization.*Bearer" compose.yml .env.example install.sh`
- `grep -n "0\.0\.0\.0" compose.yml`
- PyYAML compose security assertions:
  - LiteLLM healthcheck uses `$${LITELLM_MASTER_KEY}`.
  - `dope-context`, `adhd-engine`, `leantime-bridge`, and `webhook-receiver` published ports start with `127.0.0.1:`.
- `bash -n install.sh`
- `docker compose -f compose.yml config --quiet`
- `git diff --check`
- PAL codereview (`mcp__pal.codereview`, model `gpt-5-codex`, internal validation): no issues reported.
- `pre-commit run --files .env.example compose.yml install.sh task-packets/INDEX.md task-packets/generated/TP-SEC-COMPOSE-LITELLM-LOCALHOST-001.json claudedocs/security-compose-litellm-localhost-proof-2026-05-31.md`

### NOT_RUN

- `docker compose up` / live service boot: not required by prompt, and live Docker runtime validation was out of scope for this commit-sized security slice.
- End-to-end webhook delivery: not required and would require external provider/webhook setup.

## Prompt Conflict / Challenge Result

The audit prompt said the actual LiteLLM key was present in `compose.yml`; current repo truth on the verified base showed a redacted placeholder. The fix still removes the hardcoded bearer value from source and routes it through `LITELLM_MASTER_KEY`.

The audit prompt also described env-var `0.0.0.0` binds as the exposure. Runtime inspection showed those binds are container-internal for Docker-published services. This slice therefore restricts host-facing publication to `127.0.0.1` and documents retained container-internal binds instead of changing them to a value that could break Docker reachability.

## Precommit Status

- PASS: `git diff --check`
- PASS: PAL codereview (`gpt-5-codex`, internal validation)
- PASS: `pre-commit run --files ...`

## Commit / PR

- Commit SHA: pending
- PR URL: pending

## Residual Risk / Unknowns

- Docker runtime startup was not exercised, so actual service boot behavior remains `NOT_RUN`.
- The remaining weak defaults in `.env.example` are intentionally left for the separate security weak-defaults item.
- Existing public host publications outside the four audited lines were not remediated in this slice.

## Rollback

Revert this branch commit or restore the touched files from `origin/main`:

- `.env.example`
- `compose.yml`
- `install.sh`
- `task-packets/INDEX.md`
- `task-packets/generated/TP-SEC-COMPOSE-LITELLM-LOCALHOST-001.json`
- `claudedocs/security-compose-litellm-localhost-proof-2026-05-31.md`
