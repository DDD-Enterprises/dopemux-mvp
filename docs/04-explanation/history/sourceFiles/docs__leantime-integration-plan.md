# Leantime Integration & Dopemux Installer Plan

## Overview
Integration plan for self-hosted Leantime project management with Dopemux ADHD-optimized development platform.

## Leantime Docker Strategy

### Why Leantime?
- **ADHD-First Design**: Built specifically for ADHD, Autism, and Dyslexia
- **Goals-Focused**: Reduces cognitive overwhelm with clear task hierarchy
- **Clean Interface**: Non-overwhelming UI with fast page loads
- **Self-Hosted**: Full control over data and customization

### Docker Installation Approach
```bash
# Official Docker Compose setup
git clone https://github.com/Leantime/docker-leantime.git
cd docker-leantime
cp sample.env .env
docker compose up -d
```

#### Key Components
- **Image**: `leantime/leantime:latest`
- **Database**: MySQL 8.4 container
- **Volumes**: Persistent storage for user files, plugins, logs
- **Network**: Isolated Docker network for security

#### Critical Environment Variables
```env
LEAN_DB_HOST=mysql_leantime
LEAN_DB_USER=lean
LEAN_DB_PASSWORD=<secure_password>
LEAN_DB_DATABASE=leantime
LEAN_SESSION_PASSWORD=<secure_session_key>
LEAN_APP_URL=https://your-dopemux-domain.com
PUID=1000  # User permissions
PGID=1000  # Group permissions
```

## Dopemux Installer Architecture

### Core Components

#### 1. Pre-flight Checker
- Verify Docker and Docker Compose installation
- Check system requirements (RAM, disk space)
- Validate network connectivity
- Ensure required ports are available

#### 2. Service Orchestrator
- Pull and manage Docker images
- Generate docker-compose configurations
- Handle service dependencies and startup order
- Monitor service health and status

#### 3. Configuration Manager
- Generate secure passwords and session keys
- Manage environment variable templates
- Handle SSL certificate generation/management
- Configure reverse proxy settings

#### 4. Integration Bridge
- API connectors between Dopemux and Leantime
- Authentication synchronization
- Context sharing for ADHD workflows
- Session persistence coordination

### Installation Flow

```bash
dopemux install leantime
```

**Step-by-step process:**
1. **System Check**
   - Docker availability
   - Port conflicts (80, 443, 3306)
   - Disk space requirements
   - Network connectivity

2. **Configuration Generation**
   - Secure password generation
   - SSL certificate setup
   - Environment file creation
   - Domain/subdomain configuration

3. **Service Deployment**
   - Pull Docker images
   - Create docker-compose.yml
   - Initialize database schema
   - Start services with health checks

4. **Integration Setup**
   - Configure reverse proxy
   - Set up authentication bridge
   - Initialize Dopemux-Leantime API connections
   - Verify end-to-end functionality

5. **Post-Install Verification**
   - Service health checks
   - Database connectivity
   - Web interface accessibility
   - Integration points functional

### Integration Points

#### Authentication Sync
- Single sign-on between Dopemux and Leantime
- User role mapping and permissions
- Session management across platforms

#### ADHD Context Sharing
- Project context preservation
- Task state synchronization
- Attention metrics coordination
- Focus session integration

#### Notification Coordination
- Unified notification system
- Attention-aware alerting
- Context-switch notifications
- Progress celebrations

#### Data Integration
- Project metadata sharing
- Time tracking coordination
- Progress metrics aggregation
- Context preservation across interruptions

## Implementation Phases

### Phase 1: Basic Installation
- Docker-based Leantime deployment
- Basic configuration management
- Simple installer script

### Phase 2: Integration Bridge
- Authentication synchronization
- Basic API connectivity
- Session sharing

### Phase 3: ADHD Optimization
- Context preservation
- Attention metrics integration
- Focus session coordination

### Phase 4: Advanced Features
- Custom ADHD workflows
- Enhanced notification system
- Advanced analytics and insights

## Technical Considerations

### Security
- Docker secrets for sensitive data
- Network isolation and firewalls
- SSL/TLS encryption
- Regular security updates

### Performance
- Resource allocation and limits
- Database optimization
- Caching strategies
- Load balancing for scale

### Maintenance
- Automated backup strategies
- Update management
- Health monitoring
- Log aggregation

### ADHD Accommodations
- Installation progress visualization
- Clear error messages with recovery steps
- One-command deployment
- Automatic rollback on failures

## File Structure
```
dopemux/
├── installers/
│   ├── leantime/
│   │   ├── docker-compose.yml.template
│   │   ├── install.py
│   │   ├── config.py
│   │   └── health_check.py
│   └── common/
│       ├── preflight.py
│       ├── ssl_manager.py
│       └── proxy_config.py
└── integrations/
    └── leantime/
        ├── auth_bridge.py
        ├── api_client.py
        └── context_sync.py
```

## Next Steps

1. **Proof of Concept**: Basic Docker Compose setup
2. **Installer Script**: Python-based installation automation
3. **Integration Testing**: API connectivity and auth sync
4. **ADHD Feature Integration**: Context sharing and attention metrics
5. **Production Hardening**: Security, monitoring, and maintenance

---

**Status**: Planning Phase
**Priority**: High - Core infrastructure for ADHD-optimized project management
**Dependencies**: Docker, SSL certificates, domain configuration