# MetaMCP Integration Guide for Dopemux

## 🎯 Overview

This guide provides step-by-step instructions for integrating the official MetaMCP Docker container with your existing Dopemux MCP infrastructure. The integration creates a three-tier architecture that maximizes ADHD accommodations while achieving 95% token reduction.

## 🏗️ Architecture Overview

### **Three-Tier Integration**
```
Claude Code → Custom MetaMCP Broker → Official MetaMCP → Docker MCP Servers
     ↓              ↓                    ↓               ↓
  Role-based    ADHD           Unified        Individual
  filtering   optimizations   management      servers
```

### **Key Benefits**
- **95% token reduction** through intelligent filtering
- **ADHD-optimized** role-based tool access
- **Unified management** of all MCP servers
- **Enterprise features** like OAuth, monitoring, middleware
- **Context preservation** across all tools

---

## 🚀 Quick Start

### **Prerequisites**
- Docker and Docker Compose installed
- Existing Dopemux MCP servers running
- API keys for all MCP services
- 4GB+ RAM available for MetaMCP

### **1. Clone and Setup**
```bash
cd /Users/hue/code/dopemux-mvp/docker/metamcp

# Copy environment template
cp .env.metamcp .env

# Edit environment variables
nano .env
```

### **2. Start MetaMCP Stack**
```bash
# Start MetaMCP and dependencies
docker-compose -f docker-compose.metamcp.yml up -d

# Check status
docker-compose -f docker-compose.metamcp.yml ps
```

### **3. Configure MCP Servers**
```bash
# Open MetaMCP Web UI
open http://localhost:12008

# Import server configurations
curl -X POST http://localhost:12008/api/servers/import \
  -H "Content-Type: application/json" \
  -d @metamcp-servers-config.json
```

### **4. Test Integration**
```bash
# Test endpoint
curl http://localhost:12008/metamcp/reference/sse

# Check logs
docker-compose -f docker-compose.metamcp.yml logs metamcp
```

---

## 📋 Detailed Implementation

### **Phase 1: MetaMCP Infrastructure Setup**

#### **Step 1.1: Environment Configuration**
Edit `/docker/metamcp/.env`:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
CONTEXT7_API_KEY=your_context7_key_here
EXA_API_KEY=your_exa_key_here

# ADHD Optimization Settings
MAX_TOOLS_PER_ROLE=5
ENABLE_GENTLE_NOTIFICATIONS=true
AUTO_SAVE_INTERVAL=30
```

#### **Step 1.2: Database Initialization**
```bash
# Create init SQL for PostgreSQL
cat > docker/metamcp/metamcp-config/init.sql << EOF
-- ADHD-optimized database schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User preferences for ADHD accommodations
CREATE TABLE user_adhd_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    focus_duration INTEGER DEFAULT 1500, -- 25 minutes
    break_duration INTEGER DEFAULT 300,  -- 5 minutes
    max_tools INTEGER DEFAULT 5,
    gentle_notifications BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Token usage tracking
CREATE TABLE token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    tokens_used INTEGER NOT NULL,
    session_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Context preservation
CREATE TABLE session_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    context_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_context_session_id ON session_context(session_id);
CREATE INDEX idx_token_usage_user_role ON token_usage(user_id, role);
EOF
```

#### **Step 1.3: Prometheus Monitoring Setup**
```bash
# Create monitoring configuration
mkdir -p docker/metamcp/metamcp-config

cat > docker/metamcp/metamcp-config/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'metamcp'
    static_configs:
      - targets: ['metamcp:3000']
    metrics_path: '/api/metrics'

  - job_name: 'mcp-servers'
    static_configs:
      - targets:
        - 'mcp-context7:3002'
        - 'mcp-zen:3003'
        - 'mcp-mas-sequential-thinking:3001'
        - 'mcp-conport:3004'
        - 'mcp-task-master-ai:3005'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
