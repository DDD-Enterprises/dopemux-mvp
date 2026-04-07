# Dopemux Health Monitoring System

Comprehensive health monitoring and diagnostic system for the Dopemux ADHD-optimized development platform with integrated support for Claude Code, MCP servers, and Docker-based services.

## 🏥 Overview

The Dopemux Health Monitoring System provides real-time health checks across your entire development ecosystem with ADHD-friendly interfaces and automated remediation capabilities.

### **Monitored Components**

| Component | Description | Health Indicators |
|-----------|-------------|-------------------|
| **Dopemux Core** | Project initialization, configuration files | 🟢 Healthy / 🟡 Missing configs / 🔴 Not initialized |
| **Claude Code** | Integration status, running processes | 🟢 Running / 🟡 Partial / 🔴 Not running |
| **MCP Servers** | Python and Docker-based MCP services | 🟢 All healthy / 🟡 Some issues / 🔴 Critical errors |
| **Docker Services** | Container-based MCP server ecosystem | 🟢 All running / 🟡 Some down / 🔴 Failed |
| **System Resources** | CPU, memory, disk usage | 🟢 Normal / 🟡 High usage / 🔴 Critical |
| **ADHD Features** | Attention monitoring, context preservation | 🟢 Active / 🟡 Partial / 🔴 Inactive |

## 🚀 Quick Start

### **Basic Health Check**
```bash
# Comprehensive health overview
dopemux health

# Quick status check
dopemux health --service system_resources

# Detailed diagnostics
dopemux health --detailed

# Auto-fix unhealthy services
dopemux health --fix
```

### **Continuous Monitoring**
```bash
# Watch mode with 30-second intervals
dopemux health --watch

# Custom interval monitoring
dopemux health --watch --interval 60
```

## 📋 CLI Commands

### **Main Health Command**

```bash
dopemux health [OPTIONS]
```

#### **Options**
- `--detailed, -d` - Show detailed health information
- `--service, -s SERVICE` - Check specific service only
- `--fix, -f` - Attempt to fix unhealthy services
- `--watch, -w` - Continuous monitoring mode
- `--interval, -i SECONDS` - Watch interval (default: 30s)

#### **Service Names**
- `dopemux_core` - Core Dopemux functionality
- `claude_code` - Claude Code integration
- `mcp_servers` - MCP server health
- `docker_services` - Docker containers
- `system_resources` - System resource usage
- `adhd_features` - ADHD optimization features

### **Usage Examples**

```bash
# Check all services
dopemux health

# Check only MCP servers
dopemux health --service mcp_servers

# Detailed system resources check
dopemux health --service system_resources --detailed

# Auto-fix with detailed output
dopemux health --fix --detailed

# Monitor continuously every 10 seconds
dopemux health --watch --interval 10
```

## 🎯 Slash Commands for Claude Code

Integration with Claude Code through slash commands for instant health monitoring.

### **Available Slash Commands**

| Command | Description | Output |
|---------|-------------|--------|
| `/health` | Comprehensive health check | Full status report with all services |
| `/health-quick` | Quick status overview | Simple service status list |
| `/health-fix` | Automatic service fixes | List of restarted services |
| `/mcp-status` | MCP servers only | Detailed MCP server status |
| `/docker-status` | Docker services only | Container health information |
| `/system-status` | System resources only | CPU, memory, disk usage |
| `/adhd-status` | ADHD features only | Attention monitoring effectiveness |

### **Slash Command Usage**

#### **From Claude Code Terminal**
```bash
# Quick health overview
python scripts/slash_commands.py health-quick

# Comprehensive health check
python scripts/slash_commands.py health

# Fix unhealthy services
python scripts/slash_commands.py health-fix

# Check specific service
python scripts/slash_commands.py mcp-status
```

#### **Integration with Claude Code Workflows**
The slash commands are designed to be called directly from Claude Code sessions for real-time health monitoring during development.

## 🧠 ADHD-Optimized Features

### **Visual Health Indicators**
- 🟢 **Healthy**: All systems operational
- 🟡 **Warning**: Minor issues, system functional
- 🔴 **Critical**: Significant problems requiring attention
- ⚪ **Unknown**: Status cannot be determined

