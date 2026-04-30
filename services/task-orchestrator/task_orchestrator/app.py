"""
UNSUPPORTED RUNTIME: task_orchestrator/app.py

This Task Orchestrator runtime variant is no longer supported for PM-plane use.
All traffic must be routed to the canonical runtime in app/main.py (Port 8000).
"""

import sys

def _hard_fail():
    print("FATAL: task_orchestrator/app.py is an unsupported runtime variant.")
    print("Please use the canonical Task Orchestrator runtime in app/main.py.")
    sys.exit(1)

_hard_fail()
