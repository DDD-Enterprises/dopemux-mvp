#!/usr/bin/env python3
"""Local webhook receiver for runner webhook testing.

Usage:
  python tools/webhook_receiver.py --port 8787 --out webhook_events
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict


class ReceiverHandler(BaseHTTPRequestHandler):
    def _write(self, status: int, payload: Dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/healthz":
            self._write(HTTPStatus.OK, {"status": "ok"})
            return
        self._write(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(max(0, length))
        payload: Dict[str, Any]
        try:
            payload = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            payload = {"raw": raw.decode("utf-8", errors="replace")}

        event_id = str(payload.get("event_id") or "evt_no_id")
        target = self.server.output_dir / f"{event_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"headers": dict(self.headers.items()), "payload": payload}, indent=2, sort_keys=True), encoding="utf-8")
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._write(HTTPStatus.OK, {"status": "received", "event_id": event_id, "received_at_utc": ts})

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        return


class ReceiverServer(ThreadingHTTPServer):
    def __init__(self, host: str, port: int, output_dir: Path) -> None:
        super().__init__((host, port), ReceiverHandler)
        self.output_dir = output_dir


def main() -> None:
    parser = argparse.ArgumentParser("Local webhook receiver")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--out", type=Path, default=Path("webhook_events"))
    args = parser.parse_args()

    server = ReceiverServer(args.host, args.port, args.out)
    print(f"Listening on http://{args.host}:{args.port} writing to {args.out}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