### **Cognitive Load Reduction**
- **Quick Mode**: Essential information only
- **Detailed Mode**: Comprehensive diagnostics when needed
- **Auto-Fix**: Automated problem resolution
- **Watch Mode**: Gentle continuous monitoring

### **Attention-Friendly Design**
- **Response Times**: Sub-second health checks
- **Clear Messaging**: Simple, actionable status messages
- **Progress Indicators**: Visual feedback during operations
- **Summary Panels**: Key information highlighted

## 🔧 Technical Architecture

### **Health Checker Class**
```python
from dopemux.health import HealthChecker

# Initialize health checker
checker = HealthChecker(project_path=Path.cwd())

# Run all health checks
results = checker.check_all(detailed=True)

# Display results
checker.display_health_report(results, detailed=True)
```

### **Service Health Structure**
```python
@dataclass
class ServiceHealth:
    name: str
    status: HealthStatus  # HEALTHY, WARNING, CRITICAL, UNKNOWN
    message: str
    details: Dict[str, Any]
    response_time_ms: float
    last_check: Optional[datetime]
```

### **Health Status Levels**
```python
class HealthStatus(Enum):
    HEALTHY = ("healthy", "🟢", "green")
    WARNING = ("warning", "🟡", "yellow")
    CRITICAL = ("critical", "🔴", "red")
    UNKNOWN = ("unknown", "⚪", "dim")
```

## 🐳 Docker MCP Server Support

### **Container Health Monitoring**
- **Automatic Discovery**: Finds MCP-related containers
- **Status Tracking**: Running, stopped, restarting states
- **Resource Monitoring**: Memory, CPU usage per container
- **Port Availability**: Service endpoint health checks

### **Docker Compose Integration**
```yaml
# Health check configuration for MCP servers
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
  timeout: 10s
  retries: 3
  interval: 30s
  start_period: 30s
```

### **Supported MCP Server Types**
- **Context7**: Documentation and API references
- **Zen**: Multi-model orchestration
- **Sequential Thinking**: Multi-step reasoning
- **ConPort**: Project memory and decision tracking
- **Task Master AI**: Task management
- **Serena**: Code navigation and refactoring
- **Claude Context**: Semantic code search
- **Exa**: AI-powered web research (Custom FastMCP server)
- **MorphLLM**: Pattern-based transformations
- **Desktop Commander**: Desktop automation

## 📊 Health Check Details

### **Dopemux Core Checks**
- Project initialization status
- Configuration file presence
- Directory structure validation
- Template compatibility

### **Claude Code Checks**
- Process detection and monitoring
- Integration status verification
- MCP connection health
- Configuration validation

### **MCP Server Checks**
- Process discovery and monitoring
- Resource usage tracking
- Response time measurement
- Error rate monitoring
- Sequential thinking server health

### **Docker Service Checks**
- Container status monitoring
- Health check endpoint verification
- Resource usage tracking
- Network connectivity tests

### **System Resource Checks**
- CPU usage monitoring (alert at >80%)
- Memory usage tracking (alert at >85%)
- Disk space monitoring (alert at >90%)
- Process count verification

### **ADHD Feature Checks**
- Attention monitoring effectiveness
- Context preservation status
- Session data validation
- Feature activation verification

## 🔍 Troubleshooting Guide

### **Common Issues and Solutions**

#### **Dopemux Not Initialized**
```bash
# Problem: "Dopemux not initialized"
# Solution:
dopemux init

# Or for existing projects:
dopemux init --force
```

#### **Claude Code Not Running**
```bash
# Problem: "Claude Code not running"
# Solution:
dopemux start

# Or with background mode:
dopemux start --background
```

#### **MCP Servers Unhealthy**
```bash
# Problem: "MCP servers running but issues detected"
# Solution:
dopemux health --fix

# Or manual restart:
python docker/mcp-servers/mcp-server-mas-sequential-thinking/scripts/health_monitor.py restart
```

#### **High Resource Usage**
```bash
# Problem: "High CPU/Memory usage"
# Solution: Check specific processes
dopemux health --service system_resources --detailed

# Monitor continuously
dopemux health --watch --interval 10
```

#### **ADHD Features Inactive**
```bash
# Problem: "ADHD features not active"
# Solution: Restore attention monitoring
dopemux status --attention

# Or restart with context restoration
dopemux start --session latest
```

### **Exit Codes**
- `0` - All services healthy
- `1` - One or more critical issues detected

