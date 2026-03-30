#!/usr/bin/env python3
"""Provider-aware batch retrieval and webhook integration helpers."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from .batch_clients import (
        BatchResult,
        GeminiBatchClient,
        OpenAIBatchClient,
        UnsupportedBatchProvider,
        XAIBatchClient,
    )
except ImportError:
    from batch_clients import (  # type: ignore
        BatchResult,
        GeminiBatchClient,
        OpenAIBatchClient,
        UnsupportedBatchProvider,
        XAIBatchClient,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_COMPATIBLE_PROVIDERS = {"openai", "xai"}
SUPPORTED_RETRIEVAL_PROVIDERS = OPENAI_COMPATIBLE_PROVIDERS | {"gemini"}
TERMINAL_BATCH_STATES = {
    "completed",
    "succeeded",
    "done",
    "failed",
    "expired",
    "cancelled",
    "canceled",
    "timeout",
}


def _normalize_provider(provider: str) -> str:
    normalized = str(provider or "").strip().lower()
    if normalized not in SUPPORTED_RETRIEVAL_PROVIDERS:
        raise UnsupportedBatchProvider(
            "OpenRouter is not supported for live batch execution. Use openai, gemini, or xai. "
            "OpenRouter remains available for sync routing."
            if normalized == "openrouter"
            else f"Unsupported batch provider: {provider}"
        )
    return normalized


def _build_retrieval_client(provider: str, api_key: str):
    provider_id = _normalize_provider(provider)
    if provider_id == "openai":
        return OpenAIBatchClient(api_key=api_key)
    if provider_id == "xai":
        return XAIBatchClient(api_key=api_key)
    if provider_id == "gemini":
        return GeminiBatchClient(api_key=api_key)
    raise UnsupportedBatchProvider(f"Unsupported batch provider: {provider}")


def _read_content_as_text(content: Any) -> str:
    if hasattr(content, "text"):
        return str(content.text)
    if hasattr(content, "read"):
        value = content.read()
        if isinstance(value, (bytes, bytearray)):
            return value.decode("utf-8", errors="replace")
        return str(value)
    return str(content)


def _download_openai_compatible_file(
    client: OpenAIBatchClient,
    file_id: str,
    destination: Path,
    *,
    max_retries: int,
    retry_delay: int,
) -> str:
    last_error = ""
    for attempt in range(max_retries):
        try:
            content = client._client.files.content(file_id)  # type: ignore[attr-defined]
            destination.write_text(_read_content_as_text(content), encoding="utf-8")
            return ""
        except Exception as exc:  # pragma: no cover - defensive transport errors
            last_error = str(exc)
            if attempt == max_retries - 1:
                break
            time.sleep(retry_delay)
    return last_error or "download_failed"


def _serialize_batch_results(results: List[BatchResult]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for row in results:
        payload.append(
            {
                "custom_id": row.custom_id,
                "output_text": row.output_text,
                "error": row.error,
                "meta": row.meta,
            }
        )
    return payload


def retrieve_openai_compatible_batch(
    provider: str,
    api_key: str,
    batch_id: str,
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    provider_id = _normalize_provider(provider)
    client = _build_retrieval_client(provider_id, api_key)
    assert isinstance(client, OpenAIBatchClient)
    result: Dict[str, Any] = {
        "batch_id": batch_id,
        "provider": provider_id,
        "status": "unknown",
        "output_file": None,
        "error_file": None,
        "error": None,
        "results": [],
    }

    try:
        batch_info = client.get_batch_info(batch_id)
        status = str(batch_info.get("status") or "unknown").lower()
        result["status"] = status
        result["created_at"] = batch_info.get("created_at")
        result["completed_at"] = batch_info.get("completed_at")
        result["failed_at"] = batch_info.get("failed_at")
        result["expired_at"] = batch_info.get("expired_at")
        logger.info("Batch %s (%s): status=%s", batch_id, provider_id, status)

        output_file_id = str(batch_info.get("output_file_id") or "")
        error_file_id = str(batch_info.get("error_file_id") or "")

        if status in {"completed", "succeeded", "done"}:
            results = client.fetch_results(batch_id)
            result["results"] = _serialize_batch_results(results)
            if output_file_id:
                output_path = output_dir / f"{batch_id}_output.jsonl"
                download_error = _download_openai_compatible_file(
                    client,
                    output_file_id,
                    output_path,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                )
                if download_error:
                    result["error"] = (
                        f"Failed to download output after {max_retries} attempts: {download_error}"
                    )
                else:
                    result["output_file"] = str(output_path)
        elif status in {"failed", "expired", "cancelled", "canceled", "timeout"} and error_file_id:
            error_path = output_dir / f"{batch_id}_error.jsonl"
            download_error = _download_openai_compatible_file(
                client,
                error_file_id,
                error_path,
                max_retries=max_retries,
                retry_delay=retry_delay,
            )
            if download_error:
                result["error"] = (
                    f"Failed to download error after {max_retries} attempts: {download_error}"
                )
            else:
                result["error_file"] = str(error_path)
        return True, result
    except Exception as exc:
        result["error"] = f"Batch retrieval failed: {exc}"
        logger.error("%s", result["error"])
        return False, result


def retrieve_gemini_batch(
    api_key: str,
    batch_id: str,
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    del max_retries, retry_delay
    client = GeminiBatchClient(api_key=api_key)
    result: Dict[str, Any] = {
        "batch_id": batch_id,
        "provider": "gemini",
        "status": "unknown",
        "output_file": None,
        "error_file": None,
        "error": None,
        "results": [],
    }
    try:
        status = str(client.poll(batch_id) or "unknown").lower()
        result["status"] = status
        logger.info("Batch %s (gemini): status=%s", batch_id, status)
        if status in {"completed", "succeeded", "done"}:
            results = client.fetch_results(batch_id)
            result["results"] = _serialize_batch_results(results)
            output_path = output_dir / f"{batch_id}_output.json"
            output_path.write_text(
                json.dumps({"provider": "gemini", "batch_id": batch_id, "results": result["results"]}, indent=2, ensure_ascii=True)
                + "\n",
                encoding="utf-8",
            )
            result["output_file"] = str(output_path)
        elif status in {"failed", "expired", "cancelled", "canceled", "timeout"}:
            error_path = output_dir / f"{batch_id}_error.json"
            error_path.write_text(
                json.dumps({"provider": "gemini", "batch_id": batch_id, "status": status}, indent=2, ensure_ascii=True)
                + "\n",
                encoding="utf-8",
            )
            result["error_file"] = str(error_path)
        return True, result
    except Exception as exc:
        result["error"] = f"Batch retrieval failed: {exc}"
        logger.error("%s", result["error"])
        return False, result


def retrieve_batch(
    provider: str,
    api_key: str,
    batch_id: str,
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    provider_id = _normalize_provider(provider)
    if provider_id == "gemini":
        return retrieve_gemini_batch(
            api_key=api_key,
            batch_id=batch_id,
            output_dir=output_dir,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
    return retrieve_openai_compatible_batch(
        provider=provider_id,
        api_key=api_key,
        batch_id=batch_id,
        output_dir=output_dir,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )


def retrieve_batches(
    provider: str,
    api_key: str,
    batch_ids: List[str],
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Dict[str, Dict[str, Any]]:
    provider_id = _normalize_provider(provider)
    output_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Dict[str, Any]] = {}
    for batch_id in batch_ids:
        _success, result = retrieve_batch(
            provider=provider_id,
            api_key=api_key,
            batch_id=batch_id,
            output_dir=output_dir,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        results[batch_id] = result

    completed = sum(1 for row in results.values() if row.get("status") in {"completed", "succeeded", "done"})
    failed = sum(1 for row in results.values() if row.get("status") in {"failed", "expired", "cancelled", "canceled", "timeout"})
    errors = sum(1 for row in results.values() if row.get("error"))
    logger.info("\nBatch Retrieval Summary (%s):", provider_id)
    logger.info("  Completed: %s", completed)
    logger.info("  Failed/Expired: %s", failed)
    logger.info("  Errors: %s", errors)
    logger.info("  Total: %s", len(results))
    return results


def retrieve_openai_batch(
    api_key: str,
    batch_id: str,
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    return retrieve_openai_compatible_batch("openai", api_key, batch_id, output_dir, max_retries, retry_delay)


def retrieve_openai_batches(
    api_key: str,
    batch_ids: List[str],
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Dict[str, Dict[str, Any]]:
    return retrieve_batches("openai", api_key, batch_ids, output_dir, max_retries, retry_delay)


def retrieve_xai_batch(
    api_key: str,
    batch_id: str,
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    return retrieve_openai_compatible_batch("xai", api_key, batch_id, output_dir, max_retries, retry_delay)


def retrieve_xai_batches(
    api_key: str,
    batch_ids: List[str],
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Dict[str, Dict[str, Any]]:
    return retrieve_batches("xai", api_key, batch_ids, output_dir, max_retries, retry_delay)


def retrieve_gemini_batches(
    api_key: str,
    batch_ids: List[str],
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> Dict[str, Dict[str, Any]]:
    return retrieve_batches("gemini", api_key, batch_ids, output_dir, max_retries, retry_delay)


def integrate_batch_results_with_webhook(
    batch_results: Dict[str, Dict[str, Any]],
    event_store: Any,
    run_id: str,
    phase: str,
    step_id: str,
    partition_id: str,
    provider: str = "openai",
) -> int:
    events_integrated = 0
    provider_id = str(provider or "openai").strip().lower()
    for batch_id, result in batch_results.items():
        status = str(result.get("status") or "").strip().lower()
        if status not in TERMINAL_BATCH_STATES:
            continue

        event_type = "batch.completed" if status in {"completed", "succeeded", "done"} else "batch.failed"
        payload = {
            "schema": "DPMX_WEBHOOK_V1",
            "event": event_type,
            "event_id": f"batch_{batch_id}",
            "run_id": run_id,
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
            "batch_id": batch_id,
            "status": status,
            "generated_at_utc": result.get("completed_at", ""),
            "provider": provider_id,
            "provider_ref": batch_id,
        }

        try:
            inserted = event_store.insert_webhook_event_if_absent(
                provider=provider_id,
                idempotency_key=f"batch_{batch_id}",
                event_type=event_type,
                event_id=f"batch_{batch_id}",
                received_at_utc=result.get("completed_at", ""),
                payload_json=json.dumps(payload, ensure_ascii=True),
                headers_json="{}",
                signature_valid=True,
            )
            if inserted:
                from ledger.interface import RunEventInsert

                webhook_event_id = None
                if hasattr(event_store, "fetch_webhook_event_id"):
                    webhook_event_id = event_store.fetch_webhook_event_id(provider_id, f"batch_{batch_id}")
                event_store.append_run_event(
                    RunEventInsert(
                        run_id=run_id,
                        phase=phase,
                        step_id=step_id,
                        partition_id=partition_id,
                        provider=provider_id,
                        event_type=event_type,
                        event_id=f"batch_{batch_id}",
                        provider_ref=batch_id,
                        webhook_event_id=webhook_event_id,
                        dedupe_key=f"batch_{batch_id}_{run_id}_{phase}_{step_id}_{partition_id}",
                        orphaned=False,
                    )
                )
                events_integrated += 1
                logger.info("Integrated batch %s as webhook event", batch_id)
        except Exception as exc:
            logger.error("Failed to integrate batch %s: %s", batch_id, exc)
    return events_integrated


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser("Batch Retriever")
    parser.add_argument("batch_ids", nargs="+", help="Batch IDs to retrieve")
    parser.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_RETRIEVAL_PROVIDERS),
        default="openai",
        help="Live batch provider to retrieve from.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("batch_downloads"), help="Directory to save output files")
    parser.add_argument("--api-key-env", type=str, default=None, help="Environment variable containing the provider API key")
    args = parser.parse_args()

    default_env = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "xai": "XAI_API_KEY",
    }[args.provider]
    api_key_env = args.api_key_env or default_env
    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(f"ERROR: {api_key_env} environment variable not set")
        return 1

    try:
        results = retrieve_batches(
            provider=args.provider,
            api_key=api_key,
            batch_ids=args.batch_ids,
            output_dir=args.output_dir,
        )
    except UnsupportedBatchProvider as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"\nRetrieved {len(results)} batches from {args.provider}")
    for batch_id, result in results.items():
        print(f"  {batch_id}: {result['status']}")
        if result.get("output_file"):
            print(f"    Output: {result['output_file']}")
        if result.get("error_file"):
            print(f"    Error: {result['error_file']}")
        if result.get("error"):
            print(f"    Error: {result['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
