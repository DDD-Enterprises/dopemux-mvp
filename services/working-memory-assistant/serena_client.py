#!/usr/bin/env python3
"""
Working Memory Assistant - Serena LSP Client
Integrates with Serena MCP for code navigation context capture and restoration.
"""

import os

import logging

logger = logging.getLogger(__name__)

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

class SerenaClient:
    \"\"\"
    Client for Serena LSP integration with Working Memory Assistant.
    Captures code navigation context, cursor positions, and file state.
    \"\"\"

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or "http://localhost:3005"  # Default Serena port
        self.api_key = api_key or os.getenv('SERENA_API_KEY', '')
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def capture_code_context(self, file_path: str, cursor_line: int = None, cursor_column: int = None) -> Optional[Dict[str, Any]]:
        \"\"\"
        Capture comprehensive code context for a file including LSP information.

        Args:
            file_path: Absolute path to the file
            cursor_line: Current cursor line (0-based)
            cursor_column: Current cursor column (0-based)

        Returns:
            Code context with LSP information
        \"\"\"
        try:
            payload = {
                \"file_path\": file_path,
                \"cursor_line\": cursor_line,
                \"cursor_column\": cursor_column,
                \"include_context\": True,
                \"include_symbols\": True,
                \"include_references\": False  # Too heavy for snapshots
            }

            response = await self.client.post(f\"{self.base_url}/lsp/context\", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f\"Serena context capture failed: {e}\")
            # Return basic fallback context
            return {
                \"file_path\": file_path,
                \"cursor_position\": {\"line\": cursor_line, \"column\": cursor_column},
                \"fallback\": True,
                \"error\": str(e)
            }

    async def get_file_symbols(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        \"\"\"Get symbols (functions, classes, variables) in a file\"\"\"
        try:
            response = await self.client.get(f\"{self.base_url}/lsp/symbols\", params={\"file_path\": file_path})
            response.raise_for_status()
            return response.json().get(\"symbols\", [])
        except Exception as e:
            logger.error(f\"Serena symbols retrieval failed: {e}\")
            return []

    async def get_navigation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        \"\"\"Get recent navigation history for user\"\"\"
        try:
            response = await self.client.get(f\"{self.base_url}/navigation/history/{user_id}\",
                                           params={\"limit\": limit})
            response.raise_for_status()
            return response.json().get(\"history\", [])
        except Exception as e:
            logger.error(f\"Serena navigation history failed: {e}\")
            return []

    async def analyze_code_complexity(self, file_path: str, code_snippet: str = None) -> Optional[Dict[str, Any]]:
        \"\"\"Analyze code complexity using Serena's LSP analysis\"\"\"
        try:
            payload = {
                \"file_path\": file_path,
                \"code_snippet\": code_snippet
            }
            response = await self.client.post(f\"{self.base_url}/analysis/complexity\", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f\"Serena complexity analysis failed: {e}\")
            return None

    async def find_similar_code(self, query: str, file_path: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        \"\"\"Find similar code patterns using semantic search\"\"\"
        try:
            payload = {
                \"query\": query,
                \"file_path\": file_path,
                \"limit\": limit
            }
            response = await self.client.post(f\"{self.base_url}/search/similar\", json=payload)
            response.raise_for_status()
            return response.json().get(\"results\", [])
        except Exception as e:
            logger.error(f\"Serena similar code search failed: {e}\")
            return []

    async def get_project_structure(self, project_root: str) -> Optional[Dict[str, Any]]:
        \"\"\"Get project structure and file relationships\"\"\"
        try:
            response = await self.client.get(f\"{self.base_url}/project/structure\",
                                           params={\"root_path\": project_root})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f\"Serena project structure failed: {e}\")
            return None

# Global client instance
_serena_client = None

def get_serena_client() -> SerenaClient:
    \"\"\"Get global Serena client instance\"\"\"
    global _serena_client
    if _serena_client is None:
        _serena_client = SerenaClient()
    return _serena_client

async def close_serena_client():
    \"\"\"Close global Serena client\"\"\"
    global _serena_client
    if _serena_client:
        await _serena_client.client.aclose()
        _serena_client = None

# Integration functions for WMA
async def capture_serena_context_for_snapshot(user_id: str, file_path: str = None, cursor_line: int = None, cursor_column: int = None) -> Dict[str, Any]:
    \"\"\"
    Capture Serena LSP context for WMA snapshot creation.
    Returns comprehensive code context including cursor position, symbols, and navigation state.
    \"\"\"
    client = get_serena_client()

    # Get current file context if available
    code_context = None
    if file_path:
        code_context = await client.capture_code_context(file_path, cursor_line, cursor_column)

    # Get recent navigation history
    nav_history = await client.get_navigation_history(user_id, limit=5)

    # Get file symbols if we have a file
    symbols = []
    if file_path:
        symbols = await client.get_file_symbols(file_path)

    serena_context = {
        \"captured_at\": datetime.now().isoformat(),
        \"code_context\": code_context,
        \"navigation_history\": nav_history,
        \"file_symbols\": symbols,
        \"available\": code_context is not None
    }

    return serena_context

async def enhance_snapshot_with_serena(snapshot: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    \"\"\"
    Enhance a WMA snapshot with Serena LSP context.
    Adds code navigation state, cursor positions, and symbol information.
    \"\"\"
    try:
        # Extract file information from snapshot
        active_focus = snapshot.get('active_focus', {})
        file_path = active_focus.get('file')
        cursor_pos = active_focus.get('cursor', {})

        # Capture Serena context
        serena_context = await capture_serena_context_for_snapshot(
            user_id=user_id,
            file_path=file_path,
            cursor_line=cursor_pos.get('line'),
            cursor_column=cursor_pos.get('column')
        )

        # Add Serena context to snapshot metadata
        if 'metadata' not in snapshot:
            snapshot['metadata'] = {}
        snapshot['metadata']['serena_context'] = serena_context

        logger.info(f"Enhanced snapshot with Serena context: {len(serena_context)} items captured")

    except Exception as e:
        logger.error(f"Serena snapshot enhancement failed: {e}")
        # Continue without Serena enhancement

    return snapshot

async def restore_serena_context(serena_context: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Restore code navigation context using Serena data.
    Provides information for cursor positioning and file state restoration.
    \"\"\"
    restoration_info = {
        \"cursor_restoration\": {},
        \"file_state\": {},
        \"navigation_suggestions\": [],
        \"available\": False
    }

    try:
        if not serena_context or not serena_context.get('available'):
            return restoration_info

        code_context = serena_context.get('code_context', {})
        nav_history = serena_context.get('navigation_history', [])

        # Extract cursor position for restoration
        if code_context and 'cursor_position' in code_context:
            cursor = code_context['cursor_position']
            restoration_info['cursor_restoration'] = {
                'file': code_context.get('file_path'),
                'line': cursor.get('line'),
                'column': cursor.get('column')
            }

        # Provide navigation suggestions from history
        restoration_info['navigation_suggestions'] = [
            {
                'file': item.get('file_path'),
                'description': f"Previously viewed: {item.get('file_path')}"
            } for item in nav_history[:3]  # Top 3 recent files
        ]

        restoration_info['available'] = True

    except Exception as e:
        logger.error(f"Serena context restoration failed: {e}")

    return restoration_info