#!/usr/bin/env python3
"""
Test the /info endpoint for leantime-bridge
Verifies service discovery and auto-configuration support
"""

import json
import sys
import httpx

def test_info_endpoint():
    """Test /info endpoint structure and content"""
    url = "http://localhost:3015/info"
    
    print("=== Testing Leantime Bridge /info Endpoint ===")
    print(f"URL: {url}")
    print()
    
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        
        info = response.json()
        
        print("✅ /info endpoint accessible")
        print()
        print("Response:")
        print(json.dumps(info, indent=2))
        print()
        
        # Validate required fields
        required_fields = ["name", "version", "leantime", "mcp", "description"]
        missing = [f for f in required_fields if f not in info]
        
        if missing:
            print(f"❌ Missing required fields: {missing}")
            return False
        
        print("✅ All required fields present")
        
        # Validate leantime section
        if "leantime" in info:
            leantime = info["leantime"]
            print(f"\nLeantime Status:")
            print(f"  URL: {leantime.get('url', 'N/A')}")
            print(f"  Status: {leantime.get('status', 'N/A')}")
            print(f"  Rate Limit: {leantime.get('rate_limit_seconds', 'N/A')}s")
        
        # Validate MCP section
        if "mcp" in info:
            mcp = info["mcp"]
            print(f"\nMCP Configuration:")
            print(f"  Protocol: {mcp.get('protocol', 'N/A')}")
            if "endpoints" in mcp:
                print(f"  Endpoints:")
                for name, url in mcp["endpoints"].items():
                    print(f"    {name}: {url}")
        
        # Check metadata
        if "metadata" in info:
            meta = info["metadata"]
            print(f"\nMetadata:")
            print(f"  Role: {meta.get('role', 'N/A')}")
            print(f"  Priority: {meta.get('priority', 'N/A')}")
            print(f"  Plane: {meta.get('plane', 'N/A')}")
            print(f"  Tools: {meta.get('tools_count', 'N/A')}")
        
        print("\n✅ All tests passed!")
        return True
        
    except httpx.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_info_endpoint()
    sys.exit(0 if success else 1)
