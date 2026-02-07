"""
Semantic-search proxy helpers for dopecon-bridge.

Kept separate from main service wiring so fallback behavior can be unit-tested
without importing the full bridge runtime stack.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


async def run_semantic_search_with_fallback(
    *,
    session: Any,
    base_url: str,
    payload: Dict[str, Any],
    logger: Any,
) -> Dict[str, Any]:
    """
    Query ConPort semantic-search endpoints with compatibility fallback.

    Primary endpoint: `/api/adhd/semantic-search`
    Fallback endpoint: `/api/semantic-search` (only on 404/405 from primary)
    """
    endpoints = ["/api/adhd/semantic-search", "/api/semantic-search"]
    last_error: Optional[str] = None

    for index, endpoint in enumerate(endpoints):
        url = f"{base_url}{endpoint}"
        try:
            async with session.post(url, json=payload) as response:
                raw_text = await response.text()

                if response.status == 200:
                    if raw_text:
                        try:
                            body: Any = json.loads(raw_text)
                        except json.JSONDecodeError:
                            body = {"results": []}
                    else:
                        body = {"results": []}

                    if isinstance(body, list):
                        body = {"results": body}
                    elif not isinstance(body, dict):
                        body = {"results": []}

                    if "results" not in body and isinstance(body.get("result"), list):
                        body["results"] = body["result"]
                    body.setdefault("results", [])
                    body.setdefault("source", "conport")
                    body.setdefault("endpoint", endpoint)
                    return body

                # Only fallback on endpoint-not-found style responses
                if index == 0 and response.status in {404, 405}:
                    logger.warning(
                        "ConPort semantic search endpoint %s unavailable (%s); trying legacy endpoint",
                        endpoint,
                        response.status,
                    )
                    continue

                last_error = f"{endpoint} returned {response.status}: {raw_text}"
                break
        except Exception as exc:
            last_error = f"{endpoint} request error: {exc}"
            if index == 0:
                continue
            break

    raise RuntimeError(last_error or "ConPort semantic search failed")
