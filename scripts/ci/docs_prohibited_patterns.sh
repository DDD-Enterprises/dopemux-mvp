#!/usr/bin/env bash
# Block prohibited documentation filename patterns (NOTES, TODO, TEMP, SCRATCH).
#
# Extracted from .pre-commit-config.yaml's docs-prohibited-patterns hook so the
# matching logic is independently testable (tests/ci/test_docs_prohibited_patterns.py).
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
      # template-agent.md, template-task.md, ...), so the temp*.md/*temp*.md checks must
      # not fire on that incidental substring alone. Strip "template" occurrences before
      # testing the temp-family patterns only -- notes*.md/todo*.md/*scratch*.md are
      # still evaluated against the untouched basename, so a genuinely prohibited file
      # that happens to also say "template" (e.g. notes-template.md, todo-template.md,
      # temp-template.md, scratch-template.md) remains blocked.
      detemplated="${lbase//template/}"

      is_prohibited=false
      case "$lbase" in
        notes*.md|todo*.md|*scratch*.md)
          is_prohibited=true
          ;;
      esac
      case "$detemplated" in
        temp*.md|*temp*.md)
          is_prohibited=true
          ;;
      esac

      if [ "$is_prohibited" = true ]; then
        echo "❌ Found prohibited file pattern in changed file:"
        echo "  $file"
        prohibited_found=true
      fi
      ;;
  esac
done

if [ "$prohibited_found" = true ]; then
  echo "Use structured workflow: RFC->ADR->arc42 for documentation"
  exit 1
fi

echo "✅ No prohibited patterns found in changed docs"
