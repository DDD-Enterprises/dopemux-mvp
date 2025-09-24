"""
Document normalizer for converting extracted content into standardized AtomicUnits.

Transforms scattered documentation into consistent, tagged, and traceable units
suitable for arc42/C4/Diátaxis normalization and registry generation.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class AtomicUnit:
    """
    Standardized atomic unit of documentation content.

    Represents a normalized, traceable piece of documentation that can be
    processed by the registry builder and embedded for similarity analysis.
    """
    id: str
    content: str
    title: Optional[str] = None
    source_file: str = ""
    line_start: int = 1
    line_end: int = 1
    doc_type: str = "Document"
    entity_type: str = "Content"
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class AtomicUnitsNormalizer:
    """
    Normalizes extracted document content into standardized AtomicUnits.

    Provides consistent tagging, glossary expansion, and metadata enrichment
    for downstream processing by registry builders and embedding systems.
    """

    def __init__(self):
        self.glossary = self._load_default_glossary()

    def normalize(self, raw_units: List[Dict[str, Any]]) -> List[AtomicUnit]:
        """
        Normalize raw extracted units into standardized AtomicUnits.

        Args:
            raw_units: List of raw units from extraction phase

        Returns:
            List of normalized AtomicUnits
        """
        normalized_units = []

        for raw_unit in raw_units:
            try:
                # Create AtomicUnit from raw data
                unit = AtomicUnit(
                    id=raw_unit.get('id', f"unit-{len(normalized_units)}"),
                    content=raw_unit.get('content', ''),
                    title=raw_unit.get('title'),
                    source_file=raw_unit.get('source_file', ''),
                    line_start=raw_unit.get('line_start', 1),
                    line_end=raw_unit.get('line_end', 1),
                    doc_type=raw_unit.get('doc_type', 'Document'),
                    entity_type=raw_unit.get('entity_type', 'Content'),
                    tags=raw_unit.get('tags', []),
                    metadata=raw_unit.get('metadata', {})
                )

                # Normalize content
                unit.content = self._normalize_content(unit.content)

                # Expand glossary terms
                unit.content = self._expand_glossary(unit.content)

                # Enrich tags
                unit.tags = self._enrich_tags(unit)

                # Add metadata
                unit.metadata = self._enrich_metadata(unit)

                normalized_units.append(unit)

            except Exception as e:
                print(f"⚠️  Error normalizing unit: {e}")
                continue

        print(f"✅ Normalized {len(normalized_units)} atomic units")
        return normalized_units

    def _normalize_content(self, content: str) -> str:
        """Normalize content formatting and structure."""
        import re

        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)

        # Standardize code blocks
        content = re.sub(r'```(\w+)?\n', r'```\1\n', content)

        # Normalize headers
        content = re.sub(r'^#{1,6}\s*(.+?)\s*#+?\s*$', lambda m: f"{'#' * min(6, len(m.group(0).split()[0]))} {m.group(1).strip()}", content, flags=re.MULTILINE)

        return content.strip()

    def _expand_glossary(self, content: str) -> str:
        """Expand glossary terms and acronyms in content."""
        # Simple glossary expansion
        for acronym, expansion in self.glossary.items():
            # Only expand if acronym appears standalone
            import re
            pattern = r'\b' + re.escape(acronym) + r'\b'
            if re.search(pattern, content) and expansion not in content:
                # Add expansion in parentheses after first occurrence
                content = re.sub(pattern, f"{acronym} ({expansion})", content, count=1)

        return content

    def _enrich_tags(self, unit: AtomicUnit) -> List[str]:
        """Enrich tags based on content analysis."""
        import re

        tags = set(unit.tags)
        content_lower = unit.content.lower()

        # Technical tags
        tech_patterns = {
            'api': r'\b(api|rest|graphql|endpoint)\b',
            'database': r'\b(database|db|sql|postgres|mysql|mongodb)\b',
            'security': r'\b(security|auth|jwt|oauth|encryption|threat)\b',
            'performance': r'\b(performance|latency|throughput|benchmark|slo|sli)\b',
            'architecture': r'\b(architecture|design|system|component|service)\b',
            'testing': r'\b(test|testing|qa|quality|spec|scenario)\b',
            'deployment': r'\b(deploy|deployment|docker|kubernetes|ci|cd)\b',
            'monitoring': r'\b(monitoring|metrics|logs|alerts|observability)\b'
        }

        for tag, pattern in tech_patterns.items():
            if re.search(pattern, content_lower):
                tags.add(tag)

        # Document type tags
        if unit.doc_type:
            tags.add(unit.doc_type.lower())

        # Priority indicators
        priority_patterns = {
            'high-priority': r'\b(critical|urgent|high.priority|p0|p1)\b',
            'deprecated': r'\b(deprecated|obsolete|legacy|superseded)\b',
            'draft': r'\b(draft|wip|work.in.progress|todo)\b'
        }

        for tag, pattern in priority_patterns.items():
            if re.search(pattern, content_lower):
                tags.add(tag)

        return list(tags)

    def _enrich_metadata(self, unit: AtomicUnit) -> Dict[str, Any]:
        """Enrich metadata with derived information."""
        metadata = dict(unit.metadata)

        # Content statistics
        metadata['word_count'] = len(unit.content.split())
        metadata['line_count'] = len(unit.content.split('\n'))
        metadata['char_count'] = len(unit.content)

        # Complexity indicators
        import re
        metadata['code_blocks'] = len(re.findall(r'```', unit.content))
        metadata['links'] = len(re.findall(r'\[.*?\]\(.*?\)', unit.content))
        metadata['headers'] = len(re.findall(r'^#+\s', unit.content, re.MULTILINE))

        # Source information
        if unit.source_file:
            source_path = Path(unit.source_file)
            metadata['source_dir'] = str(source_path.parent)
            metadata['file_extension'] = source_path.suffix
            metadata['file_name'] = source_path.name

        # Processing timestamp
        from datetime import datetime
        metadata['processed_at'] = datetime.now().isoformat()

        return metadata

    def _load_default_glossary(self) -> Dict[str, str]:
        """Load default glossary for acronym expansion."""
        return {
            'API': 'Application Programming Interface',
            'REST': 'Representational State Transfer',
            'HTTP': 'HyperText Transfer Protocol',
            'JSON': 'JavaScript Object Notation',
            'SQL': 'Structured Query Language',
            'URL': 'Uniform Resource Locator',
            'UUID': 'Universally Unique Identifier',
            'JWT': 'JSON Web Token',
            'OAuth': 'Open Authorization',
            'CRUD': 'Create, Read, Update, Delete',
            'MVC': 'Model-View-Controller',
            'SLA': 'Service Level Agreement',
            'SLO': 'Service Level Objective',
            'SLI': 'Service Level Indicator',
            'RTO': 'Recovery Time Objective',
            'RPO': 'Recovery Point Objective',
            'CI': 'Continuous Integration',
            'CD': 'Continuous Deployment',
            'TDD': 'Test-Driven Development',
            'BDD': 'Behavior-Driven Development',
            'ADR': 'Architecture Decision Record',
            'RFC': 'Request for Comments',
            'C4': 'Context, Containers, Components, Code',
            'UML': 'Unified Modeling Language',
            'gRPC': 'Google Remote Procedure Call',
            'TLS': 'Transport Layer Security',
            'SSL': 'Secure Sockets Layer',
            'VPN': 'Virtual Private Network',
            'DNS': 'Domain Name System',
            'CDN': 'Content Delivery Network',
            'AWS': 'Amazon Web Services',
            'GCP': 'Google Cloud Platform',
            'K8s': 'Kubernetes',
            'DB': 'Database',
            'UI': 'User Interface',
            'UX': 'User Experience',
            'QA': 'Quality Assurance',
            'SRE': 'Site Reliability Engineering',
            'DevOps': 'Development Operations',
            'GDPR': 'General Data Protection Regulation',
            'PII': 'Personally Identifiable Information',
            'CORS': 'Cross-Origin Resource Sharing',
            'CSRF': 'Cross-Site Request Forgery',
            'XSS': 'Cross-Site Scripting'
        }