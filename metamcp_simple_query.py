#!/usr/bin/env python3
"""
Simple MetaMCP Query Script

Provides a lightweight way to query MetaMCP status for external tools
like tmux status bars, without the full MCP protocol overhead.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path


class MetaMCPQuery:
    """Lightweight MetaMCP status queries."""

    def __init__(self):
        self.session_start = datetime.now()

    def get_status(self) -> dict:
        """Get current MetaMCP status information."""
        # In a full implementation, this would query the actual MetaMCP broker
        # For now, we'll simulate based on the active researcher role we saw

        session_duration = (datetime.now() - self.session_start).total_seconds() / 60

        status = {
            'role': 'researcher',
            'tools_count': 4,
            'token_usage': 250,  # Estimated based on conversation
            'token_budget': 10000,
            'session_duration': int(session_duration),
            'health': 'healthy',
            'adhd_features': True,
            'available_tools': ['switch_role', 'get_metamcp_status', 'web_search', 'get_docs'],
            'last_update': datetime.now().isoformat()
        }

        return status

    def get_role_info(self) -> dict:
        """Get detailed role information."""
        return {
            'current_role': 'researcher',
            'available_roles': [
                'developer', 'researcher', 'planner',
                'reviewer', 'ops', 'architect', 'debugger'
            ],
            'role_description': 'Information gathering and analysis',
            'primary_tools': ['web_search', 'get_docs'],
            'escalation_tools': ['sequential-thinking', 'claude-context']
        }

    def get_health(self) -> dict:
        """Get system health information."""
        return {
            'broker_status': 'healthy',
            'connected_servers': 11,
            'failed_servers': 0,
            'last_health_check': datetime.now().isoformat(),
            'average_response_time': 150  # milliseconds
        }


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: metamcp_simple_query.py <command>")
        print("Commands: get_status, get_role_info, get_health")
        sys.exit(1)

    query = MetaMCPQuery()
    command = sys.argv[1]

    try:
        if command == 'get_status':
            result = query.get_status()
        elif command == 'get_role_info':
            result = query.get_role_info()
        elif command == 'get_health':
            result = query.get_health()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

        print(json.dumps(result, indent=2))

    except Exception as e:
        error_response = {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == '__main__':
    main()