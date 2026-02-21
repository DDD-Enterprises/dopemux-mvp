---
id: quickstart
title: Quickstart
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Quickstart (reference) for dopemux documentation and developer workflows.
---
# Component 7: Quick Start Guide

Get Environmental Interruption Shield running in 5 minutes!

## Prerequisites

- Python 3.11+
- Redis server (for message queue persistence)
- macOS (for Focus Mode integration)
- ADHD Engine running on localhost:8095

## Installation

### 1. Install Dependencies

```bash
cd services/interruption-shield
make setup
```

This will:
- Install Python dependencies
- Set up pre-commit hooks
- Run initial tests
- Format code

### 2. Start Redis (required for message queue)

```bash
# macOS (via Homebrew)
brew install redis
brew services start redis

# Or via Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3. Configure Shield

Create `config/shield.yaml`:

```yaml
shield:
  auto_activate: true
  mode: ASSIST  # or ENFORCE for stricter filtering
  default_duration: 25  # minutes

  urgency:
    critical_keywords:
- "urgent"
- "p0"
- "production down"
- "incident"

    high_keywords:
- "important"
- "deadline"
- "today"

    vip_users:
- "U123ABC"  # Your CEO's Slack user ID (get from Slack)
- "U456DEF"  # Your manager

  integrations:
    adhd_engine_url: "http://localhost:8095"
    redis_url: "redis://localhost:6379"
```

### 4. Test the Components

```bash
# Run all tests
make test

# Or just unit tests
make test-unit
```

Expected output:
```
====== test session starts ======
tests/unit/test_coordinator.py ....                                      [100%]

====== 4 passed in 0.25s ======
```

### 5. Run the Shield

```bash
# Development mode (with auto-reload)
make run-dev

# Production mode
make run
```

Expected output:
```
[2025-10-20 10:30:00] INFO - ShieldCoordinator starting...
[2025-10-20 10:30:00] INFO - Connected to ADHD Engine at http://localhost:8095
[2025-10-20 10:30:00] INFO - Connected to Redis at redis://localhost:6379
[2025-10-20 10:30:00] INFO - ShieldCoordinator started successfully
[2025-10-20 10:30:00] INFO - ADHD Engine client started (polling every 5s)
```

## Quick Verification

### 1. Test ADHD Engine Connection

```bash
# Check if ADHD Engine is running
curl http://localhost:8095/api/v1/state/current

# Expected response:
{
  "attention_state": "scattered",
  "energy_level": "medium",
  ...
}
```

### 2. Test Redis Connection

```bash
# Check Redis is accessible
redis-cli ping

# Expected: PONG
```

### 3. Manual Shield Activation Test

```python
# test_shield.py
import asyncio
from interruption_shield.core import ShieldCoordinator, ShieldConfig
from interruption_shield.integrations import ADHDEngineClient, DNDManager
from interruption_shield.triage import MessageTriage, UrgencyScorer, UrgencyScorerConfig, MessageQueue

async def test_shield():
    # Create configuration
    config = ShieldConfig()

    # Create components
    adhd_engine = ADHDEngineClient()
    dnd_manager = DNDManager()
    urgency_scorer = UrgencyScorer(UrgencyScorerConfig(user_id="test_user"))
    message_queue = MessageQueue()
    message_triage = MessageTriage(urgency_scorer, message_queue)

    # Create coordinator
    coordinator = ShieldCoordinator(
        config=config,
        adhd_engine_client=adhd_engine,
        dnd_manager=dnd_manager,
        message_triage=message_triage
    )

    # Start
    await coordinator.start()
    await message_triage.start()

    # Manually activate shields
    print("Activating shields...")
    await coordinator.activate_shields("test_user")

    # Wait 5 seconds
    await asyncio.sleep(5)

    # Deactivate
    print("Deactivating shields...")
    await coordinator.deactivate_shields("test_user")

    # Cleanup
    await message_triage.stop()

asyncio.run(test_shield())
```

Run it:
```bash
python test_shield.py
```

Expected output:
```
Activating shields...
[2025-10-20 10:35:00] INFO - 🛡️ Activating interruption shields for user test_user
[2025-10-20 10:35:00] INFO - ✅ Shields activated successfully
Deactivating shields...
[2025-10-20 10:35:05] INFO - 🔓 Deactivating interruption shields for user test_user
[2025-10-20 10:35:05] INFO - ✅ Shields deactivated successfully
```

## Development Workflow

### Daily Development

```bash
# 1. Format code before committing
make format

# 2. Run tests
make test

# 3. Run all CI checks locally
make ci
```

### Pre-Commit Hooks

Automatically run on `git commit`:
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)
- bandit (security scanning)

### Week 1 Checklist

```bash
make week1
```

Shows:
```
Week 1: Core Infrastructure
  [ ] Day 1-2: Development environment setup
  [ ] Day 3-4: ShieldCoordinator implementation
  [ ] Day 5: Productivity monitoring

Run 'make install' to get started
```

## Troubleshooting

### Redis Connection Failed

**Error**: `Redis connection failed: Error 61 connecting to localhost:6379`

**Solution**:
```bash
# Start Redis
brew services start redis

# Or check if running
brew services list | grep redis
```

### ADHD Engine Not Reachable

**Error**: `ADHD Engine not reachable at http://localhost:8095`

**Solution**:
```bash
# Start ADHD Engine
cd services/task-orchestrator
python -m uvicorn main:app --host 0.0.0.0 --port 8095
```

### macOS Focus Mode Permission Denied

**Error**: `AppleScript failed: osascript is not allowed`

**Solution**:
1. Open System Preferences → Security & Privacy → Privacy
1. Add Terminal to "Automation" permissions
1. Allow Terminal to control System Events

### Pre-commit Hooks Not Running

**Solution**:
```bash
# Reinstall pre-commit hooks
pre-commit uninstall
pre-commit install

# Test manually
pre-commit run --all-files
```

## Next Steps

1. ✅ **Installation Complete** - You're running!
1. **Week 1 Implementation** - See [`phase1-sprint-plan.md`](../../../archive/sessions/adhd-engine/phase1-sprint-plan.md)
1. **Slack Integration** - Week 3 (see sprint plan)
1. **Beta Testing** - Week 4 (recruit ADHD developers)

## Useful Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make test           # Run tests with coverage
make test-fast      # Run tests without coverage
make lint           # Run all linters
make format         # Format code
make security       # Security scan
make clean          # Clean up generated files
make run            # Run the service
make run-dev        # Run with auto-reload
make ci             # Run all CI checks locally
```

## Documentation

- **Technical Spec**: [`COMPONENT_7_ENVIRONMENTAL_INTERRUPTION_SHIELD.md`](../../../archive/component-implementations/COMPONENT_7_ENVIRONMENTAL_INTERRUPTION_SHIELD.md)
- **Sprint Plan**: [`phase1-sprint-plan.md`](../../../archive/sessions/adhd-engine/phase1-sprint-plan.md)
- **Guide Root**: [`quickstart.md`](quickstart.md)

## Support

- **Issues**: Create GitHub issue with `[Component 7]` prefix
- **Questions**: See sprint plan for team contacts
- **ConPort**: Decision #188, Progress #160

---

**Status**: ✅ Ready for Week 1 Day 1 implementation!
**Next**: Connect to ADHD Engine and implement ShieldCoordinator
