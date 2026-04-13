TDD implementation loop with Context7 documentation-driven code generation. Automatically queries Context7 for relevant library APIs and code examples before writing code.

Steps:
1. **Pre-Implementation Research**: Auto-query Context7 for libraries/APIs used in implementation
2. **Code Examples Integration**: Pull official examples and patterns from Context7
3. **TDD Test Writing**: Generate unit + integration + edge case tests using Context7-informed patterns
4. **Implementation**: Write code with up-to-date API documentation and examples in context
5. **Validation**: Cross-reference implementation against Context7 official documentation
6. **Minimal Diffs**: Use Serena for precise, surgical edits
7. **Progress Logging**: Track implementation steps and decisions in ConPort
8. **Quality Gates**: Run /complete workflow for lint/type/test/coverage validation

Expected output: Production-ready implementation with accurate library usage, comprehensive test coverage, and documentation cross-references.
