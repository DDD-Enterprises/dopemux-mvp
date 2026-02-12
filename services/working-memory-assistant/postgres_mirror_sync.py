"""
Dope-Memory Postgres Mirror Sync Worker.

Asynchronously replicates data from SQLite canonical store to Postgres mirror.
Runs as a background task, syncing new entries periodically.

Per spec 03_data_model_postgres.md:
- SQLite is canonical (single-user, edge)
- Postgres is mirror (multi-service, analytics, search)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import asyncpg

from canonical_ledger import CanonicalLedgerError, resolve_canonical_ledger
from chronicle.store import ChronicleStore

logger = logging.getLogger(__name__)

# Configuration
POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    os.getenv("DATABASE_URL", "postgresql://localhost:5432/dopemux"),
)
SYNC_INTERVAL_SEC = int(os.getenv("MIRROR_SYNC_INTERVAL_SEC", "60"))  # Default: 1 minute
BATCH_SIZE = int(os.getenv("MIRROR_SYNC_BATCH_SIZE", "100"))
TARGET_SCHEMA_VERSION = "v1.0.3"
MIRROR_SCHEMA_RESET = os.getenv("MIRROR_SCHEMA_RESET", "false").strip().lower() == "true"


class PostgresMirrorSync:
    """
    Syncs data from SQLite canonical stores to Postgres mirror.

    Uses a simple bookmark approach:
    - Tracks last synced timestamp per workspace
    - Fetches new entries since last sync
    - Upserts into Postgres mirror tables
    """

    def __init__(
        self,
        postgres_url: str = POSTGRES_URL,
        sync_interval_sec: int = SYNC_INTERVAL_SEC,
        batch_size: int = BATCH_SIZE,
    ):
        self.postgres_url = postgres_url
        self.sync_interval_sec = sync_interval_sec
        self.batch_size = batch_size

        self.pool: Optional[asyncpg.Pool] = None
        self._running = False
        self._stores: dict[str, ChronicleStore] = {}

        # Bookmarks: (workspace_id, ledger_path) -> last_synced_ts
        self._work_log_bookmarks: dict[tuple[str, str], str] = {}
        self._raw_event_bookmarks: dict[str, str] = {}
        self._issue_link_bookmarks: dict[tuple[str, str], str] = {}

    async def initialize(self) -> None:
        """Initialize Postgres connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=1,
                max_size=5,
                command_timeout=30,
            )
            logger.info(f"✅ Postgres mirror sync: connected to {self.postgres_url}")

            # Ensure schema exists
            await self._ensure_schema()
            await self._load_bookmarks()

        except Exception as e:
            logger.error(f"❌ Failed to initialize Postgres mirror sync: {e}")
            raise

    async def _ensure_schema(self) -> None:
        """Apply migration if not already applied."""
        if not self.pool:
            return

        try:
            schema_path = Path(__file__).parent / "chronicle" / "postgres_mirror.sql"
            reset_schema_path = Path(__file__).parent / "chronicle" / "postgres_mirror_reset.sql"
            if not schema_path.exists():
                logger.warning(f"⚠️  Postgres mirror schema not found: {schema_path}")
                return

            async with self.pool.acquire() as conn:
                if MIRROR_SCHEMA_RESET:
                    if not reset_schema_path.exists():
                        raise RuntimeError(
                            f"MIRROR_SCHEMA_RESET=true but reset SQL not found: {reset_schema_path}"
                        )
                    logger.warning("💣 MIRROR_SCHEMA_RESET=true, executing destructive reset")
                    reset_sql = reset_schema_path.read_text()
                    await conn.execute(reset_sql)
                    logger.warning("💣 Mirror schema reset completed")
                else:
                    logger.info("🪞 Mirror schema reset skipped (MIRROR_SCHEMA_RESET=false)")

                # Check if already migrated
                exists = await conn.fetchval(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = 'dm_schema_migrations'"
                )
                if exists:
                    version = await conn.fetchval(
                        "SELECT version FROM dm_schema_migrations WHERE version = $1 LIMIT 1",
                        TARGET_SCHEMA_VERSION,
                    )
                    if version == TARGET_SCHEMA_VERSION:
                        logger.info(
                            "✅ Postgres mirror schema already at %s",
                            TARGET_SCHEMA_VERSION,
                        )
                        return

                # Apply schema
                schema_sql = schema_path.read_text()
                await conn.execute(schema_sql)
                logger.info("✅ Applied Postgres mirror schema %s", TARGET_SCHEMA_VERSION)

        except Exception as e:
            logger.warning(f"⚠️  Could not ensure Postgres schema: {e}")

    async def _load_bookmarks(self) -> None:
        """Load persisted bookmarks into memory."""
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT workspace_id, ledger_path, last_work_log_created_at, last_issue_link_created_at
                FROM dm_mirror_bookmarks
                """
            )

        loaded = 0
        for row in rows:
            workspace_id = row["workspace_id"]
            ledger_path = row["ledger_path"]
            work_log_ts = row["last_work_log_created_at"]
            issue_link_ts = row["last_issue_link_created_at"]
            key = (workspace_id, ledger_path)
            if work_log_ts:
                self._work_log_bookmarks[key] = work_log_ts.isoformat()
            if issue_link_ts:
                self._issue_link_bookmarks[key] = issue_link_ts.isoformat()
            loaded += 1

        logger.info("🪞 Loaded mirror bookmarks for %d workspace(s)", loaded)

    def _get_store(self, ledger_path: str) -> Optional[ChronicleStore]:
        """Get or create a ChronicleStore for the given canonical ledger path."""
        db_path = Path(ledger_path)
        if not db_path.exists():
            return None
        path_key = str(db_path)
        if path_key not in self._stores:
            store = ChronicleStore(db_path)
            store.initialize_schema()
            self._stores[path_key] = store
        return self._stores[path_key]

    def _discover_workspaces(self) -> list[str]:
        """Discover workspaces with canonical chronicle ledgers.

        Returns workspace_ids (canonical ledger paths) for sync.
        """
        try:
            ledger = resolve_canonical_ledger()
            if ledger.exists():
                return [str(ledger)]
        except CanonicalLedgerError:
            pass
        return []

    async def start(self) -> None:
        """Start the sync worker."""
        if not self.pool:
            await self.initialize()

        self._running = True
        logger.info(f"📤 Postgres mirror sync started (interval: {self.sync_interval_sec}s)")

        # Force one immediate cycle so startup failures are visible immediately.
        try:
            await self._sync_all_workspaces()
        except Exception:
            logger.exception("❌ Mirror sync immediate tick failed")

        while self._running:
            try:
                await asyncio.sleep(self.sync_interval_sec)
                await self._sync_all_workspaces()
            except asyncio.CancelledError:
                logger.info("📤 Postgres mirror sync stopping")
                break
            except Exception:
                logger.exception("❌ Mirror sync loop error")
                await asyncio.sleep(self.sync_interval_sec)

    async def stop(self) -> None:
        """Stop the sync worker."""
        self._running = False
        if self.pool:
            await self.pool.close()
        logger.info("📤 Postgres mirror sync stopped")

    async def _sync_all_workspaces(self) -> None:
        """Sync all discovered workspaces."""
        logger.info("🪞 Mirror sync tick start")
        ledger_paths = self._discover_workspaces()
        workspace_id = os.getenv("DOPE_MEMORY_WORKSPACE_ID", "default").strip() or "default"
        logger.info(
            "🪞 Mirror sync discovered ledgers: %s workspace_id=%s",
            ledger_paths,
            workspace_id,
        )
        if not ledger_paths:
            return

        for ledger_path in ledger_paths:
            try:
                await self._sync_workspace(workspace_id, ledger_path)
            except Exception as e:
                logger.warning(
                    "⚠️  Failed to sync workspace=%s ledger=%s: %s",
                    workspace_id,
                    ledger_path,
                    e,
                )

    async def _sync_workspace(self, workspace_id: str, ledger_path: str) -> None:
        """Sync a single workspace to Postgres."""
        store = self._get_store(ledger_path)
        if not store:
            return

        # Sync work log entries
        work_log_count = await self._sync_work_log_entries(workspace_id, ledger_path, store)

        # Sync raw events (optional, may skip if too many)
        raw_event_count = await self._sync_raw_events(workspace_id, ledger_path, store)

        # Sync issue links
        issue_link_count = await self._sync_issue_links(workspace_id, ledger_path, store)

        if work_log_count > 0 or issue_link_count > 0:
            await self._persist_bookmarks(workspace_id, ledger_path)

        total = work_log_count + raw_event_count + issue_link_count
        if total > 0:
            logger.info(
                "📤 Synced workspace=%s ledger=%s: %d work log, %d raw, %d links",
                workspace_id,
                ledger_path,
                work_log_count,
                raw_event_count,
                issue_link_count,
            )

    async def _sync_work_log_entries(
        self, workspace_id: str, ledger_path: str, store: ChronicleStore
    ) -> int:
        """Sync work log entries to Postgres."""
        if not self.pool:
            return 0

        # Get last synced timestamp
        bookmark_key = (workspace_id, ledger_path)
        last_ts = self._work_log_bookmarks.get(bookmark_key, "1970-01-01T00:00:00Z")

        # Query new entries from SQLite
        conn = store.connect()
        cursor = conn.execute(
            """
            SELECT id, workspace_id, instance_id, session_id, ts_utc,
                   category, entry_type, workflow_phase, summary, details_json,
                   reasoning, outcome, importance_score, tags_json,
                   linked_files_json, linked_commits_json, linked_decisions_json,
                   linked_chat_range_json, parent_entry_id, duration_sec,
                   created_at_utc, updated_at_utc
            FROM work_log_entries
            WHERE created_at_utc > ?
            ORDER BY created_at_utc ASC
            LIMIT ?
            """,
            (last_ts, self.batch_size),
        )

        rows = cursor.fetchall()
        if not rows:
            logger.info(
                "🪞 work_log_entries sync workspace=%s ledger=%s selected=0 inserted=0 skipped=0 last_ts=%s",
                workspace_id,
                ledger_path,
                last_ts,
            )
            return 0

        # Insert into Postgres
        count = 0
        skipped = 0
        skipped_samples: list[str] = []
        async with self.pool.acquire() as pg_conn:
            for row in rows:
                try:
                    await pg_conn.execute(
                        """
                        INSERT INTO dm_work_log_entries (
                            id, workspace_id, ledger_path, instance_id, session_id, ts,
                            category, entry_type, workflow_phase, summary, details,
                            reasoning, outcome, importance_score, tags,
                            linked_files, linked_commits, linked_decisions,
                            linked_chat_range, parent_entry_id, duration_seconds,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6::timestamptz,
                                  $7, $8, $9, $10, $11::jsonb,
                                  $12, $13, $14, $15::text[],
                                  $16::jsonb, $17::text[], $18::text[],
                                  $19::jsonb, $20, $21,
                                  $22::timestamptz, $23::timestamptz)
                        ON CONFLICT (id) DO UPDATE SET
                            updated_at = EXCLUDED.updated_at
                        """,
                        row[0],  # id
                        workspace_id,
                        ledger_path,
                        row[2],  # instance_id
                        row[3],  # session_id
                        self._to_datetime(row[4]),  # ts_utc
                        row[5],  # category
                        row[6],  # entry_type
                        row[7],  # workflow_phase
                        row[8],  # summary
                        row[9],  # details_json (already JSON string)
                        row[10],  # reasoning
                        row[11],  # outcome
                        row[12],  # importance_score
                        json.loads(row[13] or "[]"),  # tags_json -> array
                        row[14],  # linked_files_json
                        json.loads(row[15] or "[]"),  # linked_commits_json -> array
                        self._to_text_array(row[16]),
                        row[17],  # linked_chat_range_json
                        row[18],  # parent_entry_id
                        row[19],  # duration_sec
                        self._to_datetime(row[20]),  # created_at_utc
                        self._to_datetime(row[21]),  # updated_at_utc
                    )
                    count += 1
                    self._work_log_bookmarks[bookmark_key] = row[20]  # created_at_utc
                except Exception as e:
                    skipped += 1
                    if len(skipped_samples) < 3:
                        skipped_samples.append(f"{row[0]}: {e}")
                    logger.debug("Skip work log %s: %s", row[0], e)

        logger.info(
            "🪞 work_log_entries sync workspace=%s ledger=%s selected=%d inserted=%d skipped=%d last_ts=%s",
            workspace_id,
            ledger_path,
            len(rows),
            count,
            skipped,
            last_ts,
        )
        if skipped_samples:
            logger.info("🪞 work_log_entries skip_samples=%s", skipped_samples)

        return count

    async def _sync_raw_events(
        self, workspace_id: str, ledger_path: str, store: ChronicleStore
    ) -> int:
        """Sync raw events to Postgres (limited batch)."""
        # For raw events, we only sync recent ones to avoid overwhelming Postgres
        # The canonical SQLite is the source of truth with TTL cleanup
        return 0  # Skip for Phase 1, implement in Phase 2 if needed

    async def _sync_issue_links(
        self, workspace_id: str, ledger_path: str, store: ChronicleStore
    ) -> int:
        """Sync issue links to Postgres."""
        if not self.pool:
            return 0

        bookmark_key = (workspace_id, ledger_path)
        last_ts = self._issue_link_bookmarks.get(bookmark_key, "1970-01-01T00:00:00Z")

        conn = store.connect()
        cursor = conn.execute(
            """
            SELECT id, workspace_id, instance_id, issue_entry_id, resolution_entry_id,
                   confidence, evidence_window_min, created_at_utc
            FROM issue_links
            WHERE created_at_utc > ?
            ORDER BY created_at_utc ASC
            LIMIT ?
            """,
            (last_ts, self.batch_size),
        )

        rows = cursor.fetchall()
        if not rows:
            logger.info(
                "🪞 issue_links sync workspace=%s ledger=%s selected=0 inserted=0 skipped=0 last_ts=%s",
                workspace_id,
                ledger_path,
                last_ts,
            )
            return 0

        count = 0
        skipped = 0
        skipped_samples: list[str] = []
        async with self.pool.acquire() as pg_conn:
            for row in rows:
                try:
                    await pg_conn.execute(
                        """
                        INSERT INTO dm_issue_links (
                            id, workspace_id, ledger_path, instance_id, issue_entry_id,
                            resolution_entry_id, confidence, evidence_window_min, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::timestamptz)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        row[0],
                        workspace_id,
                        ledger_path,
                        row[2],  # instance_id
                        row[3],  # issue_entry_id
                        row[4],  # resolution_entry_id
                        row[5],  # confidence
                        row[6],  # evidence_window_min
                        self._to_datetime(row[7]),  # created_at_utc
                    )
                    count += 1
                    self._issue_link_bookmarks[bookmark_key] = row[7]
                except Exception as e:
                    skipped += 1
                    if len(skipped_samples) < 3:
                        skipped_samples.append(f"{row[0]}: {e}")
                    logger.debug("Skip issue link %s: %s", row[0], e)

        logger.info(
            "🪞 issue_links sync workspace=%s ledger=%s selected=%d inserted=%d skipped=%d last_ts=%s",
            workspace_id,
            ledger_path,
            len(rows),
            count,
            skipped,
            last_ts,
        )
        if skipped_samples:
            logger.info("🪞 issue_links skip_samples=%s", skipped_samples)

        return count

    def _to_text_array(self, json_str: Optional[str]) -> Optional[list[str]]:
        """Convert JSON array string to text array."""
        if not json_str:
            return None
        try:
            items = json.loads(json_str)
            return [str(x) for x in items] if items else None
        except json.JSONDecodeError:
            return None

    def _to_datetime(self, value: Any) -> Optional[datetime]:
        """Convert ISO datetime strings to datetime for asyncpg."""
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        raise TypeError(f"Unsupported datetime value type: {type(value)}")

    async def _persist_bookmarks(self, workspace_id: str, ledger_path: str) -> None:
        """Persist in-memory bookmarks for a workspace+ledger to Postgres."""
        if not self.pool:
            return

        key = (workspace_id, ledger_path)
        work_log_ts = self._to_datetime(self._work_log_bookmarks.get(key))
        issue_link_ts = self._to_datetime(self._issue_link_bookmarks.get(key))

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO dm_mirror_bookmarks (
                    workspace_id, ledger_path, last_work_log_created_at, last_issue_link_created_at, updated_at
                ) VALUES ($1, $2, $3::timestamptz, $4::timestamptz, now())
                ON CONFLICT (workspace_id, ledger_path) DO UPDATE SET
                    last_work_log_created_at = EXCLUDED.last_work_log_created_at,
                    last_issue_link_created_at = EXCLUDED.last_issue_link_created_at,
                    updated_at = now()
                """,
                workspace_id,
                ledger_path,
                work_log_ts,
                issue_link_ts,
            )


async def run_mirror_sync() -> None:
    """Run the mirror sync worker (entry point)."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    sync = PostgresMirrorSync()
    await sync.initialize()
    await sync.start()


if __name__ == "__main__":
    asyncio.run(run_mirror_sync())
