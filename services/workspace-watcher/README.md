# Workspace Watcher Service

**Category**: Cognitive Plane  
**Status**: Production  
**Purpose**: File system monitoring and workspace change detection

## Overview

Workspace Watcher monitors file system changes across Dopemux workspaces, providing real-time change notifications and intelligent activity tracking for ADHD workflows.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d workspace-watcher

# Check status
docker logs workspace-watcher
```

## Health Check

```bash
curl http://localhost:8100/health
```

## Configuration

Environment variables:
- `PORT` - Service port (default: 8100)
- `WORKSPACE_PATHS` - Comma-separated workspace paths to monitor
- `DEFAULT_WORKSPACE_PATH` - Primary workspace (default: current directory)
- `IGNORE_PATTERNS` - Patterns to ignore (.git,node_modules,__pycache__)
- `DOPECON_BRIDGE_URL` - DopeconBridge URL (default: http://localhost:3016)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## Features

- **Real-Time Monitoring** - File creation, modification, deletion
- **Multi-Workspace** - Track multiple workspaces simultaneously
- **Intelligent Filtering** - Ignore build artifacts and dependencies
- **Change Aggregation** - Batch rapid changes to reduce noise
- **ADHD-Friendly** - Non-intrusive notifications

## Monitored Events

- File created
- File modified
- File deleted
- Directory created/deleted
- File renamed/moved

## Event Publishing

Publishes events to DopeconBridge Redis streams:
- `workspace:file_created`
- `workspace:file_modified`
- `workspace:file_deleted`
- `workspace:batch_changes`

## Use Cases

- **Auto-save Detection** - Trigger actions on file saves
- **Build Triggers** - Detect source changes for rebuilds
- **Activity Tracking** - Monitor workspace activity patterns
- **Context Switching** - Detect workspace switches

## Development

```bash
cd services/workspace-watcher
python -m workspace_watcher.main
```

## Documentation

See multi-workspace documentation for workspace isolation patterns.
