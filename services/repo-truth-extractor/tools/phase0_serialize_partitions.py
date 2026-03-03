#!/usr/bin/env python3
"""
Phase 0B Serialization Test: Verify partition work-unit payloads are pickle-safe for ProcessPool.
"""

import argparse
import json
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import traceback

# Add the service directory to path to import from run_extraction_v3
SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

try:
    from run_extraction_v3 import build_partitions, build_inventory
except ImportError as e:
    print(f"Error importing from run_extraction_v3: {e}")
    sys.exit(1)


def find_unpicklable_path(obj: Any, path: str = "") -> Optional[str]:
    """
    Recursively find the first unpicklable object and return its path.
    Returns None if object is picklable.
    """
    try:
        pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        return None
    except (pickle.PicklingError, TypeError):
        # If it's a container, recurse to find the specific unpicklable item
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_path = f"{path}.{key}" if path else str(key)
                result = find_unpicklable_path(value, key_path)
                if result:
                    return result
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                item_path = f"{path}[{i}]" if path else f"[{i}]"
                result = find_unpicklable_path(item, item_path)
                if result:
                    return result
        
        # If no children are unpicklable or it's not a container, this object is the culprit
        if path:
            return path
        return "<root>"


def test_partition_pickle(partition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Test if a partition can be pickled.
    Returns None if successful, dict with error info if failed.
    """
    partition_id = partition.get("id", "unknown")
    
    try:
        pickle.dumps(partition, protocol=pickle.HIGHEST_PROTOCOL)
        return None
    except (pickle.PicklingError, TypeError) as e:
        failing_path = find_unpicklable_path(partition)
        failing_type = type(partition)
        
        # Try to get the type at the failing path
        if failing_path and failing_path != "<root>":
            try:
                # Navigate to the failing object
                current = partition
                parts = failing_path.lstrip(".").split(".")
                for part in parts:
                    if "[" in part and "]" in part:
                        # List/tuple index
                        idx = int(part.strip("[]"))
                        current = current[idx]
                    else:
                        # Dict key
                        current = current[part]
                failing_type = type(current)
            except (KeyError, IndexError, TypeError):
                pass
        
        return {
            "partition_id": partition_id,
            "failing_path": failing_path or "<root>",
            "type": str(failing_type),
            "error": str(e),
            "repr_snippet": repr(partition)[:200] + "..." if len(repr(partition)) > 200 else repr(partition)
        }


def generate_real_inventory() -> List[Dict[str, Any]]:
    """
    Generate a real inventory by scanning actual files in the repo.
    """
    try:
        from run_extraction_v3 import Collector, is_text_candidate, safe_read, sha256_text, classify_kind
        import os
        from pathlib import Path
        
        # Use the same collector logic as the main extraction
        root = Path.cwd()
        excludes = [
            "*.pyc", "*.pyo", "*.pyd",
            ".git/*", ".venv/*", "node_modules/*",
            "__pycache__/*", "*.egg-info/*",
            "*.log", "*.lock", "*.pid",
            "*.sqlite", "*.db", "*.sqlite3",
        ]
        
        collector = Collector(root, excludes)
        
        # Collect from a few key directories to get realistic data
        subdirs = ["services", "src", "scripts", "config"]
        context_items = collector.collect(subdirs=subdirs)
        
        # Build inventory using the same logic as main extraction
        inventory = []
        unique_paths = sorted({str(Path(item["path"]).resolve()) for item in context_items if item.get("path")})
        
        for path_str in unique_paths:
            path = Path(path_str)
            if not path.exists() or not path.is_file():
                continue

            content = safe_read(path)
            char_count = len(content)
            est_chars = min(char_count, 10000)  # Use reasonable truncation
            
            try:
                st = path.stat()
                size = st.st_size
                mtime = st.st_mtime
            except Exception:
                size = 0
                mtime = 0.0

            inventory.append(
                {
                    "path": str(path),
                    "size": size,
                    "mtime": mtime,
                    "sha256": sha256_text(path),
                    "kind": classify_kind(path),
                    "char_count": char_count,
                    "char_count_estimate": est_chars,
                }
            )
        
        inventory.sort(key=lambda item: item["path"])
        return inventory
        
    except Exception as e:
        print(f"Warning: Could not generate real inventory: {e}")
        # Fall back to sample data
        return generate_sample_inventory()


def generate_sample_inventory() -> List[Dict[str, Any]]:
    """
    Generate a sample inventory for testing partition generation.
    """
    return [
        {
            "path": "/tmp/test1.py",
            "size": 1000,
            "mtime": time.time(),
            "sha256": "a" * 64,
            "kind": "code",
            "char_count": 1000,
            "char_count_estimate": 1000,
        },
        {
            "path": "/tmp/test2.py", 
            "size": 2000,
            "mtime": time.time(),
            "sha256": "b" * 64,
            "kind": "code",
            "char_count": 2000,
            "char_count_estimate": 2000,
        },
        {
            "path": "/tmp/test3.md",
            "size": 500,
            "mtime": time.time(),
            "sha256": "c" * 64,
            "kind": "doc",
            "char_count": 500,
            "char_count_estimate": 500,
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 0B Serialization Test: Verify partition work-unit payloads are pickle-safe."
    )
    parser.add_argument(
        "--max", 
        type=int, 
        default=None,
        help="Optional cap on number of partitions to test"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="proof/PHASE0_SERIALIZATION_REPORT.md",
        help="Output report path"
    )
    parser.add_argument(
        "--phase",
        type=str,
        default="A",
        help="Phase to test (default: A)"
    )
    
    args = parser.parse_args()
    
    # Try to generate real inventory first, fall back to sample if needed
    inventory = generate_real_inventory()
    
    print(f"Generated inventory with {len(inventory)} files")
    
    partitions = build_partitions(
        phase=args.phase,
        inventory=inventory,
        max_files=10,
        max_chars=10000
    )
    
    # Apply max limit if specified
    if args.max is not None:
        partitions = partitions[:args.max]
    
    # Test each partition
    results = []
    pass_count = 0
    fail_count = 0
    type_counts = {}
    
    for partition in partitions:
        result = test_partition_pickle(partition)
        if result is None:
            pass_count += 1
        else:
            fail_count += 1
            results.append(result)
            
            # Count types
            fail_type = result["type"]
            type_counts[fail_type] = type_counts.get(fail_type, 0) + 1
    
    # Generate report
    report_lines = []
    report_lines.append("# Phase 0B Serialization Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Python Version**: {sys.version}")
    report_lines.append(f"**Repo Root**: {Path.cwd()}")
    report_lines.append("")
    
    report_lines.append("## Summary")
    report_lines.append(f"- **Total Partitions Tested**: {len(partitions)}")
    report_lines.append(f"- **Pass Count**: {pass_count}")
    report_lines.append(f"- **Fail Count**: {fail_count}")
    report_lines.append("")
    
    if fail_count > 0:
        report_lines.append("## Top Failing Types")
        for type_name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- `{type_name}`: {count} failures")
        report_lines.append("")
        
        report_lines.append("## Failure Details")
        for result in sorted(results, key=lambda x: x["partition_id"]):
            report_lines.append(f"### Partition {result['partition_id']}")
            report_lines.append(f"- **Failing Path**: `{result['failing_path']}`")
            report_lines.append(f"- **Type**: `{result['type']}`")
            report_lines.append(f"- **Error**: `{result['error']}`")
            report_lines.append(f"- **Repr Snippet**: `{result['repr_snippet']}`")
            report_lines.append("")
    else:
        report_lines.append("✅ **All partitions are pickle-safe!**")
    
    # Write report
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"Report written to: {output_path}")
    print(f"Partitions tested: {len(partitions)}")
    print(f"Pass: {pass_count}, Fail: {fail_count}")
    
    # Exit code: 0 if all pass, 2 if any fail
    return 2 if fail_count > 0 else 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
