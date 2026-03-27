# Dopemux CLI Reference

## Overview

The Dopemux CLI provides ADHD-optimized commands for managing development sessions, context preservation, and task decomposition. All commands are designed with gentle, supportive UX and clear visual feedback.

## Global Options

```bash
dopemux [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]
```

### Global Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--version` | Show version and exit | `dopemux --version` |
| `--config, -c` | Specify config file path | `dopemux -c custom.yaml start` |
| `--verbose, -v` | Enable verbose output | `dopemux -v status` |

---

## Commands

### `dopemux init`

**Initialize a Dopemux project with ADHD-optimized configuration**

#### Usage
```bash
dopemux init [DIRECTORY] [OPTIONS]
```

#### Arguments
- `DIRECTORY` - Target directory (default: current directory)

#### Options

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--force` | `-f` | Overwrite existing configuration | `false` | `dopemux init --force` |
| `--template` | `-t` | Project template type | `python` | `dopemux init -t rust` |

#### Available Templates

| Template | Description | Generated Config |
|----------|-------------|------------------|
| `python` | Python project with pytest, type hints | PEP 8, Black formatting, mypy |
| `javascript` | Node.js project with modern tooling | ESLint, Prettier, Jest |
| `typescript` | TypeScript project with strict config | TSConfig, type checking |
| `rust` | Rust project with Cargo integration | Clippy, rustfmt, cargo-watch |
| `go` | Go project with modules | gofmt, golint, go test |
| `java` | Java project with Maven/Gradle | Checkstyle, JUnit, SpotBugs |

#### Examples

```bash
# Initialize current directory with Python template
dopemux init

# Initialize specific directory with TypeScript template
dopemux init ./my-project --template typescript

# Force overwrite existing configuration
dopemux init --force

# Initialize with Rust template
dopemux init ~/code/rust-project -t rust
```

#### What Gets Created

```
project/
├── .dopemux/
│   ├── config.yaml          # ADHD profile settings
│   ├── context.db           # SQLite context storage
│   └── sessions/            # Session backup directory
└── .claude/
    ├── claude.md            # Project-specific Claude instructions
    ├── context.md           # Context management configuration
    ├── llms.md              # Multi-model AI configuration
    └── session.md           # Session persistence patterns
```

#### Success Output
```
🎉 Project Initialized

📁 Configuration: /path/to/project/.claude/
🧠 ADHD features: /path/to/project/.dopemux/

Next steps:
• Run 'dopemux start' to launch Claude Code
• Use 'dopemux save' to preserve context
• Check 'dopemux status' for attention metrics
```

#### Error Handling

| Error | Solution |
|-------|----------|
| Directory doesn't exist | Create directory or use existing path |
| Already initialized | Use `--force` to overwrite |
| Permission denied | Check write permissions on directory |
| Invalid template | Use `dopemux init --help` to see available templates |

---

### `dopemux start`

**Launch Claude Code with ADHD optimizations and context restoration**

#### Usage
```bash
dopemux start [OPTIONS]
```

#### Options

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--session` | `-s` | Restore specific session ID | Latest session | `dopemux start -s abc123` |
| `--background` | `-b` | Launch in background mode | `false` | `dopemux start --background` |
| `--debug` | | Enable debug output | `false` | `dopemux start --debug` |

#### Examples

```bash
# Start with latest context
dopemux start

# Restore specific session
dopemux start --session abc12345

# Launch in background
dopemux start --background

# Debug mode for troubleshooting
dopemux start --debug
```

#### Launch Process

1. **🔍 Project Check** - Verify Dopemux initialization
2. **📍 Context Restore** - Load session context (<500ms)
3. **🚀 Claude Launch** - Start Claude Code with MCP servers
4. **🧠 Monitor Start** - Begin attention monitoring
5. **✅ Ready** - Display session information

#### Output Examples

**New Session:**
```
🆕 Starting new session

✨ Claude Code is running with ADHD optimizations
Press Ctrl+C to stop monitoring and save context
```

**Restored Session:**
```
📍 Welcome back! You were working on: Implement user authentication

🎯 Goal: Add JWT-based login system
📁 Files: 5 files restored
⏱️  Last save: 2 hours ago
🧠 Attention state: focused

✨ Claude Code is running with ADHD optimizations
Press Ctrl+C to stop monitoring and save context
```

**Background Mode:**
```
🚀 Claude Code launched in background
🆔 Process ID: 12345
📋 Use 'dopemux status' to check session
💾 Context auto-saving every 30 seconds
```

