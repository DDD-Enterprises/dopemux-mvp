# RULES.md

This document defines the rules of engagement for the dopemux-mvp repository.

These rules are not suggestions. They are constraints on how you reason, how you act, and how you validate truth.

---

## 1. Truth Hierarchy

When sources conflict, the hierarchy of truth is:

1. **Runtime code, config, and tests** (The ultimate reality)
2. **Standard workspace truth artifacts** (`TRUTH_*.md`)
3. **Canonical documentation** (`RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`)
4. **Historical or exploratory docs** (Treat as "hallucinated until proven")

---

## 2. Evidence-Based Reasoning

- Do not claim success without artifact citation.
- Do not assume a system is implemented just because it is described.
- Distinguish between **Canonical Authority** (who owns the data) and **Derived Surfaces** (who shows the data).
- Explicitly handle `UNKNOWN`. If you don't know, say so. Do not fabricate.

---

## 3. Boundary Discipline

- Respect system boundaries as defined in `ARCHITECTURE.md` and `SYSTEM_BOUNDARIES.md`.
- Do not collapse multiple systems into one based on naming similarities.
- Trace every action through the actual delegation path (e.g., `dopemux` -> `scripts/dopetask`).
- Identify the canonical writer before performing any write.

---

## 4. Operational Safety

- Never execute extraction runner scripts unless specifically instructed.
- Do not modify files outside the narrow scope of your task.
- For bug fixes, always reproduce the failure empirically first.
- Validation is the only path to finality.

---

## 5. Drift Handling

- Acknowledge and document drift instead of trying to "clean it up" narratively.
- If the runtime diverges from the docs, document the divergence.
- Treat deprecated or shadow paths as risks, not as shortcuts.
