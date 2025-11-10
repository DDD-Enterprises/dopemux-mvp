"""
Batch File Operations Handler for Dopemux

Provides parallel file operations using aiofiles to improve performance
in ADHD-optimized development workflows by reducing I/O wait times.

Key Features:
- Parallel file reads with aiofiles
- Atomic batch writes with temporary files
- Error isolation and recovery
- Integration with MCP workflows
- Resource-aware concurrency limits
"""

import asyncio
import os
import tempfile
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import aiofiles

logger = logging.getLogger(__name__)


class BatchFileOps:
    """
    Handler for batch file operations with parallel processing and error recovery.

    Optimized for Dopemux workflows that need to read/write multiple configuration
    files or process file-based data in parallel.
    """

    def __init__(self, max_concurrent: int = 10, chunk_size: int = 8192):
        """
        Initialize the batch file operations handler.

        Args:
            max_concurrent: Maximum concurrent file operations
            chunk_size: Chunk size for reading large files
        """
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @asynccontextmanager
    async def _limit_concurrency(self):
        """Context manager for limiting concurrent file operations."""
        async with self.semaphore:
            yield

    async def _read_single_file(self, file_path: Union[str, Path]) -> Tuple[Union[str, Path], Union[str, Exception]]:
        """
        Read a single file asynchronously.

        Args:
            file_path: Path to the file to read

        Returns:
            Tuple of (file_path, content_or_exception)
        """
        async with self._limit_concurrency():
            try:
                file_path = Path(file_path)
                if not file_path.exists():
                    return file_path, FileNotFoundError(f"File not found: {file_path}")

                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()

                logger.debug(f"Successfully read file: {file_path}")
                return file_path, content

            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return file_path, e

    async def _write_single_file_atomic(
        self,
        file_path: Union[str, Path],
        content: str,
        mode: str = 'w'
    ) -> Union[str, Path, Exception]:
        """
        Write content to a file atomically using a temporary file.

        Args:
            file_path: Target file path
            content: Content to write
            mode: Write mode ('w' for text, 'wb' for binary)

        Returns:
            file_path on success, Exception on failure
        """
        async with self._limit_concurrency():
            try:
                file_path = Path(file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Create temporary file in same directory for atomic rename
                with tempfile.NamedTemporaryFile(
                    mode=mode,
                    dir=file_path.parent,
                    delete=False,
                    suffix='.tmp'
                ) as tmp_file:
                    tmp_path = Path(tmp_file.name)
                    if 'b' in mode:
                        # Binary mode
                        await tmp_file.write(content)
                    else:
                        # Text mode
                        await tmp_file.write(content)

                # Atomic rename
                tmp_path.replace(file_path)
                logger.debug(f"Successfully wrote file atomically: {file_path}")
                return file_path

            except Exception as e:
                logger.error(f"Failed to write file {file_path}: {e}")
                return e

    async def batch_read_files(
        self,
        file_paths: List[Union[str, Path]],
        return_exceptions: bool = True
    ) -> Dict[Union[str, Path], Union[str, Exception]]:
        """
        Read multiple files in parallel.

        Args:
            file_paths: List of file paths to read
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            Dict mapping file paths to content (or Exception if failed)

        Example:
            files = ['config.json', 'settings.yaml', 'data.txt']
            results = await batch_ops.batch_read_files(files)
            # results['config.json'] = '{"key": "value"}'
            # results['missing.txt'] = FileNotFoundError(...)
        """
        if not file_paths:
            return {}

        logger.info(f"Batch reading {len(file_paths)} files with max {self.max_concurrent} concurrent")

        # Create read tasks
        tasks = [self._read_single_file(path) for path in file_paths]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)

        # Convert to dict format
        result_dict = {}
        for file_path, content_or_error in results:
            result_dict[file_path] = content_or_error

        # Log summary
        successful = sum(1 for v in result_dict.values() if not isinstance(v, Exception))
        failed = len(result_dict) - successful
        logger.info(f"Batch read completed: {successful} successful, {failed} failed")

        return result_dict

    async def batch_write_files(
        self,
        file_writes: Dict[Union[str, Path], str],
        return_exceptions: bool = True
    ) -> Dict[Union[str, Path], Union[Union[str, Path], Exception]]:
        """
        Write multiple files atomically in parallel.

        Args:
            file_writes: Dict mapping file paths to content strings
            return_exceptions: If True, exceptions are returned instead of raised

        Returns:
            Dict mapping file paths to success result (or Exception if failed)

        Example:
            writes = {
                'config.json': '{"updated": true}',
                'settings.yaml': 'key: value\n'
            }
            results = await batch_ops.batch_write_files(writes)
            # results['config.json'] = Path('config.json')  # Success
            # results['readonly.txt'] = PermissionError(...)  # Failed
        """
        if not file_writes:
            return {}

        logger.info(f"Batch writing {len(file_writes)} files with max {self.max_concurrent} concurrent")

        # Create write tasks
        tasks = [
            self._write_single_file_atomic(path, content)
            for path, content in file_writes.items()
        ]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)

        # Convert to dict format
        result_dict = {}
        for (file_path, _), result in zip(file_writes.items(), results):
            result_dict[file_path] = result

        # Log summary
        successful = sum(1 for v in result_dict.values() if not isinstance(v, Exception))
        failed = len(result_dict) - successful
        logger.info(f"Batch write completed: {successful} successful, {failed} failed")

        return result_dict

    async def read_config_batch(
        self,
        config_paths: List[Union[str, Path]],
        default_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Read multiple configuration files and merge them into a single config dict.

        Useful for Dopemux workflows that need to load multiple related configs.

        Args:
            config_paths: List of config file paths (JSON/YAML)
            default_values: Default values to use if files are missing

        Returns:
            Merged configuration dictionary

        Example:
            configs = ['app.json', 'user.json', 'defaults.json']
            merged = await batch_ops.read_config_batch(configs)
        """
        results = await self.batch_read_files(config_paths)

        merged_config = default_values.copy() if default_values else {}

        for path, content in results.items():
            if isinstance(content, Exception):
                logger.warning(f"Skipping config file {path} due to error: {content}")
                continue

            try:
                # Simple JSON parsing (extend for YAML if needed)
                import json
                config_data = json.loads(content)
                merged_config.update(config_data)
                logger.debug(f"Merged config from {path}")
            except Exception as e:
                logger.error(f"Failed to parse config {path}: {e}")

        return merged_config

    async def backup_files(
        self,
        file_paths: List[Union[str, Path]],
        backup_suffix: str = '.backup'
    ) -> Dict[Union[str, Path], Union[Union[str, Path], Exception]]:
        """
        Create backup copies of multiple files.

        Args:
            file_paths: Files to backup
            backup_suffix: Suffix for backup files (default '.backup')

        Returns:
            Dict mapping original paths to backup paths (or Exception)
        """
        # Read all files first
        contents = await self.batch_read_files(file_paths)

        # Create backup writes
        backup_writes = {}
        for path, content in contents.items():
            if isinstance(content, Exception):
                backup_writes[path] = content  # Pass through the error
            else:
                backup_path = str(path) + backup_suffix
                backup_writes[backup_path] = content

        # Write backups
        return await self.batch_write_files({
            k: v for k, v in backup_writes.items()
            if not isinstance(v, Exception)
        })

    def get_active_operation_count(self) -> int:
        """Get the current number of active file operations."""
        # Note: This is approximate since semaphore doesn't expose current count
        return self.max_concurrent - self.semaphore._value

    def is_available(self) -> bool:
        """Check if the handler can accept new operations."""
        return self.semaphore._value > 0

    async def wait_for_availability(self) -> None:
        """Wait until at least one operation slot is available."""
        while not self.is_available():
            await asyncio.sleep(0.1)


# Convenience functions for common Dopemux patterns
async def batch_read_configs(
    config_paths: List[Union[str, Path]],
    max_concurrent: int = 10
) -> Dict[Union[str, Path], Union[str, Exception]]:
    """
    Convenience function to batch read configuration files.

    Args:
        config_paths: List of config file paths
        max_concurrent: Max concurrent reads

    Returns:
        Dict of file contents
    """
    handler = BatchFileOps(max_concurrent=max_concurrent)
    return await handler.batch_read_files(config_paths)


async def batch_backup_configs(
    config_paths: List[Union[str, Path]],
    backup_suffix: str = '.backup',
    max_concurrent: int = 10
) -> Dict[Union[str, Path], Union[Union[str, Path], Exception]]:
    """
    Convenience function to backup configuration files before modification.

    Args:
        config_paths: Config files to backup
        backup_suffix: Backup file suffix
        max_concurrent: Max concurrent operations

    Returns:
        Dict of backup results
    """
    handler = BatchFileOps(max_concurrent=max_concurrent)
    return await handler.backup_files(config_paths, backup_suffix)