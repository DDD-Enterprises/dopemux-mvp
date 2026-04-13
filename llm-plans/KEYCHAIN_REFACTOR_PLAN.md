# Keychain Secrets Refactoring Plan

**Objective:** Securely load all sensitive API keys and database passwords dynamically from the macOS Keychain, removing hardcoded secrets and fallback passwords from `docker-compose.unified.yml` and `.env` files.

## Completed Preparation
1. **Script Creation:** Created `scripts/load_keychain_env.sh` which queries `security find-generic-password` for an array of expected secrets (e.g., `GEMINI_API_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`) and dynamically writes them to `.env.unified`.
2. **Compose File Refactoring:** Stripped hardcoded passwords (e.g., `minioadmin`, `dopemux-redis-ui`) and removed unsafe fallback default values (`${VAR:-fallback}`) from `docker-compose.unified.yml`. All secrets now strictly require an environment variable.

## Execution Phase Steps
Upon approval of this plan, the agent will:
1. Execute `./scripts/load_keychain_env.sh` to generate the populated `.env.unified` file directly from the user's secure keychain.
2. Verify the Docker Compose configuration using `docker compose --env-file .env.unified -f docker-compose.unified.yml config`.
3. Proceed with the background boot of the unified stack: `docker compose --env-file .env.unified -f docker-compose.unified.yml up -d --build`.
