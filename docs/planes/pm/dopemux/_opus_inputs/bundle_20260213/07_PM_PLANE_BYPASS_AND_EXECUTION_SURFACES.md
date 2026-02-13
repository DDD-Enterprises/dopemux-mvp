# 07 PM Plane Bypass And Execution Surfaces

## Findings (severity-tagged)

| severity | surface | why this is a bypass/execution surface | evidence |
|---|---|---|---|
| **CRITICAL** | `POST /api/decompose` | PM plane endpoint triggers decomposition flow with PAL planner + ConPort persistence writes | `services/task-orchestrator/task_orchestrator/app.py:137-149` |
| **CRITICAL** | ConPort authority writes from decomposition path | updates parent status + creates subtasks + creates links (`DECOMPOSED_INTO`) | `services/task-orchestrator/task_decomposition_endpoint.py:195-229` |
| **RISK** | `POST /api/tools/{tool_name}` | exposes executable tool dispatch surface | `services/task-orchestrator/task_orchestrator/app.py:113-121`, `services/task-orchestrator/task_orchestrator/mcp/__init__.py:109-138` |
| **RISK** | LLM planner usage inside PM path | PAL client invokes planner with model `gemini-2.5-pro` | `services/task-orchestrator/pal_client.py:85-91`, `:163-169` |
| **RISK** | Tool endpoint returns `200` on logical tool errors | error payload path can be treated as success at HTTP layer | `services/task-orchestrator/task_orchestrator/app.py:122-128` |
| **RISK** | Adapter import/path drift risk | runtime imports `adapters.conport_adapter`, but only `app/adapters/conport_adapter.py` found in repo tree scan | `services/task-orchestrator/task_orchestrator/core.py:241-243` + filesystem scan |

## Tool execution surface (callable tools in this module)
- `analyze_dependencies`
- `batch_tasks`
- `get_adhd_state`
- `get_task_recommendations`
- `record_break`
- `get_agent_status`

## Evidence excerpts
- `services/task-orchestrator/task_orchestrator/app.py:113-121`
```text
@app.post("/api/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """Execute an MCP tool."""
    try:
        arguments = await request.json()
        logger.info(f"🔧 Executing tool: {tool_name}")

        result = await handle_tool_call(tool_name, arguments)
```
- `services/task-orchestrator/task_orchestrator/app.py:137-149`
```text
@app.post("/api/decompose", response_model=DecompositionResponse)
async def decompose_task(request: DecompositionRequest):
    """
    Decompose a complex task into ADHD-friendly micro-tasks.
    Called by ADHD Engine when automatic decomposition is triggered.

    Flow:
    1. Get task from internal storage
    2. Call Pal planner for AI decomposition
    3. Convert to OrchestrationTask objects
    4. Persist to ConPort (parent BLOCKED, subtasks TODO, DECOMPOSED_INTO links)
```
- `services/task-orchestrator/task_decomposition_endpoint.py:194-205`
```text
        # Update parent task status to BLOCKED
        await conport_adapter.update_progress_entry(
            entry_id=task.id,
            status="BLOCKED",
            metadata={
                'decomposed': True,
                'decomposition_method': request.method,
                'original_estimate': task.estimated_minutes,
                'num_subtasks': len(subtasks),
                'timestamp': datetime.now().isoformat()
            }
        )
```
- `services/task-orchestrator/task_decomposition_endpoint.py:208-229`
```text
        for subtask in subtasks:
            subtask_entry = await conport_adapter.create_progress_entry(
                workspace_id=workspace_id,
                description=subtask.description,
                status="TODO",
                metadata={
                    'parent_task_id': task.id,
                    'order': subtask.order,
                }
            )

            # Link to parent (DECOMPOSED_INTO relationship)
            await conport_adapter.link_items(
                source_item_type="progress_entry",
                source_item_id=task.id,
                target_item_type="progress_entry",
                target_item_id=subtask_entry['id'],
                relationship_type="DECOMPOSED_INTO"
            )
```
- `services/task-orchestrator/pal_client.py:85-91`
```text
                response = await self.planner(
                    step=planning_prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    model="gemini-2.5-pro"
                )
```
- `services/task-orchestrator/task_orchestrator/app.py:122-128`
```text
        if "error" in result:
            logger.warning(f"❌ Tool execution failed: {result['error']}")
            # We return 200 even on logical error to match MCP protocol behavior style,
            # but usually REST implies 4xx/5xx.
            # If result has "error", DopeconBridge might treat it as result.
            return result
```
- `services/task-orchestrator/task_orchestrator/core.py:239-243`
```text
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from adapters.conport_adapter import ConPortEventAdapter
        _conport_adapter = ConPortEventAdapter(workspace_id=settings.workspace_id)
```

Filesystem scan evidence (for this risk): `find services/task-orchestrator -maxdepth 3 -type d -name adapters` returned only `services/task-orchestrator/app/adapters`.
