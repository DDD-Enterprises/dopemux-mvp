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

        # Bookmarks: workspace_id -> last_synced_ts
        self._work_log_bookmarks: dict[str, str] = {}
        self._raw_event_bookmarks: dict[str, str] = {}
        self._issue_link_bookmarks: dict[str, str] = {}

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

        except Exception as e:
            logger.error(f"❌ Failed to initialize Postgres mirror sync: {e}")
            raise

    async def _ensure_schema(self) -> None:
        """Apply migration if not already applied."""
        if not self.pool:
            return

        try:
            schema_path = Path(__file__).parent / "chronicle" / "postgres_mirror.sql"
            if not schema_path.exists():
                logger.warning(f"⚠️  Postgres mirror schema not found: {schema_path}")
                return

            async with self.pool.acquire() as conn:
                # Check if already migrated
                exists = await conn.fetchval(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = 'dm_schema_migrations'"
                )
                if exists:
                    version = await conn.fetchval(
                        "SELECT version FROM dm_schema_migrations ORDER BY applied_at DESC LIMIT 1"
                    )
                    if version == "v1.0.0":
                        logger.info("✅ Postgres mirror schema already at v1.0.0")
                        return

                # Apply schema
                schema_sql = schema_path.read_text()
                await conn.execute(schema_sql)
                logger.info("✅ Applied Postgres mirror schema v1.0.0")

        except Exception as e:
            logger.warning(f"⚠️  Could not ensure Postgres schema: {e}")

    def _get_store(self, workspace_id: str) -> ChronicleStore:
        """Get or create ChronicleStore for the canonical ledger.

        Resolves workspace_id to the single canonical ledger per ADR-213.
        Returns None if canonical ledger does not exist yet.
        """
        try:
            db_path = resolve_canonical_ledger(workspace_id)
        except CanonicalLedgerError:
            return None
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

        while self._running:
            try:
                await self._sync_all_workspaces()
                await asyncio.sleep(self.sync_interval_sec)
            except asyncio.CancelledError:
                logger.info("📤 Postgres mirror sync stopping")
                break
            except Exception as e:
                logger.error(f"❌ Mirror sync error: {e}")
                await asyncio.sleep(self.sync_interval_sec)

    async def stop(self) -> None:
        """Stop the sync worker."""
        self._running = False
        if self.pool:
            await self.pool.close()
        logger.info("📤 Postgres mirror sync stopped")

    async def _sync_all_workspaces(self) -> None:
        """Sync all discovered workspaces."""
        workspaces = self._discover_workspaces()
        if not workspaces:
            return

        for workspace_id in workspaces:
            try:
                await self._sync_workspace(workspace_id)
            except Exception as e:
                logger.warning(f"⚠️  Failed to sync workspace {workspace_id}: {e}")

    async def _sync_workspace(self, workspace_id: str) -> None:
        """Sync a single workspace to Postgres."""
        store = self._get_store(workspace_id)
        if not store:
            return

        # Sync work log entries
        work_log_count = await self._sync_work_log_entries(workspace_id, store)

        # Sync raw events (optional, may skip if too many)
        raw_event_count = await self._sync_raw_events(workspace_id, store)

        # Sync issue links
        issue_link_count = await self._sync_issue_links(workspace_id, store)

        total = work_log_count + raw_event_count + issue_link_count
        if total > 0:
            logger.info(
                f"📤 Synced {workspace_id}: "
                f"{work_log_count} work log, {raw_event_count} raw, {issue_link_count} links"
            )

    async def _sync_work_log_entries(
        self, workspace_id: str, store: ChronicleStore
    ) -> int:
        """Sync work log entries to Postgres."""
        if not self.pool:
            return 0

        # Get last synced timestamp
        last_ts = self._work_log_bookmarks.get(workspace_id, "1970-01-01T00:00:00Z")

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
            return 0

        # Insert into Postgres
        count = 0
        async with self.pool.acquire() as pg_conn:
            for row in rows:
                try:
                    await pg_conn.execute(
                        """
                        INSERT INTO dm_work_log_entries (
                            id, workspace_id, instance_id, session_id, ts,
                            category, entry_type, workflow_phase, summary, details,
                            reasoning, outcome, importance_score, tags,
                            linked_files, linked_commits, linked_decisions,
                            linked_chat_range, parent_entry_id, duration_seconds,
                            created_at, updated_at
                        ) VALUES ($1, $2::uuid, $3, $4::uuid, $5::timestamptz,
                                  $6, $7, $8, $9, $10::jsonb,
                                  $11, $12, $13, $14::text[],
                                  $15::jsonb, $16::text[], $17::uuid[],
                                  $18::jsonb, $19::uuid, $20,
                                  $21::timestamptz, $22::timestamptz)
                        ON CONFLICT (id) DO UPDATE SET
                            updated_at = EXCLUDED.updated_at
                        """,
                        row[0],  # id
                        self._to_uuid(workspace_id),  # workspace_id as UUID
                        row[2],  # instance_id
                        self._to_uuid(row[3]),  # session_id
                        row[4],  # ts_utc
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
                        self._to_uuid_array(row[16]),  # linked_decisions_json -> UUID[]
                        row[17],  # linked_chat_range_json
                        self._to_uuid(row[18]),  # parent_entry_id
                        row[19],  # duration_sec
                        row[20],  # created_at_utc
                        row[21],  # updated_at_utc
                    )
                    count += 1
                    self._work_log_bookmarks[workspace_id] = row[20]  # created_at_utc
                except Exception as e:
                    logger.debug(f"Skip work log {row[0]}: {e}")

        return count

    async def _sync_raw_events(
        self, workspace_id: str, store: ChronicleStore
    ) -> int:
        """Sync raw events to Postgres (limited batch)."""
        # For raw events, we only sync recent ones to avoid overwhelming Postgres
        # The canonical SQLite is the source of truth with TTL cleanup
        return 0  # Skip for Phase 1, implement in Phase 2 if needed

    async def _sync_issue_links(
        self, workspace_id: str, store: ChronicleStore
    ) -> int:
        """Sync issue links to Postgres."""
        if not self.pool:
            return 0

        last_ts = self._issue_link_bookmarks.get(workspace_id, "1970-01-01T00:00:00Z")

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
            return 0

        count = 0
        async with self.pool.acquire() as pg_conn:
            for row in rows:
                try:
                    await pg_conn.execute(
                        """
                        INSERT INTO dm_issue_links (
                            id, workspace_id, instance_id, issue_entry_id,
                            resolution_entry_id, confidence, evidence_window_min, created_at
                        ) VALUES ($1::uuid, $2::uuid, $3, $4::uuid, $5::uuid, $6, $7, $8::timestamptz)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        self._to_uuid(row[0]),
                        self._to_uuid(workspace_id),
                        row[2],
                        self._to_uuid(row[3]),
                        self._to_uuid(row[4]),
                        row[5],
                        row[6],
                        row[7],
                    )
                    count += 1
                    self._issue_link_bookmarks[workspace_id] = row[7]
                except Exception as e:
                    logger.debug(f"Skip issue link {row[0]}: {e}")

        return count

    def _to_uuid(self, value: Any) -> Optional[str]:
        """Convert value to UUID string or None."""
        if value is None or value == "":
            return None
        return str(value)

    def _to_uuid_array(self, json_str: Optional[str]) -> Optional[list[str]]:
        """Convert JSON array string to UUID array."""
        if not json_str:
            return None
        try:
            items = json.loads(json_str)
            return [str(x) for x in items] if items else None
        except json.JSONDecodeError:
            return None


async def run_mirror_sync() -> None:
    """Run the mirror sync worker (entry point)."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    sync = PostgresMirrorSync()
    await sync.initialize()
    await sync.start()


if __name__ == "__main__":
    asyncio.run(run_mirror_sync())