EOF
```

### **Phase 2: Server Configuration Import**

#### **Step 2.1: Import MCP Server Definitions**
```bash
# Use the MetaMCP Web UI or API
curl -X POST http://localhost:12008/api/servers/bulk-import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @metamcp-servers-config.json
```

#### **Step 2.2: Create Namespaces**
```bash
# Import namespace configurations
curl -X POST http://localhost:12008/api/namespaces/bulk-import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @metamcp-namespaces.json
```

#### **Step 2.3: Configure Middleware**
```bash
# Enable ADHD optimization middleware
curl -X POST http://localhost:12008/api/middleware/enable \
  -H "Content-Type: application/json" \
  -d '{
    "name": "adhd_optimization",
    "config": {
      "maxDecisionTime": 5000,
      "maxRoleSwitchTime": 200,
      "flowStateProtection": true,
      "gentleNotifications": true
    }
  }'
```

### **Phase 3: Custom Broker Integration**

#### **Step 3.1: Update Custom MetaMCP Broker**
Edit `metamcp_server.py`:

```python
# Add MetaMCP endpoint integration
class MetaMCPServer:
    def __init__(self):
        self.metamcp_base_url = "http://localhost:12008/metamcp"
        self.current_role = "developer"
        self.api_key = os.getenv("METAMCP_API_KEY")

    async def switch_role(self, new_role: str):
        """Switch role and update available namespace"""
        namespace_mapping = {
            "developer": "development",
            "researcher": "research",
            "architect": "planning",
            "reviewer": "quality",
            "debugger": "development",
            "planner": "planning",
            "ops": "automation"
        }

        target_namespace = namespace_mapping.get(new_role, "development")
        self.current_namespace = target_namespace
        self.current_role = new_role

        # Update MetaMCP with role change
        await self._notify_metamcp_role_change(new_role, target_namespace)

    async def handle_tool_call(self, tool_name: str, params: dict):
        """Route tool calls through MetaMCP"""
        endpoint = f"{self.metamcp_base_url}/{self.current_namespace}/sse"

        # Add ADHD context to request
        enhanced_params = {
            **params,
            "adhd_context": {
                "role": self.current_role,
                "session_id": self.current_session_id,
                "focus_mode": True,
                "gentle_response": True
            }
        }

        return await self._call_metamcp_endpoint(endpoint, tool_name, enhanced_params)
```

#### **Step 3.2: Configure Role-Based Endpoints**
```python
# Add endpoint configuration for each role
ROLE_ENDPOINTS = {
    "developer": {
        "primary": "development",
        "fallback": ["reference", "automation"]
    },
    "researcher": {
        "primary": "research",
        "fallback": ["reference"]
    },
    "architect": {
        "primary": "planning",
        "fallback": ["reference", "development"]
    }
    # ... other roles
}
```

### **Phase 4: ADHD Optimizations**

#### **Step 4.1: Context Preservation Setup**
```javascript
// MetaMCP middleware for ADHD context preservation
const adhdOptimizationMiddleware = {
  name: 'adhd_optimization',
  async process(request, response, next) {
    // Auto-save context every 30 seconds
    if (request.adhd_context?.session_id) {
      await saveContextToConPort(request.adhd_context.session_id, {
        role: request.adhd_context.role,
        currentTool: request.tool_name,
        parameters: request.parameters,
        timestamp: Date.now()
      });
    }

    // Apply gentle notification styling
    if (request.adhd_context?.gentle_response) {
      response.style = 'gentle';
      response.max_decision_options = 3;
    }

    return next();
  }
};
```

#### **Step 4.2: Tool Filtering Implementation**
```javascript
// Tool filtering middleware
const toolFilterMiddleware = {
  name: 'tool_filter',
  async process(request, response, next) {
    const userRole = request.adhd_context?.role || 'developer';
    const allowedTools = ROLE_TOOL_MAPPING[userRole] || [];

    if (!allowedTools.includes(request.tool_name)) {
      return {
        error: 'Tool not available for current role',
        suggestion: `Switch to role that supports ${request.tool_name}`,
        allowedTools: allowedTools.slice(0, 3) // Max 3 suggestions
      };
    }

    return next();
  }
};
```

### **Phase 5: Monitoring and Analytics**

#### **Step 5.1: Grafana Dashboard Setup**
```bash
# Create ADHD-specific dashboard
cat > docker/metamcp/metamcp-config/grafana/dashboards/adhd-metrics.json << EOF
{
  "dashboard": {
    "title": "ADHD Development Metrics",
    "panels": [
      {
        "title": "Token Usage by Role",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(token_usage_total) by (role)",
            "legendFormat": "{{role}}"
          }
        ]
      },
      {
        "title": "Flow State Duration",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(flow_state_duration_seconds)",
            "legendFormat": "Average Flow State"
          }
        ]
      },
      {
        "title": "Context Switch Frequency",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(context_switches_total[5m])",
            "legendFormat": "Switches per minute"
          }
        ]
      }
    ]
  }
}
EOF
```

#### **Step 5.2: Custom Metrics Collection**
```python
# Add ADHD-specific metrics to MetaMCP
from prometheus_client import Counter, Histogram, Gauge

