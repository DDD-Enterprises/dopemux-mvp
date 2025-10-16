# ConPort Knowledge Graph Terminal UI

ADHD-optimized terminal interface for exploring the ConPort Knowledge Graph with progressive disclosure and cognitive load management.

## Features

- **Top-3 ADHD Pattern**: Start with 3 most recent decisions to reduce overwhelm
- **Progressive Disclosure**: Expand from 1-hop → 2-hop → full context on demand
- **Keyboard Navigation**: Arrow keys, Enter, and single-key commands
- **Real-time API**: Connects to Integration Bridge on port 3016
- **Demo Mode**: Standalone mode with mock data for development

## Quick Start

### Demo Mode (No Backend Required)

```bash
# Run demo with mock data
./demo.sh

# Or manually:
npm run demo
```

### Development Mode (With Backend)

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run in development mode
npm run dev

# Run production build
npm start
```

## Architecture

### Three-Tier Progressive Disclosure

1. **Tier 1: Decision Browser**
   - Shows top 3 recent decisions
   - Keyboard navigation (↑↓)
   - Select with Enter
   - Quit with 'q'

2. **Tier 2: Genealogy Explorer**
   - View decision + 1-hop neighbors
   - Press 'e' to expand to 2-hop
   - Press 'f' for full context
   - Press 'b' to go back

3. **Tier 3: Deep Context Viewer**
   - Complete decision details
   - All relationships with type badges
   - Cognitive load indicator
   - Related decisions list

### API Integration

Connects to Integration Bridge at `http://localhost:3016/kg`:

- `GET /kg/decisions/recent?limit=3` - Recent decisions
- `GET /kg/decisions/{id}/neighborhood?max_hops=1` - Decision genealogy
- `GET /kg/decisions/{id}/context` - Full decision context

Environment variable: `KG_API_URL` (default: `http://localhost:3016/kg`)

## Project Structure

```
conport_kg_ui/
├── src/
│   ├── App.tsx                  # Main routing component
│   ├── cli.tsx                  # CLI entry point
│   ├── mock-server.ts          # Mock API for demo mode
│   ├── api/
│   │   └── client.ts           # HTTP client for Integration Bridge
│   ├── components/
│   │   ├── DecisionBrowser.tsx     # Tier 1: Top-3 view
│   │   ├── GenealogyExplorer.tsx   # Tier 2: Progressive neighbors
│   │   └── DeepContextViewer.tsx   # Tier 3: Full context
│   ├── types/
│   │   └── index.ts            # TypeScript interfaces
│   └── fixtures/
│       └── decisions.json      # Sample data for demo mode
├── dist/                       # Compiled JavaScript
├── demo.sh                     # Demo launcher script
├── package.json
├── tsconfig.json
└── README.md
```

## Keyboard Controls

### Decision Browser
- `↑` / `↓` - Navigate decisions
- `Enter` - Select decision
- `q` - Quit

### Genealogy Explorer
- `e` - Expand to 2-hop neighbors
- `f` - View full context
- `b` - Back to browser
- `q` - Quit

### Deep Context Viewer
- `b` - Back to explorer
- `q` - Quit

## ADHD Optimizations

- **Cognitive Load Indicators**: Color-coded complexity levels
- **Progressive Disclosure**: Essential info first, details on demand
- **Decision Reduction**: Max 3 options at decision browser
- **Visual Hierarchy**: Clear visual separation between tiers
- **Gentle Guidance**: Helpful prompts without overwhelming
- **Quick Exit**: Single-key quit from any screen

## Development

### Build System

```bash
# Clean build
rm -rf dist/
npm run build

# Watch mode (via tsx)
npm run dev
```

### Mock Server

The mock server simulates Integration Bridge API with fixture data:

```bash
# Run mock server only
npm run mock-server

# Mock server will listen on http://localhost:3016
```

### Testing with Real Backend

1. Start Integration Bridge (port 3016)
2. Ensure ConPort database is running
3. Run UI: `npm run dev`

## TypeScript Configuration

- **Module Resolution**: `bundler` (for Ink ESM compatibility)
- **Target**: ES2020
- **JSX**: React (for Ink components)
- **Strict Mode**: Enabled

## Dependencies

- **ink**: React for CLIs (terminal UI framework)
- **react**: Required by Ink
- **ink-spinner**: Loading indicators
- **tsx**: TypeScript execution (dev)
- **typescript**: TypeScript compiler

## Environment Variables

- `KG_API_URL` - Integration Bridge base URL (default: `http://localhost:3016/kg`)
- `NODE_ENV` - Set to `development` for verbose logging

## Troubleshooting

### "Error loading decisions"

- Check Integration Bridge is running on port 3016
- Try demo mode: `./demo.sh`
- Verify API connectivity: `curl http://localhost:3016/kg/decisions/recent?limit=3`

### "Cannot find module 'ink'"

- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Rebuild: `npm run build`

### Terminal rendering issues

- Ensure terminal supports colors
- Try different terminal emulator
- Check terminal size (minimum 80x24 recommended)

## License

Part of Dopemux Two-Plane Architecture Orchestrator
