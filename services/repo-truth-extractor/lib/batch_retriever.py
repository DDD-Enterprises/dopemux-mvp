#!/usr/bin/env python3
"""
OpenAI Batch Retrieval Module

This module provides functionality to retrieve OpenAI batch processing results
and integrate them with the webhook-based workflow.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .batch_clients import OpenAIBatchClient
except ImportError:
    from batch_clients import OpenAIBatchClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retrieve_openai_batch(
    api_key: str,
    batch_id: str,
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5
) -> Tuple[bool, Dict[str, Any]]:
    """
    Retrieve a single OpenAI batch and download its results.
    
    Args:
        api_key: OpenAI API key
        batch_id: Batch ID to retrieve
        output_dir: Directory to save output/error files
        max_retries: Maximum number of retries for failed downloads
        retry_delay: Delay between retries in seconds
        
    Returns:
        Tuple of (success, result_dict) where result_dict contains:
        - batch_id: The batch ID
        - status: Batch status
        - output_file: Path to output file if downloaded
        - error_file: Path to error file if downloaded
        - error: Error message if any
    """
    client = OpenAIBatchClient(api_key=api_key)
    result = {
        "batch_id": batch_id,
        "status": "unknown",
        "output_file": None,
        "error_file": None,
        "error": None
    }
    
    try:
        # Get batch information
        batch_info = client.get_batch_info(batch_id)
        status = batch_info["status"]
        result["status"] = status
        
        logger.info(f"Batch {batch_id}: status={status}")
        
        # Download output file if completed
        if status == "completed" and batch_info["output_file_id"]:
            for attempt in range(max_retries):
                try:
                    content = client._client.files.content(batch_info["output_file_id"])
                    output_path = output_dir / f"{batch_id}_output.jsonl"
                    
                    # Handle different response types
                    if hasattr(content, "read"):
                        output_path.write_bytes(content.read())
                    elif hasattr(content, "text"):
                        output_path.write_text(content.text, encoding="utf-8")
                    else:
                        output_path.write_text(str(content), encoding="utf-8")
                    
                    result["output_file"] = str(output_path)
                    logger.info(f"  ↓ Downloaded output to {output_path}")
                    break
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        result["error"] = f"Failed to download output after {max_retries} attempts: {e}"
                        logger.error(result["error"])
                    else:
                        time.sleep(retry_delay)
        
        # Download error file if failed or expired
        elif status in ("failed", "expired") and batch_info["error_file_id"]:
            for attempt in range(max_retries):
                try:
                    content = client._client.files.content(batch_info["error_file_id"])
                    error_path = output_dir / f"{batch_id}_error.jsonl"
                    
                    # Handle different response types
                    if hasattr(content, "read"):
                        error_path.write_bytes(content.read())
                    elif hasattr(content, "text"):
                        error_path.write_text(content.text, encoding="utf-8")
                    else:
                        error_path.write_text(str(content), encoding="utf-8")
                    
                    result["error_file"] = str(error_path)
                    logger.info(f"  ↓ Downloaded error to {error_path}")
                    break
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        result["error"] = f"Failed to download error file after {max_retries} attempts: {e}"
                        logger.error(result["error"])
                    else:
                        time.sleep(retry_delay)
        
        return True, result
        
    except Exception as e:
        result["error"] = f"Batch retrieval failed: {e}"
        logger.error(result["error"])
        return False, result


def retrieve_openai_batches(
    api_key: str,
    batch_ids: List[str],
    output_dir: Path,
    max_retries: int = 3,
    retry_delay: int = 5
) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve multiple OpenAI batches and download their results.
    
    Args:
        api_key: OpenAI API key
        batch_ids: List of batch IDs to retrieve
        output_dir: Directory to save output/error files
        max_retries: Maximum number of retries for failed downloads
        retry_delay: Delay between retries in seconds
        
    Returns:
        Dictionary mapping batch_id -> result_dict
    """
    output_dir.mkdir(exist_ok=True)
    results = {}
    
    for batch_id in batch_ids:
        success, result = retrieve_openai_batch(
            api_key, batch_id, output_dir, max_retries, retry_delay
        )
        results[batch_id] = result
    
    # Summary statistics
    completed = sum(1 for r in results.values() if r["status"] == "completed")
    failed = sum(1 for r in results.values() if r["status"] in ("failed", "expired"))
    errors = sum(1 for r in results.values() if r["error"])
    
    logger.info(f"\nBatch Retrieval Summary:")
    logger.info(f"  Completed: {completed}")
    logger.info(f"  Failed/Expired: {failed}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Total: {len(results)}")
    
    return results


