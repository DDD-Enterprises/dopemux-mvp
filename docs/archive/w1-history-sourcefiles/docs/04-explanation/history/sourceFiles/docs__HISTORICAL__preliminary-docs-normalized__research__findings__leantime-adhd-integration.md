# Leantime Integration with Dopemux: ADHD-Optimized Terminal Development Platform

## An open-source revolution meets terminal-based productivity

Leantime, the open-source project management platform explicitly designed for neurodivergent minds, offers a compelling integration target for Dopemux development orchestration. Built by and for people with ADHD, autism, and dyslexia, Leantime's architecture combines Laravel 11+, MySQL 8+, and a robust plugin system with behavioral science and AI to create cognitive accessibility features that transform how developers manage complex projects. The platform's **JSON-RPC 2.0 API** at `/api/jsonrpc`, extensive ADHD-specific features, and proven track record with 1.8 million Docker pulls make it an ideal foundation for terminal-based integration. 

For Dopemux integration, the key opportunity lies in bridging Leantime's neurodivergent-friendly design principles with terminal-based workflows through React Ink components and tmux multiplexing, creating an unprecedented development environment that supports both productivity and well-being. This research provides comprehensive technical implementation details, ADHD-optimized workflow strategies, and concrete code examples for building this integration.

## Leantime's technical foundation enables flexible integration

Leantime runs on a **Laravel 11+ MVC architecture** with PHP 8.2+ requirements, utilizing MySQL 8.0+ or MariaDB 10.6+ for data persistence. The platform's domain-driven design organizes functionality into distinct modules (Auth, Projects, Tickets, Users) while maintaining a clean separation of concerns. The file structure follows Laravel conventions with `/app/Plugins/` for extensions, `/app/Core/` for system files, and `/app/Domain/` for business logic modules.

The **JSON-RPC 2.0 API** deviates from traditional REST, offering a single endpoint (`/api/jsonrpc`) with method-based routing using the pattern `leantime.rpc.[domain].[method]`. Authentication occurs via `x-api-key` headers, with keys generated through the Company Settings interface. This approach provides direct access to internal service methods, enabling operations like:

```bash
curl -X POST https://leantime.example.com/api/jsonrpc \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "leantime.rpc.tickets.addTicket",
    "jsonrpc": "2.0",
    "id": "create-task-123",
    "params": {
      "headline": "Implement Dopemux integration",
      "type": "task",
      "projectId": "42",
      "priority": "3"
    }
  }'
```

The **plugin architecture** supports custom extensions through a structured approach with bootstrap initialization, event registration, and Laravel-compatible components. Plugins reside in `/app/Plugins/` with PSR-4 autoloading, enabling developers to extend functionality without modifying core code. The marketplace offers pre-built plugins including Pomodoro timers, custom fields, and AI integration.

Deployment flexibility comes through **Docker support** with official images and docker-compose configurations. The platform requires minimal resources (512MB RAM, 1GB disk) but recommends 2GB+ RAM for production. Environment-based configuration via `.env` files simplifies deployment across different environments.

## ADHD-specific features transform project management

Leantime's neurodivergent design philosophy manifests through multiple integrated features addressing ADHD challenges. The **time management tools** include built-in Pomodoro timer functionality, time blocking with iCal integration, and real-time tracking that addresses "time blindness" common in ADHD. Users can start work timers directly on tasks, providing visible time awareness and data-driven insights into actual time usage.

**Visual organization** accommodates different processing styles through multiple views: Kanban boards for visual task flow, Gantt charts for timeline visualization, calendar integration for scheduling, table views for structured data, and simple list formats. The customizable "My Work" dashboard uses widgets that can be sized and arranged according to user preferences, showing only relevant work to reduce cognitive overwhelm.

The **dopamine-driven reward system** incorporates emoji sentiment ratings (from angry face to elated unicorn) that allow users to express how they feel about tasks. AI uses this sentiment data to suggest better task organization and timing. Variable rewards provide unexpected recognition, with multiple voice tones (pirate, knight, motivational speaker) for personalized feedback. Annual progress summaries highlight accomplishments often forgotten by ADHD minds.

**AI-powered task decomposition** automatically breaks down complex projects into manageable subtasks. The system translates project descriptions into bite-sized components, creating personalized task descriptions that highlight individual roles and relevance. Progressive disclosure presents information in manageable chunks rather than overwhelming blocks, following a "Think & Make" organizational structure that separates planning from execution.

The **emotion-based prioritization** system uses task sentiment ratings to suggest task pairings that make less interesting tasks easier to tackle. Personalized recommendations adapt to user preferences and energy levels, with smart scheduling suggestions based on emotional state and task requirements. Context-aware organization arranges tasks by importance and emotional engagement level.

## Terminal UI patterns optimize for ADHD workflows

