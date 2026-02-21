#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def _load_json(path: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser("webhook-replay")
    parser.add_argument("--provider", required=True, choices=["openai", "xai", "gemini"])
    parser.add_argument("--url", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--headers", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=10)
    args = parser.parse_args()

    payload = _load_json(args.payload)
    headers = _load_json(args.headers)
    raw_body = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    req_headers = {str(k): str(v) for k, v in headers.items()}
    req_headers.setdefault("content-type", "application/json")
    request = urllib.request.Request(args.url, data=raw_body, headers=req_headers, method="POST")
    with urllib.request.urlopen(request, timeout=max(1, int(args.timeout_seconds))) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        print(
            json.dumps(
                {
                    "provider": args.provider,
                    "url": args.url,
                    "status": int(resp.status),
                    "response_body": body,
                    "sent_headers": req_headers,
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
