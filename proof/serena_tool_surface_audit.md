# Serena Tool Surface Contract Audit

## 1. Executive Summary
This audit confirms that the **"Own the Fork"** decision is reflected in a completely divergent tool surface. Upstream Serena is primarily a **Code Modifier**, whereas Dopemux Serena has been refactored into a **Cognitive Oracle**. 

## 2. Tool Family Breakdown

### 1. File Read / Navigation
#### Upstream
- capabilities: Line-range reads, recursive listing, ignored file filtering.
- representative tools: `ReadFileTool`, `ListDirTool`, `FindFileTool`.
#### Local
- capabilities: Similar to upstream but adds `find_similar_code` and `predict_navigation_from_git`.
- representative tools: `read_file`, `list_dir`, `find_similar_code`.
#### Differences
- added: `predict_navigation_from_git` (Local).
#### Classification: `intentional_product_decision`
#### Impact: Local enhances discovery but remains strictly anchored to the workspace root.
#### Recommendation: **KEEP**

### 2. File Write / Editing (HIGH PRIORITY)
#### Upstream
- capabilities: Create, overwrite, delete lines, regex replace, at-line insertion.
- representative tools: `CreateTextFileTool`, `ReplaceContentTool`, `DeleteLinesTool`.
#### Local
- capabilities: **NONE**. All write tools removed or disabled.
- representative tools: None.
#### Differences
- removed: Entire suite of upstream editing tools.
#### Classification: `intentional_hardening`
#### Impact: Local is 100% read-safe; Upstream is destructive without external gates.
#### Recommendation: **RESTORE (Option B subset)**. See Final Decision for safe reintroduction.

### 3. Symbolic Refactoring
#### Upstream
- capabilities: `rename_symbol`, `replace_symbol_body`, `safe_delete_symbol`.
- representative tools: `RenameSymbolTool`, `ReplaceSymbolBodyTool`.
#### Local
- capabilities: **NONE**.
- representative tools: None.
#### Differences
- removed: All structural edit tools.
#### Classification: `intentional_hardening`
#### Impact: Dopemux requires the operator to perform structural changes manually.
#### Recommendation: **IGNORE**. Keep local read-only for structural changes.

### 4. Project / Workspace Management
#### Upstream
- capabilities: Multi-project state, explicit activation/deactivation.
- representative tools: `ActivateProjectTool`, `ListQueryableProjectsTool`.
#### Local
- capabilities: Single workspace resolution (`.git` discovery).
- representative tools: `get_workspace_status`.
#### Differences
- removed: All multi-project activation logic.
#### Classification: `intentional_product_decision`
#### Impact: Local is more reliable for automated container flows; Upstream is better for interactive multi-repo work.
#### Recommendation: **KEEP** (Local model is correct for Dopemux orchestration).

### 5. Memory / Retrieval
#### Upstream
- capabilities: Integrated CRUD for project-scoped embeddings.
- representative tools: `ReadMemoryTool`, `WriteMemoryTool`, `ListMemoriesTool`.
#### Local
- capabilities: **NONE** (in MCP). Delegated to `SerenaAdapter`.
- representative tools: None.
#### Differences
- removed: All integrated memory tools.
#### Classification: `integration_shim`
#### Impact: Potential retrieval duplication between Serena and internal Dopemux memory systems.
#### Recommendation: **IGNORE**. Keep Serena memory-agnostic and use Dopemux's native Retrieval Plane.

### 6. Code Intelligence / Analysis
#### Upstream
- capabilities: LSP-based symbol lookup and referencing.
- representative tools: `FindSymbolTool`, `FindReferencingSymbolsTool`.
#### Local
- capabilities: Standard LSP + **Advanced Complexity Analysis**.
- representative tools: `analyze_complexity`, `get_unified_complexity`.
#### Differences
- added: Custom complexity scoring not found in upstream.
#### Classification: `local_only_extension`
#### Impact: Local provides much higher "Cognitive Signal" than upstream.
#### Recommendation: **KEEP**

### 7. Local Extensions (ADHD Tools)
#### Upstream
- capabilities: None.
#### Local
- capabilities: 20+ tools for focus tracking, untracked work detection, and abandonment tracking.
- representative tools: `filter_by_focus`, `detect_untracked_work`, `mark_abandoned`.
#### Differences
- added: The entire core of the Dopemux "Serena" value prop.
#### Classification: `local_only_extension`
#### Impact: These tools define the Dopemux identity.
#### Recommendation: **KEEP**. This system is coherent and should be defended.

## 3. Top 3 Critical Capability Gaps
1. **Unintentional Loss of `SearchForPatternTool`:** Upstream has a robust pattern search; local relies on standard grep calls within tools. Reintroducing a dedicated `search_code` tool would improve discovery.
2. **Missing `CreateTextFile` (Option B):** The absolute absence of file creation blocks many simple operator tasks (e.g., creating a new test file).
3. **Symbolic Read Parity:** Upstream has `GetSymbolsOverviewTool` (compact file summary). Local's `get_context` is more verbose and potentially noisier.

## 4. Final Decision

### Write Strategy Recommendation (Option B Subset)
We should reintroduce a **Safe Write Subset** consisting of only:
1. `create_file`: Restricted to the workspace root; fails if file exists.
2. `write_test_file`: Explicitly scoped to `tests/` directory only.
3. **NO** `replace_content` or `rename_symbol` (Keep these as suggestions).

### Tool Surface Direction
**PRUNING NEEDED**: The ADHD toolset is loosely accumulated. We should group `metric` and `pattern` tools into a unified `intelligence` toolset to reduce registry noise.

### Fork Integrity
**INTACT**: The fork is deep, evidenced, and structurally sound. 🛡️