React Ink provides the foundation for building ADHD-friendly terminal interfaces through its comprehensive component library built on Flexbox layouts using the Yoga layout engine. Essential components include `<Text>` for styled rendering, `<Box>` for layout containers, and interactive elements like `<TextInput>`, `<Select>`, and `<ProgressBar>` from the Ink UI library.

**State management** follows React patterns with hooks support:

```javascript
import React, {useState, useEffect} from 'react';
import {render, Text, Box, useFocus} from 'ink';

const TaskDashboard = () => {
  const [tasks, setTasks] = useState([]);
  const {isFocused} = useFocus();
  
  return (
    <Box 
      borderStyle={isFocused ? 'double' : 'single'}
      borderColor={isFocused ? 'cyan' : 'gray'}
      padding={1}
    >
      <Text bold color="cyan">📋 Current Tasks</Text>
      {tasks.map(task => (
        <Box key={task.id} justifyContent="space-between">
          <Text color={getStatusColor(task.status)}>
            {task.status === 'completed' ? '✓' : '○'} {task.title}
          </Text>
          <Text dimColor>{formatRelativeTime(task.dueDate)}</Text>
        </Box>
      ))}
    </Box>
  );
};
```

**Tmux multiplexed layouts** create dedicated project environments:

```bash
# ~/.tmux.conf - ADHD-friendly configuration
set -g status-style 'bg=#1e1e2e fg=#cdd6f4'
set -g pane-border-style 'fg=#585b70'
set -g pane-active-border-style 'fg=#f38ba8'

# Intuitive navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Project-specific bindings
bind-key t new-window -n 'tasks' 'leantime-cli task list'
bind-key m new-window -n 'monitor' 'leantime-cli wellness check'
```

**Color coding strategies** enhance visual hierarchy:
- **Red**: Urgent/overdue tasks requiring immediate attention
- **Yellow**: Due today or warning states
- **Green**: Completed tasks and successes  
- **Blue**: Informational notes and documentation
- **Cyan**: Navigation elements and headers
- **Gray**: Inactive or disabled items

Progressive disclosure reduces cognitive load through expandable sections, clear boundaries using ASCII art boxes, and focus indicators that highlight the current working context. The interface maintains high contrast for readability while supporting screen reader compatibility through semantic text formatting.

## ADHD workflow strategies guide task management

Effective ADHD task management requires **breaking down complexity** into manageable chunks. Research shows 15-25 minute segments match ADHD attention spans, using a maximum 3-level hierarchy (Project → Phase → Action) with verb-specific descriptions. The system adds 50% buffer time to all estimates, tracking actual versus estimated times to improve accuracy over time.

The **NOW-SOON-LATER priority framework** replaces complex matrices with intuitive categories. NOW contains 1-3 urgent items to prevent overwhelm, SOON holds tasks with approaching deadlines, and LATER stores long-term projects. Dynamic priority adjustment responds to energy levels and context availability:

```javascript
function calculateADHDPriority(task) {
    let priority = 0;
    priority += task.urgencyScore * 40;      // Deadline weight
    priority += task.interestLevel * 30;      // Engagement factor
    priority += task.contextAvailable ? 20 : 0;
    priority += (task.energyRequired <= user.currentEnergy) ? 10 : -20;
    return priority;
}
```

**Context switching minimization** groups similar tasks together through batch processing. Theme days (Monday = Admin, Tuesday = Creative) reduce transition costs. The system implements transition rituals including 5-minute warnings, quick notes about stopping points, and environmental shifts to signal context changes. Work-in-progress limits cap active tasks at three, with automatic context snapshots preserving task state.

**Executive function support** provides external scaffolding for planning and organization. Visual project timelines show task relationships, while automated sequencing suggests logical task order. Decision templates prevent analysis paralysis through time-boxed choices and "good enough" principles. Working memory supports include persistent information displays, context panels showing related details, and smart reminders based on user patterns.

**Momentum tracking** leverages dopamine-driven motivation through visual streak displays, chain visualization on calendars, and micro-wins celebration. The system includes grace periods for streak recovery, preventing all-or-nothing thinking. Progress bars, achievement badges, and completion animations provide immediate feedback. Recovery strategies offer gentle restart options after breaks, preserving partial progress and suggesting smaller tasks to rebuild momentum.

## Integration architecture connects terminal and web

The integration between Dopemux and Leantime requires careful consideration of **data synchronization patterns**. Event-driven architecture using webhooks enables real-time updates:

```javascript
// Webhook handler for Leantime events
class LeantimeWebhookHandler {
  async handleEvent(event) {
    switch(event.type) {
      case 'task.completed':
        await this.updateTerminalDashboard(event.data);
        await this.triggerCelebration(event.data.userId);
        break;
      case 'project.milestone_reached':
        await this.notifyTeam(event.data);
        await this.updateProgressMetrics(event.data);
        break;
    }
  }
}
```

