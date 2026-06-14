# dopeCode AST Implementation Summary

## 1. Tools Added
The foundational phase of dopeCode introduced 14 new logical endpoints distributed across `ast_engine.py`, `write_layer.py`, and `refactor_layer.py`.

### Navigation Layer
-   `get_file_symbols(path)`: Wraps `analyze_file` returning a normalized `SymbolID` list.
-   `get_ast_outline(path)`: Provides a hierarchical layout of files using Tree-Sitter.
-   `find_symbol(name)`: Proxies LSP `workspace_symbols` but ensures output uses normalized IDs.
-   `get_symbol_body(symbol_id)`: Implements boundary-safe local file reads using AST node extents.
-   `find_references(symbol_id)`: Proxies LSP `find_references` and returns structured paths/lines.
-   `find_callers(symbol_id)`: Bridges LSP `find_references`.
-   `find_callees(symbol_id)`: Stubbed for AST data flow in Phase 2.
-   `get_import_graph(path)`: Returns parsed `import` structural elements from the AST.
-   `search_pattern(query)`: Robust `rglob` regex fallback.

### Controlled Write Layer
-   `write_file(path, content)`: Protected by `_validate_boundary`.
-   `create_file(path, content)`: Protected by `_validate_boundary`.
-   `apply_patch(path, diff)`: Foundation for diff parsing; logs intent and safely halts without a dedicated diff applier (to be expanded).

### Refactor Layer
-   `rename_symbol(symbol_id, new_name, preview=True)`: Scans references and previews affected files before action.
-   `replace_symbol_body(symbol_id, new_body, preview=True)`: Prepares the targeted bounds preview.
-   `batch_apply_patch(operations, preview=True)`: Iterates patch operations deterministically.

## 2. Structure Changes
-   **Created:** `services/serena/dopecode/navigation/` and `services/serena/dopecode/transform/`.
-   **Integrated:** Added `SymbolManager`, `ASTEngine`, `WriteLayer`, and `RefactorLayer`.
-   **Hooked:** Initialized new layers within `mcp_server.py` `initialize()` phase to prevent breaking the monolith structure while establishing clear delegation paths.

## 3. Preserved Features
-   **Complexity Analysis:** The ADHD `analyze_complexity` tool and dynamic result limits remain intact and fully functional for existing tools.
-   **LSP Bypass Logic:** `should_use_lsp` optimizations are preserved.
-   **Workspace Boundaries:** `DOPEMUX_WORKSPACE_ROOT` detection persists.
-   **Orchestration Hooks:** All new tools are designed to be registered via standard `mcp.server.Server()` `@call_tool` decorators.