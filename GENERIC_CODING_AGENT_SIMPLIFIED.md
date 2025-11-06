# Dopemux Generic Coding Agent - Simplified Single-Candidate Implementation

**Document ID**: IP-005-GENERIC-AGENT-SIMPLE
**Version**: 1.0
**Date**: 2025-11-05
**Status**: READY FOR IMPLEMENTATION
**Classification**: IMPLEMENTATION / MVP

---

## Overview

**Generic Coding Agent**: A single-candidate iterative code repair system that proposes, tests, and refines patches one at a time. No evolutionary populations or genetic algorithms - just intelligent, bounded iteration toward a working solution.

**Key Differences from Genetic Version**:
- ✅ Single candidate per iteration (not population)
- ✅ Simple state machine (no generations/selections)
- ✅ Bounded attempts (configurable max, e.g., 5-10)
- ✅ Direct patch refinement based on failure signals
- ✅ Same MCP integrations (Serena, dope-context, ConPort, CLI)

---

## 1. Simplified State Machine

```
Idle → Propose (PatchGenerator.propose)
    → DryRun (Serena.dry_run_apply)
    → Verify (Serena.verify_apply + CLI checks)
    → Test (CLI.run_tests)
    → {
         Pass → Apply (Serena.commit_with_limits) → Done
         Fail → Analyze (extract failure signals)
               → Refine (PatchGenerator.refine) → [loop with bounded attempts]
      }
```

**Termination Conditions**:
- ✅ Success: All tests pass + static checks pass
- ❌ Max attempts reached
- ❌ Timeout exceeded
- ❌ No progress (same fitness N attempts)

---

## 2. Core Interfaces (Simplified)

### Controller Interface
```typescript
interface GenericController {
  // State
  currentAttempt: number;
  maxAttempts: number;
  solution: Patch | null;
  isComplete: boolean;

  // Core loop
  runOnce(): AttemptResult;  // Single propose→test→analyze cycle
  iterate(maxAttempts?: number): Patch | null;  // Full bounded iteration

  // Integration
  patchGenerator: PatchGenerator;
  fitnessEvaluator: FitnessEvaluator;
  memory: MemoryAdapter;

  // Logging
  logAttempt(attempt: AttemptResult): void;
  logDecision(summary: string, rationale: string): void;
}
```

### PatchGenerator Interface (renamed from Mutator)
```typescript
interface PatchGenerator {
  // Core generation
  propose(issue: IssueContext, context: CodeContext): Patch;

  // Refinement based on failures
  refine(previousPatch: Patch, failureSignals: FailureSignals): Patch;

  // Context gathering
  gatherContext(issue: IssueContext): CodeContext;
}
```

### FitnessEvaluator Interface (unchanged)
```typescript
interface FitnessEvaluator {
  evaluate(patch: Patch): FitnessResult;
  isAcceptable(result: FitnessResult): boolean;
  getFailureSignals(result: FitnessResult): FailureSignals;
}
```

### MemoryAdapter Interface (unchanged)
```typescript
interface MemoryAdapter {
  putAttempt(key: string, attempt: AttemptResult): void;
  recallSimilarIssues(query: string): AttemptResult[];
  getRecentFailures(): FailureSignals[];
}
```

---

## 3. CLI Command Structure

```bash
# Main commands
dmx fix plan <issue-description>  # Analyze and plan fix approach
dmx fix try <issue-description>   # Run single attempt
dmx fix apply <patch-id>         # Apply approved patch
dmx fix pr <patch-id>           # Create PR with patch

# Status and monitoring
dmx fix status                   # Show current attempt progress
dmx fix history                  # Show recent attempts
dmx fix abort                    # Stop current run

# Configuration
dmx fix config                   # Show/edit agent settings
```

### CLI Flags
```bash
--max-attempts=N     # Default: 5
--timeout=M          # Default: 300s
--auto-apply         # Auto-apply if tests pass
--dry-run           # Test without committing
--interactive       # Prompt for each step
```

---

## 4. Implementation Architecture

### Core Components

**Controller (GenericAgent.ts)**
```typescript
class GenericController {
  private attemptCount = 0;
  private readonly maxAttempts = 5;

  async iterate(issue: IssueContext): Promise<Patch | null> {
    const context = await this.patchGenerator.gatherContext(issue);

    while (this.attemptCount < this.maxAttempts) {
      this.attemptCount++;

      const patch = this.attemptCount === 1
        ? await this.patchGenerator.propose(issue, context)
        : await this.patchGenerator.refine(this.lastPatch, this.lastFailureSignals);

      const result = await this.runAttempt(patch);

      await this.memory.putAttempt(`attempt_${this.attemptCount}`, result);
      await this.logAttempt(result);

      if (this.fitnessEvaluator.isAcceptable(result.fitness)) {
        return patch;
      }

      this.lastPatch = patch;
      this.lastFailureSignals = this.fitnessEvaluator.getFailureSignals(result.fitness);
    }

    return null; // No solution found
  }

  private async runAttempt(patch: Patch): Promise<AttemptResult> {
    // Dry run → Verify → Test sequence
    const dryResult = await mcp_serena.dry_run_apply(patch);
    if (!dryResult.applied) return { success: false, reason: 'dry_run_failed' };

    const verifyResult = await mcp_serena.verify_apply(['syntax', 'lint']);
    const testResult = await mcp_cli.run_tests();

    const fitness = await this.fitnessEvaluator.evaluate(patch);

    return {
      patch,
      dryRun: dryResult,
      verify: verifyResult,
      tests: testResult,
      fitness,
      attemptNumber: this.attemptCount
    };
  }
}
```