**Conflict resolution** strategies handle concurrent edits through vector clocks for distributed state, operational transformation for collaborative editing, and three-way merge for complex conflicts. Delta synchronization minimizes data transfer by sending only changes since the last sync timestamp.

**State management** coordinates between terminal and web interfaces:

```javascript
class DopemuxLeantimeSync {
  constructor() {
    this.localState = new Map();
    this.remoteState = new Map();
    this.pendingSync = [];
  }
  
  async syncTask(task) {
    // Optimistic local update
    this.localState.set(task.id, task);
    this.updateTerminalUI(task);
    
    try {
      // Sync to Leantime
      const result = await this.leantimeAPI.updateTask(task);
      this.remoteState.set(task.id, result);
      this.confirmSync(task.id);
    } catch (error) {
      this.handleSyncError(task.id, error);
      this.rollbackLocalChange(task.id);
    }
  }
}
```

**Offline-first capabilities** ensure productivity continues without connectivity. Local changes queue for later synchronization, with automatic retry logic using exponential backoff. The system maintains read-your-writes consistency, ensuring users see their changes immediately even before server confirmation.

## Life management features support holistic productivity

Beyond project management, the integration supports **personal goal tracking** through OKR frameworks that align personal and professional objectives. Goals link to projects for automatic progress tracking, with separate contexts for work, life, wellness, and growth:

```javascript
class HolisticGoalManager {
  trackGoal(goal) {
    return {
      professional: this.trackProfessionalProgress(goal),
      personal: this.trackPersonalMilestones(goal),
      health: this.trackWellnessMetrics(goal),
      learning: this.trackSkillDevelopment(goal)
    };
  }
}
```

**Work-life balance tools** enforce healthy boundaries through work hour tracking with daily and weekly limits. Break reminders use contextual suggestions based on current activity. Personal time blocks protect focus periods from meeting intrusions. The system adapts break recommendations based on user behavior and preferences.

**Wellness monitoring** integrates directly with development workflows:

```javascript
class DeveloperWellnessMonitor {
  constructor() {
    this.pomodoroTimer = new PomodoroTimer(25, 5);
    this.postureReminder = new IntervalReminder(30, "Check posture 🪑");
    this.eyeStrainPrevention = new TwentyTwentyRule();
    this.hydrationTracker = new HydrationReminder();
  }
  
  integrateWithTerminal() {
    return {
      onSessionStart: () => this.startMonitoring(),
      onTaskComplete: () => this.suggestBreak(),
      onLongSession: () => this.enforceBreak()
    };
  }
}
```

**Mood and energy tracking** provides insights through daily check-ins measuring energy, mood, focus, and motivation levels. The system correlates these metrics with task completion patterns, identifying optimal work times and stress triggers. Smart scheduling then assigns tasks based on predicted energy levels and required cognitive resources.

**Personal productivity metrics** measure focus time, task velocity, and flow state percentage. The system tracks interruption sources, context switching frequency, and productivity trends over time. These insights generate personalized recommendations for improving focus and maintaining sustainable productivity.

## Implementation roadmap for Dopemux integration

To implement this integration, start by **setting up the React Ink environment** with `npx create-ink-app dopemux-leantime` and installing necessary dependencies including `@inkjs/ui` for UI components. Configure tmux with ADHD-friendly defaults including high contrast colors, clear window indicators, and project-specific layouts.

**Create core terminal components** including task lists with visual hierarchy, progress indicators with celebration animations, quick action menus for common operations, and status dashboards showing key metrics. Implement the Leantime API client using JSON-RPC:

```javascript
class LeantimeClient {
  constructor(apiKey, baseUrl) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }
  
  async callMethod(method, params) {
    const response = await fetch(`${this.baseUrl}/api/jsonrpc`, {
      method: 'POST',
      headers: {
        'x-api-key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        method: `leantime.rpc.${method}`,
        jsonrpc: "2.0",
        id: generateId(),
        params
      })
    });
    
    return response.json();
  }
}
```

**Configure webhook endpoints** to receive real-time updates from Leantime, implementing handlers for task events, project milestones, and wellness reminders. Set up bidirectional synchronization with conflict resolution and offline support.

**Deploy the integrated system** using Docker containers for both Leantime and the Dopemux terminal interface. Configure environment variables for API keys, webhook secrets, and user preferences. Implement monitoring for system health, user wellness metrics, and productivity indicators.

The combination of Leantime's neurodivergent-centered design with terminal-based development workflows creates a unique productivity environment. By implementing ADHD-optimized patterns, visual organization strategies, and holistic life management features, this integration supports both high-performance development and developer well-being. The technical architecture enables flexible extension while maintaining the cognitive accessibility that makes Leantime revolutionary for neurodivergent users.
