# ConPort-KG 2.0: Multi-Tenant Knowledge Graph

**Secure, multi-agent memory hub for the Dopemux ecosystem**

![Status](https://img.shields.io/badge/status-alpha-yellow)
![Security](https://img.shields.io/badge/security-7%2F10-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)

---

## Overview

ConPort-KG 2.0 transforms the single-user knowledge graph into a **production-ready, multi-tenant, multi-agent memory system** serving as the intelligence coordination layer for all Dopemux agents.

**Current Implementation**: Phase 1 Week 1 Complete (Decision #220)
- ✅ JWT authentication (RS256 with refresh tokens)
- ✅ Secure password management (Argon2id + bcrypt hybrid)
- ✅ User data models and database schema
- ✅ User service with CRUD operations
- ✅ PostgreSQL RLS policies (in progress - Days 6-8)
- ✅ RBAC middleware (in progress - Days 6-8)

---

## Vision

> **"Every AI agent in Dopemux shares a unified memory through ConPort-KG, enabling collaborative intelligence while maintaining workspace isolation and ADHD-optimized progressive disclosure."**

---

## Quick Start

### Authentication

\`\`\`python
from auth.service import UserService
from auth.models import UserCreate
from auth.database import get_db

service = UserService()

# Register new user
async with get_db() as db:
    user = await service.create_user(
        db,
        UserCreate(
            email="user@example.com",
            username="username",
            password="SecurePass123!@#"
        )
    )

# Authenticate
async with get_db() as db:
    result = await service.authenticate_user(
        db,
        email="user@example.com",
        password="SecurePass123!@#"
    )
\`\`\`

### Workspace Management

\`\`\`python
# Add user to workspace
async with get_db() as db:
    await service.add_user_to_workspace(
        db,
        user_id=1,
        workspace_id="workspace-uuid",
        role="member"  # owner, admin, member, viewer
    )
\`\`\`

---

## Documentation

- [Master Plan](../../docs/94-architecture/CONPORT_KG_2.0_MASTER_PLAN.md) - Complete system design
- [Phase 1 Week 1 Plan](PHASE_1_WEEK_1_PLAN.md) - Day-by-day implementation guide
- [Roadmap](ROADMAP.md) - Full 11-week timeline

---

## Status Summary

**Phase 1 Week 1**: ✅ Complete (5/5 days)
**Phase 1 Week 2**: 🚧 In Progress (Days 6-8)
**Security Score**: 7/10 (target: 9/10)
**Production Ready**: No (estimated: 8 weeks)
**Total Code**: 11,381 lines (auth system)

**Next Milestone**: PostgreSQL RLS + RBAC (3 days)