### **Log Files**
- **Dopemux Logs**: `~/.dopemux/logs/`
- **MCP Server Logs**: `~/.sequential_thinking/logs/`
- **Claude Code Logs**: System-dependent

## 🔄 Automated Monitoring

### **Continuous Health Monitoring**
```bash
# Start background monitoring
nohup dopemux health --watch --interval 60 > health.log 2>&1 &

# Monitor with auto-fix
nohup dopemux health --watch --fix --interval 300 > health-fix.log 2>&1 &
```

### **Cron Integration**
```bash
# Add to crontab for hourly health checks
0 * * * * cd /path/to/dopemux && dopemux health >> ~/.dopemux/health.log 2>&1

# Daily comprehensive health report
0 9 * * * cd /path/to/dopemux && dopemux health --detailed > ~/.dopemux/daily-health.log 2>&1
```

### **Integration with CI/CD**
```bash
# Health check in build scripts
if ! dopemux health; then
    echo "Health check failed, aborting deployment"
    exit 1
fi
```

## 🎯 Best Practices

### **Development Workflow**
1. **Start Session**: `dopemux health` before beginning work
2. **Periodic Checks**: Use `/health-quick` during development
3. **Issue Resolution**: `dopemux health --fix` when problems arise
4. **End Session**: `dopemux health --detailed` for comprehensive status

### **ADHD-Optimized Usage**
- **Quick Checks**: Use slash commands for instant feedback
- **Visual Scanning**: Rely on emoji indicators for rapid assessment
- **Auto-Fix**: Let the system resolve common issues automatically
- **Watch Mode**: Use for gentle, non-intrusive monitoring

### **Team Collaboration**
- **Shared Health**: Include health status in team standup reports
- **Documentation**: Log health issues and solutions in project notes
- **Automation**: Set up automated health monitoring for shared environments

## 📚 API Reference

### **HealthChecker Class**

#### **Methods**
```python
# Initialize health checker
checker = HealthChecker(project_path: Optional[Path] = None)

# Run all health checks
check_all(detailed: bool = False) -> Dict[str, ServiceHealth]

# Quick status overview
quick_status() -> Dict[str, str]

# Display formatted health report
display_health_report(results: Dict[str, ServiceHealth], detailed: bool = False)

# Format for slash commands
format_for_slash_command(results: Dict[str, ServiceHealth]) -> str

# Attempt to fix unhealthy services
restart_unhealthy_services() -> List[str]
```

#### **Individual Service Checks**
```python
# Check specific services
_check_dopemux_core(detailed: bool = False) -> ServiceHealth
_check_claude_code(detailed: bool = False) -> ServiceHealth
_check_mcp_servers(detailed: bool = False) -> ServiceHealth
_check_docker_services(detailed: bool = False) -> ServiceHealth
_check_system_resources(detailed: bool = False) -> ServiceHealth
_check_adhd_features(detailed: bool = False) -> ServiceHealth
```

### **Slash Command Processor**

#### **Commands**
```python
# Process slash commands
processor = SlashCommandProcessor(project_path: Optional[Path] = None)

# Available commands
process_command(command: str, args: list = None) -> Dict[str, Any]
```

#### **Supported Commands**
- `health` - Comprehensive health check
- `health-quick` - Quick status overview
- `health-fix` - Automatic service fixes
- `mcp-status` - MCP server status
- `docker-status` - Docker service status
- `system-status` - System resource status
- `adhd-status` - ADHD feature status

## 🔮 Future Enhancements

### **Planned Features**
- **Predictive Health**: AI-powered issue prediction
- **Performance Trends**: Historical health data analysis
- **Integration Monitoring**: Third-party service health checks
- **Custom Thresholds**: User-configurable health parameters
- **Alert System**: Proactive notifications for health issues

### **Docker Ecosystem Expansion**
- **Service Mesh Monitoring**: Advanced container orchestration health
- **Load Balancer Integration**: Health check routing
- **Microservice Dependencies**: Cross-service health validation
- **Resource Optimization**: Automated container scaling based on health

---

**Note**: This health monitoring system is specifically designed for ADHD-optimized development workflows, providing clear visual feedback, automated problem resolution, and gentle monitoring to reduce cognitive load while maintaining comprehensive system oversight.