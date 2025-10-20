# Component 7: Environmental Interruption Shield

ADHD-optimized external interruption prevention system that automatically activates based on ADHD Engine attention state.

## Overview

**Problem**: Dopemux has excellent internal interruption handling (hyperfocus protection, context switch recovery) but ZERO coverage of external interruptions (Slack, meetings, notifications).

**Solution**: Three-layer defense system:
1. **Predictive Prevention**: Auto-DND, meeting buffers
2. **Active Filtering**: Urgency triage, message queuing
3. **Rapid Recovery**: Component 6 integration

## Quick Start

### Installation

```bash
cd services/interruption-shield
pip install -r requirements.txt
```

### Configuration

Copy example config:
```bash
cp config/shield.example.yaml config/shield.yaml
```

Edit `config/shield.yaml`:
```yaml
shield:
  auto_activate: true
  mode: ASSIST  # or ENFORCE
  default_duration: 25  # minutes

  urgency:
    critical_keywords:
      - "urgent"
      - "p0"
      - "production down"
    vip_users:
      - "U123ABC"  # Your CEO's Slack user ID

  integrations:
    adhd_engine_url: "http://localhost:8095"
    slack_bot_token: "${SLACK_BOT_TOKEN}"
```

### Running

```bash
# Development
python -m interruption_shield.main

# Production
systemd service (coming in Phase 1 Week 4)
```

## Architecture

```
ShieldCoordinator
├── DNDManager (macOS Focus + Slack status)
├── MessageTriage (Urgency scoring + queuing)
└── NotificationManager (Batching + delivery)
```

## Development Status

- ✅ **Phase 1 Setup**: Directory structure, scaffolding complete
- 🔄 **Week 1**: Core infrastructure implementation
- ⏳ **Week 2**: macOS integration
- ⏳ **Week 3**: Slack integration
- ⏳ **Week 4**: Beta testing

See [`docs/PHASE1_SPRINT_PLAN.md`](docs/PHASE1_SPRINT_PLAN.md) for detailed sprint plan.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=interruption_shield --cov-report=html

# Run specific test file
pytest tests/unit/test_coordinator.py
```

## Documentation

- **Technical Specification**: [`/docs/COMPONENT_7_ENVIRONMENTAL_INTERRUPTION_SHIELD.md`](../../docs/COMPONENT_7_ENVIRONMENTAL_INTERRUPTION_SHIELD.md)
- **Sprint Plan**: [`docs/PHASE1_SPRINT_PLAN.md`](docs/PHASE1_SPRINT_PLAN.md)
- **ConPort Decision**: Decision #188

## Contributing

Phase 1 is in active development. See sprint plan for current tasks.

### Code Style

```bash
# Format code
black .
isort .

# Lint
flake8 .
mypy .
```

## License

Part of Dopemux MVP - ADHD-Optimized Development Platform

---

**Status**: Phase 1 Week 1 - Core Infrastructure
**Next Milestone**: ShieldCoordinator implementation complete
**Contact**: Component 7 Implementation Team
