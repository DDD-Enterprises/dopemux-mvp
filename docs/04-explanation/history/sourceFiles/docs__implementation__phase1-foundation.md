# Phase 1: Foundation Implementation - Week 1

## Overview

Phase 1 establishes the core infrastructure and datastores needed for the Dopemux orchestration system. This phase focuses on getting all services running and communicating, with basic health checks and validation.

## 🎯 **Phase 1 Objectives**

### Primary Goals
- ✅ All core datastores operational (Milvus, Redis, MySQL, Neo4j, OpenSearch)
- ✅ Docker networking with service discovery via dopemux-net bridge
- ✅ Leantime PM system installed and API-accessible
- ✅ Basic MetaMCP aggregation with health checks
- ✅ Service interdependencies validated and startup order optimized

### Success Criteria
- All services respond to health checks within 30 seconds of startup
- Inter-service communication works via service names (no hardcoded IPs)
- Leantime UI accessible and API returns valid responses
- MetaMCP can discover and list at least one MCP server
- Docker logs show no critical errors or connection failures

## 🏗️ **Infrastructure Components**

### Docker Compose Architecture

```yaml
# High-level service topology
services:
  # Core PM System
  leantime:
    depends_on: [mysql]
    networks: [dopemux-net]

  mysql:
    networks: [dopemux-net]
    volumes: [mysql-data:/var/lib/mysql]

  # Vector & Search Infrastructure
  milvus:
    depends_on: [etcd, minio]
    networks: [dopemux-net]

  opensearch:
    networks: [dopemux-net]
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true  # Dev only

  redis:
    networks: [dopemux-net]
    volumes: [redis-data:/data]

  # Graph Database
  neo4j:
    networks: [dopemux-net]
    volumes: [neo4j-data:/data]
    environment:
      - NEO4J_AUTH=neo4j/dopemux_dev_password

  # MCP Orchestration (Basic)
  metamcp:
    depends_on: [milvus, redis]
    networks: [dopemux-net]
    ports: ["3001:3000"]

  # Support Services
  etcd:  # For Milvus
    networks: [dopemux-net]

  minio:  # For Milvus
    networks: [dopemux-net]

networks:
  dopemux-net:
    driver: bridge
    name: dopemux-net
```

### Port Allocation Strategy

```yaml
external_ports:
  metamcp: "3001:3000"        # MetaMCP aggregator
  leantime: "3002:80"         # Leantime web UI
  neo4j_browser: "3003:7474"  # Neo4j browser
  neo4j_bolt: "3004:7687"     # Neo4j database
  milvus: "3005:19530"        # Milvus vector DB
  redis: "3006:6379"          # Redis cache
  opensearch: "3007:9200"     # OpenSearch API

internal_only:
  mysql: "3306"               # Leantime database
  etcd: "2379"                # Milvus coordination
  minio: "9000"               # Milvus object storage
```

### Volume Management

```yaml
volumes:
  mysql_data:
    driver: local
    driver_opts:
      type: bind
      o: bind
      device: ./data/mysql

  milvus_data:
    driver: local
    driver_opts:
      type: bind
      o: bind
      device: ./data/milvus

  neo4j_data:
    driver: local
    driver_opts:
      type: bind
      o: bind
      device: ./data/neo4j

  redis_data:
    driver: local
    driver_opts:
      type: bind
      o: bind
      device: ./data/redis

  opensearch_data:
    driver: local
    driver_opts:
      type: bind
      o: bind
      device: ./data/opensearch
```

## 📋 **Implementation Tasks**

### Task 1: Docker Environment Setup

**Duration**: 2-3 hours
**Prerequisites**: Docker and Docker Compose installed

#### Steps:
1. **Create project structure**:
   ```bash
   mkdir -p data/{mysql,milvus,neo4j,redis,opensearch}
   mkdir -p config/{leantime,metamcp,milvus}
   mkdir -p scripts/health-checks
   ```

2. **Configure environment files**:
   ```bash
   # .env for development
   COMPOSE_PROJECT_NAME=dopemux
   DOPEMUX_ENV=development

   # Database passwords
   MYSQL_ROOT_PASSWORD=dopemux_root_password
   MYSQL_PASSWORD=dopemux_db_password
   NEO4J_PASSWORD=dopemux_neo4j_password

   # API Keys (placeholder for Phase 2)
   OPENAI_API_KEY=your_key_here
   VOYAGE_API_KEY=your_key_here
   ```

3. **Create docker-compose.yml** (see Docker & Configuration section)

