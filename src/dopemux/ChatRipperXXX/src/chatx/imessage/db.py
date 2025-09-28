"""Database copy and read-only utilities for iMessage extraction."""

import shutil
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator


@contextmanager
def copy_db_for_readonly(db_path: Path) -> Iterator[Path]:
    """Copy chat.db (+ WAL if present) to temp directory for read-only access.
    
    Args:
        db_path: Path to the original chat.db file
        
    Yields:
        Path to the temporary copy of the database
        
    Note:
        This ensures consistent reads by copying WAL files and prevents
        interference with active Messages app usage.
    """
    with TemporaryDirectory(prefix="chatx_imessage_") as temp_dir:
        temp_db_path = Path(temp_dir) / "chat.db"
        
        # Copy main database file
        shutil.copy2(db_path, temp_db_path)
        
        # Copy WAL file if present (Write-Ahead Logging)
        wal_path = db_path.with_suffix(".db-wal")
        if wal_path.exists():
            temp_wal_path = temp_db_path.with_suffix(".db-wal")
            shutil.copy2(wal_path, temp_wal_path)
            
        # Copy SHM file if present (Shared Memory)
        shm_path = db_path.with_suffix(".db-shm")
        if shm_path.exists():
            temp_shm_path = temp_db_path.with_suffix(".db-shm")
            shutil.copy2(shm_path, temp_shm_path)
            
        yield temp_db_path


def open_ro(db_path: Path) -> sqlite3.Connection:
    """Open SQLite database in read-only mode with appropriate pragmas.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Read-only SQLite connection
        
    Raises:
        sqlite3.OperationalError: If database cannot be opened
    """
    # Open with read-only immutable URI to avoid locks/writes
    uri = f"file:{db_path}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    
    # Additional read-only safety pragmas
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA temp_store = memory")
    
    # Optimize for read operations
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
    conn.execute("PRAGMA mmap_size = 268435456")  # 256MB mmap
    
    return conn
