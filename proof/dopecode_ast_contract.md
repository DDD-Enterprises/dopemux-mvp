# dopeCode AST and Transformation Contract

## 1. Architectural Boundaries
The dopeCode system divides code intelligence into four logical layers:
1.  **Navigation (`dopecode/navigation`):** Provides precise, deterministic AST-based and LSP-backed queries. Outputs normalized `SymbolID` references.
2.  **Analysis (`services/serena/adhd_features`):** Existing ADHD features (complexity scoring, focus filtering) that wrap navigation results.
3.  **Transform (`dopecode/transform`):** Controlled mutation layer strictly bounded by the workspace root.
4.  **Orchestration (`mcp_server.py`):** The MCP gateway that registers tools and handles the event loop.

## 2. Symbol Model
To ensure deterministic, reconstructible identity across sessions, dopeCode uses a stable `SymbolID`.

**Format:**
`<workspace_id>::<file_path>::<symbol_name>::<line>`

**Example:**
`default_workspace::src/auth/login.py::LoginHandler::42`

**Properties:**
-   **Stable:** Easily parsed and logged.
-   **Reconstructible:** Human-readable and grep-friendly for manual verification.
-   **Deterministic:** Always represents the same structural element at a given state.

## 3. Write Model (Controlled Transformation)
The `WriteLayer` introduces safe mutation primitives to the previously read-only Serena fork.

**Rules:**
-   **Workspace Bounded:** Every write operation is intercepted by `_validate_boundary()`. Any path traversal (`../`) attempting to escape `DOPEMUX_WORKSPACE_ROOT` raises a `ValueError`.
-   **No Shell Execution:** File operations use native Python `pathlib` writing. No shell scripts or `sed`/`awk` processes are used for modifications.
-   **Audit Logging:** Every write emits a mandatory JSON log event:
    ```json
    {
      "type": "dopecode_write",
      "workspace_id": "...",
      "operation": "apply_patch",
      "files": ["..."],
      "ts": "..."
    }
    ```

## 4. Tool Families
### A. AST / Symbol Navigation
-   `get_file_symbols(path)`: Uses Tree-sitter for AST analysis.
-   `get_ast_outline(path)`: Provides hierarchical file structure.
-   `find_symbol(name)`: Wraps LSP `workspace_symbols` with normalization.
-   `get_symbol_body(symbol_id)`: Extracts symbol source code using AST.
-   `find_references(symbol_id)`: Delegates to LSP for cross-file references.
-   `find_callers(symbol_id)`: Delegates to LSP `find_references` as a fallback.
-   `find_callees(symbol_id)`: Stubbed, requires Phase 2 AST data flow analysis.
-   `get_import_graph(path)`: Parses imports using Tree-sitter.
-   `search_pattern(query)`: Workspace-wide regex search fallback.

### B. Controlled Write Layer
-   `write_file(path, content)`: Full overwrite, workspace-bounded.
-   `create_file(path, content)`: Creates new file, workspace-bounded.
-   `apply_patch(path, diff_text)`: Logs intent, actual application deferred to Phase 2.

### C. Symbol Refactor (Phase 1)
-   `rename_symbol(symbol_id, new_name, preview=True)`: Lists affected files, requires `preview=True`.
-   `replace_symbol_body(symbol_id, new_body, preview=True)`: Lists affected files, requires `preview=True`.
-   `batch_apply_patch(operations, preview=True)`: Manages deterministic multi-file operations, requires `preview=True`.

---
## 5. Validation Goals
-   AST tools return correct symbols and outlines.
-   Reference/call graph tracing works on a sample repo.
-   ADHD features remain intact.
-   Writes are strictly blocked outside workspace.
-   Batch operations are deterministic.
-   Refactor preview mode functions correctly.
-   Logging is generated for all mutations.
