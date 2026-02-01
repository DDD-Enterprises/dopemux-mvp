---
id: PM_DASHBOARD_IMPLEMENTATION
title: Pm_Dashboard_Implementation
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Dopemux PM Dashboard Implementation

## Overview
Complete PM (Project Management) dashboard system for tmux orchestration with ADHD-optimized interfaces, integrating Task Orchestrator (tactical execution) with ConPort (memory/decisions) and Leantime (strategic PM).

## Architecture

### Core Components
1. **tmux Layout**: 6-pane orchestration with PM-aware panes
2. **Status Bar**: Real-time PM metrics (tasks, decisions, energy, blockers)
3. **Dashboard Scripts**: Pane-specific PM views with live data
4. **Hotkeys**: Interactive PM workflow controls
5. **Integration**: Bidirectional sync with ConPort + Leantime

### ADHD Optimizations
- **Progressive Disclosure**: Essential info first, details on demand
- **Visual Indicators**: ✅/❌/⚠️ emojis with color coding
- **Cognitive Load Management**: Max 5 items per section
- **Energy Awareness**: ADHD Engine integration for personalized views
- **Context Preservation**: Never lose mental model during interruptions

## Implementation Details

### 1. Enhanced tmux Layout (`tmux-dopemux-orchestrator.yaml`)

```yaml
session_name: dopemux-orchestrator
windows:
  - window_name: orchestration
    layout: tiled
    options:
      status: on
      status-interval: 30  # Update every 30s
      status-left: "#[fg=colour33] Dopemux PM #[default]"
      status-right: "#[fg=colour166] #(./scripts/pm-status.sh) #[default]"
    panes:
      # Pane 0: Task Orchestrator + PM Overview
      - watch -n 30 './scripts/pm-dashboard.sh orchestrator'
      # Pane 1: ConPort Memory Hub (Enhanced PM Dashboard)
      - watch -n 30 './scripts/pm-dashboard.sh conport'
      # Pane 2: Leantime Strategic PM
      - watch -n 30 './scripts/pm-dashboard.sh leantime'
      # Pane 3: Playwright Validation (With PM Links)
      - watch -n 30 './scripts/pm-dashboard.sh validation'
      # Pane 4: Morph Code Apply (With Task Links)
      - watch -n 30 './scripts/pm-dashboard.sh morph'
      # Pane 5: Zen Reasoning (Background with PM Context)
      - watch -n 30 './scripts/pm-dashboard.sh zen'
```

### 2. Status Bar Script (`scripts/pm-status.sh`)

**Purpose**: At-a-glance PM metrics in tmux status bar

**Features**:
- Tasks count from ConPort upcoming queue
- Recent decisions count
- Energy level indicator (ADHD Engine)
- Blocker count with visual alerts
- Caching for performance (30s TTL)
- Error handling with fallbacks

**Output Example**:
```
Tasks: 3 Dec: 2 ⚡ ❌1
```

**Key Functions**:
- `get_pm_metrics()`: Queries ConPort for live data
- `get_energy_level()`: ADHD Engine energy assessment
- Caching mechanism for performance

### 3. Dashboard Scripts (`scripts/pm-dashboard.sh`)

**Purpose**: Pane-specific PM views with rich, interactive displays

**Pane Types**:
- **orchestrator**: High-level overview (next task, sprint progress, recent activity)
- **conport**: Memory hub (upcoming work, recent decisions, work status)
- **leantime**: Strategic PM (tickets, milestones, alignment status)
- **validation**: QA results (test status, screenshots, attached artifacts)
- **morph**: Code changes (applied diffs, task links, performance metrics)
- **zen**: AI reasoning (current sessions, PM context, consensus status)

**ADHD Features**:
- **Visual Indicators**: Priority colors (🔴 High, 🟡 Medium, 🟢 Low)
- **Progress Bars**: `[████░░] 60%` for completion tracking
- **Cognitive Load**: 🟢 Low/🟡 Medium/🔴 High indicators
- **Progressive Disclosure**: Essential info first, details available
- **Real-Time Updates**: `watch -n 30` for live data refresh

**Example Output** (ConPort Pane):
```
🧠 ConPort Memory Hub
2025-11-01 10:30:15

📋 Upcoming Work (Top 5):
  HIGH: Dark mode toggle
  MEDIUM: User authentication
  LOW: Database optimization

🤔 Recent Decisions:
  📝 Use React hooks over class components...
  📝 Implement optimistic updates for UX...

📊 Work Status:
  🔄 In Progress: 1
  📋 Upcoming: 3
  ✅ Completed: 1
```

### 4. Enhanced Hotkeys (`.tmux.conf`)

**Core PM Navigation**:
- `prefix + o`: Get next task from ConPort
- `prefix + m`: Log decision in ConPort
- `prefix + v`: Run Playwright validation
- `prefix + z`: Toggle Zen consensus

**PM Dashboard Controls**:
- `prefix + p`: Show PM overview pane
- `prefix + P`: Rearrange panes for PM view

**Pane Focus**:
- `prefix + O`: Task Orchestrator (PM Hub)
- `prefix + M`: ConPort Memory (PM Data)
- `prefix + V`: Validation (PM Quality)
- `prefix + Z`: Zen Reasoning (PM Analysis)

**Workflow Commands**:
- `prefix + T`: Sync with Leantime strategic PM
- `prefix + R`: Reset ConPort context
- `prefix + S`: Save session + ConPort checkpoint

