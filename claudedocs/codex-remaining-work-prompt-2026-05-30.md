# Codex Prompt — Dopemux Remaining Beta Work (2026-05-30)

Paste this entire file as a Codex task. It is self-contained.

---

## Context

Repo: `DDD-Enterprises/dopemux-mvp`  
Local path: `/Users/hue/code/dopemux-mvp`  
Today: 2026-05-30  
Goal: Ship the remaining beta-readiness work listed below. Read `AGENTS.md` and `.claude/CLAUDE.md` first (Truth Order, branch discipline, proof bundle). Never work on `main`.

---

## Already merged / in-flight — DO NOT redo

These are either merged or have auto-merge set and will land shortly:

| PR | Description |
|----|-------------|
| #725 | RTE remediation P0+P1+P2 (auto-merge set) |
| #734 | Palette clobber restore — 17 /dx: cmds + config.yaml (open, mergeable) |
| #735 | BETA-INSTALL-02 — dopemux-network creation (auto-merge set) |
| #737 | BETA-INSTALL-01 + BETA-MCP-01 — .mcp.json path + port defaults (auto-merge set) |
| #738 | Auditor-router governance reconciliation (open, mergeable) |
| #740 | BETA-CLI-01 — decisions list/show/query/review/update-outcome (auto-merge set) |

**PR #724** (`codex/tp-cs-101-plugin-path-b`, feat(hooks): orchestrator plugin Path B) is OPEN and MERGEABLE but was blocked on #734. Once #734 merges, enable auto-merge on #724.

---

## Work to implement

Implement each item below as a separate branch + PR. Read AGENTS.md §8 for the proof bundle requirement. Commit with `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`.

---

### ITEM 1 — BETA-MCP-02: compose.yml cold-start race conditions [MED]

**Problem:** Several services in `compose.yml` use bare-list `depends_on` (just service names, no condition) or `condition: service_started` for dependencies on `conport`, `task-orchestrator`, and `adhd-engine`. These services don't guarantee readiness before dependents try to connect — causing intermittent cold-start failures.

**Verify first:** Read `compose.yml` and identify every `depends_on` entry that references `conport`, `task-orchestrator`, `adhd-engine`, `redis-primary`, or `postgres` using bare-list or `service_started`. Check whether each of those services has a working `healthcheck` block.

**Fix:**
1. For services that have a `healthcheck`, change dependent `depends_on` entries to `condition: service_healthy` instead of bare-list or `service_started`.
2. For any critical dependency that lacks a healthcheck, add a minimal one (e.g. `curl -f http://localhost:PORT/health || exit 1`). Match the pattern already used in compose.yml for similar services.
3. Do NOT change `leantime` or `mysql_leantime` — those healthchecks are already set correctly.

**Branch:** `fix/beta-mcp-02-compose-healthchecks`

---

### ITEM 2 — BETA-MCP-03: per-instance Redis isolation [MED]

**Problem:** `adhd-engine` stores attention/break/energy state keyed only by user, not by worktree instance. Two Claude Code sessions on different branches for the same user collide — one session's break state bleeds into the other.

**Verify first:** Read `compose.yml` around `adhd-engine` and `redis-primary`. Check whether there's an `instance_overlay` compose file or `ADHD_ENGINE_INSTANCE_ID` / `ADHD_ENGINE_REDIS_PREFIX` env var that scopes the keys. Check `services/adhd_engine/` for how Redis keys are constructed.

**Fix options (pick the correct one after reading the code):**
- If the adhd-engine already supports a `REDIS_KEY_PREFIX` or `INSTANCE_ID` env var, expose it in compose.yml via `${DOPEMUX_INSTANCE_ID:-default}` so parallel instances get isolated namespaces.
- If no such var exists, add one to the adhd-engine Redis key construction (e.g. prefix all keys with `${INSTANCE_ID}:`).
- Document the fix in a brief inline comment.

**Branch:** `fix/beta-mcp-03-adhd-engine-redis-isolation`

---

### ITEM 3 — Security: remove hardcoded LiteLLM key from compose.yml healthcheck [HIGH]

**Problem:** `compose.yml` line ~312 contains a hardcoded LiteLLM master key in a healthcheck command:
```
curl -f -H 'Authorization: Bearer <REDACTED_LITELLM_MASTER_KEY>' http://localhost:4000/health
```
The actual value was redacted in the audit but is present in the repo. This is a secret committed to source control.

**Verify:** `grep -n "LITELLM_MASTER_KEY\|Authorization.*Bearer" compose.yml` — confirm the hardcoded value is present.

**Fix:**
1. Replace the hardcoded key with `${LITELLM_MASTER_KEY}` (env var reference).
2. Add `LITELLM_MASTER_KEY` to `.env.example` with a placeholder value and a comment explaining it.
3. Add `LITELLM_MASTER_KEY` to `install.sh`'s required-env validation list if it's not already there.

**Branch:** `fix/security-litellm-key-compose`

---

### ITEM 4 — Security: bind MCP services to 127.0.0.1 in compose.yml [HIGH]

