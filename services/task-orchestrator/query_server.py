#!/usr/bin/env python3
"""
UNSUPPORTED RUNTIME: query_server.py

This Task Orchestrator runtime variant is no longer supported for PM-plane use.
All traffic must be routed to the canonical runtime in app/main.py (Port 8000).
"""

import sys

if __name__ == "__main__":
    print("FATAL: query_server.py is an unsupported runtime variant.")
    print("Please use the canonical Task Orchestrator runtime in app/main.py.")
    sys.exit(1)
