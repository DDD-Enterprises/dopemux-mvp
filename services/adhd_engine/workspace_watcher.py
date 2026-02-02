"""
Workspace Watcher - Monitors file system activity for ADHD events.

Phase 7: Full I/O Wiring

Emits events to EventBus when file activity is detected:
- FILE_OPENED (when file is accessed)
- FILE_SAVED (when file is modified)
- FILE_UNCHANGED_30MIN (when same file stays open without changes)

Uses watchdog library for efficient filesystem monitoring.
Falls back to poll-based approach if watchdog is unavailable.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import watchdog for efficient monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not available - using poll-based file monitoring")


@dataclass
class FileActivity:
    """Record of file activity."""
    file_path: str
    action: str  # opened, saved, closed
    timestamp: datetime = field(default_factory=datetime.now)
    line_count: Optional[int] = None


class WorkspaceEventEmitter:
    """
    Emit file activity events to EventBus.
    
    Can be used with watchdog FileSystemEventHandler or poll-based approach.
    """
    
    # File extensions to track
    TRACKED_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.rb', '.java',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.kt', '.scala',
        '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.sh', '.bash',
        '.html', '.css', '.scss', '.less', '.sql'
    }
    
    # Directories to ignore
    IGNORED_DIRS = {
        '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
        '.mypy_cache', '.pytest_cache', '.tox', 'dist', 'build',
        '.next', '.nuxt', 'coverage', '.coverage', 'htmlcov',
        '.eggs', '*.egg-info', '.cache', '.idea', '.vscode'
    }
    
    def __init__(self, event_bus, workspace_path: str):
        """
        Initialize workspace event emitter.
        
        Args:
            event_bus: EventBus instance for publishing events
            workspace_path: Root path to monitor
        """
        self.event_bus = event_bus
        self.workspace_path = Path(workspace_path).resolve()
        
        # Track file activity
        self.last_modified: Dict[str, datetime] = {}
        self.file_activity: List[FileActivity] = []
        self._activity_lock = asyncio.Lock()
        
        # Track unchanged files for hyperfocus detection
        self._unchanged_check_interval = 300  # 5 minutes
        self._unchanged_threshold = 1800  # 30 minutes
    
    def should_track(self, path: str) -> bool:
        """Check if file should be tracked."""
        try:
            path_obj = Path(path)
            
            # Check extension
            if path_obj.suffix.lower() not in self.TRACKED_EXTENSIONS:
                return False
            
            # Check for ignored directories
            parts = path_obj.parts
            for ignored in self.IGNORED_DIRS:
                if ignored in parts:
                    return False
            
            return True
        except Exception:
            return False
    
    async def emit_file_event(self, file_path: str, action: str):
        """
        Emit file activity event to EventBus.
        
        Args:
            file_path: Path to the file
            action: 'opened', 'saved', or 'closed'
        """
        if not self.should_track(file_path):
            return
        
        try:
            # Determine event type
            from event_bus import Event, EventType
            
            if action == "saved":
                event_type = EventType.FILE_SAVED
            elif action == "opened":
                event_type = EventType.FILE_OPENED
            else:
                event_type = getattr(EventType, 'FILE_ACTIVITY', 'file_activity')
            
            # Get relative path for cleaner logging
            try:
                rel_path = Path(file_path).relative_to(self.workspace_path)
            except ValueError:
                rel_path = file_path
            
            event = Event(
                type=event_type,
                data={
                    "file": str(file_path),
                    "relative_path": str(rel_path),
                    "action": action,
                    "timestamp": datetime.now().isoformat(),
                    "extension": Path(file_path).suffix
                },
                source="workspace_watcher"
            )
            
            await self.event_bus.publish("dopemux:events", event)
            
            # Track activity
            async with self._activity_lock:
                self.last_modified[file_path] = datetime.now()
                self.file_activity.append(FileActivity(
                    file_path=file_path,
                    action=action
                ))
                
                # Keep only last 100 activities
                if len(self.file_activity) > 100:
                    self.file_activity = self.file_activity[-100:]
            
            logger.debug(f"📁 File {action}: {rel_path}")
            
        except ImportError:
            logger.warning("EventBus not available - file event not emitted")
        except Exception as e:
            logger.error(f"Failed to emit file event: {e}")
    
    async def check_unchanged_files(self):
        """Check for files unchanged for extended periods (hyperfocus indicator)."""
        try:
            now = datetime.now()
            unchanged_threshold = timedelta(seconds=self._unchanged_threshold)
            
            for file_path, last_mod in list(self.last_modified.items()):
                if now - last_mod > unchanged_threshold:
                    # File unchanged for >30 min - possible hyperfocus
                    from event_bus import Event, EventType
                    
                    event = Event(
                        type=getattr(EventType, 'FILE_UNCHANGED_30MIN', 'file_unchanged'),
                        data={
                            "file": file_path,
                            "unchanged_minutes": int((now - last_mod).total_seconds() / 60),
                            "timestamp": now.isoformat()
                        },
                        source="workspace_watcher"
                    )
                    
                    await self.event_bus.publish("dopemux:events", event)
                    logger.info(f"🔥 Possible hyperfocus: {file_path} unchanged for 30+ min")
                    
                    # Remove from tracking to avoid repeated alerts
                    del self.last_modified[file_path]
                    
        except Exception as e:
            logger.error(f"Error checking unchanged files: {e}")
    
    def get_recent_activity(self, minutes: int = 15) -> List[FileActivity]:
        """Get file activity from the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [a for a in self.file_activity if a.timestamp > cutoff]


