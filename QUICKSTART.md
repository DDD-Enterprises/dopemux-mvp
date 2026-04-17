# ━━━◆ Ø ◆━━━

Status: [LIVE] Quick Start Ready

# Dopemux MVP Quick Start

This guide provides the shortest credible path to running the Dopemux multi-system stack locally. 

Because Dopemux is a composed workspace and not a single monolithic application, starting the stack involves spinning up a set of interacting services.

## Prerequisites

- Python 3.11+
- Node 18+ (for UI dashboards)
- Docker with `docker compose` (20.10+)
- `uv` (for fast Python dependency management)

## 1. Install and Initialize

Clone the repository and install core dependencies.

```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp

# Install CLI and dev dependencies
uv sync --frozen --extra dev
```

Generate workspace configurations:

```bash
python scripts/render_workspace_configs.py --set-default
source "$(python scripts/workspace_env_path.py)"
```

## 2. Start the Core Stack

Dopemux coordinates several background services (Postgres, Redis, ConPort, task-orchestrator, dopecon-bridge, adhd-engine, etc.). Start them using Docker Compose:

```bash
docker compose -f compose.yml up -d --build
```
*(If testing the ADHD-specific MVP inner loop, use `docker compose -f compose.adhd-stack.yml up -d --build`)*

**Verify Service Health:**

Ensure the core routing and authority services are reachable:

```bash
python tools/ports_health_audit.py --mode runtime --services conport,task-orchestrator,dopecon-bridge
```

## 3. Start the Control CLI

With the background systems running, use the `dopemux` CLI to engage with the workspace.

```bash
dopemux start
```

This command prepares your terminal context, aligns MCP server configurations (like Serena, Dope-Context), and updates your local `.claude.json` or `.dopemux/config.yaml` to route correctly.

## 4. Run the Dashboard UI (Optional)

The frontend UI is maintained separately from the core Python stack.

```bash
cd ui-dashboard
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

## 5. First Successful Checks

Verify that the PM and Memory planes are operating correctly.

**Check Bridge Routing (Requires dev token if auth is enabled):**
```bash
curl -i http://localhost:3316/health
```

**Check ConPort Semantic Retrieval Node:**
```bash
curl -i http://localhost:3304/health
```

**Emit a Workspace Switch Event (to test transport):**
```bash
docker compose exec workspace-watcher \
  python main.py \
  --emit-switch \
  --redis-url redis://redis:6379 \
  --from-app Terminal \
  --to-app "Claude Code" \
  --from-workspace /tmp/fake --to-workspace $(pwd)
```
You can verify the event flow by reading from the Redis stream `dopemux:events`.

## Common Failures

- **Ports already in use (e.g., 55432, 8000, 3316):** Ensure no other Postgres, task-orchestrator, or bridge instances are running locally.
- **"Task not routed" / 503 from Bridge:** The backend service (Leantime, ConPort, or task-orchestrator) is not healthy. Check `docker compose logs dopecon-bridge`.
- **ConPort Disconnected (`📴` in statusline):** Ensure `context_portal/context.db` exists and `mcp-conport` is running. Initialize it via: `mcp__conport__get_active_context --workspace_id $(pwd)`.

## Where To Go Next

- Review `ARCHITECTURE.md` to understand how authority is split across these services.
- Read `SERVICE_CATALOG.md` for a full inventory of the services running in the stack.
- Check `PM_PLANE.md` to understand where your project management data actually lives.
