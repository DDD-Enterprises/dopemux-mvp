# Upstream Serena vs Dopemux Serena: Decision-Grade Contract Diff

## 1. Executive Summary
**Verdict:** `OWN THE FORK` (Intentional Divergence)

Dopemux Serena is no longer a standard Serena instance; it is a **hardened, read-only intelligence service** optimized for ADHD developers and large workspace performance. The divergences in the Editing, Project, and ADHD families are fundamental to the Dopemux product mission.

## 2. Core Family Divergences (Decision Drivers)

### A. Editing & Write Family
- **Upstream:** First-class write capability (`CreateTextFile`, `ReplaceContent`). Designed as an active refactoring agent.
- **Local:** **Strictly Read-Only**. Hardened at the `call_tool` level.
- **Rationale:** `intentional_hardening`. Dopemux treats Serena as an "Oracle" for code understanding, not a direct writer.

### B. Project & State Family
- **Upstream:** Stateful multi-project management (`ActivateProject`). Supports multiple registered roots.
- **Local:** **Stateless / Workspace-Root Scoped**. Detection anchored to `.git` or `DOPEMUX_WORKSPACE_ROOT`.
- **Rationale:** `intentional_product_decision`. Overfits for reliable workspace resolution in containerized/orchestrated environments.

### C. Refactoring Family
- **Upstream:** **Symbolic Edits** (`ReplaceSymbolBody`, `RenameSymbol`). Performs structural code modification.
- **Local:** **Analysis-Only**. Provides suggestions (`suggest_refactor`) but never executes them.
- **Rationale:** `intentional_hardening`. Preserves "Operator-in-the-Loop" for all codebase mutations.

### D. ADHD & Extension Family (Local Only)
- **Local Only:** `analyze_complexity`, `filter_by_focus`, `get_navigation_patterns`, `detect_untracked_work`.
- **Value:** This family represents 60%+ of the local tool surface and 100% of the unique Dopemux value prop.
- **Rationale:** `local_only_extension`. This is the reason the fork exists.

## 3. Top 3 Highest-Risk Divergences
1. **Architectural Drift (High):** Local is a 5.5k line monolithic file; upstream is modular. Maintenance of the local monolith is high-cost but necessary to preserve the integrated ADHD features.
2. **Retrieval Duality (Medium):** Upstream has a built-in memory system. Dopemux uses an external `SerenaAdapter`. This risks "double-indexing" or inconsistent project memory.
3. **LSP Reliance (Low):** Both use `pylsp`, but local has a custom "Bypass" threshold (5k files) that upstream lacks.

## 4. Final Disposition
The local implementation should be formalized as **Dopemux Serena (Fork)**. 
- **Preserve:** Read-only hardening, ADHD extensions, and workspace-root scoping.
- **Abandon:** Upstream editing, memory tools, and multi-project state.
- **Backport Only:** Security fixes and core LSP optimization from `serena.util`.