**Problem:** Several services in `compose.yml` bind to `0.0.0.0` via env vars:
- Line ~329: `MCP_SERVER_HOST=0.0.0.0` 
- Line ~436: `HOST=0.0.0.0`
- Line ~594: `MCP_SERVER_HOST=0.0.0.0`
- Line ~620: `WEBHOOK_RECEIVER_HOST=0.0.0.0`

These expose internal MCP services on all network interfaces — reachable from the local network without authentication.

**Verify:** `grep -n "0\.0\.0\.0" compose.yml` — confirm which services and lines.

**Fix:** Change each `0.0.0.0` binding to `127.0.0.1` for services that are not explicitly intended to be network-accessible. Services that ARE intentionally public (e.g. the main dopemux API) should be left unchanged or documented as intentional. Check each service name before changing.

**Branch:** `fix/security-localhost-bind-mcp-services`

---

### ITEM 5 — Security: default secrets in .env.example must not be weak [HIGH]

**Problem:** `.env.example` ships with placeholder values like `your_secure_task_orchestrator_key_here` and `dev-key-456`. Install scripts may copy these as-is. At minimum, the install flow should warn when these are unset or still at their default values.

**Verify:** `grep -n "your_secure\|dev-key\|changeme\|secret\|password" .env.example` — identify the weak defaults.

**Fix:**
1. Replace all weak placeholder values with `CHANGE_ME_$(openssl rand -hex 8)_placeholder` style values that are obviously invalid (not accidentally usable).
2. In `install.sh` or `scripts/setup.sh`, add a check: if the key is still at its placeholder value, emit a `warning` and prompt for a real value (or generate one). Model this on any existing secret-validation pattern in `install.sh`.
3. Add a `# REQUIRED: generate with: openssl rand -hex 32` comment above each sensitive key in `.env.example`.

**Branch:** `fix/security-weak-default-secrets`

---

### ITEM 6 — UI dashboard build: fix broken build [HIGH]

**Problem:** The `ui-dashboard` (Vite/React app at `ui-dashboard/`) fails to build. This was flagged as RV-13 in the beta-readiness audit.

**Verify:** 
```bash
cd ui-dashboard && npm install && npm run build 2>&1 | tail -30
```
Identify the exact error.

**Fix:** Resolve whatever is breaking the build — likely a missing dependency, a TypeScript error, or a broken import. Do not change the app's logic or UI; only make the build pass. If the fix requires adding a dependency, use `npm install --save-dev <pkg>` and commit the updated `package.json` and `package-lock.json`.

**Branch:** `fix/ui-dashboard-build`

---

### ITEM 7 — Docs: fix first-touch docs that describe wrong product [MED]

**Problem:** The beta-readiness audit found that the project's "Start Here" / onboarding documentation describes a different product ("chatx") and is stale. A new user cloning the repo cannot follow the setup steps.

**Verify:** 
- `grep -rn "chatx\|chat-x\|ChatX" docs/ README.md INSTALL.md 2>/dev/null | head -20`
- Read `docs/01-tutorials/` (or whatever the first-touch path is) for onboarding correctness.

**Fix:**
1. Replace all "chatx" / "chat-x" references with "dopemux" or the correct product name.
2. Update the "Start Here" / quickstart doc to reflect the actual install flow: `./install.sh` → `dopemux start` → open Claude Code.
3. Do not rewrite docs you haven't read — only fix the specific stale/wrong content you can confirm.

**Branch:** `fix/docs-first-touch-product-name`

---

### ITEM 8 — CI: gate the full test suite [MED]

**Problem:** CI only runs a fraction of the test suite. The beta-readiness audit noted that `services/repo-truth-extractor/tests/` (1100+ tests) and `tests/auditor_router/` (broken imports, 3 dead security tests) are not gated.

**Verify:** Read `.github/workflows/` to understand what currently runs. Run `find . -path "*/tests/test_*.py" | head -20` to see what's not covered.

**Fix:**
1. Add `services/repo-truth-extractor/tests/` to the CI test matrix (use `PYTHONPATH=src pytest services/repo-truth-extractor/tests/ -q --tb=short`).
2. Fix the broken imports in `tests/auditor_router/` so the 3 dead security tests actually run (check what they import and why it fails).
3. Add `tests/auditor_router/` to CI.
4. Do NOT add live/integration tests that require Docker or real API keys — mark them with `@pytest.mark.integration` and skip in CI.

**Branch:** `fix/ci-full-test-suite`

---

## Ordering

Work sequentially. Each item is independent except:
- Do ITEM 3 (LiteLLM key) before ITEM 4 (0.0.0.0 binds) — both touch compose.yml, do them in the same PR if cleaner.
- ITEM 6 (UI build) can be done anytime.
- After all PRs are open, run: `gh pr merge <N> --repo DDD-Enterprises/dopemux-mvp --rebase --auto` on each.

## Validation per item

- Run the relevant test suite after each change.
- `git diff --check` before committing.
- No live/Docker tests required — mark NOT_RUN with reason.
- Proof bundle per AGENTS.md §8 in a `claudedocs/` file for the batch.

## PR hygiene

- One branch per item (or combine 3+4 if touching same file).
- Branch naming: `fix/<slug>` as shown above.
- Commit message: `fix(<scope>): <ITEM-ID> — <what and why>`.
- PR body: problem, fix, test plan, NOT_RUN items.
- `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` on all commits.
