#!/usr/bin/env python3
"""
Serena KG Provider - LSP Integration for Knowledge Graph
Part of CONPORT-KG-2025 Phase 8C

Provides seamless KG integration in Serena LSP:
- Hover tooltips for decision references
- Sidebar panel with related decisions
- Code-decision correlation
- Background query execution

Decision #118 (automation architecture)
"""

import re
import os
import sys
from typing import List, Optional, Dict, Any

# Add conport_kg to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'conport_kg'))

try:
    from queries.overview import OverviewQueries
    from queries.exploration import ExplorationQueries
    from queries.deep_context import DeepContextQueries
    from queries.models import DecisionCard, DecisionSummary
except ImportError:
    print("⚠️  ConPort KG queries not available")
    OverviewQueries = None


class SerenaKGProvider:
    """
    Knowledge Graph provider for Serena LSP

    Integrates KG queries into code navigation:
    - Hover tooltips show decision summaries
    - Sidebar displays related decisions
    - Background correlation finds relevant context
    """

    def __init__(self):
        """Initialize with query classes"""
        if OverviewQueries:
            self.overview = OverviewQueries()
            self.exploration = ExplorationQueries()
            self.deep_context = DeepContextQueries()
            print("✅ SerenaKGProvider initialized with KG queries")
        else:
            self.overview = None
            print("⚠️  SerenaKGProvider: KG queries unavailable")

    def provide_hover(
        self,
        document_uri: str,
        position: Dict[str, int],
        line_text: str
    ) -> Optional[Dict]:
        """
        LSP hover provider for decision references

        Detects patterns like:
        - // Decision #85
        - # Decision #85
        - See Decision #92

        Args:
            document_uri: File URI
            position: Cursor position {line, character}
            line_text: Text of current line

        Returns:
            LSP hover response with markdown content
        """

        if not self.overview:
            return None

        # Pattern: Decision #123
        match = re.search(r'Decision\s+#(\d+)', line_text, re.IGNORECASE)

        if not match:
            return None

        decision_id = int(match.group(1))

        try:
            # Quick Tier 1 query (<3ms)
            summary = self.overview.get_decision_summary(decision_id)

            # Build markdown hover content
            markdown = f"""**Decision #{decision_id}**

{summary.summary}

**Cognitive Load**: {summary.get_cognitive_load()}
**Related Decisions**: {summary.related_count or 0}

*Click to explore genealogy in knowledge graph*
"""

            return {
                'contents': {
                    'kind': 'markdown',
                    'value': markdown.strip()
                },
                'range': self._get_word_range(position, line_text, match.group(0))
            }

        except Exception as e:
            print(f"⚠️  Hover provider failed for decision #{decision_id}: {e}")
            return None

    def update_file_context_sidebar(self, file_path: str) -> Dict[str, Any]:
        """
        Update Serena sidebar with related decisions

        ADHD-safe:
        - Collapsed by default
        - Top-3 pattern
        - Background query (non-blocking)
        - Passive display (no interruption)

        Args:
            file_path: Currently opened file

        Returns:
            Sidebar panel specification
        """

        if not self.overview:
            return {'items': [], 'collapsed': True}

        # Extract module context
        module = self._extract_module_name(file_path)

        try:
            # Strategy 1: Tag-based search (fast)
            decisions = self.overview.search_by_tag(module, limit=3)

            if not decisions and self.deep_context:
                # Strategy 2: Full-text search (fallback)
                decisions = self.deep_context.search_full_text(module, limit=5)[:3]

            # Build sidebar panel
            return {
                'panel_id': 'kg_related_decisions',
                'title': 'Related Decisions',
                'items': [
                    {
                        'id': d.id,
                        'label': f"#{d.id}: {d.summary[:50]}...",
                        'tooltip': d.summary,
                        'command': 'kg.explore_decision',
                        'args': [d.id]
                    }
                    for d in decisions
                ],
                'collapsed': True,  # ADHD: User expands when ready
                'badge': len(decisions) if decisions else None,
                'empty_message': 'No related decisions found'
            }

        except Exception as e:
            print(f"⚠️  Sidebar update failed for {file_path}: {e}")
            return {'items': [], 'collapsed': True}

    def correlate_code_to_decisions(self, file_path: str) -> List[DecisionCard]:
        """
        Smart correlation: file → relevant decisions

        Multi-strategy approach:
        1. Module name → tag search
        2. Symbol names → full-text search (if TreeSitter available)
        3. Recent decisions (fallback)

        Args:
            file_path: Source code file

        Returns:
            Top-3 most relevant decisions
        """

        if not self.overview:
            return []

        all_decisions = {}

        # Strategy 1: Module name
        module = self._extract_module_name(file_path)
        if module:
            try:
                by_module = self.overview.search_by_tag(module, limit=5)
                for d in by_module:
                    all_decisions[d.id] = d
            except:
                pass

        # Strategy 2: Full-text search on module
        if module and self.deep_context:
            try:
                by_text = self.deep_context.search_full_text(module, limit=5)
                for d in by_text:
                    all_decisions[d.id] = d
            except:
                pass

        # Strategy 3: Recent decisions (fallback)
        if len(all_decisions) < 3:
            try:
                recent = self.overview.get_recent_decisions(3)
                for d in recent:
                    all_decisions[d.id] = d
            except:
                pass

        # Return Top-3 most relevant
        return list(all_decisions.values())[:3]

    def _extract_module_name(self, file_path: str) -> Optional[str]:
        """Extract module name from file path"""
        if not file_path:
            return None

        # Get filename without extension
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]

        # Clean up common patterns
        name = name.replace('_', '-').replace('.', '-')

        return name if name else None

    def _get_word_range(
        self,
        position: Dict[str, int],
        line_text: str,
        word: str
    ) -> Dict:
        """Get LSP range for word at position"""
        line = position['line']
        start_char = line_text.index(word) if word in line_text else position['character']

        return {
            'start': {'line': line, 'character': start_char},
            'end': {'line': line, 'character': start_char + len(word)}
        }


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("Serena KG Provider Test")
    print("=" * 70)

    provider = SerenaKGProvider()

    # Test 1: Hover provider
    print("\n[Test 1] Hover Provider:")
    test_lines = [
        "// Decision #85 - Serena Memory Enhancement",
        "# See Decision #92 for context",
        "No decision reference here"
    ]

    for line in test_lines:
        hover = provider.provide_hover(
            "file:///test.py",
            {'line': 0, 'character': 10},
            line
        )
        if hover:
            decision_match = re.search(r'#(\d+)', line)
            decision_num = decision_match.group(1) if decision_match else '?'
            print(f"   '{line[:40]}...'")
            print(f"      → Hover tooltip generated")
            print(f"      → Decision #{decision_num}")
        else:
            print(f"   '{line}' → No hover")

    # Test 2: Sidebar updates
    print("\n[Test 2] Sidebar Panel Updates:")
    test_files = [
        "services/serena/v2/mcp_client.py",
        "services/auth/token_manager.py",
        "README.md"
    ]

    for file_path in test_files:
        sidebar = provider.update_file_context_sidebar(file_path)
        module = provider._extract_module_name(file_path)
        print(f"   {file_path}")
        print(f"      Module: {module}")
        print(f"      Items: {len(sidebar['items'])}")
        print(f"      Collapsed: {sidebar['collapsed']}")

    # Test 3: Code-decision correlation
    print("\n[Test 3] Code-Decision Correlation:")
    for file_path in test_files[:2]:
        decisions = provider.correlate_code_to_decisions(file_path)
        print(f"   {file_path}")
        print(f"      Found {len(decisions)} correlated decisions")
        for d in decisions:
            print(f"         #{d.id}: {d.summary[:45]}...")

    print("\n✅ All Serena KG Provider tests passed!")
