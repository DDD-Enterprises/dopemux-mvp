#!/usr/bin/env python3
"""
Phase 0C Determinism Check: Compare outputs from workers=1 vs workers=N runs.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import traceback


def normalize_json_content(content: str) -> str:
    """
    Normalize JSON content for deterministic comparison.
    """
    try:
        parsed = json.loads(content)
        # Sort keys and use consistent separators for deterministic output
        normalized = json.dumps(
            parsed, 
            sort_keys=True, 
            separators=(',', ':'),
            ensure_ascii=False
        )
        return normalized
    except json.JSONDecodeError:
        # If not valid JSON, return original content
        return content


def hash_file_content(file_path: Path) -> Tuple[str, Optional[str]]:
    """
    Hash file content with normalization for JSON files.
    Returns (hash_hex, normalized_content) or (None, None) on error.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Normalize if JSON file
        if file_path.suffix.lower() == '.json':
            normalized_content = normalize_json_content(content)
        else:
            normalized_content = content
        
        # Hash the normalized content
        file_hash = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
        return file_hash, normalized_content
    except Exception as e:
        print(f"Warning: Could not hash {file_path}: {e}")
        return None, None


def scan_directory(
    root_dir: Path, 
    include_glob: str = "*.json",
    ignore_glob: str = ""
) -> Dict[str, Path]:
    """
    Scan directory for files matching include_glob, excluding ignore_glob.
    Returns dict of relative_path -> absolute_path.
    """
    files = {}
    
    if not root_dir.exists():
        print(f"Warning: Directory does not exist: {root_dir}")
        return files
    
    # Find all files matching include pattern
    for file_path in root_dir.rglob(include_glob):
        if file_path.is_file():
            rel_path = file_path.relative_to(root_dir)
            files[str(rel_path)] = file_path
    
    # Apply ignore pattern if specified
    if ignore_glob:
        import fnmatch
        to_remove = []
        for rel_path, file_path in files.items():
            if fnmatch.fnmatch(rel_path, ignore_glob):
                to_remove.append(rel_path)
        
        for rel_path in to_remove:
            del files[rel_path]
    
    return files


def compare_directories(
    dir_a: Path,
    dir_b: Path,
    include_glob: str = "*.json",
    ignore_glob: str = ""
) -> Tuple[int, Dict[str, Any]]:
    """
    Compare two directories and return comparison results.
    Returns (exit_code, results_dict) where exit_code is 0 if identical, 2 if mismatches.
    """
    # Scan both directories
    files_a = scan_directory(dir_a, include_glob, ignore_glob)
    files_b = scan_directory(dir_b, include_glob, ignore_glob)
    
    # Get all unique paths
    all_paths = set(files_a.keys()) | set(files_b.keys())
    
    results = {
        "dir_a": str(dir_a),
        "dir_b": str(dir_b),
        "include_glob": include_glob,
        "ignore_glob": ignore_glob,
        "total_files_a": len(files_a),
        "total_files_b": len(files_b),
        "total_unique_paths": len(all_paths),
        "missing_in_a": [],
        "missing_in_b": [],
        "hash_mismatches": [],
        "hash_matches": 0
    }
    
    # Compare files
    for rel_path in sorted(all_paths):
        file_a = files_a.get(rel_path)
        file_b = files_b.get(rel_path)
        
        if file_a is None:
            results["missing_in_a"].append(rel_path)
            continue
        
        if file_b is None:
            results["missing_in_b"].append(rel_path)
            continue
        
        # Both files exist, compare hashes
        hash_a, _ = hash_file_content(file_a)
        hash_b, _ = hash_file_content(file_b)
        
        if hash_a is None or hash_b is None:
            results["hash_mismatches"].append({
                "path": rel_path,
                "hash_a": hash_a or "ERROR",
                "hash_b": hash_b or "ERROR",
                "reason": "hash_error"
            })
        elif hash_a != hash_b:
            results["hash_mismatches"].append({
                "path": rel_path,
                "hash_a": hash_a,
                "hash_b": hash_b,
                "reason": "content_differ"
            })
        else:
            results["hash_matches"] += 1
    
    # Determine exit code
    has_mismatches = (
        len(results["missing_in_a"]) > 0 or 
        len(results["missing_in_b"]) > 0 or 
        len(results["hash_mismatches"]) > 0
    )
    
    return (2 if has_mismatches else 0, results)


