# Dopemux Platform Features

Feature specifications for dopemux platform development.

**Scope:** dopemux platform only (NOT copied to external projects)

## Active Features

| ID | Feature | Status | ADHD-Critical |
|----|---------|--------|---------------|
| F001 | Untracked Work Detection | In Development | Yes |
| F002 | Multi-Session Support | In Development | Yes |

## Naming Convention

- Format: `F###-descriptive-name.md`
- Sequential: F001, F002, F003, ...
- Never reuse numbers

## Frontmatter Template

```yaml
---
feature_id: F###
title: Feature Name
status: in_development | production | deprecated
adhd_critical: true | false
version: 1.0
created: YYYY-MM-DD
owner: name
tags: [tag1, tag2]
---
```

## See Also

- [Architecture Decisions](../90-adr/) - Major architectural choices
- [RFCs](../91-rfc/) - Proposals under discussion
