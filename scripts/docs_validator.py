#!/usr/bin/env python3
"""
Documentation Validator for Knowledge Graph Architecture

Validates that all documentation follows the graph schema and ADHD-friendly patterns.
Prevents creation of ad-hoc files that bypass the structured workflow.

Usage:
  python scripts/docs_validator.py                    # validate all docs
  python scripts/docs_validator.py --fix              # fix issues when possible
  python scripts/docs_validator.py --check-orphans    # find unlinked docs
  python scripts/docs_validator.py path/to/file.md    # validate single file
"""

import sys
import os
import re
import yaml
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

# Graph node types from knowledge graph schema
VALID_NODE_TYPES = {
    'Decision', 'ADR', 'Caveat', 'Pattern', 'DocPage',
    'Symbol', 'File', 'Task', 'Milestone', 'Error'
}

# Valid document types
VALID_DOC_TYPES = {'adr', 'rfc', 'caveat', 'pattern', 'runbook', 'tutorial', 'how-to', 'reference', 'explanation'}

# Valid status values
VALID_STATUSES = {
    'adr': {'proposed', 'accepted', 'rejected', 'superseded'},
    'rfc': {'draft', 'review', 'accepted', 'rejected', 'superseded'},
    'caveat': {'active', 'resolved', 'superseded'},
    'pattern': {'draft', 'accepted', 'deprecated'},
    'runbook': {'active', 'outdated', 'superseded'}
}

# Required frontmatter fields by document type
REQUIRED_FIELDS = {
    'base': ['id', 'title', 'type', 'date', 'author'],
    'adr': ['status', 'prelude', 'graph_metadata'],
    'rfc': ['status', 'prelude', 'derived_from'],
    'caveat': ['severity', 'impact', 'prelude'],
    'pattern': ['usage_context', 'prelude'],
    'runbook': ['owner', 'last_review', 'next_review']
}

# Prohibited file patterns
PROHIBITED_PATTERNS = [
    r'README.*\.md$',
    r'NOTES.*\.md$',
    r'TODO.*\.md$',
    r'TEMP.*\.md$',
    r'DRAFT.*\.md$',
    r'.*[Tt]emp.*\.md$'
]

# Allowed paths for documentation
ALLOWED_PATHS = [
    'docs/90-adr/',
    'docs/91-rfc/',
    'docs/92-runbooks/',
    'docs/94-architecture/',
    'docs/01-tutorials/',
    'docs/02-how-to/',
    'docs/03-reference/',
    'docs/04-explanation/'
]

@dataclass
class ValidationError:
    """Represents a validation error found in documentation."""
    file_path: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    line: Optional[int] = None
    fixable: bool = False

