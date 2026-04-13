# ConPort Knowledge Graph Terminal UI

ADHD-optimized terminal interface for CONPORT-KG-2025 decision genealogy navigation.

**Version**: 1.0.0
**Part of**: Epic DB-001 CONPORT-KG-2025 Database Foundation

---

## Features

**3-Tier Progressive Disclosure**:
- **Tier 1**: Decision Browser (Top-3 ADHD pattern)
- **Tier 2**: Genealogy Explorer (1-hop → 2-hop expansion)
- **Tier 3**: Deep Context Viewer (complete analysis)

**ADHD Optimizations**:
- Top-3 pattern prevents overwhelm
- Progressive disclosure (user controls expansion)
- Green/cyan/yellow color theme
- Single-letter keyboard shortcuts
- Cognitive load indicators

**Performance**:
- <10ms HTTP overhead
- 2-5ms backend queries
- Instant UI responsiveness
- Connection pooling

---

## Quick Start

### Prerequisites

1. Integration Bridge running:
```bash
cd services/mcp-integration-bridge
python main.py
# Should start on port 3016 (PORT_BASE + 16)
```

2. PostgreSQL AGE database operational:
```bash
docker ps | grep postgres-age
# Should show: dopemux-postgres-age (healthy)
```

### Installation

```bash
cd services/conport_kg_ui
npm install
```

### Run

**Development mode** (with auto-reload):
```bash
npm run dev
```

**Production mode**:
```bash
npm run build
npm start
```

---

## Usage Guide

### Decision Browser (Start Screen)

```
Decision Browser (Top-3 ADHD Pattern)
Navigate: ↑↓ | Select: Enter | Quit: q

  ▸ #120: CONPORT-KG-2025 Phase 8: Intelligence Orchestrator...
    #117: Phase 2 Query API Implementation Strategy...
    #114: Complete CONPORT-KG-2025 Interface Architecture...

Showing 3 of 3 recent decisions
```

**Controls**:
- `↑↓` - Navigate through list
- `Enter` - View selected decision in Genealogy Explorer
- `q` - Quit application

### Genealogy Explorer (Tier 2)

```
Genealogy Explorer - Decision #120
e: Expand to 2-hop | f: Full Context | b: Back | q: Quit

CONPORT-KG-2025 Phase 8: Intelligence Orchestrator

1-hop neighbors (1):
  → #117: Phase 2 Query API Implementation Strategy...

Press 'e' to expand to 2-hop neighbors

Total network: 1 decisions
```

**Controls**:
- `e` - Expand to show 2-hop neighbors
- `f` - View full context (Tier 3)
- `b` - Back to Decision Browser
- `q` - Quit application

**After pressing 'e'**:
```
2-hop neighbors (3):
  ⇒ #114: Complete CONPORT-KG-2025 Interface Architecture...
  ⇒ #113: Migration Simplification: Direct SQLite→AGE...
  ⇒ #111: PostgreSQL AGE Docker Deployment Strategy...

Total network: 4 decisions (fully expanded)
```

### Deep Context Viewer (Tier 3)

```
Deep Context - Decision #120
b: Back | q: Quit

CONPORT-KG-2025 Phase 8: Intelligence Orchestrator

Cognitive Load: HIGH

Rationale:
User correctly identified critical architectural gap: we had designed
Query API (Phases 1-7) but not the automation/intelligence layer...

Relationships (1):
  #120 →[IMPLEMENTS]→ #117

Related decisions: 1
Total network: 1
```

**Controls**:
- `b` - Back to Genealogy Explorer
- `q` - Quit application

---

## Configuration

### Environment Variables

```bash
# Integration Bridge API URL
export KG_API_URL=http://localhost:3016/kg

# Or for different PORT_BASE
export KG_API_URL=http://localhost:3046/kg  # PORT_BASE=3030
```

### Custom Port Configuration

If your Integration Bridge runs on a different port:

```bash
# In services/conport_kg_ui/src/api/client.ts
const BASE_URL = 'http://localhost:YOUR_PORT/kg';
```

---

## Architecture

### Component Hierarchy

```
App (routing state machine)
├── DecisionBrowser (Tier 1)
│   └── Top-3 list with arrow navigation
├── GenealogyExplorer (Tier 2)
│   └── Progressive tree (1-hop → 2-hop)
└── DeepContextViewer (Tier 3)
    └── Complete decision analysis
```

### Data Flow

```
User Interaction
  ↓ (keyboard input via useInput)
Component State Change
  ↓ (useEffect trigger)
HTTP Fetch to Integration Bridge
  ↓ (GET /kg/*)
Query API (Python)
  ↓ (psycopg2)
PostgreSQL AGE Database
  ↓
Knowledge Graph (113 decisions + 12 relationships)
```

---

## Development

### Project Structure

```
services/conport_kg_ui/
├── package.json        (dependencies)
├── tsconfig.json       (TypeScript config)
├── src/
│   ├── cli.tsx         (entry point)
│   ├── App.tsx         (routing)
│   ├── types/
│   │   └── index.ts    (TypeScript interfaces)
│   ├── api/
│   │   └── client.ts   (HTTP wrapper)
│   └── components/
│       ├── DecisionBrowser.tsx (120 lines)
│       ├── GenealogyExplorer.tsx (160 lines)
│       └── DeepContextViewer.tsx (180 lines)
└── README.md          (this file)
```

### Building

```bash
npm run build
# Output: dist/
```

### Running Compiled Version

```bash
node dist/cli.js
```

---

## Troubleshooting

### "Failed to load decisions" Error

**Cause**: Integration Bridge not running

**Solution**:
```bash
# Start Integration Bridge
cd services/mcp-integration-bridge
python main.py

# Verify it's running
curl http://localhost:3016/kg/health
```

### "Connection refused" Error

**Cause**: Wrong port or Integration Bridge not started

**Solution**:
```bash
# Check Integration Bridge port
ps aux | grep "python.*main.py"

# Verify port 3016 is listening
lsof -i :3016
```

### TypeScript Compilation Errors

**Solution**:
```bash
# Clean and rebuild
rm -rf dist node_modules
npm install
npm run build
```

---

## ADHD Features

### Top-3 Pattern
- Decision Browser shows maximum 3 items
- Prevents decision paralysis
- Clear scanning pattern

### Progressive Disclosure
- Start with minimal info (1-hop)
- User expands when ready (press 'e')
- Can't accidentally overload
- Clear expansion hints

### Visual Design
- **Green**: Headers and important info
- **Cyan**: Selected items and labels
- **Yellow**: Hints and relationship types
- **Magenta**: Analytics and cognitive load
- **Dim**: Help text and secondary info

### Keyboard Navigation
- Single-letter commands (e, f, b, q)
- Arrow keys for lists (↑↓)
- Enter for selection
- No complex combinations

---

## Performance

**Query Times** (from backend benchmarks):
- Tier 1 (Overview): p95 2.52ms
- Tier 2 (Exploration): p95 3.44ms
- Tier 3 (Deep Context): p95 4.76ms

**HTTP Overhead**: <10ms
**Total Response**: <15ms for any query

---

## Next Steps

After Phase 9 complete:
- **Phase 11**: Production deployment with Docker
- **Future**: WebSocket streaming for real-time updates
- **Future**: Search interface for full-text queries
- **Future**: Export functionality (markdown, JSON)

---

**Status**: Phase 9 COMPLETE - Terminal UI operational
**Next**: Production deployment (Phase 11)
