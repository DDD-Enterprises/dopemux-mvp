#!/usr/bin/env python3
"""
MCP Tool Verification Script
Tests actual MCP tool calls to determine what works
"""

import requests
import json

def test_tool_call(server_url, tool_name, arguments=None, headers=None):
    """Test an MCP tool call"""
    if arguments is None:
        arguments = {}
    
    if headers is None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    payload = {
        "jsonrpc": "2.0",
        "method": tool_name,
        "params": arguments,
        "id": 1
    }
    
    try:
        response = requests.post(
            server_url,
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        
        return {
            "success": True,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def test_dope_context():
    """Test Dope-Context tools"""
    print("=" * 60)
    print("TESTING DOPE-CONTEXT (http://localhost:3010/mcp)")
    print("=" * 60)
    
    # Test get_index_status
    result = test_tool_call(
        "http://localhost:3010/mcp",
        "get_index_status",
        {}
    )
    
    print(f"Tool: get_index_status")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Status: {result['status_code']}")
        print(f"Response: {result['body'][:200]}...")
    else:
        print(f"Error: {result['error']}")
    print()

def test_pal():
    """Test PAL tools"""
    print("=" * 60)
    print("TESTING PAL (http://localhost:3003/mcp)")
    print("=" * 60)
    
    # Test list_models (common PAL tool)
    result = test_tool_call(
        "http://localhost:3003/mcp",
        "list_models",
        {}
    )
    
    print(f"Tool: list_models")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Status: {result['status_code']}")
        print(f"Response: {result['body'][:200]}...")
    else:
        print(f"Error: {result['error']}")
    print()

def test_serena():
    """Test Serena tools"""
    print("=" * 60)
    print("TESTING SERENA (http://localhost:3006/mcp)")
    print("=" * 60)
    
    # Serena requires session ID, so this will likely fail
    # but we can see the error format
    result = test_tool_call(
        "http://localhost:3006/mcp",
        "list_tools",
        {}
    )
    
    print(f"Tool: list_tools")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Status: {result['status_code']}")
        print(f"Response: {result['body'][:200]}...")
    else:
        print(f"Error: {result['error']}")
    print()

def test_conport():
    """Test ConPort tools"""
    print("=" * 60)
    print("TESTING CONPORT (http://localhost:3004/mcp)")
    print("=" * 60)
    
    # Try a generic tool call
    result = test_tool_call(
        "http://localhost:3004/mcp",
        "get_active_context",
        {}
    )
    
    print(f"Tool: get_active_context")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Status: {result['status_code']}")
        print(f"Response: {result['body'][:200]}...")
    else:
        print(f"Error: {result['error']}")
    print()

def test_dope_memory_rest():
    """Test Dope-Memory REST endpoints directly"""
    print("=" * 60)
    print("TESTING DOPE-MEMORY REST (http://localhost:8096/tools/)")
    print("=" * 60)
    
    # Test memory_recap endpoint
    try:
        response = requests.post(
            "http://localhost:8096/tools/memory_recap",
            json={
                "workspace_id": "default",
                "instance_id": "A",
                "scope": "today"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Endpoint: /tools/memory_recap")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    print("MCP Tool Verification Script")
    print("Testing actual MCP tool calls...")
    print()
    
    test_dope_context()
    test_pal()
    test_serena()
    test_conport()
    test_dope_memory_rest()
    
    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)