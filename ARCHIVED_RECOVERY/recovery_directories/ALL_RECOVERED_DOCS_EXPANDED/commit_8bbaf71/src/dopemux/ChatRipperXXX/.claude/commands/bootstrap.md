# ChatX Development Bootstrap

**Preflight validation and context setup for ChatX privacy-focused development**

## Execution Steps

1. **Task Summary** (≤5 bullets)
   - Summarize current development task with privacy implications
   - Identify required Policy Shield coverage threshold (99.5% default, 99.9% strict)
   - Note any differential privacy parameters (ε, δ) relevant to task

2. **Hot Files Discovery**
   - Search for privacy-critical files: `src/chatx/redaction/policy_shield.py`
   - Identify psychology analysis modules: `src/chatx/psychology/`
   - Check for any local LLM configurations: `src/chatx/enrichment/`
   - Validate test coverage exists for privacy components

3. **context7 Documentation Retrieval**
   - Query context7 for relevant privacy engineering patterns
   - Fetch sections on differential privacy implementation
   - Retrieve forensic analysis best practices if applicable

4. **Memory & Context Loading**
   - **OpenMemory**: Query for ChatX privacy preferences and learned patterns
   - **ConPort**: Retrieve recent decisions on privacy thresholds, psychology analysis approaches
   - Load any active privacy compliance decisions or constraints

5. **Privacy Validation Preflight**
   - Verify no `.env` or secrets in current working directory
   - Check that any planned cloud interactions have `--allow-cloud` considerations
   - Validate differential privacy parameters if statistical queries planned
   - Ensure Policy Shield configuration aligns with task requirements

6. **TDD Plan Generation**
   - Generate privacy-aware test plan prioritizing:
     - Policy Shield coverage validation
     - Differential privacy parameter testing
     - Psychology analysis confidence thresholds
     - Local-first processing verification
   - Include negative test cases for privacy boundary violations
   - Plan integration tests for forensic workflow validation

## Privacy Engineering Reminders

- **Default**: All processing is local-only unless `--allow-cloud` explicitly specified
- **Coverage**: Policy Shield must achieve ≥99.5% coverage (≥99.9% for strict mode)
- **Differential Privacy**: Statistical queries require (ε,δ) parameter validation
- **Psychology Analysis**: Confidence gating with τ=0.7, hysteresis boundaries
- **Forensic Chain**: Maintain complete provenance tracking for all transformations

## Success Criteria

✅ Privacy context loaded and validated  
✅ Relevant hot files identified and accessible  
✅ Test strategy includes privacy boundary validation  
✅ Development plan respects ChatX architectural constraints  
✅ Ready for TDD implementation with privacy-first approach
