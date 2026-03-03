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
    client = OpenAIBatchClient(api_key)
    
    try:
        # Check status
        status = client.poll(batch_id)
        result = {
            "batch_id": batch_id,
            "status": status,
            "output_file": None,
            "error_file": None,
            "error": None,
            "completed_at": "",
        }
        
        if status == "completed":
            # Fetch results
            batch_info = client.get_batch(batch_id)
            result["completed_at"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(batch_info.get("completed_at", time.time())))
            
            output_file_id = batch_info.get("output_file_id")
            if output_file_id:
                output_path = output_dir / f"{batch_id}_output.jsonl"
                if client.download_file(output_file_id, output_path):
                    result["output_file"] = str(output_path)
            
            error_file_id = batch_info.get("error_file_id")
            if error_file_id:
                error_path = output_dir / f"{batch_id}_errors.jsonl"
                if client.download_file(error_file_id, error_path):
                    result["error_file"] = str(error_path)
                    
            return True, result
            
        elif status in ("failed", "expired", "cancelled"):
            batch_info = client.get_batch(batch_id)
            result["error"] = f"Batch failed with status: {status}"
            if "errors" in batch_info:
                result["error"] = json.dumps(batch_info["errors"])
            return False, result
            
        else:
            return False, result
            
    except Exception as e:
        logger.error(f"Error retrieving batch {batch_id}: {e}")
        return False, {"batch_id": batch_id, "status": "error", "error": str(e)}


def retrieve_openai_batches(
    api_key: str,
    batch_ids: List[str],
    output_dir: Path
) -> Dict[str, Dict[str, Any]]:
    """Retrieve multiple OpenAI batches."""
    results = {}
    for batch_id in batch_ids:
        _, result = retrieve_openai_batch(api_key, batch_id, output_dir)
        results[batch_id] = result
    return results


def retrieve_gemini_batches(
    api_key: str,
    batch_ids: List[str],
    output_dir: Path
) -> Dict[str, Dict[str, Any]]:
    """Retrieve multiple Gemini batches (Stub implementation)."""
    # This would use a GeminiBatchClient similar to OpenAI
    results = {}
    for batch_id in batch_ids:
        results[batch_id] = {
            "batch_id": batch_id,
            "status": "not_implemented",
            "error": "Gemini batch retrieval not yet implemented",
            "output_file": None,
            "error_file": None,
        }
    return results


def integrate_batch_results_with_webhook(
    batch_results: Dict[str, Any],
    event_store: Any,
    run_id: str,
    phase: str,
    step_id: str,
    partition_id: str,
    provider: str = "openai"
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
        provider: Batch provider (openai or gemini)
        
    Returns:
        Number of events successfully integrated
    """
    events_integrated = 0
    
    for batch_id, result in batch_results.items():
        status = result["status"]
        
        # Only create events for terminal states
        terminal_states = ("completed", "failed", "expired", "succeeded", "done")
        if status not in terminal_states:
            continue
        
        # Create synthetic webhook payload
        event_type = "batch.completed" if status in ("completed", "succeeded", "done") else "batch.failed"
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
            "provider": provider,
            "provider_ref": batch_id,
        }
        
        try:
            # Insert webhook event
            inserted = event_store.insert_webhook_event_if_absent(
                provider=provider,
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
                    webhook_event_id = event_store.fetch_webhook_event_id(provider, f"batch_{batch_id}")
                
                event_store.append_run_event(
                    RunEventInsert(
                        run_id=run_id,
                        phase=phase,
                        step_id=step_id,
                        partition_id=partition_id,
                        provider=provider,
                        event_type=event_type,
                        event_id=f"batch_{batch_id}",
                        provider_ref=batch_id,
                        webhook_event_id=webhook_event_id,
                        dedupe_key=f"batch_{batch_id}_{run_id}_{phase}_{step_id}_{partition_id}",
                        orphaned=False,
                    )
                )
                events_integrated += 1
                logger.info(f"Integrated {provider} batch {batch_id} as webhook event")
            else:
                logger.debug(f"Batch {batch_id} already processed (duplicate)")
                
        except Exception as e:
            logger.error(f"Failed to integrate {provider} batch {batch_id}: {e}")
    
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
        sys.exit(1)
    
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
    
    sys.exit(0)


if __name__ == "__main__":
    main()