**ADHD Controls**:
- `prefix + B`: Trigger break reminder
- `prefix + E`: Check current energy level
- `prefix + F`: Toggle ADHD focus mode

## Integration Workflows

### Hello-Flow PM Integration
1. **Pick Work**: `conport.upcoming_next()` provides prioritized tasks
2. **Plan & Execute**: Task Orchestrator updates ConPort status
3. **Validate**: Playwright attaches screenshots to ConPort artifacts
4. **Close Loop**: Final status + decisions logged in ConPort
5. **Dashboard Sync**: All panes update with real-time PM data

### ConPort + Leantime Synchronization
**Bidirectional Sync**:
- **Pull**: Leantime tickets → ConPort work items (with priority mapping)
- **Push**: ConPort progress → Leantime status updates
- **Alignment**: Dashboard shows sync status and resolution options

**Mapping Logic**:
```javascript
// Leantime → ConPort
leantime_priority_map = {
  "urgent": "critical",
  "high": "high",
  "normal": "medium",
  "low": "low"
}

// ConPort → Leantime
conport_status_map = {
  "done": "done",
  "in_progress": "in_progress",
  "blocked": "blocked"
}
```

## Testing & Validation

### Manual Testing Steps
1. **Start tmux**: `tmuxp load tmux-dopemux-orchestrator.yaml`
2. **Verify Status Bar**: Should show "Tasks: X Dec: Y ⚡ ❌Z"
3. **Check Panes**: Each pane should show relevant PM data
4. **Test Hotkeys**: Try `prefix + p` for PM overview
5. **Validate Updates**: Make ConPort changes, watch dashboard refresh

### Automated Testing
```bash
# Test dashboard scripts
./scripts/pm-dashboard.sh conport | grep -q "ConPort Memory Hub"
./scripts/pm-status.sh | grep -q "Tasks:"

# Test with mock data
export MOCK_CONPORT=true
./scripts/pm-dashboard.sh conport  # Should show sample data
```

### Performance Validation
- **Refresh Rate**: < 2s for dashboard updates
- **Memory Usage**: < 50MB additional for scripts
- **CPU Overhead**: < 5% during normal operation
- **Error Recovery**: Graceful fallback when MCPs unavailable

## Deployment & Usage

### Installation
```bash
# Ensure scripts are executable
chmod +x scripts/pm-status.sh scripts/pm-dashboard.sh

# Start tmux session
tmuxp load tmux-dopemux-orchestrator.yaml
```

### Configuration
```bash
# Environment variables
export LEAN_MCP_TOKEN="your-leantime-token"  # Optional
export WORKSPACE_ID="/path/to/project"

# ADHD Engine integration (if available)
export ADHD_ENGINE_URL="http://localhost:8080"
```

### Daily Workflow
1. **Session Start**: Load tmux session → PM dashboard initializes
2. **Work Intake**: Check status bar → `prefix + o` for next task
3. **Progress Tracking**: Watch pane updates → `prefix + m` to log decisions
4. **Quality Gates**: `prefix + v` for validation → Review artifacts
5. **Session End**: `prefix + S` saves state to ConPort

## ADHD Optimization Details

### Progressive Disclosure
- **Status Bar**: Essential metrics (3-5 items max)
- **Pane Headers**: Summary with expansion options
- **Detail Views**: Available but not overwhelming

### Cognitive Load Management
- **Item Limits**: Max 5 work items, 3 decisions shown
- **Color Coding**: Intuitive priority system (red=urgent, green=low)
- **Time Boxing**: 30s refresh prevents information overload

### Context Preservation
- **Session State**: tmux resurrect saves dashboard layout
- **Data Persistence**: ConPort maintains state across restarts
- **Energy Tracking**: ADHD Engine adapts display based on user state

### Accessibility Features
- **Keyboard Only**: All operations via hotkeys
- **Visual Feedback**: Clear success/error indicators
- **Error Recovery**: Graceful degradation when services unavailable

## Future Enhancements

### Planned Features
- **Mobile Companion**: Sync PM data to mobile devices
- **Advanced Analytics**: Historical trends and productivity insights
- **Team Collaboration**: Multi-user PM dashboard sharing
- **Custom Dashboards**: User-configurable pane layouts

### Integration Opportunities
- **Git Integration**: Link commits to PM tasks
- **CI/CD Pipeline**: Automated validation triggers
- **Time Tracking**: Pomodoro-style session management
- **Notification System**: External alerts for blockers

## Troubleshooting

### Common Issues
1. **Blank Dashboards**: Check ConPort MCP connectivity
2. **Slow Updates**: Verify 30s refresh interval
3. **Color Issues**: Ensure tmux supports 256 colors
4. **Hotkey Conflicts**: Check existing tmux configuration

### Debug Commands
```bash
# Test individual components
./scripts/pm-status.sh
./scripts/pm-dashboard.sh conport

# Check tmux configuration
tmux source-file .tmux.conf

# Verify MCP connectivity
docker ps | grep conport
curl http://localhost:3004/health  # ConPort health check
```

### Performance Tuning
- **Reduce Refresh Rate**: Change `watch -n 60` for less frequent updates
- **Disable Heavy Panes**: Comment out resource-intensive pane updates
- **Cache Optimization**: Adjust TTL in status script for different environments

---

This implementation creates a cohesive, ADHD-optimized PM experience that seamlessly integrates strategic planning (Leantime) with tactical execution (Task Orchestrator) through persistent memory (ConPort), all presented in an intuitive terminal-based dashboard system.