4. **Validate compose file**:
   ```bash
   docker-compose config  # Check syntax
   docker-compose ps      # Verify service definitions
   ```

### Task 2: Core Datastore Deployment

**Duration**: 3-4 hours
**Dependencies**: Docker environment

#### Deployment Sequence:
1. **Start infrastructure services first**:
   ```bash
   docker-compose up -d etcd minio mysql
   sleep 30  # Allow initialization
   ```

2. **Start databases**:
   ```bash
   docker-compose up -d milvus redis neo4j opensearch
   sleep 60  # Milvus takes longer to initialize
   ```

3. **Verify database connectivity**:
   ```bash
   # Test each database
   scripts/health-checks/check-mysql.sh
   scripts/health-checks/check-milvus.sh
   scripts/health-checks/check-redis.sh
   scripts/health-checks/check-neo4j.sh
   scripts/health-checks/check-opensearch.sh
   ```

#### Health Check Scripts:
```bash
#!/bin/bash
# scripts/health-checks/check-milvus.sh
echo "Testing Milvus connection..."
curl -X GET "http://localhost:3005/health" || echo "Milvus not ready"

# scripts/health-checks/check-redis.sh
echo "Testing Redis connection..."
docker exec dopemux_redis_1 redis-cli ping || echo "Redis not ready"

# scripts/health-checks/check-neo4j.sh
echo "Testing Neo4j connection..."
curl -u neo4j:dopemux_neo4j_password http://localhost:3003/db/data/ || echo "Neo4j not ready"
```

### Task 3: Leantime Installation

**Duration**: 2-3 hours
**Dependencies**: MySQL running

#### Installation Steps:
1. **Deploy Leantime container**:
   ```bash
   docker-compose up -d leantime
   ```

2. **Configure Leantime environment**:
   ```yaml
   # docker-compose.yml leantime service
   environment:
     LEAN_DB_HOST: mysql
     LEAN_DB_USER: leantime
     LEAN_DB_PASSWORD: dopemux_db_password
     LEAN_DB_DATABASE: leantime
     LEAN_SESSION_PASSWORD: dopemux_session_secret
     LEAN_SESSION_SALT: dopemux_session_salt
   ```

3. **Initialize Leantime database**:
   ```bash
   # Wait for Leantime to initialize (may take 2-3 minutes)
   docker-compose logs -f leantime

   # Look for "Installation completed" or similar message
   ```

4. **Complete web installation**:
   - Navigate to http://localhost:3002
   - Follow setup wizard to create admin account
   - Configure basic project structure for testing

5. **Validate API access**:
   ```bash
   # Test Leantime API endpoints
   curl -X GET "http://localhost:3002/api/projects" \
     -H "Authorization: Bearer $LEANTIME_API_TOKEN"
   ```

### Task 4: Basic MetaMCP Setup

**Duration**: 2-3 hours
**Dependencies**: Core datastores running

#### MetaMCP Configuration:
1. **Create MetaMCP configuration**:
   ```yaml
   # config/metamcp/config.yaml
   servers:
     basic_health:
       command: ["echo", '{"tools": [{"name": "health", "description": "Health check"}]}']
       transport: "stdio"

   workspaces:
     default:
       allowed_servers: ["basic_health"]

   auth:
     type: "none"  # Development only

   logging:
     level: "info"
     format: "json"
   ```

2. **Deploy MetaMCP container**:
   ```bash
   docker-compose up -d metamcp
   ```

3. **Test MCP aggregation**:
   ```bash
   # Test MetaMCP health
   curl -X GET "http://localhost:3001/health"

   # Test server discovery
   curl -X GET "http://localhost:3001/servers"

   # Test tool listing
   curl -X GET "http://localhost:3001/tools"
   ```

## ✅ **Validation & Testing**

### Automated Health Check Suite

```bash
#!/bin/bash
# scripts/validate-phase1.sh

echo "🔍 Phase 1 Validation Suite"
echo "=========================="

# Service availability
services=("mysql" "milvus" "redis" "neo4j" "opensearch" "leantime" "metamcp")
for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
        exit 1
    fi
done

# Network connectivity
echo "\n🌐 Testing network connectivity..."
docker-compose exec leantime ping -c 1 mysql > /dev/null && echo "✅ leantime -> mysql"
docker-compose exec metamcp ping -c 1 milvus > /dev/null && echo "✅ metamcp -> milvus"
docker-compose exec metamcp ping -c 1 redis > /dev/null && echo "✅ metamcp -> redis"

# API endpoints
echo "\n🔌 Testing API endpoints..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002 | grep -q "200" && echo "✅ Leantime UI"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/health | grep -q "200" && echo "✅ MetaMCP API"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3005/health | grep -q "200" && echo "✅ Milvus API"

echo "\n🎉 Phase 1 validation complete!"
```

