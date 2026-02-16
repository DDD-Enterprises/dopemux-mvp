#!/usr/bin/env python3
"""
Orchestration script for Dopemux upgrades extraction pipeline.
Handles Phase A (Repo Control Plane), Phase H (Home Control Plane), and Phase D (Docs).
Includes redaction, exclusion logic, and partitioning support.
"""

import argparse
import fnmatch
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_extraction")

# --- Constants & Configuration ---

HOME_DIRS = [
    ".dopemux",
    ".config/dopemux",
    ".config/taskx",
    ".config/litellm",
    ".config/mcp",
]

# Standard exclusions for repo scanning
REPO_EXCLUDES = [
    ".git",
    ".gitignore",
    ".gitmodules",
    ".gitattributes",
    "__pycache__",
    "*.pyc",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "*.egg-info",
    ".DS_Store",
    "dopemux_dashboard.py",  # Exclude specific files if needed
]

# Standard exclusions for home scanning (avoid caches, sessions)
HOME_EXCLUDES = [
    "cache",
    "caches",
    "sessions",
    "history",
    "logs",
    "tmp",
    "temp",
    "*.log",
    "*.lock",
    "*.sqlite",
    "*.db",
]

DOCS_ORDER = ["D0", "D3", "M1", "QA", "CL"]

# --- Redaction Logic ---

