# trigger/run
Interact with **Trigger.dev** via its MCP server.

**Args**: `$ARGUMENTS` = `<TASK_NAME or ID> [:: JSON payload]`

**Steps**
1) Ensure Trigger.dev MCP is connected; if auth required, tell me to run `npx trigger.dev login`.
2) List tasks/projects, pick the best match for `<TASK_NAME>`.
3) If a payload is supplied, validate JSON; then trigger the task.
4) Show run URL and a short live summary (status/log tail if available).

**Tools**: trigger MCP only.