### Performance Baselines

```bash
#!/bin/bash
# scripts/measure-baseline-performance.sh

echo "📊 Measuring Phase 1 Performance Baselines"

# Database response times
echo "Database response times:"
time curl -s http://localhost:3005/health > /dev/null  # Milvus
time curl -s http://localhost:3006 > /dev/null         # Redis
time curl -s http://localhost:3003 > /dev/null         # Neo4j

# Container resource usage
echo "\nContainer resource usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Disk usage
echo "\nData directory sizes:"
du -sh data/*
```

### Manual Verification Checklist

#### Infrastructure ✅
- [ ] All Docker containers start without errors
- [ ] Docker logs show successful service initialization
- [ ] Service discovery works (containers can ping each other by name)
- [ ] External ports are accessible from host

#### Datastores ✅
- [ ] **MySQL**: Leantime can connect and create tables
- [ ] **Milvus**: Health endpoint returns 200, can create collections
- [ ] **Redis**: Can set/get keys, memory usage reasonable
- [ ] **Neo4j**: Browser accessible, can run basic Cypher queries
- [ ] **OpenSearch**: API responds, can create indices

#### Leantime ✅
- [ ] Web UI accessible at localhost:3002
- [ ] Setup wizard completes successfully
- [ ] Can create test project and tasks
- [ ] API endpoints return valid JSON responses
- [ ] Database contains expected tables and data

#### MetaMCP ✅
- [ ] Health endpoint returns service status
- [ ] Can list configured MCP servers
- [ ] Basic tool discovery works
- [ ] Logs show no connection errors to datastores

## 🚨 **Common Issues & Troubleshooting**

### Docker & Networking Issues

**Problem**: Services can't connect to each other
```bash
# Solution: Check network configuration
docker network ls | grep dopemux
docker network inspect dopemux-net

# Verify services are on correct network
docker-compose ps
```

**Problem**: Port conflicts
```bash
# Solution: Check what's using ports
lsof -i :3001-3007
netstat -tulpn | grep :300

# Update port mapping in docker-compose.yml if needed
```

### Database Initialization Issues

**Problem**: Milvus fails to start
```bash
# Solution: Check etcd and minio are running first
docker-compose logs etcd
docker-compose logs minio

# Increase startup delay
sleep 60  # before starting Milvus
```

**Problem**: MySQL connection refused
```bash
# Solution: Check MySQL initialization
docker-compose logs mysql | grep "ready for connections"

# Verify database creation
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"
```

### Leantime Issues

**Problem**: Leantime setup fails
```bash
# Solution: Check database permissions
docker-compose exec mysql mysql -u root -p -e "
  SHOW GRANTS FOR 'leantime'@'%';
  SELECT User, Host FROM mysql.user;
"

# Reset Leantime if needed
docker-compose down leantime
docker volume rm dopemux_leantime_data
docker-compose up -d leantime
```

## 📈 **Success Metrics**

### Technical Metrics
- **Startup Time**: All services up within 3 minutes
- **Memory Usage**: Total stack < 8GB RAM
- **Response Times**: All health checks < 500ms
- **Disk Usage**: Data directories < 2GB initial

### Functional Validation
- **Service Discovery**: 100% of inter-service connections work
- **API Availability**: All external endpoints return 200 OK
- **Data Persistence**: Data survives container restart
- **Network Isolation**: Services only accessible through defined ports

## 🔄 **Next Steps (Phase 2 Preparation)**

### Documentation Required for Phase 2:
1. **Service URLs**: Document all internal/external endpoints
2. **Credentials**: Secure storage of all passwords and API keys
3. **Network Topology**: Document service communication patterns
4. **Performance Baselines**: Resource usage and response times

### Phase 2 Prerequisites:
1. **All Phase 1 services stable** and passing health checks
2. **Leantime API access** validated with test data
3. **MetaMCP basic aggregation** working with simple servers
4. **Development environment** fully functional for MCP server development

---

Generated: 2025-09-24
Phase: Foundation Infrastructure (Week 1)
Status: Ready for implementation
Next: Phase 2 Integration (Doc-Context MCP + Role Workspaces)