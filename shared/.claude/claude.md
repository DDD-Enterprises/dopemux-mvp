# Shared Libraries Context

> **TL;DR**: Shared code between services. Minimize dependencies, high test coverage, stable APIs.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Purpose

Code shared across multiple services:
- Common utilities
- Shared data models
- Cross-service clients
- Base classes

---

## Guidelines

### ✅ DO
- Keep dependencies minimal
- Maintain 90%+ test coverage
- Document public APIs
- Version changes carefully

### ❌ DON'T
- Add service-specific logic
- Create circular dependencies
- Change APIs without migration path
- Add heavy dependencies

---

## Structure

```
shared/
├── config.py              # Shared configuration models
├── dependency_container.py  # Dependency injection container
├── monitoring/            # Monitoring utilities (directory)
├── monitoring.py          # Monitoring helpers
├── service_discovery.py   # Service discovery client
├── storage.py             # Shared storage abstractions
└── README.md
```

Note: `models/`, `clients/`, `utils/` subdirectories do **not** exist in the current codebase.