class DocumentValidator:
    """Validates documentation against knowledge graph schema."""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.project_root = Path.cwd()

    def validate_file(self, file_path: str, fix: bool = False) -> bool:
        """Validate a single documentation file."""
        path = Path(file_path)

        if not path.exists():
            self.add_error(file_path, "File does not exist")
            return False

        # Check if file is in allowed location
        if not self._is_allowed_path(file_path):
            self.add_error(file_path, f"Documentation file not in allowed path. Use one of: {', '.join(ALLOWED_PATHS)}")
            return False

        # Check for prohibited patterns
        if self._matches_prohibited_pattern(file_path):
            self.add_error(file_path, "File matches prohibited pattern (README, NOTES, TODO, etc.)")
            return False

        # Parse and validate content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.add_error(file_path, f"Cannot read file: {e}")
            return False

        # Validate frontmatter
        frontmatter, body = self._parse_frontmatter(content)
        if not frontmatter:
            self.add_error(file_path, "Missing YAML frontmatter", fixable=True)
            return False

        # Validate frontmatter structure
        valid_fm = self._validate_frontmatter(file_path, frontmatter, fix)

        # Validate graph metadata
        valid_graph = self._validate_graph_metadata(file_path, frontmatter)

        # Validate prelude length
        valid_prelude = self._validate_prelude(file_path, frontmatter)

        # Validate content structure
        valid_content = self._validate_content_structure(file_path, body, frontmatter.get('type'))

        return all([valid_fm, valid_graph, valid_prelude, valid_content])

    def _is_allowed_path(self, file_path: str) -> bool:
        """Check if file is in an allowed documentation path."""
        rel_path = os.path.relpath(file_path, self.project_root)
        return any(rel_path.startswith(allowed) for allowed in ALLOWED_PATHS)

    def _matches_prohibited_pattern(self, file_path: str) -> bool:
        """Check if filename matches prohibited patterns."""
        filename = os.path.basename(file_path)
        return any(re.match(pattern, filename, re.IGNORECASE) for pattern in PROHIBITED_PATTERNS)

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Parse YAML frontmatter from markdown content."""
        if not content.startswith('---\n'):
            return None, content

        end_marker = content.find('\n---\n', 4)
        if end_marker == -1:
            return None, content

        try:
            fm_content = content[4:end_marker]
            body = content[end_marker + 5:]
            frontmatter = yaml.safe_load(fm_content)
            return frontmatter, body
        except yaml.YAMLError as e:
            return None, content

    def _validate_frontmatter(self, file_path: str, frontmatter: Dict, fix: bool) -> bool:
        """Validate frontmatter structure and required fields."""
        valid = True
        doc_type = frontmatter.get('type')

        # Check document type
        if not doc_type or doc_type not in VALID_DOC_TYPES:
            self.add_error(file_path, f"Invalid or missing type. Must be one of: {', '.join(VALID_DOC_TYPES)}")
            valid = False

        # Check required base fields
        for field in REQUIRED_FIELDS['base']:
            if field not in frontmatter:
                self.add_error(file_path, f"Missing required field: {field}", fixable=True)
                valid = False

        # Check type-specific fields
        if doc_type and doc_type in REQUIRED_FIELDS:
            for field in REQUIRED_FIELDS[doc_type]:
                if field not in frontmatter:
                    self.add_error(file_path, f"Missing required field for {doc_type}: {field}", fixable=True)
                    valid = False

        # Validate status
        if 'status' in frontmatter and doc_type in VALID_STATUSES:
            status = frontmatter['status']
            if status not in VALID_STATUSES[doc_type]:
                valid_statuses = ', '.join(VALID_STATUSES[doc_type])
                self.add_error(file_path, f"Invalid status '{status}' for {doc_type}. Must be one of: {valid_statuses}")
                valid = False

        # Validate date format
        if 'date' in frontmatter:
            try:
                datetime.fromisoformat(frontmatter['date'])
            except ValueError:
                self.add_error(file_path, "Invalid date format. Use YYYY-MM-DD")
                valid = False

        return valid

    def _validate_graph_metadata(self, file_path: str, frontmatter: Dict) -> bool:
        """Validate graph metadata for semantic retrieval."""
        valid = True
        graph_meta = frontmatter.get('graph_metadata', {})

        if not isinstance(graph_meta, dict):
            self.add_error(file_path, "graph_metadata must be a dictionary")
            return False

        # Check node type
        node_type = graph_meta.get('node_type')
        if node_type and node_type not in VALID_NODE_TYPES:
            valid_types = ', '.join(VALID_NODE_TYPES)
            self.add_error(file_path, f"Invalid node_type '{node_type}'. Must be one of: {valid_types}")
            valid = False

        # Check impact level
        impact = graph_meta.get('impact')
        if impact and impact not in {'low', 'medium', 'high'}:
            self.add_error(file_path, "impact must be one of: low, medium, high")
            valid = False

        # Check relates_to is a list
        relates_to = graph_meta.get('relates_to', [])
        if not isinstance(relates_to, list):
            self.add_error(file_path, "relates_to must be a list of related entities")
            valid = False

        return valid

    def _validate_prelude(self, file_path: str, frontmatter: Dict) -> bool:
        """Validate prelude for embedding generation."""
        prelude = frontmatter.get('prelude', '')

        if not prelude:
            self.add_warning(file_path, "Missing prelude for semantic search embeddings")
            return True  # Warning, not error

        # Rough token count (words * 1.3 as approximation)
        word_count = len(prelude.split())
        approx_tokens = int(word_count * 1.3)

        if approx_tokens > 100:
            self.add_error(file_path, f"Prelude too long (~{approx_tokens} tokens). Must be ≤100 tokens for efficient embeddings")
            return False

        return True

    def _validate_content_structure(self, file_path: str, body: str, doc_type: Optional[str]) -> bool:
        """Validate document content structure based on type."""
        valid = True

        if doc_type == 'adr':
            required_sections = ['Context', 'Decision', 'Consequences']
            valid &= self._check_sections(file_path, body, required_sections)

        elif doc_type == 'rfc':
            required_sections = ['Problem', 'Options', 'Proposed Direction']
            valid &= self._check_sections(file_path, body, required_sections)

        elif doc_type == 'caveat':
            required_sections = ['Issue', 'Impact', 'Mitigation']
            valid &= self._check_sections(file_path, body, required_sections)

        return valid

    def _check_sections(self, file_path: str, body: str, required_sections: List[str]) -> bool:
        """Check that required sections are present in document."""
        valid = True

        for section in required_sections:
            # Look for markdown headers (## or ###)
            pattern = rf'^##+ {section}|^# {section}'
            if not re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
                self.add_warning(file_path, f"Missing recommended section: {section}")
                # Note: warnings don't make validation fail

        return valid

    def validate_all_docs(self, fix: bool = False) -> bool:
        """Validate all documentation files in the project."""
        docs_dir = self.project_root / 'docs'
        if not docs_dir.exists():
            self.add_error(str(docs_dir), "docs/ directory not found")
            return False

        all_valid = True

        for md_file in docs_dir.rglob('*.md'):
            file_valid = self.validate_file(str(md_file), fix)
            all_valid = all_valid and file_valid

        return all_valid

    def check_orphaned_docs(self) -> List[str]:
        """Find documentation files that aren't referenced by others."""
        # This would implement graph traversal to find unlinked nodes
        # For now, return empty list as placeholder
        orphaned = []

        # TODO: Implement graph traversal to find orphaned documents
        # This would check for files not referenced by:
        # - derived_from links
        # - relates_to references
        # - arc42 cross-references

        return orphaned

    def add_error(self, file_path: str, message: str, line: Optional[int] = None, fixable: bool = False):
        """Add a validation error."""
        self.errors.append(ValidationError(file_path, 'error', message, line, fixable))

    def add_warning(self, file_path: str, message: str, line: Optional[int] = None):
        """Add a validation warning."""
        self.warnings.append(ValidationError(file_path, 'warning', message, line))

    def print_results(self):
        """Print validation results."""
        if self.errors:
            print(f"\n❌ {len(self.errors)} error(s) found:")
            for error in self.errors:
                location = f"{error.file_path}:{error.line}" if error.line else error.file_path
                fixable = " [FIXABLE]" if error.fixable else ""
                print(f"  {location}: {error.message}{fixable}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                location = f"{warning.file_path}:{warning.line}" if warning.line else warning.file_path
                print(f"  {location}: {warning.message}")

        if not self.errors and not self.warnings:
            print("✅ All documentation follows the knowledge graph schema!")

    def has_errors(self) -> bool:
        """Check if any validation errors were found."""
        return len(self.errors) > 0

def main():
    parser = argparse.ArgumentParser(description='Validate documentation against knowledge graph schema')
    parser.add_argument('files', nargs='*', help='Specific files to validate (default: all docs)')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    parser.add_argument('--check-orphans', action='store_true', help='Find orphaned documentation')

    args = parser.parse_args()

    validator = DocumentValidator()

    if args.check_orphans:
        orphans = validator.check_orphaned_docs()
        if orphans:
            print(f"🔍 Found {len(orphans)} orphaned documents:")
            for orphan in orphans:
                print(f"  {orphan}")
        else:
            print("✅ No orphaned documents found")
        return

    if args.files:
        # Validate specific files
        all_valid = True
        for file_path in args.files:
            valid = validator.validate_file(file_path, args.fix)
            all_valid = all_valid and valid
    else:
        # Validate all documentation
        all_valid = validator.validate_all_docs(args.fix)

    validator.print_results()

    # Exit with error code if validation failed
    sys.exit(0 if all_valid else 1)

if __name__ == '__main__':
    main()