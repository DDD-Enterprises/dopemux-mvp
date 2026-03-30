# Dopemux Slash Commands for Claude Code

Seamless integration between Dopemux health monitoring and Claude Code through slash commands, providing instant access to system health, MCP server status, and automated fixes directly from your development environment.

## 🎯 Overview

Slash commands provide real-time health monitoring capabilities within Claude Code sessions, designed with ADHD-friendly interfaces for quick status checks and automated problem resolution.

### **Key Benefits**
- ⚡ **Instant Access**: Sub-second health checks from Claude Code
- 🧠 **ADHD-Optimized**: Clear visual indicators and minimal cognitive load
- 🔧 **Auto-Fix**: Automated service restart and problem resolution
- 📊 **Comprehensive**: Full system monitoring without leaving your IDE

## 🚀 Available Commands

### **Core Health Commands**

#### **`/health`** - Comprehensive Health Check
**Usage**: `/health [--detailed]`

Returns complete system health overview with all monitored services.

**Example Output**:
```
🏥 **Dopemux Health Check** 🟢

**Overall Status**: Healthy
**Summary**: 🟢 5 healthy • 🟡 1 warnings

🟢 **Dopemux Core**: Core configuration valid
🟢 **Claude Code**: Claude Code running (2 processes)
🟡 **Mcp Servers**: MCP servers running but issues detected
🟢 **Docker Services**: No Docker MCP services (normal)
🟢 **System Resources**: System resources healthy
🟢 **Adhd Features**: All ADHD features active
```

#### **`/health-quick`** - Quick Status Overview
**Usage**: `/health-quick`

Fast status check showing only essential information.

**Example Output**:
```
🏥 **Quick Health**:
dopemux_core: 🟢 Core configuration valid
claude_code: 🟢 Claude Code running (2 processes)
mcp_servers: 🟡 MCP servers running but issues detected
docker_services: 🟢 No Docker MCP services (normal)
system_resources: 🟢 System resources healthy
adhd_features: 🟢 All ADHD features active
```

#### **`/health-fix`** - Automatic Service Fixes
**Usage**: `/health-fix`

Attempts to automatically restart unhealthy services and resolve common issues.

**Example Output**:
```
🔧 **Health Fix**: Restarted MCP Sequential Thinking Server
```

### **Service-Specific Commands**

#### **`/mcp-status`** - MCP Server Health
**Usage**: `/mcp-status`

Detailed status of all MCP servers including process information and resource usage.

**Example Output**:
```
🟡 **Mcp Status**: MCP servers running but issues detected
```

#### **`/docker-status`** - Docker Services Health
**Usage**: `/docker-status`

Status of Docker-based MCP services and container health.

**Example Output**:
```
🟢 **Docker Status**: No Docker MCP services (normal)
```

#### **`/system-status`** - System Resources
**Usage**: `/system-status`

Current system resource usage including CPU, memory, and disk space.

**Example Output**:
```
🟢 **System Status**: System resources healthy
```

#### **`/adhd-status`** - ADHD Features
**Usage**: `/adhd-status`

Status of ADHD optimization features including attention monitoring and context preservation.

**Example Output**:
```
🟢 **Adhd Status**: All ADHD features active
```

## 🛠 Implementation

### **Script Location**
```
scripts/slash_commands.py
```

### **Direct Usage**
```bash
# From project root directory
python scripts/slash_commands.py [command] [options]
```

### **Available Commands**
- `health` - Comprehensive health check
- `health-quick` - Quick status overview
- `health-fix` - Automatic service fixes
- `mcp-status` - MCP server status
- `docker-status` - Docker service status
- `system-status` - System resource status
- `adhd-status` - ADHD feature status

### **Output Formats**
```bash
# Claude Code format (default)
python scripts/slash_commands.py health

# JSON format for automation
python scripts/slash_commands.py health --format json
```

## 📋 Integration Patterns

### **Development Workflow Integration**

#### **Session Start**
```bash
# Quick health check at session start
/health-quick
```

#### **During Development**
```bash
# Check if MCP servers are responding
/mcp-status

# Monitor system resources during intensive tasks
/system-status
```

#### **Issue Resolution**
```bash
# Auto-fix common problems
/health-fix

# Comprehensive diagnostics
/health --detailed
```

#### **Session End**
```bash
# Final health check before ending session
/health
```

### **ADHD-Optimized Workflow**

#### **Focus Sessions**
- Use `/health-quick` for minimal distraction
- Set up automated monitoring to reduce manual checks
- Rely on visual indicators for rapid status assessment

#### **Attention Switching**
- Use `/adhd-status` to check attention monitoring effectiveness
- Quick `/system-status` for resource awareness
- `/health-fix` for automated problem resolution

