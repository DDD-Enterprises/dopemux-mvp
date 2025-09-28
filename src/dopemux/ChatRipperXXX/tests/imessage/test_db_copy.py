"""Tests for database copy and read-only utilities."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from chatx.imessage.db import copy_db_for_readonly, open_ro


class TestCopyDbForReadonly:
    """Test safe database copying functionality."""
    
    def test_copies_main_db_file(self, tmp_path):
        """Test that main database file is copied correctly."""
        # Create a test database
        test_db = tmp_path / "test_chat.db"
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.execute("INSERT INTO test (data) VALUES ('test data')")
        conn.commit()
        conn.close()
        
        # Copy and verify
        with copy_db_for_readonly(test_db) as copied_db:
            assert copied_db.exists()
            assert copied_db.name == "chat.db"
            
            # Verify data is intact
            with sqlite3.connect(copied_db) as conn:
                result = conn.execute("SELECT data FROM test").fetchone()
                assert result[0] == "test data"
        
        # Verify cleanup
        assert not copied_db.exists()
    
    def test_copies_wal_file_when_present(self, tmp_path):
        """Test that WAL file is copied when present."""
        test_db = tmp_path / "test_chat.db"
        wal_file = tmp_path / "test_chat.db-wal"
        
        # Create test files
        test_db.write_text("fake db")
        wal_file.write_text("fake wal")
        
        with copy_db_for_readonly(test_db) as copied_db:
            copied_wal = copied_db.with_suffix(".db-wal")
            assert copied_wal.exists()
            assert copied_wal.read_text() == "fake wal"
    
    def test_copies_shm_file_when_present(self, tmp_path):
        """Test that SHM file is copied when present."""
        test_db = tmp_path / "test_chat.db"
        shm_file = tmp_path / "test_chat.db-shm"
        
        # Create test files
        test_db.write_text("fake db")
        shm_file.write_text("fake shm")
        
        with copy_db_for_readonly(test_db) as copied_db:
            copied_shm = copied_db.with_suffix(".db-shm")
            assert copied_shm.exists()
            assert copied_shm.read_text() == "fake shm"
    
    def test_cleanup_on_exception(self, tmp_path):
        """Test that temporary files are cleaned up even on exceptions."""
        test_db = tmp_path / "test_chat.db"
        test_db.write_text("fake db")
        
        temp_db_path = None
        try:
            with copy_db_for_readonly(test_db) as copied_db:
                temp_db_path = copied_db
                assert temp_db_path.exists()
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify cleanup happened despite exception
        assert not temp_db_path.exists()


class TestOpenRo:
    """Test read-only database connection utilities."""
    
    def test_opens_readonly_connection(self, tmp_path):
        """Test that connection is properly opened in read-only mode."""
        # Create test database
        test_db = tmp_path / "test.db"
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test DEFAULT VALUES")
        conn.commit()  # Make sure data is committed
        conn.close()
        
        # Open read-only and verify
        ro_conn = open_ro(test_db)
        
        # Should be able to read
        result = ro_conn.execute("SELECT COUNT(*) FROM test").fetchone()
        assert result[0] == 1
        
        # Should NOT be able to write
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            ro_conn.execute("INSERT INTO test DEFAULT VALUES")
        
        ro_conn.close()
    
    def test_handles_nonexistent_file(self, tmp_path):
        """Test error handling for nonexistent database file."""
        nonexistent = tmp_path / "does_not_exist.db"
        
        with pytest.raises(sqlite3.OperationalError):
            open_ro(nonexistent)