def generate_report(results: Dict[str, Any], report_path: Path) -> None:
    """
    Generate markdown report from comparison results.
    """
    report_lines = []
    report_lines.append("# Phase 0C Determinism Report")
    report_lines.append("")
    report_lines.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Python Version**: {sys.version}")
    report_lines.append(f"**Directory A**: {results['dir_a']}")
    report_lines.append(f"**Directory B**: {results['dir_b']}")
    report_lines.append(f"**Include Glob**: {results['include_glob']}")
    if results['ignore_glob']:
        report_lines.append(f"**Ignore Glob**: {results['ignore_glob']}")
    report_lines.append("")
    
    # Summary
    report_lines.append("## Summary")
    report_lines.append(f"- **Files in A**: {results['total_files_a']}")
    report_lines.append(f"- **Files in B**: {results['total_files_b']}")
    report_lines.append(f"- **Unique paths**: {results['total_unique_paths']}")
    report_lines.append(f"- **Hash matches**: {results['hash_matches']}")
    report_lines.append(f"- **Missing in A**: {len(results['missing_in_a'])}")
    report_lines.append(f"- **Missing in B**: {len(results['missing_in_b'])}")
    report_lines.append(f"- **Hash mismatches**: {len(results['hash_mismatches'])}")
    report_lines.append("")
    
    # Determine overall status
    has_mismatches = (
        len(results["missing_in_a"]) > 0 or 
        len(results["missing_in_b"]) > 0 or 
        len(results["hash_mismatches"]) > 0
    )
    
    if has_mismatches:
        report_lines.append("❌ **DETERMINISM FAILED**: Outputs differ between runs")
    else:
        report_lines.append("✅ **DETERMINISM PASSED**: Outputs are identical")
    
    report_lines.append("")
    
    # Missing files sections
    if results['missing_in_a']:
        report_lines.append("## Files Missing in A (workers=1)")
        for path in results['missing_in_a']:
            report_lines.append(f"- `{path}`")
        report_lines.append("")
    
    if results['missing_in_b']:
        report_lines.append("## Files Missing in B (workers=N)")
        for path in results['missing_in_b']:
            report_lines.append(f"- `{path}`")
        report_lines.append("")
    
    # Hash mismatches
    if results['hash_mismatches']:
        report_lines.append("## Hash Mismatches")
        report_lines.append("")
        report_lines.append("| Path | Hash A | Hash B | Reason |")
        report_lines.append("|-----|--------|--------|--------|")
        
        for mismatch in results['hash_mismatches'][:50]:  # Limit to first 50 for readability
            report_lines.append(f"| `{mismatch['path']}` | `{mismatch['hash_a']}` | `{mismatch['hash_b']}` | {mismatch['reason']} |")
        
        if len(results['hash_mismatches']) > 50:
            report_lines.append(f"\n*... and {len(results['hash_mismatches']) - 50} more mismatches*")
        
        report_lines.append("")
    
    # Write report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 0C Determinism Check: Compare outputs from workers=1 vs workers=N runs."
    )
    parser.add_argument("--out-a", type=str, required=True, help="Output directory A (workers=1)")
    parser.add_argument("--out-b", type=str, required=True, help="Output directory B (workers=N)")
    parser.add_argument("--include-glob", type=str, default="*.json", 
                       help="Glob pattern for files to include (default: *.json)")
    parser.add_argument("--ignore-glob", type=str, default="",
                       help="Glob pattern for files to ignore (default: empty)")
    parser.add_argument("--report", type=str, default="proof/PHASE0_DETERMINISM_REPORT.md",
                       help="Output report path")
    
    args = parser.parse_args()
    
    # Convert to Path objects
    dir_a = Path(args.out_a)
    dir_b = Path(args.out_b)
    report_path = Path(args.report)
    
    print(f"Comparing directories:")
    print(f"  A (workers=1): {dir_a}")
    print(f"  B (workers=N): {dir_b}")
    print(f"  Include: {args.include_glob}")
    if args.ignore_glob:
        print(f"  Ignore: {args.ignore_glob}")
    print("")
    
    # Perform comparison
    exit_code, results = compare_directories(
        dir_a, dir_b, 
        include_glob=args.include_glob,
        ignore_glob=args.ignore_glob
    )
    
    # Generate report
    generate_report(results, report_path)
    
    print(f"Report written to: {report_path}")
    print(f"Files in A: {results['total_files_a']}")
    print(f"Files in B: {results['total_files_b']}")
    print(f"Hash matches: {results['hash_matches']}")
    print(f"Missing in A: {len(results['missing_in_a'])}")
    print(f"Missing in B: {len(results['missing_in_b'])}")
    print(f"Hash mismatches: {len(results['hash_mismatches'])}")
    
    has_mismatches = (
        len(results["missing_in_a"]) > 0 or 
        len(results["missing_in_b"]) > 0 or 
        len(results["hash_mismatches"]) > 0
    )
    
    if has_mismatches:
        print("❌ DETERMINISM FAILED: Outputs differ")
    else:
        print("✅ DETERMINISM PASSED: Outputs are identical")
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