#### Requirements Check

The command will verify:
- ✅ Project is initialized (`.dopemux/` exists)
- ✅ Claude Code is installed and accessible
- ✅ MCP servers are configured
- ✅ SQLite database is accessible

#### Auto-initialization

If project is not initialized:
```
⚠️  Project not initialized. Run 'dopemux init' first.

Initialize now? (y/N): y
```

---

### `dopemux save`

**Manually save current development context**

#### Usage
```bash
dopemux save [OPTIONS]
```

#### Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--message` | `-m` | Add save message/note | `dopemux save -m "Before refactoring"` |
| `--force` | `-f` | Force save even if no changes | `dopemux save --force` |

#### Examples

```bash
# Quick save
dopemux save

# Save with descriptive message
dopemux save --message "Completed user model, starting authentication"

# Force save (useful for testing)
dopemux save --force

# Save before major change
dopemux save -m "Before switching to async approach"
```

#### What Gets Saved

| Context Type | Information Captured |
|--------------|---------------------|
| **File State** | Open files, cursor positions, selections |
| **Mental Model** | Current goal, approach, blockers |
| **Session Data** | Git branch, recent changes, time spent |
| **ADHD Metrics** | Attention state, focus duration, breaks |
| **Decision History** | Choices made, rationale, outcomes |

#### Success Output
```
✅ Context saved (session: abc12345)
💾 Captured 7 open files, 3 recent edits
🧠 Attention state: focused (87% focus score)
⏱️  Session duration: 23 minutes

Note: Completed user model implementation
```

#### Performance
- ⚡ **Save time:** <50ms (invisible to user)
- 💾 **Storage:** ~2-5KB per session
- 🔄 **Auto-save:** Every 30 seconds in background

---

### `dopemux restore`

**Restore previous development context**

#### Usage
```bash
dopemux restore [OPTIONS]
```

#### Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--session` | `-s` | Specific session ID to restore | `dopemux restore -s abc123` |
| `--list` | `-l` | List available sessions | `dopemux restore --list` |

#### Examples

```bash
# Restore latest session
dopemux restore

# Restore specific session
dopemux restore --session abc12345

# List all available sessions
dopemux restore --list

# List and then restore interactively
dopemux restore -l
# (shows list, then user can copy session ID)
```

#### Session List Output

```bash
dopemux restore --list
```

```
Available Sessions
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID       ┃ Timestamp           ┃ Goal                                               ┃ Files   ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ f7a3b2c8 │ 2024-01-15 14:30:22 │ Implement user authentication system              │ 7       │
│ e9d1a4f6 │ 2024-01-15 11:15:45 │ Fix database connection timeout issue             │ 4       │
│ b5c8e2a9 │ 2024-01-15 09:45:12 │ Add input validation to user registration         │ 3       │
│ d4f7b1c3 │ 2024-01-14 16:20:33 │ Refactor authentication middleware                │ 5       │
│ a8e3c6d2 │ 2024-01-14 13:55:18 │ Write unit tests for user service                 │ 8       │
└──────────┴─────────────────────┴────────────────────────────────────────────────────┴─────────┘
```

#### Restore Success Output

```
✅ Restored session from 2024-01-15 14:30:22

🎯 Goal: Implement user authentication system
📁 Files: 7 files restored to exact positions
🧠 Previous attention state: focused
⏱️  Session was: 45 minutes of focused work

Welcome back! You were working on the login endpoint implementation.
Last action: Added password hashing to User model
Next planned step: Create JWT token generation
```

#### Restoration Performance
- ⚡ **Restore time:** <500ms (ADHD requirement)
- 🎯 **Accuracy:** Exact file positions, selections, context
- 💾 **Storage:** Compressed JSON with indexing

---

### `dopemux status`

**Show current session status and ADHD metrics**

#### Usage
```bash
dopemux status [OPTIONS]
```

#### Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--attention` | `-a` | Show only attention metrics | `dopemux status -a` |
| `--context` | `-c` | Show only context information | `dopemux status -c` |
| `--tasks` | `-t` | Show only task progress | `dopemux status -t` |

#### Examples

```bash
# Show all status information
dopemux status

# Show only attention metrics
dopemux status --attention

# Show only context information
dopemux status --context

# Show only task progress
dopemux status --tasks
```

#### Full Status Output

```bash
dopemux status
```

