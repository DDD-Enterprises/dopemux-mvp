#!/usr/bin/env python3
"""Bridge stdio JSON-RPC traffic to an MCP HTTP endpoint."""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
import urllib.error
import urllib.request
from json import JSONDecodeError
from typing import Any, Dict, Optional


JSONRPC_VERSION = "2.0"
PARSE_ERROR_CODE = -32700
INVALID_REQUEST_CODE = -32600
INTERNAL_ERROR_CODE = -32603
SERVER_ERROR_CODE = -32000
DEFAULT_TIMEOUT = 30.0

logger = logging.getLogger(__name__)


def _jsonrpc_error(
    request_id: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    if data:
        payload["error"]["data"] = data
    return payload


def _write_stdout(payload: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _resolve_timeout(cli_timeout: Optional[float]) -> float:
    if cli_timeout is not None:
        return cli_timeout

    raw_timeout = os.getenv("DOPEMUX_MCP_BRIDGE_TIMEOUT")
    if not raw_timeout:
        return DEFAULT_TIMEOUT

    try:
        parsed = float(raw_timeout)
    except ValueError:
        return DEFAULT_TIMEOUT

    return parsed if parsed > 0 else DEFAULT_TIMEOUT


def _forward_request(base_url: str, request_data: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}/mcp"
    request_body = json.dumps(request_data).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=request_body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8").strip()
    except urllib.error.HTTPError as exc:
        detail = ""
        if exc.fp is not None:
            detail = exc.fp.read().decode("utf-8", errors="replace").strip()
        message = f"HTTP {exc.code} from MCP endpoint"
        if detail:
            message = f"{message}: {detail[:400]}"
        raise RuntimeError(message) from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            raise RuntimeError(f"Timeout contacting MCP endpoint after {timeout}s") from exc
        raise RuntimeError(f"Connection error to MCP endpoint: {reason}") from exc
    except socket.timeout as exc:
        raise RuntimeError(f"Timeout contacting MCP endpoint after {timeout}s") from exc

    if not body:
        raise RuntimeError("Empty response body from MCP endpoint")

    try:
        parsed = json.loads(body)
    except JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from MCP endpoint: {body[:200]}") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Invalid MCP response payload: expected JSON object")

    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge stdio JSON-RPC to MCP HTTP")
    parser.add_argument("--base-url", required=True, help="MCP server base URL (for example: http://localhost:3004)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="HTTP timeout in seconds (defaults to DOPEMUX_MCP_BRIDGE_TIMEOUT or 30)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    timeout = _resolve_timeout(args.timeout)

    while True:
        line = sys.stdin.readline()
        if line == "":
            return 0

        line = line.strip()
        if not line:
            continue

        request_id: Any = None
        try:
            request_data = json.loads(line)
        except JSONDecodeError:
            _write_stdout(_jsonrpc_error(None, PARSE_ERROR_CODE, "Parse error"))
            continue

        if not isinstance(request_data, dict):
            _write_stdout(_jsonrpc_error(None, INVALID_REQUEST_CODE, "Invalid Request"))
            continue

        request_id = request_data.get("id")
        try:
            response = _forward_request(args.base_url, request_data, timeout)
        except Exception as exc:
            logger.debug("Bridge forward error", exc_info=True)
            _write_stdout(
                _jsonrpc_error(
                    request_id,
                    SERVER_ERROR_CODE,
                    "Bridge transport error",
                    {"detail": str(exc)},
                )
            )
            continue

        _write_stdout(response)


if __name__ == "__main__":
    raise SystemExit(main())
