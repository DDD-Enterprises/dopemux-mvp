#!/usr/bin/env python3
"""
MCP Stdio to HTTP Bridge

Reads JSON-RPC messages from stdin and forwards them to an MCP HTTP endpoint.
Writes responses back to stdout.
"""
import sys
import json
import logging
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp-bridge")

def send_rpc_error(rpc_id: Optional[str], code: int, message: str, data: Optional[Any] = None):
    """Send a JSON-RPC error response to stdout."""
    error_obj = {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        },
        "id": rpc_id
    }
    if data:
        error_obj["error"]["data"] = data
    
    print(json.dumps(error_obj), flush=True)

def forward_request(base_url: str, request_data: Dict[str, Any], timeout: float = 30.0):
    """Forward JSON-RPC request to HTTP endpoint."""
    url = f"{base_url.rstrip('/')}/mcp"
    headers = {'Content-Type': 'application/json'}
    
    try:
        data = json.dumps(request_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                logger.error(f"HTTP Error {response.status}: {response.reason}")
                send_rpc_error(
                    request_data.get("id"), 
                    -32000, 
                    f"HTTP Error {response.status}: {response.reason}"
                )
                return

            response_data = response.read().decode('utf-8')
            # The MCP HTTP spec says the response body IS the JSON-RPC response
            # We just print it to stdout as a single line
            print(response_data.strip(), flush=True)
            
    except urllib.error.URLError as e:
        logger.error(f"Connection error to {url}: {e}")
        send_rpc_error(
            request_data.get("id"),
            -32000,
            f"Connection error: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        send_rpc_error(
            request_data.get("id"),
            -32603,
            f"Internal error: {e}"
        )

def main():
    parser = argparse.ArgumentParser(description="MCP Stdio to HTTP Bridge")
    parser.add_argument("--base-url", required=True, help="Base URL of the MCP server (e.g., http://localhost:3004)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    args = parser.parse_args()

    logger.info(f"Starting bridge to {args.base_url}")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                send_rpc_error(None, -32700, "Parse error")
                continue
                
            forward_request(args.base_url, request, args.timeout)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            break

if __name__ == "__main__":
    main()