```
🧠 Attention Metrics
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric          ┃ Value       ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Current State   │ focused     │ 🎯        │
│ Session Duration│ 23.5 min    │ ⏱️         │
│ Focus Score     │ 87.2%       │ 🎯        │
│ Context Switches│ 3           │ 🔄        │
│ Break Count     │ 1           │ ☕        │
│ Keystroke Rate  │ 52/min      │ ⌨️         │
│ Error Rate      │ 3.1%        │ 🐛        │
└─────────────────┴─────────────┴───────────┘

📍 Context Information
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Item            ┃ Value                                            ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Current Goal    │ Implement JWT token generation                   │
│ Open Files      │ 5                                                │
│ Last Save       │ 2 minutes ago                                    │
│ Git Branch      │ feature/authentication                           │
│ Project         │ /Users/dev/myproject                             │
│ Session ID      │ f7a3b2c8                                         │
└─────────────────┴──────────────────────────────────────────────────┘

📋 Task Progress
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ Task                                          ┃ Status  ┃ Progress  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ Set up user model with password hashing      │ ✅      │ 100%      │
│ Create login endpoint with validation        │ 🔄      │ 75%       │
│ Add JWT token generation                     │ ⏳      │ 0%        │
│ Write authentication tests                   │ ⏳      │ 0%        │
└───────────────────────────────────────────────┴─────────┴───────────┘
```

#### Attention State Indicators

| State | Emoji | Description | Recommendation |
|-------|-------|-------------|----------------|
| 🎯 focused | Green | High productivity, low errors | Continue current approach |
| 😊 normal | Blue | Balanced work pattern | Standard development pace |
| 🌪️ scattered | Yellow | Frequent context switches | Take break or focus on single task |
| 🔥 hyperfocus | Orange | Very high intensity | Monitor for burnout, suggest breaks |
| 😵‍💫 distracted | Red | Low focus, high errors | Take break, try grounding exercise |

#### Context Switch Thresholds

| Count | Status | ADHD Impact |
|-------|--------|-------------|
| 0-5 | 🟢 Stable | Focused work session |
| 6-15 | 🟡 Moderate | Normal development pattern |
| 16-30 | 🟠 High | Possible scattered attention |
| 31+ | 🔴 Excessive | Likely distraction/overwhelm |

---

### `dopemux task`

**ADHD-friendly task management with 25-minute chunks**

#### Usage
```bash
dopemux task [DESCRIPTION] [OPTIONS]
dopemux task [OPTIONS]  # When using --list
```

#### Arguments
- `DESCRIPTION` - Task description (required unless using `--list`)

#### Options

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--duration` | `-d` | Task duration in minutes | `25` | `dopemux task "Fix bug" -d 45` |
| `--priority` | `-p` | Priority level | `medium` | `dopemux task "Security fix" -p high` |
| `--list` | `-l` | List current tasks | | `dopemux task --list` |

#### Priority Levels

| Priority | Description | Visual Indicator | Recommended Duration |
|----------|-------------|------------------|---------------------|
| `high` | Critical/blocking work | 🔴 | 25-45 minutes |
| `medium` | Standard development | 🟡 | 25 minutes |
| `low` | Nice-to-have features | 🟢 | 15-25 minutes |

#### Examples

```bash
# Add new task with default settings (25 min, medium priority)
dopemux task "Fix authentication bug"

# Add high-priority task with custom duration
dopemux task "Security vulnerability patch" --priority high --duration 45

# Add low-priority task
dopemux task "Update documentation" -p low -d 15

# List all current tasks
dopemux task --list

# Quick task addition
dopemux task "Refactor user service"
```

#### Task List Output

```bash
dopemux task --list
```

```
Current Tasks
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Task                                          ┃ Priority  ┃ Duration ┃ Status        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ Fix authentication timeout issue             │ 🔴 high   │ 25m      │ 🔄 In Progress│
│ Add input validation to registration form    │ 🟡 medium │ 25m      │ ⏳ Pending    │
│ Write unit tests for user service           │ 🟡 medium │ 30m      │ ⏳ Pending    │
│ Update API documentation                     │ 🟢 low    │ 15m      │ ⏳ Pending    │
│ Refactor database connection pooling        │ 🟡 medium │ 25m      │ ✅ Complete   │
└───────────────────────────────────────────────┴───────────┴──────────┴───────────────┘

📊 Progress Summary:
• 🔄 Active: 1 task
• ⏳ Pending: 3 tasks
• ✅ Completed: 1 task
• ⏱️ Total estimated time: 95 minutes (3h 55min)
• 🎯 Recommended next: Fix authentication timeout issue (high priority)
```

#### Task Addition Output

```bash
dopemux task "Implement password reset functionality" --priority medium --duration 30
```

```
✅ Task added: Implement password reset functionality

