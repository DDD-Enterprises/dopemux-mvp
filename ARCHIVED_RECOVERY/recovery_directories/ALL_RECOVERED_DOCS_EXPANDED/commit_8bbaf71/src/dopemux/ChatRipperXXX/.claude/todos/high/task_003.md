## Task: Standardize RFC 7807 problem+json error handling
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [1]

### Description
Implement a unified error representation and mappers to RFC-7807 across CLI/services and modules.

### Implementation Details
Implementation:
- Define ProblemDetails model (pydantic) and exception types; add helpers to serialize/deserialize
- Map internal exceptions (I/O, model load, provider errors, DB) to problem+json
- Provide CLI/JSON output and optional HTTP middleware wrapper if used by API gateway
Model:
class ProblemDetails(BaseModel):
  type: AnyUrl = 'about:blank'
  title: str
  status: int
  detail: str | None = None
  instance: str | None = None
  extensions: dict[str, Any] = {}
class AppError(Exception):
  def __init__(self, title, status=500, detail=None, type='about:blank', ext=None):
    super().__init__(title)
    self.problem = ProblemDetails(title=title, status=status, detail=detail, type=type, extensions=ext or {})
# Usage: raise AppError('Model unavailable', 503, detail='Stella not loaded')
- Add decorators/utilities to wrap async entrypoints and return problem+json on failure
- Ensure errors redact secrets and large payloads
- Logging: log as structured JSON with problem fields


### Test Strategy
- Unit tests mapping representative exceptions to ProblemDetails
- Snapshot test JSON structure matches RFC-7807 (type, title, status, detail, instance)
- Ensure secrets are not leaked in problem details
- Tests for CLI mode verify pretty printed problem and JSON mode emits correct content

### Migration Notes
- Originally Task ID: 3
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [1]

### Related Files
- Original: .taskmaster/tasks/tasks.json
