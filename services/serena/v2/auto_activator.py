"""
Serena v2 Auto-Activator

Automatically activates Serena v2 intelligence system when workspace is opened.
Provides seamless "magical" integration with zero manual configuration.

Features:
- Automatic workspace detection via .git directory
- Session restoration from NavigationSequence database
- LSP initialization with existing 31-component system
- File watcher integration for automatic code analysis
- ADHD-optimized progressive activation
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Import existing Serena intelligence components
# Use absolute imports to support both module and direct execution
try:
    from services.serena.v2.intelligence.database import SerenaIntelligenceDatabase, create_intelligence_database
    from services.serena.v2.intelligence import setup_complete_cognitive_load_management_system
    from services.serena.v2.file_watcher import FileWatcherManager
except ImportError:
    # Fallback for when run directly
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from services.serena.v2.intelligence.database import SerenaIntelligenceDatabase, create_intelligence_database
    from services.serena.v2.intelligence import setup_complete_cognitive_load_management_system
    from services.serena.v2.file_watcher import FileWatcherManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.serena' / 'auto_activator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SerenaAutoActivator:
    """
    Automatically activates Serena v2 on workspace open.

    Leverages existing 31-component intelligence system with minimal new code.
    """

    def __init__(self):
        self.workspace_path: Optional[Path] = None
        self.session_context: Optional[Dict[str, Any]] = None
        self.serena_system: Optional[Dict[str, Any]] = None
        self.database: Optional[SerenaIntelligenceDatabase] = None
        self.file_watcher: Optional[FileWatcherManager] = None

    def detect_workspace(self, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Detect workspace root by searching for .git directory.

        Args:
            start_path: Starting directory for search (defaults to current directory)

        Returns:
            Absolute path to workspace root or None if not found

        Performance: <50ms
        """
        start_time = time.perf_counter()

        try:
            # Start from provided path or current directory
            current = Path(start_path or Path.cwd()).resolve()

            logger.debug(f"Searching for workspace starting from: {current}")

            # Walk up directory tree looking for .git
            max_depth = 10  # Prevent infinite loops
            for _ in range(max_depth):
                git_dir = current / '.git'

                # Check if .git exists (file or directory)
                if git_dir.exists():
                    # Resolve any symlinks
                    workspace = current.resolve()

                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    logger.info(f"Workspace detected: {workspace} ({elapsed_ms:.2f}ms)")

                    return workspace

                # Move up one directory
                parent = current.parent
                if parent == current:
                    # Reached filesystem root
                    break
                current = parent

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(f"No workspace found starting from {start_path or Path.cwd()} ({elapsed_ms:.2f}ms)")
            return None

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error detecting workspace: {e} ({elapsed_ms:.2f}ms)")
            return None

    async def connect_database(self) -> bool:
        """
        Connect to existing Serena intelligence database and validate schema.

        Uses existing SerenaIntelligenceDatabase class for connection pooling
        and optimized performance.

        Returns:
            True if connection successful and schema valid, False otherwise
        """
        start_time = time.perf_counter()

        try:
            logger.info("Connecting to Serena intelligence database...")

            # Use existing database creation function (includes connection pooling)
            self.database = await create_intelligence_database()

            # Validate that navigation_patterns table exists
            validation_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'navigation_patterns'
            );
            """

            result = await self.database.execute_query(validation_query)

            if result and result[0].get('exists', False):
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(f"Database connected and schema validated ({elapsed_ms:.2f}ms)")
                return True
            else:
                logger.error("navigation_patterns table not found in database")
                return False

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Database connection failed: {e} ({elapsed_ms:.2f}ms)")
            return False

    async def get_last_session(self) -> Optional[Dict[str, Any]]:
        """
        Query most recent NavigationSequence for current workspace.

        Queries navigation_patterns table by workspace_path and returns
        the most recent session context.

        Returns:
            Dictionary with session data or None if no session found

        Performance: <100ms
        """
        start_time = time.perf_counter()

        if not self.database or not self.workspace_path:
            logger.error("Database or workspace not initialized")
            return None

        try:
            workspace_str = str(self.workspace_path)

            # Query for most recent navigation pattern for this workspace
            query = """
            SELECT
                id,
                user_session_id,
                workspace_path,
                pattern_sequence,
                pattern_type,
                context_switches,
                total_duration_ms,
                complexity_progression,
                effectiveness_score,
                completion_status,
                attention_span_seconds,
                adhd_accommodations,
                created_at,
                updated_at,
                last_occurrence
            FROM navigation_patterns
            WHERE workspace_path = $1
            ORDER BY last_occurrence DESC
            LIMIT 1
            """

            results = await self.database.execute_query(query, (workspace_str,))

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if results and len(results) > 0:
                session_data = results[0]
                logger.info(f"Last session found (last active: {session_data['last_occurrence']}) ({elapsed_ms:.2f}ms)")
                return session_data
            else:
                logger.info(f"No previous session found for workspace ({elapsed_ms:.2f}ms)")
                return None

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error querying last session: {e} ({elapsed_ms:.2f}ms)")
            return None

    def restore_session_context(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Restore session context from NavigationSequence data.

        Extracts: file_path, symbol, breadcrumbs, attention_state from pattern_sequence JSON.

        Args:
            session_data: Raw database row from navigation_patterns table

        Returns:
            Structured context dictionary or None if data corrupted
        """
        start_time = time.perf_counter()

        try:
            # Extract pattern_sequence JSON
            pattern_sequence = session_data.get('pattern_sequence', {})

            if not pattern_sequence:
                logger.warning("No pattern_sequence data in session")
                return None

            # Build context from available data
            context = {
                'workspace_path': session_data.get('workspace_path'),
                'user_session_id': session_data.get('user_session_id'),
                'pattern_type': session_data.get('pattern_type', 'exploration'),
                'last_active': session_data.get('last_occurrence'),
                'effectiveness_score': session_data.get('effectiveness_score', 0.0),
                'attention_span_seconds': session_data.get('attention_span_seconds', 0),
                'adhd_accommodations': session_data.get('adhd_accommodations', {}),
                'pattern_data': pattern_sequence,
                'restored_at': datetime.now(timezone.utc)
            }

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Session context restored ({elapsed_ms:.2f}ms)")

            self.session_context = context
            return context

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error restoring session context: {e} ({elapsed_ms:.2f}ms)")
            return None

    async def initialize_serena_system(self) -> bool:
        """
        Initialize complete Serena v2 cognitive load management system.

        Calls existing setup_complete_cognitive_load_management_system() which
        initializes all 31 components including database, graph operations,
        adaptive learning, ConPort bridge, and more.

        Returns:
            True if initialization successful, False otherwise

        Performance: <1 second
        """
        start_time = time.perf_counter()

        try:
            logger.info("Initializing Serena v2 cognitive load management system...")

            workspace_str = str(self.workspace_path) if self.workspace_path else None

            # Call existing setup function (31 components!)
            self.serena_system = await setup_complete_cognitive_load_management_system(
                database_config=None,  # Uses defaults
                workspace_id=workspace_str,
                performance_monitor=None  # Creates new one
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            if self.serena_system:
                logger.info(f"Serena v2 initialized successfully ({elapsed_ms:.2f}ms)")
                logger.info(f"  Version: {self.serena_system.get('version')}")
                logger.info(f"  Components: {self.serena_system.get('total_components')}")
                logger.info(f"  Phase 2E: {self.serena_system.get('phase2e_complete')}")
                return True
            else:
                logger.error(f"Serena initialization failed ({elapsed_ms:.2f}ms)")
                return False

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error initializing Serena system: {e} ({elapsed_ms:.2f}ms)")
            return False

    def display_welcome_message(self, context: Optional[Dict[str, Any]]) -> None:
        """
        Display welcome back message with session context.

        Shows: time since last session, pattern type, effectiveness score,
        and ADHD-friendly continuation options.

        Args:
            context: Restored session context or None for fresh workspace
        """
        print("\n" + "=" * 60)
        print("  SERENA V2 - ADHD-OPTIMIZED CODE INTELLIGENCE")
        print("=" * 60)

        if context:
            last_active = context.get('last_active')
            if last_active:
                time_ago = datetime.now(timezone.utc) - last_active
                if time_ago.days > 0:
                    time_str = f"{time_ago.days} days ago"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds // 3600} hours ago"
                else:
                    time_str = f"{time_ago.seconds // 60} minutes ago"

                print(f"\n  Welcome back! Last session was {time_str}")
            else:
                print(f"\n  Welcome back!")

            print(f"  Pattern: {context.get('pattern_type', 'exploration')}")
            print(f"  Effectiveness: {context.get('effectiveness_score', 0.0):.1%}")

            if context.get('attention_span_seconds', 0) > 0:
                attention_min = context.get('attention_span_seconds') // 60
                print(f"  Last attention span: {attention_min} minutes")

            print("\n  Ready to continue where you left off!")
        else:
            print("\n  Welcome to a fresh workspace!")
            print("  Serena v2 is ready to learn your navigation patterns.")

        print("\n" + "=" * 60)
        print()

    def start_file_watcher(self) -> bool:
        """
        Start file watcher for automatic code change detection.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            if not self.serena_system or not self.workspace_path:
                logger.error("Cannot start file watcher - system not initialized")
                return False

            self.file_watcher = FileWatcherManager(
                self.serena_system,
                self.workspace_path
            )

            return self.file_watcher.start()

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            return False

    def stop_file_watcher(self) -> None:
        """Stop file watcher gracefully."""
        if self.file_watcher:
            self.file_watcher.stop()


async def main():
    """Main entry point for auto-activator."""
    logger.info("=" * 60)
    logger.info("Serena v2 Auto-Activator Starting")
    logger.info("=" * 60)

    # Create activator instance
    activator = SerenaAutoActivator()

    # Task 1.1: Detect workspace
    workspace = activator.detect_workspace()

    if not workspace:
        logger.error("No workspace detected - cannot activate Serena v2")
        logger.info("Make sure you're in a git repository")
        sys.exit(1)

    activator.workspace_path = workspace
    logger.info(f"Workspace: {workspace}")

    # Task 1.2: Connect to database
    db_connected = await activator.connect_database()

    if not db_connected:
        logger.error("Database connection failed - cannot activate Serena v2")
        sys.exit(1)

    logger.info("Database connection successful")

    # Task 1.3: Query last session
    last_session = await activator.get_last_session()

    # Task 1.4: Restore session context (if session exists)
    restored_context = None
    if last_session:
        restored_context = activator.restore_session_context(last_session)

    # Task 1.5: Initialize Serena v2 system (31 components)
    system_initialized = await activator.initialize_serena_system()

    if not system_initialized:
        logger.error("Serena system initialization failed")
        await activator.database.close()
        sys.exit(1)

    # Task 1.6: Display welcome message
    activator.display_welcome_message(restored_context)

    logger.info("=" * 60)
    logger.info("EPIC 1 COMPLETE: Auto-Activator Foundation Ready")
    logger.info("=" * 60)

    # Epic 2: Start file watcher for automatic code change detection
    watcher_started = activator.start_file_watcher()

    if watcher_started:
        logger.info("=" * 60)
        logger.info("EPIC 2 COMPLETE: File Watcher Active")
        logger.info("All seamless integration components operational")
        logger.info("=" * 60)
        print("\nSerena v2 is now watching your workspace...")
        print("Code changes will be automatically analyzed!")
        print("\nPress Ctrl+C to stop\n")

        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            activator.stop_file_watcher()
    else:
        logger.warning("File watcher failed to start - running in manual mode")

    # Cleanup
    if activator.serena_system and activator.serena_system.get('database'):
        await activator.serena_system['database'].close()
    elif activator.database:
        await activator.database.close()


if __name__ == "__main__":
    # Ensure .serena directory exists
    serena_dir = Path.home() / '.serena'
    serena_dir.mkdir(exist_ok=True)

    # Run async main
    asyncio.run(main())