def integrate_batch_results_with_webhook(
    batch_results: Dict[str, Dict[str, Any]],
    event_store: Any,
    run_id: str,
    phase: str,
    step_id: str,
    partition_id: str
) -> int:
    """
    Integrate retrieved batch results with the webhook event store.
    
    This function creates synthetic webhook events for completed batches
    so they can be processed by the existing webhook-based workflow.
    
    Args:
        batch_results: Dictionary of batch results from retrieve_openai_batches
        event_store: Webhook event store
        run_id: Run ID to associate with events
        phase: Phase ID
        step_id: Step ID
        partition_id: Partition ID
        
    Returns:
        Number of events successfully integrated
    """
    events_integrated = 0
    
    for batch_id, result in batch_results.items():
        status = result["status"]
        
        # Only create events for terminal states
        if status not in ("completed", "failed", "expired"):
            continue
        
        # Create synthetic webhook payload
        event_type = "batch.completed" if status == "completed" else "batch.failed"
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
            "provider": "openai",
            "provider_ref": batch_id,
        }
        
        try:
            # Insert webhook event
            inserted = event_store.insert_webhook_event_if_absent(
                provider="openai",
                idempotency_key=f"batch_{batch_id}",
                event_type=event_type,
                event_id=f"batch_{batch_id}",
                received_at_utc=result.get("completed_at", ""),
                payload_json=json.dumps(payload, ensure_ascii=True),
                headers_json="{}",
                signature_valid=True,
            )
            
            if inserted:
                # Create corresponding run event
                from ledger.interface import RunEventInsert
                
                webhook_event_id = None
                if hasattr(event_store, "fetch_webhook_event_id"):
                    webhook_event_id = event_store.fetch_webhook_event_id("openai", f"batch_{batch_id}")
                
                event_store.append_run_event(
                    RunEventInsert(
                        run_id=run_id,
                        phase=phase,
                        step_id=step_id,
                        partition_id=partition_id,
                        provider="openai",
                        event_type=event_type,
                        event_id=f"batch_{batch_id}",
                        provider_ref=batch_id,
                        webhook_event_id=webhook_event_id,
                        dedupe_key=f"batch_{batch_id}_{run_id}_{phase}_{step_id}_{partition_id}",
                        orphaned=False,
                    )
                )
                events_integrated += 1
                logger.info(f"Integrated batch {batch_id} as webhook event")
            else:
                logger.debug(f"Batch {batch_id} already processed (duplicate)")
                
        except Exception as e:
            logger.error(f"Failed to integrate batch {batch_id}: {e}")
    
    return events_integrated


def main() -> None:
    """Command-line interface for batch retrieval."""
    import argparse
    
    parser = argparse.ArgumentParser("OpenAI Batch Retriever")
    parser.add_argument("batch_ids", nargs="+", help="OpenAI batch IDs to retrieve")
    parser.add_argument("--output-dir", type=Path, default=Path("batch_downloads"),
                       help="Directory to save output files")
    parser.add_argument("--api-key-env", type=str, default="OPENAI_API_KEY",
                       help="Environment variable containing OpenAI API key")
    
    args = parser.parse_args()
    
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"ERROR: {args.api_key_env} environment variable not set")
        return 1
    
    results = retrieve_openai_batches(
        api_key=api_key,
        batch_ids=args.batch_ids,
        output_dir=args.output_dir
    )
    
    print(f"\nRetrieved {len(results)} batches")
    for batch_id, result in results.items():
        print(f"  {batch_id}: {result['status']}")
        if result['output_file']:
            print(f"    Output: {result['output_file']}")
        if result['error_file']:
            print(f"    Error: {result['error_file']}")
        if result['error']:
            print(f"    Error: {result['error']}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
