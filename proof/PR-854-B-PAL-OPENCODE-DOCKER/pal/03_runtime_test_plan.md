# PAL-3 — Runtime Test Plan

## stage
PAL-3 Runtime Test Plan

## tool_or_mode
UNAVAILABLE_MANUAL_STAGE (Claude Sonnet)

## model
claude-sonnet-4-6

---

## Test 1: verify-pal.sh

**Command:**
```bash
bash scripts/opencode/verify-pal.sh
```

**Expected outcome:**
```
✅ opencode.jsonc exists
✅ PAL behavior guide exists
✅ PAL agents exist
⚠️  opencode CLI not found in PATH — skipping runtime config check  (or ✅ if opencode installed)
✅ Basic wiring verification complete.
```

**Pass condition:** exit code 0, checks 1–4 all ✅
**Block condition:** any ❌ exit with non-zero
**Secret risk:** NONE — script only checks file existence and CLI output, no secrets
**Forbidden file risk:** NONE — read-only

**Output file:** `VERIFY_PAL.log`

---

## Test 2: pal-stdio Docker Build

**Dockerfile path:** `docker/mcp-servers/pal-stdio/Dockerfile` (compose path; identical to source variant)
**Build context:** `.` (repo root, required for `COPY docker/mcp-servers/pal/pal-mcp-server/`)

**Command:**
```bash
docker build \
  -f docker/mcp-servers-source/pal-stdio/Dockerfile \
  -t dopemux-pal-stdio:pr854 \
  .
```

**Expected outcome:** exit code 0, image tagged `dopemux-pal-stdio:pr854`
**Pass condition:** exit 0
**Block condition:** non-zero exit (Dockerfile path wrong, deps unavailable, etc.)
**Secret risk:** NONE — build stage only, no env vars passed to `docker build`
**Forbidden file risk:** NONE — read-only (Docker reads files)

**Output file:** `PAL_STDIO_BUILD.log`

---

## Test 3: PAL Stdio With Stdin Attached

**Purpose:** Verify the container starts the stdio MCP loop and remains alive when stdin is kept open.

**Command (Python subprocess, -i flag = keep stdin pipe open):**
```python
import subprocess, time
cmd = ["docker", "run", "--rm", "-i", "--name", "pal-stdio-with-stdin-test", "dopemux-pal-stdio:pr854"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
time.sleep(5)
alive = p.poll() is None
# terminate for cleanup
p.terminate()
```

**Pass condition:** `alive_after_5s= True`
**Block condition:** `alive_after_5s= False` (exits before 5s when stdin held open)
**Secret risk:** NONE — no env vars passed to `docker run`; container has no API keys in this test
**Forbidden file risk:** NONE
**Cleanup:** container removed via `--rm` flag

**Output file:** `PAL_STDIO_WITH_STDIN.log`

---

## Test 4: PAL Stdio Without Stdin

**Purpose:** Capture behavior when no stdin is provided (simulates plain `docker run` without attachment).

**Command:**
```bash
timeout 10 docker run --rm --name pal-stdio-no-stdin-test dopemux-pal-stdio:pr854
# exit_code 124 = timeout (still running); other = exited
```

**Interpretation:**
- exit 124 → container still running after 10s → note as `NO_STDIN_RESULT=TIMEOUT_STILL_RUNNING`
- other exit → container exited → note as `NO_STDIN_RESULT=EXITED_EXPECTED_FOR_NO_STDIN`

**Note:** Quick exit here is expected for a readline-based stdio server. The compose restart behavior is what matters.
**Secret risk:** NONE — no env vars passed
**Forbidden file risk:** NONE

**Output file:** `PAL_STDIO_NO_STDIN.log`

---

## Test 5: Compose Restart-Loop Test

**Purpose:** Verify the `pal-stdio` service does NOT restart-loop under compose with `restart: unless-stopped`.

**Commands:**
```bash
docker compose build pal-stdio
docker compose up -d pal-stdio
sleep 15
CID=$(docker compose ps -q pal-stdio)
docker inspect "$CID" --format '...'
docker compose logs --no-color --tail=80 pal-stdio
docker compose stop pal-stdio
docker compose rm -f pal-stdio
```

**Pass condition:** `restart_count == 0` after 15 seconds
**Block condition:** `restart_count > 0` → `BLOCKED_RESTART_LOOP`
**Secret risk:** LOW — compose will pass env vars from shell environment (OPENAI_API_KEY, etc.). Since we're running in a dev environment, these may be set. However: (a) the server.py startup does NOT expose keys in stdout/logs under normal operation, and (b) we capture `--tail=80` of logs. **We will review log output for secret exposure before saving.** If API keys appear in logs, we truncate that section and note it.
**Forbidden file risk:** NONE — compose.yml is read-only, we don't edit it
**Cleanup:** `docker compose stop pal-stdio && docker compose rm -f pal-stdio`

**Output file:** `PAL_STDIO_COMPOSE_RESTART_TEST.log`

---

## Ordering
1. verify-pal.sh (fastest, structural)
2. Docker build (prerequisite for tests 3 + 4)
3. Stdin-attached test (uses just-built image)
4. No-stdin test (uses just-built image)
5. Compose restart test (separate build via compose, slowest, most uncertain)

## assumptions
- Docker daemon is running
- Internet access for package install during build (or cached layers exist)
- No other container named `pal-stdio-with-stdin-test` or `pal-stdio-no-stdin-test` or `mcp-pal-stdio` is running
- We will NOT read or print env var values — only inspect exit codes and structured output

## confidence
high

## verdict
PASS — plan is safe, avoids secrets, avoids forbidden files, all operations are reversible
