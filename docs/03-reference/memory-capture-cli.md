---
id: memory-capture-cli
title: Memory Capture Cli
type: reference
owner: '@hu3mann'
last_review: '2026-02-09'
next_review: '2026-05-09'
author: '@hu3mann'
date: '2026-02-09'
prelude: CLI reference for Dopemux memory capture and global rollup commands with
  usage examples and best practices.
---

# Memory Capture CLI Reference

Command-line interface for Dopemux memory capture and global rollup operations.

## Command Overview

```bash
dopemux memory              # Memory capture operations
dopemux memory rollup       # Global rollup index management
```

## Global Rollup Commands

The global rollup provides cross-project lookup over project-owned chronicle ledgers while maintaining read-only access to ensure single authority per project.

### `dopemux memory rollup build`

Build or update the global rollup index from project ledgers.

**Usage:**
```bash
dopemux memory rollup build [OPTIONS]
```

**Options:**
- `--projects-file PATH` - File containing list of project roots (newline or JSON)
- `--index-path PATH` - Global index path (default: `~/.dopemux/global_index.sqlite`)

**Examples:**

```bash
# Build from projects file (newline-separated paths)
dopemux memory rollup build --projects-file ~/projects.txt

# Build with custom index location
dopemux memory rollup build \
  --projects-file ~/work/projects.json \
  --index-path ~/custom_index.sqlite
```

**Projects File Format:**

Newline-separated:
```
/home/user/project1
/home/user/project2
/home/user/project3
```

JSON array:
```json
[
  "/home/user/project1",
  "/home/user/project2",
  "/home/user/project3
]
```

**Output:**
```
Resolved 3 project(s)
✓ Projects registered: 3
✓ Pointers indexed: 142
✓ Index: /Users/hue/.dopemux/global_index.sqlite
```

**Behavior:**
1. Resolves project roots from provided file
2. Opens each project's chronicle ledger in read-only mode
3. Registers projects in global index
4. Indexes pointers to promoted work log entries
5. Never writes to project ledgers (read-only guarantee)

---

### `dopemux memory rollup list`

List all projects registered in the global rollup index.

**Usage:**
```bash
dopemux memory rollup list [OPTIONS]
```

**Options:**
- `--index-path PATH` - Global index path (default: `~/.dopemux/global_index.sqlite`)

**Examples:**

```bash
# List all registered projects
dopemux memory rollup list

# List from custom index
dopemux memory rollup list --index-path ~/custom_index.sqlite
```

**Output:**
```
                         Registered Projects
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Project ID           ┃ Repo Root            ┃ Last Seen            ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ /home/user/project1  │ /home/user/project1  │ 2026-02-09T00:15:23  │
│ /home/user/project2  │ /home/user/project2  │ 2026-02-09T00:15:24  │
│ /home/user/project3  │ /home/user/project3  │ 2026-02-09T00:15:25  │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

**Information Displayed:**
- **Project ID**: Unique identifier (typically the repo root path)
- **Repo Root**: Absolute path to the project repository
- **Last Seen**: Timestamp of last index build/update for this project

---

### `dopemux memory rollup search`

Search promoted work log entries across all registered projects.

**Usage:**
```bash
dopemux memory rollup search QUERY [OPTIONS]
```

**Arguments:**
- `QUERY` - Search query (uses SQL LIKE pattern matching)

**Options:**
- `--limit N` - Maximum results (default: 10, max: 100)
- `--index-path PATH` - Global index path (default: `~/.dopemux/global_index.sqlite`)

**Examples:**

```bash
# Search for authentication-related entries
dopemux memory rollup search "authentication"

# Search with more results
dopemux memory rollup search "test" --limit 20

# Search from custom index
dopemux memory rollup search "bug fix" \
  --index-path ~/custom_index.sqlite \
  --limit 50
