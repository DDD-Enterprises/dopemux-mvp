import re

with open("services/dopecon-bridge/dopecon_bridge/routes.py", "r") as f:
    content = f.read()

# using simpler replacement
start_marker = '@tasks_router.get("/next/{project_id}")'
end_marker = 'raise HTTPException(status_code=500, detail=str(e))'

idx_start = content.find(start_marker)
idx_end = content.find(end_marker, idx_start) + len(end_marker)

if idx_start != -1 and idx_end != -1:
    new_func = """@tasks_router.get("/next/{project_id}")
async def get_next_tasks(project_id: str, limit: int = Query(5, ge=1, le=20)):
    \"\"\"Get next actionable tasks for ADHD-friendly workflow via normalized PM-plane reads.\"\"\"
    from dopemux.pm.reads import pm_get_priority_queue
    
    try:
        result = await pm_get_priority_queue(project_id)
        
        return {
            "success": True,
            "project_id": project_id,
            "count": len(result.queue_items[:limit]),
            "tasks": result.queue_items[:limit]
        }
    except Exception as e:
        logger.error(f"Failed to get next tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))"""
        
    content = content[:idx_start] + new_func + content[idx_end:]

    with open("services/dopecon-bridge/dopecon_bridge/routes.py", "w") as f:
        f.write(content)
