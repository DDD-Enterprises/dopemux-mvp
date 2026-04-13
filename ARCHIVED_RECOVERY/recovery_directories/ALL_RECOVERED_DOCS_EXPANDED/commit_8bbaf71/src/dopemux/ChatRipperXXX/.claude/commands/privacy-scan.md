# Privacy Scan Command

**Comprehensive privacy compliance validation for ChatX development**

## Purpose

Perform on-demand privacy engineering validation to ensure all code changes maintain ChatX's strict privacy standards. This command runs comprehensive checks for Policy Shield coverage, differential privacy parameters, PII leakage prevention, and cloud boundary enforcement.

## Execution Steps

1. **Deploy Privacy-Guardian Agent**
   - Launch the privacy-guardian agent with full repository access
   - Set validation mode to comprehensive (all privacy patterns)
   - Configure alert thresholds for immediate issues vs warnings

2. **Privacy Pattern Analysis**
   - Scan all Python files in `src/chatx/` for privacy-sensitive patterns
   - Validate Policy Shield threshold configurations (≥99.5% coverage)
   - Check differential privacy parameters within acceptable bounds
   - Identify potential PII leakage in logging statements

3. **Cloud Boundary Validation**
   - Search for cloud service API calls without explicit authorization
   - Verify all cloud operations require `--allow-cloud` flag validation
   - Check for attachment upload prevention in cloud integrations
   - Validate that only coarse psychology labels reach cloud services

4. **Configuration Compliance Check**
   - Validate differential privacy configuration files
   - Ensure epsilon (ε) ∈ (0,10], delta (δ) ∈ (0,0.01]
   - Check confidence thresholds for psychology analysis (τ=0.7 default)
   - Verify local LLM configuration prevents telemetry

5. **Test Coverage Validation**
   - Ensure privacy-critical modules have corresponding test files
   - Validate test cases include negative privacy boundary scenarios
   - Check for differential privacy parameter edge case testing
   - Verify Policy Shield coverage testing exists

6. **Generate Privacy Report**
   - Create comprehensive privacy compliance report
   - Document any violations with severity levels and remediation steps
   - Provide privacy engineering recommendations for improvements
   - Log findings to ConPort for persistent tracking

## Privacy Validation Rules

### Critical Issues (Must Fix)
- Policy Shield coverage below 99.5% threshold
- Differential privacy parameters outside acceptable bounds  
- PII logging without redaction mechanisms
- Cloud service usage without authorization checks
- Raw attachment upload attempts to cloud services

### Warning Issues (Should Review)
- Missing test coverage for privacy-critical components
- Hardcoded privacy thresholds without configuration
- Psychology analysis without confidence gating
- Missing provenance tracking in data transformations

### Best Practice Recommendations
- Consistent salt file usage for deterministic operations
- Comprehensive audit trail implementation
- Privacy budget tracking for differential privacy
- Coarse/fine label taxonomy adherence

## Success Criteria

✅ No critical privacy violations detected  
✅ All differential privacy parameters within bounds  
✅ Policy Shield coverage meets or exceeds thresholds  
✅ Cloud boundaries properly enforced  
✅ Privacy-critical components have test coverage  
✅ Privacy compliance report generated and logged

## Integration Points

- **Privacy-Guardian Agent**: Primary validation executor
- **ConPort**: Log findings for persistent project memory
- **context7**: Reference privacy engineering best practices
- **Quality Gates**: Integrate results into CI/CD pipeline