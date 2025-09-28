"""
Pipeline Cleanup System - File tracking and automated cleanup

Monitors file operations during pipeline execution and provides comprehensive
cleanup capabilities with detailed activity reporting for ADHD-friendly transparency.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import stat
from collections import defaultdict
import glob


@dataclass
class FileOperation:
    """Record of a single file operation."""
    operation_type: str  # created, modified, deleted, accessed
    file_path: str
    timestamp: str
    size_bytes: int = 0
    permissions: str = ""
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CleanupConfig:
    """Configuration for pipeline cleanup operations."""
    dry_run: bool = False
    keep_outputs: bool = True
    keep_processing_logs: bool = True
    keep_cache_files: bool = False
    cleanup_temp_files: bool = True
    max_file_age_hours: int = 24
    report_format: str = "markdown"  # markdown, json, table


@dataclass
class CleanupResult:
    """Results from cleanup operation."""
    config: CleanupConfig
    success: bool
    processing_time: float

    # File operation counts
    files_removed: int = 0
    files_kept: int = 0
    space_freed_bytes: int = 0

    # Detailed tracking
    removed_files: List[str] = field(default_factory=list)
    kept_files: List[str] = field(default_factory=list)
    activity_report: Dict[str, Any] = field(default_factory=dict)

    error_message: Optional[str] = None


class FileTracker:
    """
    Comprehensive file operation tracker for pipeline execution.

    Monitors all file system operations during pipeline execution
    and provides detailed reporting for transparency and debugging.
    """

    def __init__(self, tracking_directory: Optional[Path] = None):
        """Initialize file tracker."""
        self.tracking_directory = tracking_directory or Path.cwd()
        self.tracking_active = False

        # Operation tracking
        self.file_operations: List[FileOperation] = []
        self.initial_file_snapshot: Dict[str, Dict[str, Any]] = {}
        self.tracking_start_time: Optional[datetime] = None

        # File categorization
        self.temp_patterns = [
            "*.tmp", "*.temp", "*~", "*.bak", "*.swp",
            ".DS_Store", "Thumbs.db", "__pycache__",
            "*.pyc", "*.pyo", ".pytest_cache"
        ]

        self.interim_patterns = [
            "*_partial_*", "*_interim_*", "*_processing_*",
            "*.part", "*.incomplete", "*_temp_*"
        ]

        self.cache_patterns = [
            "*cache*", "*.cache", ".cache", "cached_*"
        ]

    def start_tracking(self):
        """Begin tracking file operations."""
        if self.tracking_active:
            return

        self.tracking_start_time = datetime.now()
        self.tracking_active = True

        # Create initial snapshot
        self._create_file_snapshot()
        print(f"📊 File tracking started at {self.tracking_start_time.strftime('%H:%M:%S')}")

    def stop_tracking(self):
        """Stop tracking file operations."""
        if not self.tracking_active:
            return

        self.tracking_active = False

        # Create final snapshot and detect changes
        self._detect_file_changes()

        processing_time = (datetime.now() - self.tracking_start_time).total_seconds()
        print(f"📊 File tracking stopped after {processing_time:.2f}s")

    def tracking(self):
        """Context manager for file tracking."""
        return FileTrackingContext(self)

    def log_operation(self, operation_type: str, file_path: Path, metadata: Optional[Dict[str, Any]] = None):
        """Log a file operation."""
        if not self.tracking_active:
            return

        try:
            # Get file information
            size_bytes = 0
            permissions = ""

            if file_path.exists():
                stat_info = file_path.stat()
                size_bytes = stat_info.st_size
                permissions = oct(stat_info.st_mode)[-3:]

            operation = FileOperation(
                operation_type=operation_type,
                file_path=str(file_path.resolve()),
                timestamp=datetime.now().isoformat(),
                size_bytes=size_bytes,
                permissions=permissions,
                metadata=metadata or {}
            )

            self.file_operations.append(operation)

        except Exception as e:
            # Don't let tracking errors break the pipeline
            print(f"⚠️ File tracking error for {file_path}: {e}")

    def _create_file_snapshot(self):
        """Create snapshot of current file system state."""
        self.initial_file_snapshot = {}

        try:
            for file_path in self.tracking_directory.rglob('*'):
                if file_path.is_file():
                    try:
                        stat_info = file_path.stat()
                        self.initial_file_snapshot[str(file_path.resolve())] = {
                            'size': stat_info.st_size,
                            'mtime': stat_info.st_mtime,
                            'mode': stat_info.st_mode
                        }
                    except (OSError, FileNotFoundError):
                        # Skip files that can't be accessed
                        continue

        except Exception as e:
            print(f"⚠️ Error creating file snapshot: {e}")

    def _detect_file_changes(self):
        """Detect file changes since tracking started."""
        try:
            current_files = {}

            # Get current state
            for file_path in self.tracking_directory.rglob('*'):
                if file_path.is_file():
                    try:
                        stat_info = file_path.stat()
                        file_key = str(file_path.resolve())
                        current_files[file_key] = {
                            'size': stat_info.st_size,
                            'mtime': stat_info.st_mtime,
                            'mode': stat_info.st_mode
                        }

                        # Check if file was created
                        if file_key not in self.initial_file_snapshot:
                            self.log_operation('created', file_path)

                        # Check if file was modified
                        elif current_files[file_key]['mtime'] > self.initial_file_snapshot[file_key]['mtime']:
                            self.log_operation('modified', file_path)

                    except (OSError, FileNotFoundError):
                        continue

            # Check for deleted files
            for file_key in self.initial_file_snapshot:
                if file_key not in current_files:
                    self.log_operation('deleted', Path(file_key))

        except Exception as e:
            print(f"⚠️ Error detecting file changes: {e}")

    def generate_activity_report(self) -> Dict[str, Any]:
        """Generate comprehensive activity report."""
        if not self.tracking_start_time:
            return {}

        # Categorize operations
        operations_by_type = defaultdict(list)
        for op in self.file_operations:
            operations_by_type[op.operation_type].append(op)

        # Calculate sizes and counts
        total_created_size = sum(op.size_bytes for op in operations_by_type['created'])
        total_modified_size = sum(op.size_bytes for op in operations_by_type['modified'])

        # File categorization
        file_categories = self._categorize_files()

        report = {
            'execution_info': {
                'start_time': self.tracking_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.tracking_start_time).total_seconds(),
                'tracking_directory': str(self.tracking_directory)
            },
            'operation_summary': {
                'total_operations': len(self.file_operations),
                'files_created': len(operations_by_type['created']),
                'files_modified': len(operations_by_type['modified']),
                'files_deleted': len(operations_by_type['deleted']),
                'total_created_size_bytes': total_created_size,
                'total_modified_size_bytes': total_modified_size
            },
            'file_categories': file_categories,
            'detailed_operations': [
                {
                    'type': op.operation_type,
                    'path': op.file_path,
                    'timestamp': op.timestamp,
                    'size_bytes': op.size_bytes,
                    'metadata': op.metadata
                }
                for op in self.file_operations
            ]
        }

        return report

    def _categorize_files(self) -> Dict[str, List[str]]:
        """Categorize files by type for better organization."""
        categories = {
            'output_files': [],
            'temp_files': [],
            'interim_files': [],
            'cache_files': [],
            'log_files': [],
            'config_files': [],
            'other_files': []
        }

        for operation in self.file_operations:
            file_path = operation.file_path
            filename = Path(file_path).name.lower()

            # Categorize based on patterns
            if any(self._matches_pattern(filename, pattern) for pattern in self.temp_patterns):
                categories['temp_files'].append(file_path)
            elif any(self._matches_pattern(filename, pattern) for pattern in self.interim_patterns):
                categories['interim_files'].append(file_path)
            elif any(self._matches_pattern(filename, pattern) for pattern in self.cache_patterns):
                categories['cache_files'].append(file_path)
            elif filename.endswith(('.log', '.logs')):
                categories['log_files'].append(file_path)
            elif filename.endswith(('.json', '.yaml', '.yml', '.cfg', '.ini', '.conf')):
                if operation.operation_type == 'created':
                    categories['output_files'].append(file_path)
                else:
                    categories['config_files'].append(file_path)
            elif filename.endswith(('.md', '.txt', '.csv', '.tsv', '.html')):
                categories['output_files'].append(file_path)
            else:
                categories['other_files'].append(file_path)

        return categories

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a glob pattern."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)


class FileTrackingContext:
    """Context manager for file tracking."""

    def __init__(self, tracker: FileTracker):
        self.tracker = tracker

    def __enter__(self):
        self.tracker.start_tracking()
        return self.tracker

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tracker.stop_tracking()


class PipelineCleanup:
    """
    Comprehensive pipeline cleanup system.

    Handles identification and removal of temporary files, interim processing
    files, and cache files with detailed reporting and safety checks.
    """

    def __init__(self, config: CleanupConfig):
        """Initialize cleanup system."""
        self.config = config

        # Cleanup patterns
        self.always_safe_patterns = [
            "__pycache__/**",
            "*.pyc",
            "*.pyo",
            "*.tmp",
            "*.temp",
            "*~",
            ".DS_Store",
            "Thumbs.db"
        ]

        self.interim_patterns = [
            "*_partial_*",
            "*_interim_*",
            "*_processing_*",
            "*.part",
            "*.incomplete"
        ]

        self.cache_patterns = [
            ".cache/**",
            "**/cache/**",
            "*.cache",
            "cached_*"
        ]

    def cleanup_pipeline_files(self, activity_report: Dict[str, Any], target_directory: Path) -> CleanupResult:
        """
        Perform comprehensive cleanup of pipeline files.

        Args:
            activity_report: Report from FileTracker
            target_directory: Directory to clean up

        Returns:
            Detailed cleanup results
        """
        start_time = time.time()

        try:
            print("🧹 Starting pipeline cleanup...")

            # Identify files to remove
            files_to_remove = self._identify_cleanup_candidates(activity_report, target_directory)

            # Perform cleanup
            removed_files = []
            space_freed = 0

            if not self.config.dry_run:
                removed_files, space_freed = self._remove_files(files_to_remove)
            else:
                print("🔍 Dry run mode - no files will be removed")
                removed_files = files_to_remove
                space_freed = sum(self._get_file_size(Path(f)) for f in files_to_remove)

            # Generate final activity report
            final_report = self._generate_cleanup_report(activity_report, removed_files, space_freed)

            processing_time = time.time() - start_time
            print(f"✅ Cleanup complete! ({processing_time:.2f}s)")

            return CleanupResult(
                config=self.config,
                success=True,
                processing_time=processing_time,
                files_removed=len(removed_files),
                space_freed_bytes=space_freed,
                removed_files=removed_files,
                activity_report=final_report
            )

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Cleanup failed: {e}")

            return CleanupResult(
                config=self.config,
                success=False,
                processing_time=processing_time,
                error_message=str(e)
            )

    def _identify_cleanup_candidates(self, activity_report: Dict[str, Any], target_directory: Path) -> List[str]:
        """Identify files that are candidates for cleanup."""
        candidates = []

        # Get file categories from activity report
        file_categories = activity_report.get('file_categories', {})

        # Always clean temp files
        if self.config.cleanup_temp_files:
            candidates.extend(file_categories.get('temp_files', []))

        # Clean interim files unless keeping outputs
        if not self.config.keep_outputs:
            candidates.extend(file_categories.get('interim_files', []))

        # Clean cache files if configured
        if not self.config.keep_cache_files:
            candidates.extend(file_categories.get('cache_files', []))

        # Clean old log files unless keeping them
        if not self.config.keep_processing_logs:
            log_files = file_categories.get('log_files', [])
            candidates.extend(self._filter_old_files(log_files))

        # Add files matching always-safe patterns
        for pattern in self.always_safe_patterns:
            candidates.extend(self._find_files_by_pattern(target_directory, pattern))

        # Remove duplicates and ensure files exist
        unique_candidates = []
        seen = set()

        for file_path in candidates:
            if file_path not in seen and Path(file_path).exists():
                unique_candidates.append(file_path)
                seen.add(file_path)

        print(f"🎯 Identified {len(unique_candidates)} files for cleanup")
        return unique_candidates

    def _filter_old_files(self, file_paths: List[str]) -> List[str]:
        """Filter files older than max_file_age_hours."""
        cutoff_time = datetime.now() - timedelta(hours=self.config.max_file_age_hours)
        old_files = []

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if mtime < cutoff_time:
                        old_files.append(file_path)
            except (OSError, FileNotFoundError):
                continue

        return old_files

    def _find_files_by_pattern(self, directory: Path, pattern: str) -> List[str]:
        """Find files matching a glob pattern."""
        try:
            matches = []
            for match in directory.rglob(pattern):
                if match.is_file():
                    matches.append(str(match.resolve()))
            return matches
        except Exception:
            return []

    def _remove_files(self, file_paths: List[str]) -> Tuple[List[str], int]:
        """Remove files and return list of removed files and space freed."""
        removed_files = []
        space_freed = 0

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    # Get file size before deletion
                    file_size = path.stat().st_size

                    # Remove file or directory
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)

                    removed_files.append(file_path)
                    space_freed += file_size

            except Exception as e:
                print(f"⚠️ Could not remove {file_path}: {e}")

        return removed_files, space_freed

    def _get_file_size(self, path: Path) -> int:
        """Get file size safely."""
        try:
            if path.exists():
                return path.stat().st_size
            return 0
        except (OSError, FileNotFoundError):
            return 0

    def _generate_cleanup_report(self, activity_report: Dict[str, Any], removed_files: List[str],
                                space_freed: int) -> Dict[str, Any]:
        """Generate comprehensive cleanup report."""
        return {
            'cleanup_summary': {
                'files_removed': len(removed_files),
                'space_freed_bytes': space_freed,
                'space_freed_mb': round(space_freed / (1024 * 1024), 2),
                'dry_run': self.config.dry_run
            },
            'removed_files_by_category': self._categorize_removed_files(removed_files),
            'original_activity': activity_report,
            'cleanup_config': {
                'keep_outputs': self.config.keep_outputs,
                'keep_processing_logs': self.config.keep_processing_logs,
                'keep_cache_files': self.config.keep_cache_files,
                'max_file_age_hours': self.config.max_file_age_hours
            }
        }

    def _categorize_removed_files(self, removed_files: List[str]) -> Dict[str, List[str]]:
        """Categorize removed files for reporting."""
        categories = {
            'temp_files': [],
            'cache_files': [],
            'interim_files': [],
            'log_files': [],
            'other_files': []
        }

        for file_path in removed_files:
            filename = Path(file_path).name.lower()

            if any(self._matches_pattern(filename, pattern) for pattern in ["*.tmp", "*.temp", "*~", "*.pyc"]):
                categories['temp_files'].append(file_path)
            elif 'cache' in filename or '.cache' in file_path:
                categories['cache_files'].append(file_path)
            elif any(keyword in filename for keyword in ['interim', 'partial', 'processing']):
                categories['interim_files'].append(file_path)
            elif filename.endswith('.log'):
                categories['log_files'].append(file_path)
            else:
                categories['other_files'].append(file_path)

        return categories

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches a glob pattern."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)


def cleanup_pipeline(target_directory: Path,
                    activity_report: Optional[Dict[str, Any]] = None,
                    dry_run: bool = False,
                    keep_outputs: bool = True) -> CleanupResult:
    """
    Convenience function for pipeline cleanup.

    Args:
        target_directory: Directory to clean up
        activity_report: Optional activity report from FileTracker
        dry_run: If True, don't actually remove files
        keep_outputs: If True, keep final output files

    Returns:
        Cleanup results with detailed reporting
    """
    config = CleanupConfig(
        dry_run=dry_run,
        keep_outputs=keep_outputs
    )

    cleanup_system = PipelineCleanup(config)

    # If no activity report provided, create a basic one
    if activity_report is None:
        activity_report = {
            'file_categories': {
                'temp_files': [],
                'interim_files': [],
                'cache_files': [],
                'log_files': [],
                'output_files': []
            }
        }

    return cleanup_system.cleanup_pipeline_files(activity_report, target_directory)