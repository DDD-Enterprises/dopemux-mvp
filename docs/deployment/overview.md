---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Deployment Documentation

Production and staging deployment guides for Dopemux.

## Quick Links

- **[Production Deployment](DEPLOYMENT-INSTRUCTIONS.md)** - Step-by-step production setup
- **[Deployment Checklist](DEPLOYMENT-CHECKLIST.md)** - Pre-deployment verification
- **[Worktree Deployment](DEPLOYMENT-WORKTREE-INSTRUCTIONS.md)** - Git worktree deployment

---

## Deployment Guides

### Production Deployment
**File:** [DEPLOYMENT-INSTRUCTIONS.md](DEPLOYMENT-INSTRUCTIONS.md)

Complete guide for deploying Dopemux to production:
- Environment setup
- Service configuration
- Database initialization
- MCP server deployment
- Verification steps

### Deployment Checklist
**File:** [DEPLOYMENT-CHECKLIST.md](DEPLOYMENT-CHECKLIST.md)

Pre-flight checklist covering:
- Security fixes verification
- Environment configuration
- Database setup
- Service health checks
- Post-deployment validation

### Worktree Deployment
**File:** [DEPLOYMENT-WORKTREE-INSTRUCTIONS.md](DEPLOYMENT-WORKTREE-INSTRUCTIONS.md)

Deploy using git worktrees:
- Worktree setup
- Branch management
- Deployment workflow
- Rollback procedures

---

## Deployment Strategies

### Standard Deployment
Best for: Production environments, stable releases
- Use tagged releases
- Full integration tests
- Gradual rollout

### Worktree Deployment
Best for: Multi-environment setups, parallel deployments
- Isolated environments
- Quick environment switching
- Testing branches in isolation

---

## Environment Requirements

### Minimum Requirements
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+
- Python 3.11+
- Node.js 18+ (for MCP servers)

### Recommended Resources
- 4GB RAM minimum
- 2 CPU cores
- 20GB disk space
- Ubuntu 22.04 LTS or similar

---

## Related Documentation

- **[Architecture Overview](../04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)** - Understand the system
- **[How-To Guides](../02-how-to/)** - Operational guides
- **[System Configuration](../03-reference/configuration/)** - Config reference

---

## Deployment Support

### Pre-Deployment
1. Review deployment checklist
2. Verify all dependencies
3. Run integration tests
4. Backup existing data

### During Deployment
1. Follow guide step-by-step
2. Verify each stage
3. Monitor service health
4. Document any issues

### Post-Deployment
1. Run verification tests
2. Monitor for 24 hours
3. Update documentation
4. Communicate to team

---

## Troubleshooting

### Common Issues

**Services won't start**
- Check Docker logs: `docker-compose logs`
- Verify environment variables
- Check port conflicts

**Database connection fails**
- Verify PostgreSQL is running
- Check connection string
- Verify credentials

**MCP servers not responding**
- Check Node.js version
- Verify MCP server configs
- Check network connectivity

### Getting Help

1. Check deployment logs
2. Review [How-To Guides](../02-how-to/)
3. Consult [Architecture Docs](../04-explanation/)
4. Check [Issues](https://github.com/your-repo/issues)

---

**Maintained by:** DevOps Team
**Last Updated:** 2025-10-29
