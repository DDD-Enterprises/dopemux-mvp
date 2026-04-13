## Task: Enhance Semantic Content Detection for Psychology Module
- **ID**: 20250906-185622
- **Priority**: Low
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [18]

### Description
Improve psychology content detection by moving beyond simple keyword matching to more robust semantic analysis.

### Implementation Details
Integrate a lightweight NLP library (e.g., spaCy >=3.7, or HuggingFace Transformers for small models) to perform semantic similarity or intent classification. Refactor src/chatx/embeddings/psychology.py to use vector-based or transformer-based detection. Tune model for performance and accuracy. Document new detection logic.

### Test Strategy
Create a labeled dataset for psychology content. Write tests to measure precision, recall, and F1 score of new detection logic. Benchmark performance impact and optimize as needed.

### Migration Notes
- Originally Task ID: 19
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: low
- Status mapping: pending
- Dependencies: [18]

### Related Files
- Original: .taskmaster/tasks/tasks.json
