#!/usr/bin/env bash
# Block prohibited documentation filename patterns (NOTES, TODO, TEMP, SCRATCH).
#
# Extracted from .pre-commit-config.yaml's docs-prohibited-patterns hook so the
# matching logic is independently testable (tests/governance/test_docs_prohibited_patterns.py).
#
# Usage: docs_prohibited_patterns.sh <file> [<file> ...]
set -e

prohibited_found=false

for file in "$@"; do
  case "$file" in
    docs/*|task-packets/*)
      # Skip quarantined files
      if [[ "$file" =~ ^docs/04-explanation/history/sourceFiles/ ]]; then
        continue
      fi

      base="$(basename "$file")"
      lbase="$(echo "$base" | tr '[:upper:]' '[:lower:]')"

      # "template" legitimately contains the substring "temp" (task-packet-template.md,
      # template-agent.md, template-task.md, ...). Treat any filename containing
      # "template" as a template asset, not a temporary/scratch file, before applying
      # the temp/notes/todo/scratch prohibition below.
      case "$lbase" in
        *template*)
          continue
          ;;
      esac

      case "$lbase" in
        notes*.md|todo*.md|temp*.md|*temp*.md|*scratch*.md)
          echo "❌ Found prohibited file pattern in changed file:"
          echo "  $file"
          prohibited_found=true
          ;;
      esac
      ;;
  esac
done

if [ "$prohibited_found" = true ]; then
  echo "Use structured workflow: RFC->ADR->arc42 for documentation"
  exit 1
fi

echo "✅ No prohibited patterns found in changed docs"
