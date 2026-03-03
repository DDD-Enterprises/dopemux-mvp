#!/usr/bin/env python3
"""
SQLite File Watcher for ConPort MCP
Monitors context.db for changes using watchdog
"""

import os
import sqlite3
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)


class ConPortDBWatcher(FileSystemEventHandler):
    """Watch ConPort MCP SQLite database for changes"""
    
    def __init__(self, db_path: str, callback: Callable[[Dict[str, Any]], None]):
        self.db_path = Path(db_path)
        self.callback = callback
        self.last_row_id = self._get_max_row_id()
        logger.info(f"👁️  Watching {self.db_path}, starting at row {self.last_row_id}")
    
    def _get_max_row_id(self, table: str = "decisions") -> int:
        """Get max row ID from decisions table"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX(id) FROM {table}")
            result = cursor.fetchone()
            conn.close()
            return result[0] or 0
        except Exception as e:
            logger.error(f"Error getting max row ID: {e}")
            return 0
    
    def on_modified(self, event):
        """Called when database file is modified"""
        if event.src_path != str(self.db_path):
            return
        
        # Check for new rows in decisions table
        self._check_new_decisions()
        
        # Could also check progress, system_patterns, etc.
    
    def _check_new_decisions(self):
        """Check for new decision rows and publish events"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get new rows since last check
            cursor.execute("""
                SELECT id, summary, rationale, implementation_details,
                       tags, timestamp
                FROM decisions
                WHERE id > ?
                ORDER BY id
            """, (self.last_row_id,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                # Convert row to dict
                decision = dict(row)
                
                # Publish event
                self.callback({
                    "event_type": "decision.logged",
                    "data": decision,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "source": "conport-mcp"
                })
                
                self.last_row_id = decision["id"]
            
            conn.close()
            
            if rows:
                logger.info(f"✅ Found {len(rows)} new decision(s)")
                
        except Exception as e:
            logger.error(f"❌ Error checking new decisions: {e}")
    
    def start_watching(self) -> Observer:
        """Start watching the database directory"""
        observer = Observer()
        observer.schedule(self, str(self.db_path.parent), recursive=False)
        observer.start()
        logger.info("✅ File system observer started")
        return observer


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(event):
        print(f"📨 Event: {event['event_type']}")
        print(f"   Summary: {event['data']['summary']}")
    
    # Find ConPort MCP database
    db_path = Path.home() / "code/dopemux-mvp/context_portal/context.db"
    
    if db_path.exists():
        watcher = ConPortDBWatcher(str(db_path), test_callback)
        observer = watcher.start_watching()
        
        try:
            import time
            print("\n👁️  Watching for changes... (Ctrl+C to stop)")
            print("   Create a decision in ConPort MCP to test\n")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n👋 Stopping...")
        observer.join()
    else:
        print(f"❌ Database not found: {db_path}")
