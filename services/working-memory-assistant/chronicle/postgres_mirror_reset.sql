-- DEV ONLY reset. This script is executed only when MIRROR_SCHEMA_RESET=true.
-- Drops in dependency-safe order.

DROP TABLE IF EXISTS dm_raw_activity_events;
DROP TABLE IF EXISTS dm_work_log_entries;
DROP TABLE IF EXISTS dm_issue_links;
DROP TABLE IF EXISTS dm_mirror_bookmarks;

-- Keep migrations table, clear applied versions so schema can be re-applied.
DELETE FROM dm_schema_migrations;