🆔 ID: t7a3b2c8
⏱️ Duration: 30 minutes
🎯 Priority: medium
📅 Status: pending

💡 Tip: This task will be automatically broken into focused segments
🚀 Use 'dopemux start' to begin working with task context
```

#### Automatic Task Decomposition

For complex tasks (>45 minutes or high complexity), Dopemux automatically suggests breakdown:

```bash
dopemux task "Build complete user management system" --duration 120
```

```
🤔 This looks like a complex task! Let me break it down:

📋 Suggested breakdown:
├── 📝 Task 1: Design user model schema (25 min)
├── 📝 Task 2: Implement user CRUD operations (25 min)
├── 📝 Task 3: Add authentication endpoints (25 min)
├── 📝 Task 4: Create user management UI (25 min)
└── 📝 Task 5: Write comprehensive tests (20 min)

✅ Accept this breakdown? (Y/n): y

🎉 Created 5 focused tasks totaling 120 minutes
🎯 Ready to start with: Design user model schema
```

#### Task Status Management

Tasks automatically update status based on session activity:

- ⏳ **Pending** → 🔄 **In Progress** (when files related to task are opened)
- 🔄 **In Progress** → ✅ **Complete** (when marked complete or time target met)
- Any status → 📋 **On Hold** (when blocked or waiting for dependencies)

---

### `dopemux autoresponder`

**Manage Claude Auto Responder integration for automatic confirmations**

The autoresponder automatically handles Claude Code confirmation prompts with ADHD-optimized controls and attention-aware features.

#### Usage
```bash
dopemux autoresponder COMMAND [OPTIONS]
```

#### Subcommands

##### `setup`
**Download and configure ClaudeAutoResponder tool**

```bash
dopemux autoresponder setup
```

Sets up the ClaudeAutoResponder repository and dependencies. Only needs to be run once per project.

**Example Output:**
```
🔧 Setting up ClaudeAutoResponder...
✅ ClaudeAutoResponder setup complete
🚀 Run 'dopemux autoresponder start' to begin
```

##### `start`
**Start automatic confirmation monitoring**

```bash
dopemux autoresponder start [OPTIONS]
```

**Options:**

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--terminal-scope` | `-t` | Terminal monitoring scope | `current` | `--terminal-scope all` |
| `--delay` | `-d` | Response delay in seconds | `0.0` | `--delay 1.5` |
| `--timeout` | | Auto-stop timeout (minutes) | `30` | `--timeout 60` |
| `--whitelist` | | Enable tool whitelisting | `true` | `--whitelist` |
| `--no-whitelist` | | Disable tool whitelisting | | `--no-whitelist` |
| `--debug` | | Enable debug logging | `false` | `--debug` |

**Terminal Scope Options:**
- `current` - Monitor only current terminal window
- `all` - Monitor all terminal windows
- `project` - Monitor project-related terminals

**Examples:**
```bash
# Basic start with default settings
dopemux autoresponder start

# Start with 1-second delay for scattered attention
dopemux autoresponder start --delay 1.0

# Monitor all terminals with debug logging
dopemux autoresponder start -t all --debug

# Extended session with 60-minute timeout
dopemux autoresponder start --timeout 60
```

**Sample Output:**
```
🚀 Starting auto responder...
✅ Claude Auto Responder is now active
🎯 Monitoring for Claude Code confirmation prompts
📡 Scope: current
💤 Auto-stop after 30 minutes of inactivity
```

##### `stop`
**Stop automatic confirmation monitoring**

```bash
dopemux autoresponder stop
```

Stops the autoresponder and displays session statistics.

**Sample Output:**
```
⏹️ Stopping auto responder...
✅ Claude Auto Responder stopped

📊 Session Statistics:
  ⏱️ Uptime: 45.3 minutes
  ✅ Responses sent: 23
  📈 Rate: 0.51 responses/min
```

##### `status`
**Show current autoresponder status and metrics**

```bash
dopemux autoresponder status
```

