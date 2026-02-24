# Heuristics Library v1

This file contains the heuristics that should be used for prompt rewriting.
The actual content should be pasted here as provided in the original instructions.

## Discovery Heuristics

### Step 1: Input Analysis
- Analyze input structure and content types
- Identify stable content keys for deterministic IDs
- Validate input completeness against schema requirements

### Step 2: Evidence Collection
- Extract facts only from in-scope inputs
- Attach evidence provenance to every extracted fact
- Handle missing data with UNKNOWN markers

### Step 3: Transformation Rules
- Apply domain-specific transformation logic
- Normalize data formats consistently
- Validate output schema compliance

## Failure Mode Patterns

### Common Failure Patterns
- Missing required input fields
- Invalid data formats
- Schema validation failures
- Evidence provenance gaps

### Recovery Strategies
- Emit UNKNOWN for unsatisfied values
- Provide detailed error context
- Maintain deterministic behavior

## Domain-Specific Guidelines

### For each prompt domain:
- Include 4-8 step-specific discovery steps
- Add 1-2 domain-specific failure mode bullets
- Ensure Legacy Context is treated as intent guidance only

Note: This is a placeholder. Replace with the actual heuristics content provided in the original instructions.