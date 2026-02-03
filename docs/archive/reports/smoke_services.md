# G33 Phase 0: Service Smoke Stack Inventory

**Total Services**: 48
**Smoke-Enabled**: 3
**Infrastructure**: 0
**MCP Services**: 1
**Coordination**: 1
**Cognitive**: 2

## Smoke-Enabled Services

| Service | Port | Entry Point | Env Vars | Category |
|---------|------|-------------|----------|----------|
| conport | 3004 | app.py | 8 | mcp |
| dopecon-bridge | 3016 | main.py | 26 | coordination |
| task-orchestrator | 8000 | server.py | 10 | cognitive |

## All Services

| Service | Smoke | Port | Has Main | Has Dockerfile | Env Vars |
|---------|-------|------|----------|----------------|----------|
| activity-capture | ❌ | N/A | ✅ | ✅ | 7 |
| adhd-dashboard | ❌ | N/A | ❌ | ❌ | 0 |
| adhd-engine | ❌ | 8095 | ❌ | ❌ | 0 |
| adhd-notifier | ❌ | N/A | ✅ | ❌ | 2 |
| adhd_engine | ❌ | N/A | ✅ | ✅ | 3 |
| agents | ❌ | N/A | ❌ | ❌ | 0 |
| break-suggester | ❌ | N/A | ❌ | ✅ | 0 |
| claude-brain | ❌ | N/A | ❌ | ❌ | 0 |
| claude_brain | ❌ | N/A | ✅ | ✅ | 0 |
| complexity_coordinator | ❌ | N/A | ❌ | ❌ | 0 |
| conport | ✅ | 3004 | ✅ | ✅ | 8 |
| conport-bridge | ❌ | N/A | ❌ | ❌ | 0 |
| conport-kg | ❌ | N/A | ❌ | ❌ | 0 |
| conport_kg | ❌ | N/A | ❌ | ❌ | 0 |
| conport_kg_ui | ❌ | N/A | ❌ | ❌ | 0 |
| context-switch-tracker | ❌ | N/A | ❌ | ❌ | 0 |
| context7 | ❌ | N/A | ❌ | ❌ | 0 |
| dddpg | ❌ | N/A | ❌ | ❌ | 0 |
| dope-context | ❌ | N/A | ❌ | ✅ | 0 |
| dopecon-bridge | ✅ | 3016 | ✅ | ✅ | 26 |
| dopemux-gpt-researcher | ❌ | N/A | ❌ | ✅ | 0 |
| energy-trends | ❌ | N/A | ❌ | ❌ | 0 |
| genetic-agent | ❌ | N/A | ❌ | ❌ | 0 |
| genetic_agent | ❌ | N/A | ✅ | ✅ | 0 |
| intelligence | ❌ | N/A | ❌ | ❌ | 0 |
| interruption-shield | ❌ | N/A | ❌ | ❌ | 0 |
| litellm | ❌ | N/A | ❌ | ❌ | 0 |
| mcp-client | ❌ | N/A | ✅ | ✅ | 6 |
| mcp-conport | ❌ | N/A | ❌ | ❌ | 0 |
| mcp-integration-bridge | ❌ | N/A | ❌ | ❌ | 0 |
| ml-predictions | ❌ | N/A | ✅ | ❌ | 0 |
| ml-risk-assessment | ❌ | N/A | ❌ | ❌ | 0 |
| monitoring | ❌ | N/A | ❌ | ❌ | 0 |
| monitoring-dashboard | ❌ | N/A | ✅ | ✅ | 0 |
| orchestrator | ❌ | N/A | ❌ | ❌ | 0 |
| roast-engine | ❌ | N/A | ✅ | ❌ | 0 |
| serena | ❌ | N/A | ✅ | ❌ | 12 |
| session-intelligence | ❌ | N/A | ❌ | ❌ | 0 |
| session_intelligence | ❌ | N/A | ❌ | ❌ | 0 |
| slack-integration | ❌ | N/A | ❌ | ❌ | 0 |
| task-orchestrator | ✅ | 8000 | ✅ | ✅ | 10 |
| task-router | ❌ | N/A | ❌ | ❌ | 0 |
| taskmaster | ❌ | N/A | ✅ | ❌ | 10 |
| taskmaster-mcp-client | ❌ | N/A | ❌ | ❌ | 0 |
| voice-commands | ❌ | N/A | ❌ | ✅ | 0 |
| working-memory-assistant | ❌ | N/A | ✅ | ✅ | 10 |
| workspace-watcher | ❌ | N/A | ✅ | ❌ | 0 |
| zen | ❌ | N/A | ❌ | ❌ | 0 |