if WATCHDOG_AVAILABLE:
    class WatchdogHandler(FileSystemEventHandler):
        """Watchdog event handler that bridges to async WorkspaceEventEmitter."""
        
        def __init__(self, emitter: WorkspaceEventEmitter, loop: asyncio.AbstractEventLoop):
            self.emitter = emitter
            self.loop = loop
            super().__init__()
        
        def on_modified(self, event):
            if event.is_directory:
                return
            if self.emitter.should_track(event.src_path):
                asyncio.run_coroutine_threadsafe(
                    self.emitter.emit_file_event(event.src_path, "saved"),
                    self.loop
                )
        
        def on_created(self, event):
            if event.is_directory:
                return
            if self.emitter.should_track(event.src_path):
                asyncio.run_coroutine_threadsafe(
                    self.emitter.emit_file_event(event.src_path, "opened"),
                    self.loop
                )


class WorkspaceWatcher:
    """
    High-level workspace watcher that monitors file system activity.
    
    Uses watchdog for efficient monitoring when available,
    falls back to poll-based approach otherwise.
    """
    
    def __init__(self, event_bus, workspace_path: str):
        """
        Initialize workspace watcher.
        
        Args:
            event_bus: EventBus instance for publishing events
            workspace_path: Root path to monitor
        """
        self.event_bus = event_bus
        self.workspace_path = Path(workspace_path).resolve()
        self.emitter = WorkspaceEventEmitter(event_bus, workspace_path)
        
        self._running = False
        self._observer = None
        self._poll_task = None
        self._unchanged_task = None
    
    async def start(self):
        """Start watching the workspace."""
        if self._running:
            return
        
        self._running = True
        
        if WATCHDOG_AVAILABLE:
            await self._start_watchdog()
        else:
            await self._start_polling()
        
        # Start unchanged file checker
        self._unchanged_task = asyncio.create_task(
            self._check_unchanged_loop()
        )
        
        logger.info(f"👁️ Workspace Watcher started for {self.workspace_path}")
    
    async def _start_watchdog(self):
        """Start watchdog-based monitoring."""
        loop = asyncio.get_event_loop()
        handler = WatchdogHandler(self.emitter, loop)
        
        self._observer = Observer()
        self._observer.schedule(handler, str(self.workspace_path), recursive=True)
        self._observer.start()
        
        logger.info("Using watchdog for efficient file monitoring")
    
    async def _start_polling(self):
        """Start poll-based monitoring (fallback)."""
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Using poll-based file monitoring (install watchdog for efficiency)")
    
    async def _poll_loop(self):
        """Poll filesystem for changes (fallback when watchdog unavailable)."""
        known_mtimes: Dict[str, float] = {}
        poll_interval = 5  # seconds
        
        while self._running:
            try:
                for root, dirs, files in os.walk(self.workspace_path):
                    # Skip ignored directories
                    dirs[:] = [d for d in dirs if d not in self.emitter.IGNORED_DIRS]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        if not self.emitter.should_track(file_path):
                            continue
                        
                        try:
                            mtime = os.path.getmtime(file_path)
                            
                            if file_path in known_mtimes:
                                if mtime > known_mtimes[file_path]:
                                    # File was modified
                                    await self.emitter.emit_file_event(file_path, "saved")
                            
                            known_mtimes[file_path] = mtime
                        except OSError:
                            continue
                
                await asyncio.sleep(poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Poll loop error: {e}")
                await asyncio.sleep(poll_interval)
    
    async def _check_unchanged_loop(self):
        """Periodically check for unchanged files."""
        while self._running:
            try:
                await asyncio.sleep(self.emitter._unchanged_check_interval)
                await self.emitter.check_unchanged_files()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unchanged check error: {e}")
    
    async def stop(self):
        """Stop watching the workspace."""
        self._running = False
        
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        
        if self._unchanged_task:
            self._unchanged_task.cancel()
            try:
                await self._unchanged_task
            except asyncio.CancelledError:
                pass
            self._unchanged_task = None
        
        logger.info("📭 Workspace Watcher stopped")
    
    def get_recent_activity(self, minutes: int = 15) -> List[FileActivity]:
        """Get recent file activity."""
        return self.emitter.get_recent_activity(minutes)


def create_workspace_watcher(event_bus, workspace_path: str) -> WorkspaceWatcher:
    """
    Factory function to create workspace watcher.
    
    Args:
        event_bus: EventBus instance
        workspace_path: Path to monitor
        
    Returns:
        Configured WorkspaceWatcher
    """
    return WorkspaceWatcher(event_bus, workspace_path)
