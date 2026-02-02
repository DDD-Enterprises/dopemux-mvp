#!/bin/bash

cd /Users/hue/code/dopemux-mvp

# Create directories
mkdir -p docs/archive/implementation-history
mkdir -p docs/archive/deprecated

# Move implementation-history files
mv docs/DOPESMUX_ULTRA_UI_MVP_COMPLETION.md docs/archive/implementation-history/ 2>/dev/null && echo "✅ Moved DOPESMUX_ULTRA_UI_MVP_COMPLETION.md"
mv docs/PHASE1_SERVICES_INTEGRATION_COMPLETED.md docs/archive/implementation-history/ 2>/dev/null && echo "✅ Moved PHASE1_SERVICES_INTEGRATION_COMPLETED.md"
mv docs/PHASE_3_NEXT_STEPS_PLANNING.md docs/archive/implementation-history/ 2>/dev/null && echo "✅ Moved PHASE_3_NEXT_STEPS_PLANNING.md"
mv docs/REORGANIZATION-2025-10-29.md docs/archive/implementation-history/ 2>/dev/null && echo "✅ Moved REORGANIZATION-2025-10-29.md"
mv docs/RELEASE_NOTES_v0.1.0.md docs/archive/implementation-history/ 2>/dev/null && echo "✅ Moved RELEASE_NOTES_v0.1.0.md"
mv docs/pm-integration-changes.md docs/archive/implementation-history/ 2>/dev/null && echo "✅ Moved pm-integration-changes.md"

# Move deprecated files
mv docs/claude-code-tools-integration-plan.md docs/archive/deprecated/ 2>/dev/null && echo "✅ Moved claude-code-tools-integration-plan.md"
mv docs/conport_enhancement_decisions.json docs/archive/deprecated/ 2>/dev/null && echo "✅ Moved conport_enhancement_decisions.json"

echo ""
echo "📁 Contents of implementation-history/:"
ls -1 docs/archive/implementation-history/

echo ""
echo "📁 Contents of deprecated/:"
ls -1 docs/archive/deprecated/