class Redactor:
    """Handles text redaction for sensitive patterns."""

    def __init__(self):
        self.patterns = [
            # Common API Key patterns (handles optional quotes for JSON/YAML keys)
            (r'(?i)(?:["\']?)(api[_-]?key|token|secret|password|bearer|authorization)(?:["\']?)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', "REDACTED_SECRET"),
            # JWT tokens (naive regex for 3 parts separated by dots)
            (r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', "REDACTED_JWT"),
            # PEM blocks (RSA/Private Key)
            (r'-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----', "REDACTED_PEM_BLOCK"),
            # Generic high-entropy strings (e.g. 40+ hex chars)
            (r'\b[a-fA-F0-9]{40,}\b', "REDACTED_HIGH_ENTROPY_HEX"),
            # Cookie values (common session cookies)
            (r'(?i)(cookie)\s*[:=]\s*["\']?([^"\';\n]+)["\']?', "REDACTED_COOKIE"),
        ]
        self.hits: List[Dict[str, Any]] = []

    def redact_text(self, text: str, file_path: str) -> str:
        """Redacts sensitive patterns from text and logs hits."""
        redacted_text = text
        for pattern, replacement in self.patterns:
            matches = list(re.finditer(pattern, redacted_text, re.DOTALL))
            for match in reversed(matches):  # Reverse to avoid index shifting issues
                start, end = match.span()
                matched_str = match.group(0)

                # Check if group 2 exists (value part of key=value), otherwise redact full match
                if match.lastindex and match.lastindex >= 2:
                    # Redact specifically the value group if present
                    val_start, val_end = match.span(2)
                    prefix = redacted_text[start:val_start]
                    suffix = redacted_text[val_end:end]

                    # Apply replacement
                    redacted_text = redacted_text[:val_start] + replacement + redacted_text[val_end:]

                    self.hits.append({
                        "file": file_path,
                        "pattern": replacement,
                        "location": f"{val_start}-{val_end}",
                        "snippet": "..." # Don't store the secret even in hits
                    })
                else:
                    # Redact the whole match
                    redacted_text = redacted_text[:start] + replacement + redacted_text[end:]

                    self.hits.append({
                        "file": file_path,
                        "pattern": replacement,
                        "location": f"{start}-{end}",
                        "snippet": "..."
                    })

        return redacted_text

    def get_report(self) -> List[Dict[str, Any]]:
        return self.hits

    def clear_report(self):
        self.hits = []


# --- Collection Logic ---

class ContentCollector:
    """Collects file content with exclusion and redaction."""

    def __init__(self, root_dir: Path, excludes: List[str]):
        self.root_dir = root_dir
        self.excludes = excludes
        self.redactor = Redactor()
        self.collected_files: List[Dict[str, Any]] = []
        self.excluded_count = 0

    def is_excluded(self, path: Path) -> bool:
        """Check if path matches exclusion patterns using relative path."""
        try:
            rel_path = path.relative_to(self.root_dir)
        except ValueError:
            # Should not happen if we walk properly, but fallback to name
            rel_path = Path(path.name)

        str_rel = str(rel_path)

        for pattern in self.excludes:
            if fnmatch.fnmatch(str_rel, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
            # Also check if any parent directory matches (e.g. sessions/foo)
            for part in rel_path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def collect(self, scan_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Recursively collect files from root_dir or specific subdirs.
        """
        self.collected_files = []
        self.redactor.clear_report()
        self.excluded_count = 0

        paths_to_scan = [self.root_dir]
        if scan_dirs:
            paths_to_scan = [self.root_dir / d for d in scan_dirs]

        for scan_path in paths_to_scan:
            scan_path = scan_path.expanduser().resolve()
            if not scan_path.exists():
                logger.warning(f"Path does not exist: {scan_path}")
                continue

            if scan_path.is_file():
                self._process_file(scan_path)
                continue

            for root, dirs, files in os.walk(scan_path):
                # Modify dirs in-place to skip excluded directories
                # We need to check relative path for directories too
                dirs[:] = [d for d in dirs if not self.is_excluded(Path(root) / d)]

                for file in files:
                    file_path = Path(root) / file
                    if self.is_excluded(file_path):
                        self.excluded_count += 1
                        continue

                    self._process_file(file_path)

        if self.excluded_count == 0 and self.excludes:
             logger.warning("Zero files excluded despite exclusion patterns. Check patterns.")

        return self.collected_files

    def _process_file(self, file_path: Path):
        try:
            # Basic check for text files (extensions or content)
            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.pyc']:
                return

            # Read content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                return # Skip binary or unreadable

            # Redact
            redacted_content = self.redactor.redact_text(content, str(file_path))

            self.collected_files.append({
                "path": str(file_path),
                "content": redacted_content,
                "size": len(content)
            })
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    def save_report(self, output_dir: Path, phase_name: str):
        """Save redaction report."""
        report = self.redactor.get_report()
        if report:
            report_path = output_dir / f"{phase_name}_REDACTION_REPORT.json"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Redaction report saved to {report_path} ({len(report)} hits)")


# --- Runner Logic ---

def run_phase_a(output_dir: Path, dry_run: bool):
    """Run Phase A: Repo Control Plane Scan."""
    logger.info("Starting Phase A: Repo Control Plane...")

    # Phase A targets specific repo config/instruction files
    # We'll scan the whole repo root but exclude code/docs/etc to find configs
    collector = ContentCollector(Path.cwd(), REPO_EXCLUDES + ["docs", "services", "src", "tests", "reports"])
    # Actually we want specific files/folders often found in root or .config
    # Let's just scan root non-recursively + .github + .taskx + .claude + config/

    # Since we need "instruction/config surfaces", we scan known config dirs
    scan_targets = [".", ".github", ".claude", ".taskx", "config"]
    # We use the collector on these, it handles recursion and exclusion

    # Note: "." will recurse into everything if we don't exclude properly in collector
    # But we passed REPO_EXCLUDES which excludes 'src', 'services', 'docs', 'tests'

    results = collector.collect(scan_dirs=None) # Scans from root with exclusions

    if dry_run:
        out_file = output_dir / "PHASE_A_TRACE.json"
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Phase A dry-run trace saved to {out_file}")
        collector.save_report(output_dir, "PHASE_A")
    else:
        # Here we would call LLM with PHASE_A_REPO_CONTROL_PLANE.md prompt + results
        logger.error("Live execution not implemented (LLM integration required). Use --dry-run to generate traces.")
        raise NotImplementedError("LLM integration missing from runner.")

def run_phase_h(output_dir: Path, dry_run: bool):
    """Run Phase H: Home Control Plane Scan."""
    logger.info("Starting Phase H: Home Control Plane...")

    home = Path.home()
    collector = ContentCollector(home, HOME_EXCLUDES)

    # Scan specific roots
    scan_dirs = []
    for d in HOME_DIRS:
        full_path = home / d
        if full_path.exists():
            scan_dirs.append(d) # relative to home

    if not scan_dirs:
        logger.warning("No Home Control Plane directories found.")
        return

    results = collector.collect(scan_dirs=scan_dirs)

    if dry_run:
        out_file = output_dir / "PHASE_H_TRACE.json"
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Phase H dry-run trace saved to {out_file}")
        collector.save_report(output_dir, "PHASE_H")
    else:
        logger.error("Live execution not implemented (LLM integration required). Use --dry-run to generate traces.")
        raise NotImplementedError("LLM integration missing from runner.")

def run_phase_d(output_dir: Path, dry_run: bool, partition: Optional[str] = None):
    """Run Phase D: Docs Pipeline."""
    logger.info("Starting Phase D: Docs Pipeline...")

    # Check if we have D0 output (Inventory)
    inventory_file = output_dir / "DOC_INVENTORY.json"
    partition_plan_file = output_dir / "PARTITION_PLAN.json"

    # D0: Inventory
    if not inventory_file.exists() and not partition:
        logger.info("Running D0: Inventory & Partition...")
        # Scan docs/ folder
        collector = ContentCollector(Path.cwd() / "docs", ["archive"]) # Exclude archive from D0?
        # Actually D0 logic is specific: just list files, don't read content yet
        # But for this runner we simulate content reading or just metadata

        # We need to run D0 logic. Since we don't have the D0 script, we mock it or use collector
        # Assuming D0 prompt does the work if we feed it file list.
        # But D0 usually produces the JSONs.

        # For dry run, we just trace.
        if dry_run:
             logger.info("D0 dry-run: Scanning docs/...")
             # Mock D0 output
             with open(partition_plan_file, "w") as f:
                 json.dump({"partitions": {"P1": ["doc1.md"], "P2": ["doc2.md"]}}, f)
             logger.info(f"Created mock {partition_plan_file}")

    # D1/D2: Deep Extraction (Partitioned)
    if partition:
        logger.info(f"Running D1/D2 for partition: {partition}")
        if not partition_plan_file.exists():
            logger.error(f"Partition plan not found: {partition_plan_file}. Run D0 first.")
            return

        # Load partition plan
        try:
            with open(partition_plan_file) as f:
                plan = json.load(f)
            # Check if partition exists
            # This logic depends on actual plan structure
            logger.info(f"Processing partition {partition}...")
        except Exception as e:
            logger.error(f"Failed to read partition plan: {e}")

        if dry_run:
            logger.info(f"D1/D2 dry-run for {partition} complete.")
            return

    # Remaining phases: D3, M1, QA, CL
    # Only run if not partitioning (or if we want to run full pipeline)
    if not partition:
        for phase in ["D3", "M1", "QA", "CL"]:
            # Check deps
            if phase == "M1":
                # Check if D1/D2 outputs exist (mock check)
                # In real runner, we would look for D1_* and D2_* files
                pass

            logger.info(f"Running Phase {phase}...")
            if dry_run:
                logger.info(f"{phase} dry-run complete.")


def main():
    parser = argparse.ArgumentParser(description="Dopemux Extraction Runner")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Priority command (Phases A + H)
    parser_priority = subparsers.add_parser("priority", help="Run Priority Control Plane (A + H)")
    parser_priority.add_argument("--dry-run", action="store_true", help="Generate trace files only")
    parser_priority.add_argument("--output-dir", default="extraction_out", help="Output directory")

    # Docs command (Phase D)
    parser_docs = subparsers.add_parser("docs", help="Run Docs Pipeline (D0-D5)")
    parser_docs.add_argument("--dry-run", action="store_true", help="Generate trace files only")
    parser_docs.add_argument("--output-dir", default="extraction_out", help="Output directory")
    parser_docs.add_argument("--doc-partition", help="Run specific doc partition (e.g. P1)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.command == "priority":
        run_phase_a(output_dir, args.dry_run)
        run_phase_h(output_dir, args.dry_run)
    elif args.command == "docs":
        run_phase_d(output_dir, args.dry_run, args.doc_partition)

if __name__ == "__main__":
    main()