**Sample Output:**
```
🤖 Claude Auto Responder Status
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property              │ Value                                                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Status                │ 🟢 Running                                                     │
│ Running               │ Yes                                                             │
│ Uptime                │ 15.2 minutes                                                   │
│ Responses Sent        │ 8                                                               │
│ Response Rate         │ 0.53/min                                                       │
│ Attention State       │ focused                                                         │
│ Last Response         │ 2024-01-15T14:30:45                                           │
└───────────────────────┴─────────────────────────────────────────────────────────────────┘

⚙️ Configuration
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Setting               │ Value                                                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Enabled               │ Yes                                                             │
│ Terminal Scope        │ current                                                         │
│ Response Delay        │ 0.0s                                                            │
│ Timeout               │ 30 minutes                                                      │
│ Whitelist Tools       │ Yes                                                             │
│ Debug Mode            │ No                                                              │
└───────────────────────┴─────────────────────────────────────────────────────────────────┘
```

##### `config`
**Configure autoresponder settings**

```bash
dopemux autoresponder config [OPTIONS]
```

**Options:**

| Option | Description | Values | Example |
|--------|-------------|--------|---------|
| `--enabled` | Enable autoresponder | | `--enabled` |
| `--disabled` | Disable autoresponder | | `--disabled` |
| `--terminal-scope` | Set monitoring scope | `current`, `all`, `project` | `--terminal-scope all` |
| `--delay` | Set response delay | `0.0` to `10.0` seconds | `--delay 2.0` |
| `--timeout` | Set timeout duration | Minutes | `--timeout 45` |
| `--whitelist` | Enable tool whitelisting | | `--whitelist` |
| `--no-whitelist` | Disable tool whitelisting | | `--no-whitelist` |
| `--debug` | Enable debug mode | | `--debug` |
| `--no-debug` | Disable debug mode | | `--no-debug` |

**Examples:**
```bash
# Show current configuration
dopemux autoresponder config

# Enable with specific settings
dopemux autoresponder config --enabled --delay 1.0 --terminal-scope all

# Configure for hyperfocus sessions (no delay, extended timeout)
dopemux autoresponder config --delay 0.0 --timeout 90

# Configure for scattered attention (with delays)
dopemux autoresponder config --delay 2.0 --timeout 20
```

**Sample Configuration Update:**
```
✅ Configuration updated
  enabled: True
  delay: 1.0
  terminal_scope: all
🔄 Restarting auto responder with new settings...
```

#### ADHD-Optimized Usage Patterns

**For Different Attention States:**

**🎯 Hyperfocus Sessions:**
```bash
# No delays, extended timeout for deep work
dopemux autoresponder config --delay 0.0 --timeout 120
dopemux autoresponder start
```

**🌪️ Scattered Attention:**
```bash
# Gentle delays to reduce overwhelm
dopemux autoresponder config --delay 1.5 --timeout 20
dopemux autoresponder start
```

**⚡ Context Switching:**
```bash
# Project-specific scope to avoid interference
dopemux autoresponder config --terminal-scope project
dopemux autoresponder start
```

**🔧 Development Setup:**
```bash
# Safe defaults for coding sessions
dopemux autoresponder config --enabled --whitelist --timeout 45
dopemux autoresponder start
```

#### Integration with Other Commands

The autoresponder integrates seamlessly with other Dopemux commands:

```bash
# Start complete development session
dopemux start --with-autoresponder

# Check status including autoresponder
dopemux status  # Shows autoresponder in overview

# Save context with autoresponder metrics
dopemux save -m "Completed with auto-responses: 15"
```

---

## Error Handling

### Common Errors and Solutions

#### Project Not Initialized
```bash
Error: No Dopemux project found in current directory

Solution:
• Run 'dopemux init' to initialize current directory
• Navigate to existing Dopemux project
• Use 'dopemux init /path/to/project' for specific directory
```

#### Claude Code Not Found
```bash
Error: Claude Code not found. Please install Claude Code first.

Solution:
• Install Claude Code from https://claude.ai/code
• Ensure claude-code is in your PATH
• Verify installation: claude-code --version
```

#### Session Restore Failed
```bash
Error: Session f7a3b2c8 not found

Solution:
• Use 'dopemux restore --list' to see available sessions
• Check session ID spelling (case-sensitive)
• Try 'dopemux restore' to restore latest session
```

#### Database Locked
```bash
Error: Context database is locked by another process

Solution:
• Close other Dopemux instances
• Wait 30 seconds and try again
• Check for zombie processes: ps aux | grep dopemux
```

#### Permission Denied
```bash
Error: Permission denied writing to .dopemux/context.db

Solution:
• Check directory permissions: ls -la .dopemux/
• Ensure you own the project directory
• Try: chmod 755 .dopemux/ && chmod 644 .dopemux/*
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
dopemux --verbose start --debug
```

