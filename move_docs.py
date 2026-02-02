#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

# Base directory
base = Path("/Users/hue/code/dopemux-mvp/docs")

# Create directories
impl_history = base / "archive" / "implementation-history"
deprecated = base / "archive" / "deprecated"

impl_history.mkdir(parents=True, exist_ok=True)
deprecated.mkdir(parents=True, exist_ok=True)

# Files to move to implementation-history
impl_files = [
    "DOPESMUX_ULTRA_UI_MVP_COMPLETION.md",
    "PHASE1_SERVICES_INTEGRATION_COMPLETED.md",
    "PHASE_3_NEXT_STEPS_PLANNING.md",
    "REORGANIZATION-2025-10-29.md",
    "RELEASE_NOTES_v0.1.0.md",
    "pm-integration-changes.md"
]

# Files to move to deprecated
deprecated_files = [
    "claude-code-tools-integration-plan.md",
    "conport_enhancement_decisions.json"
]

moved_impl = []
moved_dep = []
errors = []

# Move implementation-history files
for f in impl_files:
    src = base / f
    if src.exists():
        dst = impl_history / f
        shutil.move(str(src), str(dst))
        moved_impl.append(f)
    else:
        errors.append(f"Not found: {f}")

# Move deprecated files
for f in deprecated_files:
    src = base / f
    if src.exists():
        dst = deprecated / f
        shutil.move(str(src), str(dst))
        moved_dep.append(f)
    else:
        errors.append(f"Not found: {f}")

print("✅ Successfully moved to implementation-history/:")
for f in moved_impl:
    print(f"  - {f}")

print("\n✅ Successfully moved to deprecated/:")
for f in moved_dep:
    print(f"  - {f}")

if errors:
    print("\n⚠️ Errors:")
    for e in errors:
        print(f"  - {e}")

# List final directory contents
print("\n📁 Contents of implementation-history/:")
for f in sorted(impl_history.iterdir()):
    print(f"  - {f.name}")

print("\n📁 Contents of deprecated/:")
for f in sorted(deprecated.iterdir()):
    print(f"  - {f.name}")
