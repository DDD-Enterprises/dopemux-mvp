#!/usr/bin/env python3
"""
Fix MCP token limit issue by adding content truncation to docs_search.
"""

import re
from pathlib import Path

mcp_server_file = Path("/Users/hue/code/code-audit/services/dope-context/src/mcp/server.py")

# Read file
with open(mcp_server_file, 'r') as f:
    content = f.read()

# Patch 1: Add max_content_length to _docs_search_impl signature
old_impl_sig = """async def _docs_search_impl(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> List[Dict]:"""

new_impl_sig = """async def _docs_search_impl(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
    max_content_length: int = 2000,
) -> List[Dict]:"""

content = content.replace(old_impl_sig, new_impl_sig)

# Patch 2: Add truncation in return statement
old_return = """    return [
        {
            "source_path": r.file_path,
            "text": r.content,
            "score": r.score,
            "doc_type": r.payload.get("doc_type", "unknown"),
        }
        for r in results[:top_k]
    ]"""

new_return = """    return [
        {
            "source_path": r.file_path,
            "text": r.content[:max_content_length] + ("..." if len(r.content) > max_content_length else ""),
            "score": r.score,
            "doc_type": r.payload.get("doc_type", "unknown"),
            "truncated": len(r.content) > max_content_length,
            "original_length": len(r.content),
        }
        for r in results[:top_k]
    ]"""

content = content.replace(old_return, new_return)

# Patch 3: Update public docs_search function
old_public = """async def docs_search(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> List[Dict]:"""

new_public = """async def docs_search(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
    max_content_length: int = 2000,
) -> List[Dict]:"""

content = content.replace(old_public, new_public)

# Patch 4: Update docs_search call in docstring
old_call = """    return await _docs_search_impl(query, top_k, filter_doc_type, workspace_path)"""

new_call = """    return await _docs_search_impl(query, top_k, filter_doc_type, workspace_path, max_content_length)"""

content = content.replace(old_call, new_call)

# Patch 5: Update docs_search call in _search_all_impl
old_search_all_call = """    docs_results_task = _docs_search_impl(
        query, top_k // 2, workspace_path=str(workspace)
    )"""

new_search_all_call = """    docs_results_task = _docs_search_impl(
        query, top_k // 2, workspace_path=str(workspace), max_content_length=2000
    )"""

content = content.replace(old_search_all_call, new_search_all_call)

# Write patched file
with open(mcp_server_file, 'w') as f:
    f.write(content)

print("✅ Patched server.py with content truncation:")
print("   - Added max_content_length parameter (default 2000 chars)")
print("   - Truncates doc content with '...' indicator")
print("   - Adds 'truncated' and 'original_length' fields")
print()
print("🔄 Restart required: Restart Claude Code session to load updated MCP server")