Debug output includes:
- 📊 Performance timing for all operations
- 🔧 MCP server configuration details
- 💾 Database query execution times
- 🧠 Attention classification algorithm details
- 📁 File system operation logging

---

## Environment Variables

### Configuration Override

| Variable | Description | Example |
|----------|-------------|---------|
| `DOPEMUX_CONFIG` | Override config file location | `export DOPEMUX_CONFIG=/custom/config.yaml` |
| `DOPEMUX_DEBUG` | Enable debug mode | `export DOPEMUX_DEBUG=1` |
| `DOPEMUX_CLAUDE_PATH` | Custom Claude Code path | `export DOPEMUX_CLAUDE_PATH=/usr/local/bin/claude-code` |

### ADHD Profile Override

| Variable | Description | Example |
|----------|-------------|---------|
| `DOPEMUX_FOCUS_DURATION` | Override focus duration | `export DOPEMUX_FOCUS_DURATION=30` |
| `DOPEMUX_BREAK_INTERVAL` | Override break interval | `export DOPEMUX_BREAK_INTERVAL=10` |
| `DOPEMUX_AUTO_SAVE_INTERVAL` | Override auto-save interval | `export DOPEMUX_AUTO_SAVE_INTERVAL=15` |

### MCP Server Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DOPEMUX_MCP_CLAUDE_CONTEXT` | claude-context server path | `export DOPEMUX_MCP_CLAUDE_CONTEXT=/path/to/server` |
| `DOPEMUX_MCP_SEQUENTIAL_THINKING` | mas-sequential-thinking path | `export DOPEMUX_MCP_SEQUENTIAL_THINKING=/path/to/server` |

---

## Shell Integration

### Bash/Zsh Completion

Add to your `.bashrc` or `.zshrc`:

```bash
# Dopemux completion
eval "$(_DOPEMUX_COMPLETE=bash_source dopemux)"  # bash
eval "$(_DOPEMUX_COMPLETE=zsh_source dopemux)"   # zsh
```

### Aliases and Functions

```bash
# Quick aliases
alias ds='dopemux status'
alias dsa='dopemux save'
alias dre='dopemux restore'
alias dtl='dopemux task --list'

# Smart function to save with timestamp message
dsm() {
    local message="${1:-Auto-save $(date '+%H:%M')}"
    dopemux save --message "$message"
}

# Function to restore specific session by partial ID
drs() {
    local partial_id="$1"
    local full_id=$(dopemux restore --list | grep "$partial_id" | head -1 | awk '{print $1}')
    if [[ -n "$full_id" ]]; then
        dopemux restore --session "$full_id"
    else
        echo "No session found matching: $partial_id"
        dopemux restore --list
    fi
}
```

---

## Tips and Best Practices

### ADHD-Optimized Workflows

#### Daily Start Routine
```bash
# 1. Check status from yesterday
dopemux status

# 2. Restore previous context or start fresh
dopemux start

# 3. Review planned tasks
dopemux task --list

# 4. Begin focused work session
```

#### Hyperfocus Management
```bash
# Save context before entering hyperfocus
dopemux save -m "About to dive deep into complex refactoring"

# Set up task chunking even for hyperfocus
dopemux task "Complex refactoring session" -d 90 -p high
```

#### Context Switch Recovery
```bash
# When interrupted, quickly save context
dopemux save -m "Interrupted for meeting"

# After interruption, restore and check status
dopemux restore
dopemux status --attention
```

#### End of Day Routine
```bash
# Save final context
dopemux save -m "End of day - good stopping point"

# Review accomplishments
dopemux task --list
dopemux status
```

### Performance Tips

#### Faster Context Operations
```bash
# Use partial session IDs (first 6-8 characters)
dopemux restore -s f7a3b2

# Background saves for large projects
dopemux save --force &
```

#### Reduce Cognitive Load
```bash
# Use focused status view when overwhelmed
dopemux status --attention

# Simple task view when scattered
dopemux task --list | head -5
```

---

**📚 CLI Reference Summary:**

The Dopemux CLI provides 5 core commands designed for ADHD developers:
- ✅ `init` - Project setup with ADHD-optimized templates
- ✅ `start` - Context restoration and Claude Code launch
- ✅ `save` - Manual context preservation with notes
- ✅ `restore` - Session navigation and restoration
- ✅ `status` - Real-time ADHD metrics and progress
- ✅ `task` - 25-minute chunk task management

**All commands feature gentle UX, clear visual feedback, and <500ms performance for ADHD needs. 🧠💚**