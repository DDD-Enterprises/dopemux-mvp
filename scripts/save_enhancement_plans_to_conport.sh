#!/bin/bash
#
# Save ConPort Enhancement Plans to ConPort
# Run this script when ConPort MCP is available to log the design as decisions
#

WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

echo "📝 Saving ConPort enhancement plans to ConPort..."

# Note: This requires ConPort MCP to be running
# You can call this from Claude Code when ConPort tools are available
# Or convert to Python script using conport-mcp CLI directly

cat << 'EOF'
When ConPort MCP is available, log these decisions:

1. MAIN DECISION (#146):
   Summary: Implement comprehensive ConPort enhancements for ADHD-optimized decision support
   Tags: conport, adhd-optimization, pattern-learning, decision-support, roadmap
   Rationale: Current decision logging is basic. Need confidence tracking, pattern learning,
              outcome measurement, decision genealogy, ADHD dashboard, and CLI visualization
   Implementation: 7-sprint roadmap detailed in docs/CONPORT_ENHANCEMENTS_DESIGN.md

2. PHASE 1 DECISION (#147 - builds_upon #146):
   Summary: Enhanced Decision Model - Add metadata fields for tracking
   Tags: conport, phase-1, data-model, migration
   Rationale: Need richer metadata for downstream features
   Implementation: 14 new fields, database migration, backward compatible
   Estimated: 1 week

3. PHASE 2 DECISION (#148 - builds_upon #147):
   Summary: Decision Visualization CLI - List, show, filter
   Tags: conport, phase-2, cli, visualization
   Implementation: dopemux decisions list/show/stats commands
   Estimated: 1 week

4. PHASE 3 DECISION (#149 - builds_upon #148):
   Summary: Pattern Detection Engine - Auto-detect decision patterns
   Tags: conport, phase-3, pattern-learning, ml-foundation
   Implementation: Tag clustering, decision chains, timing analysis, success prediction
   Estimated: 2 weeks

PROGRESS ENTRIES (Link to #146):
- [ ] Sprint 1: Enhanced Decision Model (1 week)
- [ ] Sprint 2: Basic Visualization (1 week)
- [ ] Sprint 3: Pattern Detection (2 weeks)
- [ ] Sprint 4: Decision Graph (1 week)
- [ ] Sprint 5: ADHD Dashboard Alpha (2 weeks)
- [ ] Sprint 6: Review System (1 week)
- [ ] Sprint 7: Advanced Features (4 weeks)

QUICK WINS (Can start today):
- [ ] Decision review command (~2h)
- [ ] Decision stats command (~3h)
- [ ] Energy logging (~2h)

EOF

echo ""
echo "✅ Plan template created"
echo "📄 Full design: docs/CONPORT_ENHANCEMENTS_DESIGN.md (909 lines)"
echo "📦 Committed and pushed: 67564fc0"
echo ""
echo "To log to ConPort (when MCP available):"
echo "  Use Claude Code with ConPort MCP enabled"
echo "  Ask: 'Log the ConPort enhancement decisions from /tmp/conport_decisions.json'"