**PatchGenerator (SimplePatchGenerator.ts)**
```typescript
class SimplePatchGenerator {
  async propose(issue: IssueContext, context: CodeContext): Promise<Patch> {
    // Gather relevant code snippets
    const symbols = await mcp_dope_context.retrieve_symbols(issue.functionName);
    const snippets = await mcp_dope_context.file_snippets(
      context.filePath,
      context.startLine - 5,
      context.endLine + 5
    );

    // Call Serena to propose patch
    return await mcp_serena.propose_patch({
      file_path: context.filePath,
      region: issue.functionName,
      issue_description: issue.description,
      constraints: context.constraints
    });
  }

  async refine(previousPatch: Patch, signals: FailureSignals): Promise<Patch> {
    const enhancedIssue = `${previousPatch.summary}\n\nFailure signals: ${signals.join(', ')}`;

    return await mcp_serena.propose_patch({
      file_path: previousPatch.filePath,
      region: previousPatch.region,
      issue_description: enhancedIssue,
      constraints: ['address previous failures']
    });
  }
}
```

---

## 5. Configuration & Limits

### Default Settings
```json
{
  "maxAttempts": 5,
  "timeoutSeconds": 300,
  "autoApply": false,
  "commitLimits": {
    "maxLines": 50,
    "maxTokens": 8000
  },
  "fitnessWeights": {
    "testsWeight": 1.0,
    "lintPenalty": 0.1,
    "typePenalty": 1.0,
    "sizePenalty": 0.01
  }
}
```

### Safety Guards
- **Max attempts**: Hard limit prevents infinite loops
- **Timeout**: Per-attempt and total time limits
- **Commit limits**: Prevent massive unintended changes
- **Rollback capability**: Git integration for safety
- **Dry-run verification**: Test patches before committing

---

## 6. MCP Integration Points

### Primary Tools Used
```typescript
// Serena v2 - Core patch operations
mcp_serena.propose_patch()
mcp_serena.dry_run_apply()
mcp_serena.verify_apply()
mcp_serena.commit_with_limits()

// CLI Tools - Testing and validation
mcp_cli.run_tests()
mcp_cli.run_lint()
mcp_cli.run_typecheck()

// Dope-Context - Code intelligence
mcp_dope_context.retrieve_symbols()
mcp_dope_context.file_snippets()
mcp_dope_context.symbol_reference_graph()

// ConPort - Decision logging
mcp_conport.log_decision()
```

### Error Handling Strategy
```typescript
// Circuit breaker pattern
class MCPClient {
  private failureCount = 0;
  private readonly maxFailures = 3;

  async call(method: string, params: any) {
    try {
      const result = await this.rawCall(method, params);
      this.failureCount = 0; // Reset on success
      return result;
    } catch (error) {
      this.failureCount++;
      if (this.failureCount >= this.maxFailures) {
        throw new Error('MCP service circuit broken');
      }
      await this.backoff();
      return this.call(method, params); // Retry
    }
  }
}
```

---

## 7. Testing & Validation Strategy

### Unit Tests
```typescript
describe('GenericController', () => {
  it('should succeed on first attempt', async () => {
    const controller = new GenericController(mockDeps);
    const patch = await controller.iterate(testIssue);

    expect(patch).toBeDefined();
    expect(controller.attemptCount).toBe(1);
  });

  it('should refine after failures', async () => {
    const controller = new GenericController(mockDeps);
    // Mock failures for first 2 attempts
    const patch = await controller.iterate(testIssue);

    expect(controller.attemptCount).toBe(3); // 2 failures + 1 success
  });

  it('should abort after max attempts', async () => {
    const controller = new GenericController({...mockDeps, maxAttempts: 2});
    const patch = await controller.iterate(testIssue);

    expect(patch).toBeNull();
    expect(controller.attemptCount).toBe(2);
  });
});
```

