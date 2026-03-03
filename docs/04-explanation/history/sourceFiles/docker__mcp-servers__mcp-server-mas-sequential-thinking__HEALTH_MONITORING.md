# MCP Sequential Thinking Server - Health Monitoring Guide

This guide provides comprehensive health monitoring and diagnostic capabilities for your custom MCP Sequential Thinking Server.

## 🏥 Health Monitoring Features

### **1. Built-in MCP Health Check Tools**

The server now includes two built-in MCP tools accessible through Claude Code:

#### `health_check` Tool
- **Purpose**: Quick server status overview
- **Returns**: JSON with server state, team status, process info, and environment
- **Usage**: Call via MCP protocol in Claude Code
- **Response Time**: < 100ms typically

#### `server_diagnostics` Tool
- **Purpose**: Deep diagnostic information for troubleshooting
- **Returns**: Detailed technical data including system info and configuration
- **Usage**: Call via MCP protocol in Claude Code
- **Response Time**: < 200ms typically

### **2. External Health Monitor Script**

Location: `scripts/health_monitor.py`

#### Quick Commands:
```bash
# Basic server status
python scripts/health_monitor.py status

# Comprehensive health check
python scripts/health_monitor.py health

# Show running processes
python scripts/health_monitor.py processes

# View recent logs
python scripts/health_monitor.py logs

# Continuous monitoring (30s intervals)
python scripts/health_monitor.py monitor

# Restart server
python scripts/health_monitor.py restart
```

## 📊 Health Check Categories

### **Process Health**
- **Process Discovery**: Automatically finds all MCP server instances
- **Resource Usage**: Memory consumption, CPU usage, thread count
- **Uptime Tracking**: Process creation time and running duration
- **Status Monitoring**: Process state (running, stopped, zombie)

### **Environment Health**
- **API Key Validation**: Checks for required API keys (DeepSeek, OpenAI, GitHub, Exa)
- **Provider Configuration**: Validates LLM provider settings
- **Key Security**: Reports if keys are set without exposing values

### **Server State Health**
- **Initialization Status**: Server state and team initialization
- **Session Activity**: Active sessions and statistics
- **Configuration Validation**: Provider, team mode, timeouts

### **System Health**
- **Resource Availability**: CPU count, memory, disk usage
- **Platform Information**: OS details, Python version, architecture
- **Performance Metrics**: Response times and efficiency

## 🚨 Health Status Indicators

### Status Levels:
- **`healthy`**: All systems operational
- **`warning`**: Minor issues, server functional
- **`unhealthy`**: Critical issues, server may not work
- **`error`**: Health check itself failed

### Process Status:
- **`running`**: Server processes active
- **`stopped`**: No server processes found
- **`degraded`**: Some but not all processes running

## 🔧 Troubleshooting Guide

### **Common Issues & Solutions**

#### 1. "Not connected" MCP Error
```bash
# Check if server processes are running
python scripts/health_monitor.py processes

# Restart server if needed
python scripts/health_monitor.py restart

# Verify Claude Code can connect
/mcp  # Run in Claude Code to check connections
```

#### 2. Server Startup Failures
```bash
# Check environment variables
python scripts/health_monitor.py health | grep environment

# View recent logs for errors
python scripts/health_monitor.py logs

# Test manual startup
DEEPSEEK_API_KEY="your_key" python -m mcp_server_mas_sequential_thinking.main
```

#### 3. High Memory Usage
```bash
# Monitor continuously
python scripts/health_monitor.py monitor

# Check individual process usage
python scripts/health_monitor.py processes

# Restart if memory leak suspected
python scripts/health_monitor.py restart
```

#### 4. API Key Issues
```bash
# Verify all required keys are set
python scripts/health_monitor.py health | jq .environment

# Check key formats (GitHub tokens need specific prefixes)
echo $GITHUB_TOKEN | cut -c1-10
```

## 📈 Monitoring Best Practices

### **Development Environment**
1. **Regular Health Checks**: Run `python scripts/health_monitor.py health` daily
2. **Process Monitoring**: Use `monitor` command during active development
3. **Log Review**: Check logs weekly with `logs` command

### **Production Environment**
1. **Automated Monitoring**: Set up cron job for health checks
2. **Alert Thresholds**: Monitor memory usage > 500MB
3. **Uptime Tracking**: Alert if uptime < expected
4. **Resource Limits**: Set CPU and memory limits

### **Continuous Monitoring Setup**
```bash
# Add to crontab for hourly health checks
echo "0 * * * * cd /path/to/server && python scripts/health_monitor.py health >> health.log 2>&1" | crontab -

# Start continuous monitoring in background
nohup python scripts/health_monitor.py monitor --interval 60 > monitor.log 2>&1 &
```

## 🔍 Advanced Diagnostics

### **Performance Analysis**
```bash
# Response time analysis
for i in {1..10}; do
  python scripts/health_monitor.py health | jq .response_time_ms
  sleep 1
done

# Memory trend analysis
python scripts/health_monitor.py monitor --interval 10 | tee memory_trend.log
```

### **Environment Validation**
```bash
# Complete environment check
python scripts/health_monitor.py health | jq '.environment'

# API key length validation
python scripts/health_monitor.py health | jq '.environment | to_entries[] | select(.key | endswith("_length"))'
```

### **Process Deep Dive**
```bash
# Detailed process information
python scripts/health_monitor.py processes

# Process tree analysis
pstree -p $(python scripts/health_monitor.py processes | jq -r '.[] | .pid')
```

## 📋 Health Check Automation

### **Shell Functions** (Add to `.bashrc` or `.zshrc`)
```bash
# Quick aliases for MCP server health
alias mcp-status='cd /path/to/server && python scripts/health_monitor.py status'
alias mcp-health='cd /path/to/server && python scripts/health_monitor.py health'
alias mcp-restart='cd /path/to/server && python scripts/health_monitor.py restart'
alias mcp-logs='cd /path/to/server && python scripts/health_monitor.py logs'
```

### **Health Check Script** (`health_check.sh`)
```bash
#!/bin/bash
cd /path/to/mcp-server-mas-sequential-thinking
HEALTH=$(python scripts/health_monitor.py health)
STATUS=$(echo "$HEALTH" | jq -r .overall_status)

if [ "$STATUS" != "healthy" ]; then
    echo "⚠️  MCP Server Health Alert: $STATUS"
    echo "$HEALTH" | jq .
    # Add notification logic here (email, Slack, etc.)
fi
```

## 🎯 Integration with Dopemux ADHD Features

### **ADHD-Optimized Monitoring**
- **Gentle Notifications**: Non-intrusive status updates
- **Progress Visualization**: Clear health status indicators
- **Context Preservation**: Health history for attention management
- **Simple Commands**: Easy-to-remember monitoring aliases

### **Attention Management**
- **Quick Status**: `mcp-status` for fast overview
- **Detailed When Needed**: `mcp-health` for deep dive
- **Automated Monitoring**: Reduce cognitive load with scripts

---

**Note**: This health monitoring system is specifically designed for the MCP Sequential Thinking Server with ADHD-optimized development workflows. All monitoring data respects privacy by not exposing sensitive API keys while providing comprehensive operational visibility.