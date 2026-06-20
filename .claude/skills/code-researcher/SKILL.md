---
name: code-researcher
description: Produce evidence-backed workflow research before any plan or implementation work begins.
---

# Code Researcher

Use this skill for the `research` phase.

## Contract

- Read the live codebase first; do not speculate when the repo can answer the question.
- Capture references, relevant files, risks, and open questions.
- Propose exact verification commands that the later implementation can run.
- Do not write a plan or code in this phase.

## Required Output

- `research.md`
- Evidence summary with file references
- Risk list
- Candidate verification commands

## Completion Rule

Emit:

```xml
<workflow-checkpoint phase="research" status="complete" task="task-001" summary="Research captured" artifact="/abs/path/research.md" verification="pytest -q;;ruff check src" />
```