### Integration Tests
```typescript
describe('MCP Integration', () => {
  it('should handle Serena failures gracefully', async () => {
    // Mock Serena timeout
    const controller = new GenericController(mockDeps);
    const patch = await controller.iterate(testIssue);

    // Should retry or abort cleanly
    expect(patch).toBeDefined();
  });

  it('should respect commit limits', async () => {
    const largePatch = createLargePatch();
    const result = await mcp_serena.commit_with_limits(largePatch, 10, 1000);

    expect(result.committed).toBe(false);
  });
});
```

---

## 8. User Experience

### Terminal Output Examples

**Planning Phase**:
```bash
$ dmx fix plan "fix null pointer in parse_user function"

🔍 Analyzing issue: null pointer in parse_user
📋 Found 3 related symbols, 2 test files
🎯 Plan: Add null check guard + update error handling
💡 Estimated attempts: 2-3

Proceed? (y/n): y
```

**Execution Phase**:
```bash
$ dmx fix try "fix null pointer in parse_user"

🚀 Starting attempt 1/5...

📝 Generated patch: Add null check in parse_user
🧪 Running tests...
❌ Tests failed: 2/10 passed
🔍 Analyzing failures: null check too restrictive

📝 Refining patch: Adjust null check condition
🧪 Running tests...
✅ Tests passed: 10/10
🔧 Applying patch (23 lines changed)
💾 Committed: fix(parse_user): add null check guard
```

**Status Monitoring**:
```bash
$ dmx fix status

📊 Current Run Status
├── Attempt: 2/5
├── Time elapsed: 45s
├── Last result: Tests failed (8/10 passed)
└── Next action: Refining patch based on failures
```

---

## 9. Deployment & Operations

### Docker Configuration
```dockerfile
FROM node:18-alpine
WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install

# Copy agent code
COPY src/ .

# MCP configuration
ENV MCP_SERVERS=serena,dopemux-cli,dopemux-conport
ENV MAX_ATTEMPTS=5
ENV TIMEOUT_SECONDS=300

CMD ["npm", "start"]
```

### Monitoring & Logging
```typescript
// ConPort decision logging
await mcp_conport.log_decision({
  summary: `Attempt ${attemptNumber}: ${success ? 'Success' : 'Failed'}`,
  rationale: `Patch applied with ${testResults.passed}/${testResults.total} tests passing`,
  tags: ['generic-agent', success ? 'success' : 'failure']
});

// Performance metrics
const metrics = {
  attemptNumber,
  duration: Date.now() - startTime,
  patchSize: patch.diff.length,
  testsPassed: testResults.passed,
  testsTotal: testResults.total,
  serenaCalls: callCount
};
```

---

## 10. Success Criteria & Metrics

### Functional Success
- ✅ Resolves >70% of simple bug types (null checks, bounds errors, logic fixes)
- ✅ Generates patches <50 lines of code
- ✅ Passes all existing tests without introducing regressions
- ✅ Provides clear explanations of changes made

### Performance Success
- ✅ Average resolution time <5 minutes
- ✅ Token usage <5000 per attempt
- ✅ Success rate >60% for well-specified issues
- ✅ <10% failure rate due to MCP timeouts

### User Experience Success
- ✅ Clear progress indication and status updates
- ✅ Easy rollback and intervention capabilities
- ✅ Helpful error messages and suggestions
- ✅ Integration with existing Dopemux workflows

---

## 11. Future Extensions

### Phase 2 Additions (Post-MVP)
- **Multi-file patches**: Handle changes across multiple files
- **Interactive mode**: Allow user guidance during iteration
- **Pattern learning**: Remember successful fix patterns
- **Performance optimization**: Parallel verification steps

### Integration Points
- **VS Code extension**: GUI for patch review and application
- **GitHub integration**: Automatic PR creation and review
- **CI/CD integration**: Automated testing in pipelines
- **Team collaboration**: Shared agent instances and knowledge

---

## Implementation Checklist

### Week 1: Core Infrastructure
- [ ] GenericController class with basic iteration loop
- [ ] PatchGenerator with propose/refine methods
- [ ] FitnessEvaluator with MCP CLI integration
- [ ] MemoryAdapter with attempt logging

### Week 2: MCP Integration
- [ ] Serena v2 propose/dry-run/verify/commit integration
- [ ] CLI tools (run_tests, run_lint, run_typecheck) integration
- [ ] Dope-context symbol/file retrieval
- [ ] ConPort decision logging

### Week 3: CLI & UX
- [ ] CLI command structure (dmx fix plan/try/apply)
- [ ] Progress indicators and status displays
- [ ] Error handling and user feedback
- [ ] Configuration system

### Week 4: Testing & Polish
- [ ] Unit and integration test suite
- [ ] Performance benchmarking
- [ ] Documentation and examples
- [ ] Production deployment preparation

---

**Ready for Implementation**: This simplified generic agent maintains all the powerful MCP integrations while removing the complexity of evolutionary algorithms. Focus on clean iteration, robust error handling, and clear user feedback.