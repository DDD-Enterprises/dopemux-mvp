# Source Code Development Context

**Scope**: Core application code and business logic
**Inherits**: Two-Plane Architecture from project root
**Focus**: Implementation excellence with ADHD-friendly development patterns

## 🎯 Domain-Specific Guidelines

### Python Development Standards
- **Type Hints**: Mandatory for all public interfaces and complex functions
- **Pydantic Models**: Use for all data validation and serialization
- **FastAPI Patterns**: Async/await, dependency injection, structured responses
- **Error Handling**: Explicit exception types with clear error messages

### Code Organization Principles
- **Module Structure**: Clear separation between domain logic, API layer, and infrastructure
- **Dependency Injection**: Use FastAPI's dependency system for testability
- **Configuration**: Environment-based config with Pydantic settings
- **Logging**: Structured logging with correlation IDs for debugging

## 🧠 ADHD-Optimized Development

### Cognitive Load Management
- **Small Functions**: Break complex logic into focused, single-purpose functions
- **Clear Naming**: Self-documenting variable and function names
- **Progressive Implementation**: Build features incrementally with working states
- **Visual Structure**: Use consistent indentation and whitespace patterns

### Development Workflow
- **Test-First**: Write tests before implementation for complex business logic
- **Frequent Commits**: Small, focused commits with clear messages
- **Refactor Regularly**: Keep code clean and maintainable through continuous improvement
- **Document Decisions**: Use inline comments for non-obvious business logic

## 🚀 Agent Coordination

### Developer Agent (Primary)
**When Working in src/**:
- Focus on code quality and maintainability
- Ensure type safety and proper error handling
- Integrate with project-wide patterns and standards
- Log implementation decisions in ConPort

### Architect Agent (Consultation)
**For Design Decisions**:
- Review module boundaries and dependency directions
- Validate design patterns and architectural principles
- Ensure new code aligns with system architecture
- Guide refactoring efforts for better structure

### Code Quality Standards
- **Complexity**: Keep cyclomatic complexity under 10 per function
- **Documentation**: Docstrings for all public functions and classes
- **Testing**: Minimum 80% code coverage for business logic
- **Performance**: Profile critical paths and optimize for ADHD workflow efficiency

## 🔧 Technology-Specific Patterns

### FastAPI Development
```python
# Preferred pattern for route handlers
@router.post("/endpoint", response_model=ResponseModel)
async def create_resource(
    data: CreateModel,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> ResponseModel:
    """Clear, specific docstring describing the endpoint purpose."""
    try:
        # Implementation logic
        result = await service.create_resource(data, current_user.id)
        return ResponseModel.from_domain(result)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Database Patterns
```python
# Preferred SQLAlchemy pattern
class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID with clear error handling."""
        result = await self.session.get(User, user_id)
        return result
```

### Error Handling
```python
# Custom exception hierarchy
class DomainException(Exception):
    """Base exception for business logic errors."""
    pass

class ValidationError(DomainException):
    """Validation-specific errors with clear messages."""
    pass
```

## 📁 File Organization

### Module Structure
```
src/
├── dopemux/              # Main package
│   ├── api/             # FastAPI routes and handlers
│   ├── core/            # Business logic and domain models
│   ├── infrastructure/  # External service integrations
│   ├── models/          # Pydantic models and schemas
│   └── services/        # Service layer orchestration
```

### Import Conventions
- **Absolute Imports**: Use full module paths for clarity
- **Type Imports**: Use `from __future__ import annotations` for forward references
- **External Dependencies**: Group and order alphabetically
- **Internal Imports**: Keep local to reduce coupling

---

**Developer Experience**: ADHD-friendly patterns with clear structure and minimal cognitive overhead
**Code Quality**: High standards maintained through incremental improvement and clear patterns
**Integration**: Seamless coordination with project-wide Two-Plane Architecture