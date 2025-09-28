# Repo Prompt XML Apply — Project Standard
_Last updated: 2025-09-02 UTC_

This project standardizes on **Repo Prompt's XML-based apply format** for web/chat edits. Agents must produce an **XML edits document** that Repo Prompt can apply deterministically across many files.

## Why XML apply?
- Handles **large & multi-file** changes
- **Parsable, idempotent**, previewable
- Works with Claude Code via MCP and other models

## How to use
1. Load this repo in Repo Prompt (or connect via MCP).
2. Ask the model to output **XML edits** (see skeleton below).
3. Apply in Repo Prompt's **Apply** tab (or call its MCP tool).
4. Run `pytest -q`, `ruff check .`, `mypy --ignore-missing-imports .`; update docs/ADRs; commit; PR.

## XML skeleton (generic)
```xml
<edits>
  <create path="path/to/new_file.py"><![CDATA[
# new file content here
]]></create>

  <replace path="src/module/foo.py">
    <find><![CDATA[
def old_fn():
    pass
]]></find>
    <with><![CDATA[
def old_fn() -> None:
    """Deprecated; use new_fn."""
    raise NotImplementedError("Use new_fn")
]]></with>
  </replace>

  <append path="tests/test_foo.py"><![CDATA[
def test_hello():
    assert True
]]></append>

  <delete path="obsolete/legacy.py" />
</edits>
```

### Agent rules

* Keep edits **minimal and surgical**; avoid wholesale rewrites.
* Include just enough context in <find> to match unambiguously.
* Use **CDATA** blocks for code; ensure XML is well-formed.
* After apply, update `/docs` and ADRs in the same PR.