```

**Output:**
```
                    Search Results: authentication
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Timestamp          ┃ Type     ┃ Summary              ┃ Project    ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 2026-02-09 00:12   │ code     │ Implement JWT auth   │ project1   │
│ 2026-02-08 23:45   │ decision │ Use OAuth 2.0        │ project2   │
│ 2026-02-08 15:30   │ code     │ Fix auth middleware  │ project1   │
└────────────────────┴──────────┴──────────────────────┴────────────┘

Showing 3 of up to 10 results
```

**Search Behavior:**
- Uses SQL LIKE pattern matching (`%query%`)
- Searches in event summaries and metadata
- Results sorted by: `ts_utc DESC`, `event_id ASC` (deterministic)
- Only searches promoted work log entries (not raw activity)

---

## Best Practices

### Building the Index

1. **Initial Setup**: Create a projects file with all your active repositories
2. **Regular Updates**: Rebuild the index periodically to capture new work
3. **Automation**: Consider adding to cron/scheduled tasks for automatic updates

```bash
# Example cron entry (daily at 2 AM)
0 2 * * * dopemux memory rollup build --projects-file ~/projects.txt
```

### Search Tips

1. **Keep queries simple**: Single words or short phrases work best
2. **Use quotes for multi-word searches**: `dopemux memory rollup search "bug fix"`
3. **Adjust limit based on needs**: Default 10 is good for quick checks
4. **Case-insensitive**: Search is case-insensitive by default

### Project Management

1. **Add new projects incrementally**: Just append to projects file and rebuild
2. **Remove stale projects**: Remove from projects file, but old data remains queryable
3. **Backup the index**: The global index is just a SQLite file - easy to backup

```bash
# Backup the global index
cp ~/.dopemux/global_index.sqlite ~/.dopemux/global_index.backup.sqlite
```

---

## Troubleshooting

### No Results in Search

**Possible causes:**
1. Projects not yet built into index
2. No promoted work log entries in projects
3. Query doesn't match any summaries

**Solution:**
```bash
# Verify projects are registered
dopemux memory rollup list

# Rebuild index if needed
dopemux memory rollup build --projects-file ~/projects.txt
```

### Permission Errors

**Issue:** Cannot read project ledgers

**Solution:**
- Ensure you have read access to project directories
- Check that `.dopemux/chronicle.sqlite` exists in each project
- Verify no file locks on ledger files

### Index Corruption

**Issue:** Errors reading global index

**Solution:**
```bash
# Remove corrupted index
rm ~/.dopemux/global_index.sqlite

# Rebuild from scratch
dopemux memory rollup build --projects-file ~/projects.txt
```

---

## Technical Details

### Read-Only Guarantees

All rollup operations maintain strict read-only access:

1. Project ledgers opened with `?mode=ro` URI parameter
2. No write operations to project databases
3. Only metadata and pointers stored in global index
4. Original project ledgers remain authoritative

### Data Model

**Global Index Schema:**

```sql
-- Projects registry
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    repo_root TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

-- Promoted entry pointers
CREATE TABLE promoted_pointers (
    ptr_id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    ts_utc TEXT NOT NULL,
    event_type TEXT,
    summary TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

### Performance Characteristics

- **Build time**: ~1-5 seconds per 1000 entries
- **Search time**: < 100ms for typical queries
- **Index size**: ~1KB per promoted entry
- **Memory usage**: Minimal (<50MB for large indices)

---

## Related Documentation

- [ADR-213: Capture Adapters Single Ledger](../90-adr/ADR-213-capture-adapters-single-ledger.md)
- [Derived Memory Pipeline Specification](../spec/dope-memory/v1/02_derived_memory_pipeline.md)
- [Global Rollup Implementation](../../src/dopemux/memory/global_rollup.py)

---

## Quick Reference Card

```bash
# Build index
dopemux memory rollup build --projects-file ~/projects.txt

# List projects
dopemux memory rollup list

# Search
dopemux memory rollup search "your query" --limit 20

# Custom index location
dopemux memory rollup list --index-path /custom/path.sqlite
```