#### **Context Preservation**
- Monitor ADHD features with `/adhd-status`
- Use health checks to ensure context preservation is working
- Auto-fix to maintain optimal ADHD support environment

## 🔧 Technical Details

### **Slash Command Processor**
```python
class SlashCommandProcessor:
    def __init__(self, project_path: Optional[Path] = None)
    def process_command(self, command: str, args: list = None) -> Dict[str, Any]
```

### **Response Format**
```python
# Successful response
{
    "success": True,
    "command": "health",
    "overall_status": "healthy",
    "overall_emoji": "🟢",
    "services": {...},
    "summary": "🟢 5 healthy • 🟡 1 warnings",
    "timestamp": "2025-09-19T10:30:00"
}

# Error response
{
    "success": False,
    "error": "Unknown command: invalid",
    "available_commands": [...]
}
```

### **Health Status Mapping**
| Status | Emoji | Color | Meaning |
|--------|-------|-------|---------|
| `healthy` | 🟢 | Green | All systems operational |
| `warning` | 🟡 | Yellow | Minor issues, system functional |
| `critical` | 🔴 | Red | Significant problems requiring attention |
| `unknown` | ⚪ | White | Status cannot be determined |

## 🎯 Advanced Usage

### **Custom Project Path**
```bash
# Monitor different project
python scripts/slash_commands.py health --project-path /path/to/project
```

### **Automation Integration**
```bash
# JSON output for scripting
python scripts/slash_commands.py health --format json | jq '.overall_status'

# Check specific service programmatically
python scripts/slash_commands.py mcp-status --format json | jq '.status'
```

### **Continuous Monitoring**
```bash
# Monitor health every 30 seconds
while true; do
    python scripts/slash_commands.py health-quick
    sleep 30
done
```

## 🧠 ADHD-Specific Features

### **Cognitive Load Reduction**
- **Minimal Output**: Essential information only
- **Visual Indicators**: Emoji-based status for quick scanning
- **Automated Fixes**: Reduce decision fatigue with auto-resolution
- **Consistent Format**: Same structure across all commands

### **Attention Management**
- **Quick Commands**: Fast execution to maintain focus
- **Clear Feedback**: Immediate status indication
- **Non-Intrusive**: Gentle monitoring without disruption
- **Context Aware**: Understands ADHD workflow patterns

### **Executive Function Support**
- **Simple Commands**: Easy to remember slash command syntax
- **Automated Actions**: Reduces manual intervention requirements
- **Status Summarization**: Key information highlighted
- **Error Prevention**: Proactive health monitoring

## 🔍 Troubleshooting

### **Common Issues**

#### **Command Not Found**
```bash
# Ensure you're in the correct directory
cd /path/to/dopemux-mvp

# Check if script exists
ls scripts/slash_commands.py

# Verify Python path
python scripts/slash_commands.py --help
```

#### **Import Errors**
```bash
# Install Dopemux in development mode
pip install -e .

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### **Health Check Failures**
```bash
# Run with detailed error information
python scripts/slash_commands.py health --format json

# Check individual service
python scripts/slash_commands.py mcp-status
```

### **Error Messages**
```python
# Unknown command
{
    "success": False,
    "error": "Unknown command: invalid-command",
    "available_commands": ["health", "health-quick", ...]
}

# Service check failure
{
    "success": False,
    "error": "Health check failed: Service unavailable",
    "command": "mcp-status"
}
```

## 📊 Performance Metrics

### **Response Times**
- `/health-quick`: < 100ms
- `/health`: < 500ms
- `/mcp-status`: < 200ms
- `/docker-status`: < 300ms
- `/system-status`: < 50ms
- `/adhd-status`: < 100ms
- `/health-fix`: 1-5 seconds

### **Resource Usage**
- **Memory**: < 50MB per command execution
- **CPU**: Minimal impact during execution
- **Network**: Local system calls only
- **Disk**: Temporary log files only

## 🔮 Future Enhancements

### **Planned Features**
- **Interactive Mode**: Dynamic command selection
- **History Tracking**: Command execution history
- **Custom Alerts**: User-defined health thresholds
- **Integration Webhooks**: External service notifications

### **Claude Code Integration**
- **Native Slash Commands**: Direct Claude Code integration
- **Status Bar**: Persistent health indicators
- **Notification System**: Proactive health alerts
- **Quick Actions**: One-click fix buttons

### **ADHD Optimizations**
- **Attention Patterns**: Adaptive monitoring based on focus state
- **Gentle Reminders**: Non-intrusive health check suggestions
- **Context Switching**: Health state preservation across sessions
- **Personalization**: User-specific health monitoring preferences

---

**Note**: These slash commands are specifically designed to integrate seamlessly with ADHD-optimized development workflows, providing immediate health insights while maintaining focus and reducing cognitive overhead.