# ADHD-specific metrics
flow_state_duration = Histogram(
    'flow_state_duration_seconds',
    'Duration of uninterrupted work sessions',
    buckets=[300, 900, 1500, 2100, 3000]  # 5min to 50min
)

context_switches = Counter(
    'context_switches_total',
    'Number of role/tool context switches',
    ['from_role', 'to_role']
)

cognitive_load = Gauge(
    'cognitive_load_score',
    'Current cognitive load based on active tools',
    ['user_id', 'role']
)

decision_time = Histogram(
    'decision_time_seconds',
    'Time taken to select appropriate tool',
    buckets=[1, 3, 5, 10, 20]  # 1s to 20s
)
```

---

## 🔧 Configuration Management

### **Environment Variables**
Key environment variables for ADHD optimization:

```bash
# ADHD Core Settings
MAX_TOOLS_PER_ROLE=5
MAX_DECISION_TIME=5000
ENABLE_GENTLE_NOTIFICATIONS=true
AUTO_SAVE_INTERVAL=30

# Token Optimization
ENABLE_TOKEN_TRACKING=true
ENFORCE_CONTEXT7_FIRST=true
ENABLE_SMART_CACHING=true

# Performance Targets
TARGET_RESPONSE_TIME_FAST=500
TARGET_RESPONSE_TIME_NORMAL=2000
TARGET_RESPONSE_TIME_COMPLEX=10000
```

### **Role-Based Budgets**
Configure token budgets per role:

```bash
BUDGET_DEVELOPER=15000
BUDGET_RESEARCHER=10000
BUDGET_ARCHITECT=25000
BUDGET_REVIEWER=15000
BUDGET_DEBUGGER=12000
BUDGET_PLANNER=8000
BUDGET_OPS=6000
```

### **Namespace Configuration**
Map roles to namespaces:

```yaml
roleMapping:
  developer:
    primaryNamespaces: ["reference", "development"]
    secondaryNamespaces: ["automation"]
    tokenBudget: 15000

  architect:
    primaryNamespaces: ["reference", "planning"]
    secondaryNamespaces: ["development"]
    tokenBudget: 25000
```

---

## 🧪 Testing and Validation

### **Step 1: Individual Server Testing**
```bash
# Test each MCP server through MetaMCP
for namespace in reference development research planning quality automation; do
  echo "Testing namespace: $namespace"
  curl -H "Authorization: Bearer $API_KEY" \
    "http://localhost:12008/metamcp/$namespace/sse" \
    -d '{"method": "tools/list"}' | jq '.tools | length'
done
```

### **Step 2: Role Switching Testing**
```bash
# Test role-based tool filtering
python test_role_switching.py
```

```python
# test_role_switching.py
import asyncio
import json
from metamcp_client import MetaMCPClient

async def test_role_switching():
    client = MetaMCPClient("http://localhost:12008")

    # Test developer role
    await client.switch_role("developer")
    dev_tools = await client.list_tools()
    assert len(dev_tools) <= 5, f"Too many tools for developer: {len(dev_tools)}"

    # Test architect role
    await client.switch_role("architect")
    arch_tools = await client.list_tools()
    assert "mas-sequential-thinking" in [t.name for t in arch_tools]

    print("✅ Role switching tests passed")

if __name__ == "__main__":
    asyncio.run(test_role_switching())
```

### **Step 3: Token Optimization Testing**
```bash
# Measure token usage before/after optimization
python measure_token_efficiency.py --role developer --task "simple_feature"
```

### **Step 4: ADHD Accommodation Testing**
```bash
# Test context preservation during interruptions
python test_adhd_features.py
```

---

## 🚨 Troubleshooting

### **Common Issues**

#### **MetaMCP Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.metamcp.yml logs metamcp

# Common fixes
docker-compose -f docker-compose.metamcp.yml down
docker volume prune
docker-compose -f docker-compose.metamcp.yml up -d
```

