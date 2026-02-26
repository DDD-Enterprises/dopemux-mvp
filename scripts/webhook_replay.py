#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path


def _load_json(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _read_raw_payload(path: str) -> bytes:
    payload_path = Path(path)
    if not payload_path.is_file():
        raise FileNotFoundError(f"Missing payload file: {payload_path}")
    return payload_path.read_bytes()


def main() -> None:
    parser = argparse.ArgumentParser("webhook-replay")
    parser.add_argument("--provider", required=True, choices=["openai", "xai", "gemini"])
    parser.add_argument("--url", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--headers", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=10)
    args = parser.parse_args()

    headers = _load_json(args.headers)
    raw_body = _read_raw_payload(args.payload)
    req_headers = {str(k): str(v) for k, v in headers.items()}
    req_headers.setdefault("content-type", "application/json")
    request = urllib.request.Request(args.url, data=raw_body, headers=req_headers, method="POST")
    body_hash = hashlib.sha256(raw_body).hexdigest()
    try:
        with urllib.request.urlopen(request, timeout=max(1, int(args.timeout_seconds))) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = int(resp.status)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = int(exc.code)

    print(
        json.dumps(
            {
                "provider": args.provider,
                "url": args.url,
                "status": status,
                "response_body": body,
                "sent_headers": req_headers,
                "payload_bytes": len(raw_body),
                "payload_sha256": body_hash,
                "payload_path": str(Path(args.payload).resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
