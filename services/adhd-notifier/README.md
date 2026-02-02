# ADHD Notifier Service

**Category**: Cognitive Plane  
**Status**: Production  
**Purpose**: Intelligent ADHD-aware notification delivery

## Overview

ADHD Notifier provides intelligent notification routing with ADHD accommodations, including break reminders, focus mode support, and cognitive load-aware delivery.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d adhd-notifier

# Check status
docker logs adhd-notifier
```

## Health Check

```bash
curl http://localhost:8098/health
```

## Configuration

Environment variables:
- `PORT` - Service port (default: 8098)
- `ADHD_ENGINE_URL` - ADHD Engine URL (default: http://localhost:8080)
- `NOTIFICATION_CHANNELS` - Enabled channels (terminal,voice,system)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## Features

- **Smart Delivery** - Respect focus mode and cognitive load
- **Break Reminders** - 25-minute Pomodoro-style breaks
- **Multi-Channel** - Terminal, voice, system notifications
- **Context-Aware** - Suppress during hyperfocus, deliver during breaks
- **Priority Routing** - Critical notifications bypass quiet modes

## Notification Channels

1. **Terminal** - In-session notifications via tmux
2. **Voice** - Text-to-speech announcements (optional)
3. **System** - OS-level notifications
4. **Mobile** - Via Happy Coder integration (if enabled)

## ADHD Engine Integration

Checks ADHD state before delivery:
- Energy level (low/medium/high)
- Attention state (focused/distracted)
- Break recommendations
- Cognitive load

## Development

```bash
cd services/adhd-notifier
python -m adhd_notifier.main
```

## Documentation

See [docs/03-reference/systems/adhd-intelligence/](../../docs/03-reference/systems/adhd-intelligence/) for integration patterns.