#### **MCP Servers Not Connecting**
```bash
# Check network connectivity
docker network inspect mcp-network
docker network inspect metamcp-network

# Test individual server health
curl http://localhost:3002/health  # Context7
curl http://localhost:3003/health  # Zen
```

#### **High Token Usage**
```bash
# Check token tracking
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:12008/api/metrics/tokens" | jq

# Verify Context7 first rule
grep "context7_first" docker/metamcp/metamcp-config/middleware.yml
```

#### **Role Switching Not Working**
```bash
# Check custom broker logs
tail -f logs/metamcp_custom_broker.log

# Verify namespace mapping
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:12008/api/namespaces" | jq '.[] | {name, servers}'
```

### **Performance Issues**

#### **Slow Response Times**
```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=response_time_seconds

# Optimize database
docker exec metamcp-postgres psql -U metamcp -d metamcp -c "VACUUM ANALYZE;"
```

#### **Memory Issues**
```bash
# Check container resource usage
docker stats metamcp

# Increase memory limits in docker-compose.metamcp.yml
deploy:
  resources:
    limits:
      memory: 4G
```

---

## 📊 Monitoring and Metrics

### **Key Metrics to Monitor**

#### **ADHD-Specific Metrics**
- **Flow State Duration:** Average uninterrupted work time
- **Context Switch Frequency:** Role/tool changes per hour
- **Decision Time:** Time to select appropriate tool
- **Cognitive Load Score:** Number of active tools/choices

#### **Token Efficiency Metrics**
- **Token Reduction Percentage:** Actual vs baseline usage
- **Cost per Session:** Dollar cost per development session
- **Cache Hit Rate:** Percentage of queries served from cache
- **Context7 First Success:** Percentage of documentation-first queries

#### **Performance Metrics**
- **Response Time by Tool:** Latency for each MCP server
- **Error Rate:** Failed requests per hour
- **Uptime:** Service availability percentage
- **Throughput:** Requests per minute

### **Dashboard Setup**
Access monitoring dashboards:
- **MetaMCP Admin:** http://localhost:12008/admin
- **Grafana:** http://localhost:3001 (admin/dopemux_admin_2024)
- **Prometheus:** http://localhost:9090

---

## 🎯 Success Criteria

### **Phase 1 Success (Week 1-2)**
- ✅ MetaMCP stack running successfully
- ✅ All MCP servers connected and healthy
- ✅ Basic namespace configuration working
- ✅ 50% token reduction achieved

### **Phase 2 Success (Week 3-4)**
- ✅ Custom broker integration complete
- ✅ Role-based tool filtering active
- ✅ ADHD optimizations functional
- ✅ 75% token reduction achieved

### **Phase 3 Success (Month 2)**
- ✅ Advanced monitoring and analytics
- ✅ Context preservation across interruptions
- ✅ Smart caching and optimization
- ✅ 90% token reduction achieved

### **Final Success (Month 3+)**
- ✅ 95% token reduction target met
- ✅ ADHD accommodations validated by users
- ✅ System running reliably in production
- ✅ Team productivity measurably improved

---

## 🔄 Maintenance and Updates

### **Regular Maintenance Tasks**
```bash
# Weekly database maintenance
docker exec metamcp-postgres psql -U metamcp -d metamcp -c "VACUUM ANALYZE;"

# Monthly log rotation
docker-compose -f docker-compose.metamcp.yml exec metamcp npm run logs:rotate

# Quarterly optimization review
python scripts/analyze_usage_patterns.py --period quarterly
```

### **Update Procedures**
```bash
# Update MetaMCP container
docker-compose -f docker-compose.metamcp.yml pull metamcp
docker-compose -f docker-compose.metamcp.yml up -d metamcp

# Backup before major updates
docker exec metamcp-postgres pg_dump -U metamcp metamcp > backup_$(date +%Y%m%d).sql
```

This comprehensive integration guide provides everything needed to successfully deploy MetaMCP with ADHD optimizations and achieve the target 95% token reduction while maintaining excellent developer experience.