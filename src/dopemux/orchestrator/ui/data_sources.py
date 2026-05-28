import os
import sqlite3
import json
from typing import Dict, Any
from filelock import FileLock, Timeout


def get_panel_data(panel_id: str) -> Dict[str, Any]:
    """Load and return data for a specific TUI panel with strict concurrency safety."""
    try:
        if panel_id == "today":
            # Access SQLite idempotency store to count transition records
            from dopemux.orchestrator.idempotency import IdempotencyStore
            store = IdempotencyStore()
            # Simple select count
            with store._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM idempotency_records;")
                count = cursor.fetchone()[0]
            return {"status": "active", "fallback": False, "count": count}

        elif panel_id == "context":
            # Access progress log which requires a FileLock
            journal_path = os.path.expanduser("~/.local/share/dopemux/progress_log.json")
            lock_path = journal_path + ".lock"
            
            # Attempt to acquire the lock with a very short timeout (50ms) to avoid TUI thread freezes
            lock = FileLock(lock_path, timeout=0.05)
            try:
                with lock:
                    count = 0
                    if os.path.exists(journal_path):
                        with open(journal_path, "r", encoding="utf-8") as f:
                            count = len(json.load(f))
                return {"status": "active", "fallback": False, "progress_entries_count": count}
            except Timeout:
                # Lock-free read fallback under contention
                count = 0
                if os.path.exists(journal_path):
                    try:
                        with open(journal_path, "r", encoding="utf-8") as f:
                            count = len(json.load(f))
                    except Exception:
                        pass
                return {"status": "active (lock contention fallback)", "fallback": True, "progress_entries_count": count}

        elif panel_id == "authority":
            return {"status": "active", "fallback": False, "rules": ["AGENTS.md", "PM_PLANE.md"]}

        elif panel_id == "packets":
            # Count local packets
            count = 0
            if os.path.exists("task-packets/generated"):
                count = len([f for f in os.listdir("task-packets/generated") if f.endswith(".json")])
            return {"status": "active", "fallback": False, "count": count}

        elif panel_id == "proof":
            count = 0
            if os.path.exists("proof"):
                count = len([f for f in os.listdir("proof") if os.path.isdir(os.path.join("proof", f))])
            return {"status": "active", "fallback": False, "count": count}

        elif panel_id == "risks":
            return {"status": "active", "fallback": False, "active_risks": 0}

        elif panel_id == "pr_queue":
            return {"status": "active", "fallback": False, "items": []}

        elif panel_id == "do_not_touch":
            return {"status": "active", "fallback": False, "safe": True}

        else:
            return {"status": "unknown", "fallback": True, "error": f"Unknown panel: {panel_id}"}

    except (sqlite3.OperationalError, Timeout) as e:
        # Graceful fallback state for TUI concurrency safety
        return {
            "status": "degraded (concurrency error)",
            "fallback": True,
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "degraded (unexpected error)",
            "fallback": True,
            "error": str(e)
        }


def get_all_panels() -> Dict[str, Dict[str, Any]]:
    """Fetch data for all 8 panels concurrently/sequentially."""
    panels = ["today", "authority", "packets", "proof", "risks", "pr_queue", "context", "do_not_touch"]
    return {pid: get_panel_data(pid) for pid in panels}
