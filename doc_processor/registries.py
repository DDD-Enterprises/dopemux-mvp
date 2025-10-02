"""
Registry builder for creating canonical TSV registries from extracted documents.

Generates standardized registries for Features, Components, Subsystems, and Research with
stable IDs, ownership, interfaces, dependencies, and full traceability following
the comprehensive specification for arc42/C4/Diátaxis normalization.

Includes research as a first-class citizen with evidence propagation into RFCs/ADRs/arc42/C4.
"""

import csv
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .normalizer import AtomicUnit


@dataclass
class FeatureEntry:
    """Feature registry entry following canonical schema."""
    feature_id: str
    title: str
    type: str = "Feature"
    status: str = "Proposed"
    priority: str = ""
    owner: str = ""
    subsystem_ids: str = ""
    component_ids: str = ""
    description: str = ""
    acceptance_criteria: str = ""
    non_goals: str = ""
    risk: str = ""
    level_of_effort: str = ""
    story_points: int = 0
    target_release: str = ""
    rfc_ids: str = ""
    adr_ids: str = ""
    source_uri: str = ""
    source_lines: str = ""
    created_at: str = ""
    updated_at: str = ""
    tags: str = ""


@dataclass
class ComponentEntry:
    """Component registry entry following canonical schema."""
    component_id: str
    name: str
    subsystem_id: str = ""
    container_name: str = ""
    purpose: str = ""
    public_interfaces: str = ""
    data_owned: str = ""
    dependencies: str = ""
    tech: str = ""
    stack: str = ""
    repo: str = ""
    owner: str = ""
    slo_availability: str = ""
    slo_latency: str = ""
    sli_metrics: str = ""
    alerts: str = ""
    security_notes: str = ""
    threat_model_refs: str = ""
    adr_ids: str = ""
    rfc_ids: str = ""
    source_uri: str = ""
    source_lines: str = ""
    created_at: str = ""
    updated_at: str = ""
    tags: str = ""


@dataclass
class SubsystemEntry:
    """Subsystem registry entry following canonical schema."""
    subsystem_id: str
    name: str
    domain: str = ""
    description: str = ""
    containers: str = ""
    owning_team: str = ""
    upstream: str = ""
    dependent_on: str = ""
    data_stores: str = ""
    events: str = ""
    rto: str = ""
    rpo: str = ""
    sla: str = ""
    external_interfaces: str = ""
    security_posture: str = ""
    owner: str = ""
    adr_ids: str = ""
    rfc_ids: str = ""
    source_uri: str = ""
    source_lines: str = ""
    created_at: str = ""
    updated_at: str = ""
    tags: str = ""


@dataclass
class ResearchEntry:
    """Research registry entry following canonical schema."""
    research_id: str
    title: str
    research_type: str = "Tech Spike"  # Tech Spike | Benchmark | Competitor | User Interview | Market | Standards/Regulatory
    status: str = "Complete"
    author: str = ""
    date_collected: str = ""
    recency_days: int = 0
    source_quality: str = ""  # High | Medium | Low
    sample_size: str = ""
    method: str = ""
    claim_summary: str = ""
    key_findings: str = ""
    key_metrics: str = ""  # JSON string of structured metrics
    limitations: str = ""
    risks: str = ""
    recommendation: str = ""
    confidence: float = 0.0  # [0,1] computed from recency, quality, sample_size, method_rigor
    score_breakdown: str = ""  # recency:0.9|quality:0.8|sample:0.6|method:0.8
    sources: str = ""
    source_uri: str = ""
    source_lines: str = ""
    use_by: str = ""  # TTL date for volatile domains
    tags: str = ""


@dataclass
class EvidenceLink:
    """Evidence link between research and other entities."""
    from_id: str
    from_type: str  # Research
    to_id: str
    to_type: str    # ADR | Component | Feature | Subsystem
    relation: str   # supports | contradicts | informs | risks | mitigates | requires
    rationale: str
    confidence: float


class RegistryBuilder:
    """
    Builds canonical TSV registries from AtomicUnits following comprehensive specification.

    Creates four machine-generated registries:
    - features.tsv: User-facing capabilities (Epic/Feature/Story)
    - components.tsv: C4 L2 building blocks inside containers
    - subsystems.tsv: Cohesive sets of containers/components (bounded contexts)
    - research.tsv: Research findings with evidence propagation
    - evidence_links.tsv: Relationships between research and other entities

    Uses deterministic extraction rules with regex seeds for:
    - Features: product docs, RFCs, PRDs, Acceptance Criteria
    - Components: C4 diagrams, ADRs, code references, API specs
    - Subsystems: arc42 §5 building blocks, bounded contexts
    - Research: spikes, benchmarks, interviews, with metrics and confidence scoring
    """

    def __init__(self, output_directory: Path):
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Registry storage
        self.features: Dict[str, FeatureEntry] = {}
        self.components: Dict[str, ComponentEntry] = {}
        self.subsystems: Dict[str, SubsystemEntry] = {}
        self.research: Dict[str, ResearchEntry] = {}
        self.evidence_links: List[EvidenceLink] = []

        # ID tracking for uniqueness
        self.seen_feature_ids: Set[str] = set()
        self.seen_component_ids: Set[str] = set()
        self.seen_subsystem_ids: Set[str] = set()
        self.seen_research_ids: Set[str] = set()

        # Deduplication thresholds
        self.cosine_threshold = 0.90
        self.jaccard_threshold = 0.82

        # Research quality scoring weights
        self.quality_weights = {
            'recency': 0.25,    # How recent the research is
            'quality': 0.25,    # Source quality (primary > secondary > vendor blog)
            'sample': 0.25,     # Sample size and method rigor
            'method': 0.25      # Method reproducibility
        }

        # Default TTL for research types (days)
        self.research_ttl = {
            'Tech Spike': 180,
            'Benchmark': 90,
            'Competitor': 365,
            'User Interview': 180,
            'Market': 365,
            'Standards/Regulatory': 1095  # 3 years
        }

    def build_registries(self, atomic_units: List[AtomicUnit]) -> Dict[str, int]:
        """
        Build all canonical registries from atomic units.

        Follows the comprehensive workflow:
        1. Harvest candidates using deterministic extraction rules
        2. Score & dedupe using similarity thresholds
        3. Enrich with ownership, SLO stubs, ADR/RFC links
        4. Build research registry with confidence scoring
        5. Generate evidence links between research and other entities
        6. Emit TSV files for version control

        Args:
            atomic_units: List of normalized atomic units

        Returns:
            Dict with counts of extracted entries
        """
        print("🏗️  Building canonical registries with deterministic extraction...")

        # Phase 1: Harvest candidates
        print("📋 Phase 1: Harvesting candidates from AtomicUnits...")
        for unit in atomic_units:
            self._extract_features(unit)
            self._extract_components(unit)
            self._extract_subsystems(unit)
            self._extract_research(unit)

        # Phase 2: Score & dedupe
        print("🔍 Phase 2: Deduplicating with similarity thresholds...")
        self._deduplicate_entries()

        # Phase 3: Enrich relationships
        print("🔗 Phase 3: Enriching with ownership and cross-references...")
        self._enrich_relationships()
        self._enrich_ownership()
        self._enrich_slo_stubs()

        # Phase 4: Research confidence scoring
        print("🧪 Phase 4: Computing research confidence scores...")
        self._compute_research_confidence()

        # Phase 5: Generate evidence links
        print("🔬 Phase 5: Generating evidence links...")
        self._generate_evidence_links()

        # Phase 6: Emit TSV files
        print("📄 Phase 6: Writing TSV registries...")
        counts = self._write_registries()

        # Phase 7: Optional SQLite database
        sqlite_path = self.output_dir / "registries.db"
        if self._should_generate_sqlite():
            print("📄 Phase 7: Writing SQLite database...")
            self.write_sqlite_db(sqlite_path)

        print(f"✅ Canonical registries built: {counts['features']} features, {counts['components']} components, {counts['subsystems']} subsystems, {counts['research']} research, {counts['evidence_links']} evidence links")
        return counts

    def _should_generate_sqlite(self) -> bool:
        """Determine if SQLite database should be generated."""
        # Generate SQLite if we have significant data to analyze
        total_entries = len(self.features) + len(self.components) + len(self.subsystems) + len(self.research)
        return total_entries >= 10  # Threshold for useful relational analysis

    def _extract_features(self, unit: AtomicUnit):
        """
        Extract feature entries using deterministic rules.

        Patterns from specification:
        - Headings: Feature, Epic, Capability, User Story, Acceptance Criteria
        - Regex seeds: ^#{1,3}\s*(Epic|Feature|Capability)\b
        - Content: Given/When/Then, Story:, Non-Goals, Out of scope
        """
        if not self._is_feature_candidate(unit):
            return

        feature_id = self._generate_feature_id(unit)
        if feature_id in self.features:
            return

        # Extract rich feature details
        acceptance_criteria = self._extract_acceptance_criteria(unit.content)
        non_goals = self._extract_non_goals(unit.content)
        priority = self._extract_priority(unit.content)
        risk_level = self._extract_risk_level(unit.content)
        effort = self._extract_level_of_effort(unit.content)
        story_points = self._extract_story_points(unit.content)
        target_release = self._extract_target_release(unit.content)

        self.features[feature_id] = FeatureEntry(
            feature_id=feature_id,
            title=unit.title or "Unnamed Feature",
            type=self._classify_feature_type(unit),
            description=unit.content[:500],
            acceptance_criteria=acceptance_criteria,
            non_goals=non_goals,
            priority=priority,
            risk=risk_level,
            level_of_effort=effort,
            story_points=story_points,
            target_release=target_release,
            rfc_ids=self._extract_rfc_ids(unit.content),
            adr_ids=self._extract_adr_ids(unit.content),
            source_uri=unit.source_file,
            source_lines=f"{unit.line_start}-{unit.line_end}",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags="|".join(unit.tags) if unit.tags else ""
        )

    def _extract_components(self, unit: AtomicUnit):
        """
        Extract component entries using deterministic rules.

        Patterns from specification:
        - C4 PlantUML/Mermaid: Component(, Container(, Rel()
        - Headings: Service, Module, Package, Library, Adapter, Gateway
        - Code references: repo:, import, module, API specs (OpenAPI, gRPC .proto)
        """
        if not self._is_component_candidate(unit):
            return

        component_id = self._generate_component_id(unit)
        if component_id in self.components:
            return

        # Extract rich component details
        interfaces = self._extract_public_interfaces(unit.content)
        dependencies = self._extract_component_dependencies(unit.content)
        tech_info = self._extract_tech_stack(unit.content)
        repo_info = self._extract_repo_info(unit.content)
        sli_metrics = self._extract_sli_metrics(unit.content)
        security_notes = self._extract_security_notes(unit.content)
        data_owned = self._extract_data_owned(unit.content)

        self.components[component_id] = ComponentEntry(
            component_id=component_id,
            name=unit.title or "Unnamed Component",
            purpose=unit.content[:200],
            public_interfaces=interfaces,
            data_owned=data_owned,
            dependencies=dependencies,
            tech=tech_info.get('tech', ''),
            stack=tech_info.get('stack', ''),
            repo=repo_info,
            sli_metrics=sli_metrics,
            security_notes=security_notes,
            adr_ids=self._extract_adr_ids(unit.content),
            rfc_ids=self._extract_rfc_ids(unit.content),
            source_uri=unit.source_file,
            source_lines=f"{unit.line_start}-{unit.line_end}",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags="|".join(unit.tags) if unit.tags else ""
        )

    def _extract_subsystems(self, unit: AtomicUnit):
        """
        Extract subsystem entries using deterministic rules.

        Patterns from specification:
        - arc42 §5 L1/L2 headings, Bounded Context, Subsystem, Domain
        - Container enumerations with shared data/events
        - Domain groupings by shared terms and diagram adjacency
        """
        if not self._is_subsystem_candidate(unit):
            return

        subsystem_id = self._generate_subsystem_id(unit)
        if subsystem_id in self.subsystems:
            return

        # Extract rich subsystem details
        containers = self._extract_containers(unit.content)
        data_stores = self._extract_data_stores(unit.content)
        events = self._extract_events(unit.content)
        external_interfaces = self._extract_external_interfaces(unit.content)
        domain = self._extract_domain(unit.content)
        upstream_deps = self._extract_upstream_dependencies(unit.content)
        downstream_deps = self._extract_downstream_dependencies(unit.content)
        sla_info = self._extract_sla_info(unit.content)

        self.subsystems[subsystem_id] = SubsystemEntry(
            subsystem_id=subsystem_id,
            name=unit.title or "Unnamed Subsystem",
            domain=domain,
            description=unit.content[:300],
            containers=containers,
            upstream=upstream_deps,
            dependent_on=downstream_deps,
            data_stores=data_stores,
            events=events,
            external_interfaces=external_interfaces,
            sla=sla_info.get('sla', ''),
            rto=sla_info.get('rto', ''),
            rpo=sla_info.get('rpo', ''),
            adr_ids=self._extract_adr_ids(unit.content),
            rfc_ids=self._extract_rfc_ids(unit.content),
            source_uri=unit.source_file,
            source_lines=f"{unit.line_start}-{unit.line_end}",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tags="|".join(unit.tags) if unit.tags else ""
        )

    def _extract_research(self, unit: AtomicUnit):
        """
        Extract research entries using deterministic rules.

        Patterns from specification:
        - Block detection: Hypothesis|Goal|Question, Method|Protocol, Dataset|Sample
        - Results|Findings, Benchmark|Throughput|Latency, Limitations, Recommendation
        - Interview/UX: Participant, Quote, Task success rate, Severity, NPS, SUS
        - Confidence scoring from recency, source quality, sample size, method rigor
        """
        if not self._is_research_candidate(unit):
            return

        research_id = self._generate_research_id(unit)
        if research_id in self.research:
            return

        # Extract research details with structured content grabbing
        claim_summary = self._grab_research_section(unit.content, "Abstract|Goal|Hypothesis") or unit.content[:300]
        key_findings = self._grab_research_section(unit.content, "Findings|Results")
        method = self._grab_research_section(unit.content, "Method|Protocol|Methodology")
        limitations = self._grab_research_section(unit.content, "Limitations|Constraints")
        risks = self._grab_research_section(unit.content, "Risk|Risks")
        recommendation = self._grab_research_section(unit.content, "Recommendation|Recommendations")

        # Parse structured metrics
        key_metrics = self._parse_research_metrics(unit.content)

        # Determine research type
        research_type = self._classify_research_type(unit)

        # Extract temporal information
        date_collected = self._extract_research_date(unit.content)
        recency_days = self._calculate_recency_days(date_collected)

        # Extract quality indicators
        source_quality = self._assess_source_quality(unit)
        sample_size = self._extract_sample_size(unit.content)

        # Set TTL based on research type
        use_by = self._calculate_use_by_date(research_type, date_collected)

        self.research[research_id] = ResearchEntry(
            research_id=research_id,
            title=unit.title or "Untitled Research",
            research_type=research_type,
            status="Complete",
            author=self._extract_author(unit.content),
            date_collected=date_collected,
            recency_days=recency_days,
            source_quality=source_quality,
            sample_size=sample_size,
            method=method,
            claim_summary=claim_summary,
            key_findings=key_findings,
            key_metrics=json.dumps(key_metrics) if key_metrics else "",
            limitations=limitations,
            risks=risks,
            recommendation=recommendation,
            confidence=0.0,  # Will be computed later
            score_breakdown="",  # Will be computed later
            sources=self._extract_research_sources(unit.content),
            source_uri=unit.source_file,
            source_lines=f"{unit.line_start}-{unit.line_end}",
            use_by=use_by,
            tags="|".join(unit.tags) if unit.tags else ""
        )

    def _is_feature_candidate(self, unit: AtomicUnit) -> bool:
        """Check if atomic unit is a feature candidate using deterministic rules."""
        title_text = (unit.title or "") + " " + unit.content

        # Deterministic extraction rules from specification
        feature_patterns = [
            # Header patterns
            r'^#{1,3}\s*(Epic|Feature|Capability)\b',
            # Content patterns
            r'(?i)Acceptance Criteria|Given/When/Then|Story:',
            r'(?i)\b(epic|feature|capability|user story|acceptance criteria)\b',
            # Product space indicators
            r'(?i)\b(non.goals|out of scope|constraints|quality scenarios)\b'
        ]

        return any(re.search(pattern, title_text, re.MULTILINE) for pattern in feature_patterns)

    def _is_component_candidate(self, unit: AtomicUnit) -> bool:
        """Check if atomic unit is a component candidate using deterministic rules."""
        title_text = (unit.title or "") + " " + unit.content

        # Deterministic extraction rules from specification
        component_patterns = [
            # C4 PlantUML/Mermaid patterns - exact from specification
            r'\bComponent\(',
            r'\bContainer\(',
            r'\bRel\(',
            # Service class patterns in headings - exact from specification
            r'(?i)^#{1,6}.*\b(Service|Module|Package|Library|Adapter|Gateway)\b',
            # API/Interface patterns
            r'(?i)\b(API|interface|endpoint)\b',
            # Code fences naming packages or repos - from specification
            r'(?i)```.*\b(repo:|import|module)\b',
            r'(?i)\b(OpenAPI|gRPC|\.proto)\b'
        ]

        return any(re.search(pattern, title_text, re.MULTILINE) for pattern in component_patterns)

    def _is_subsystem_candidate(self, unit: AtomicUnit) -> bool:
        """Check if atomic unit is a subsystem candidate using deterministic rules."""
        title_text = (unit.title or "") + " " + unit.content

        # Deterministic extraction rules from specification
        subsystem_patterns = [
            # arc42 §5 patterns
            r'(?i)\b(subsystem|bounded context|domain)\b',
            # Building block view patterns
            r'^#{1,2}\s+\w+.*(?:System|Service|Module)',
            # Container enumeration patterns
            r'(?i)\b(containers?.*shared|building blocks?)\b',
            # Domain slice patterns
            r'(?i)\b(domain.*slice|context.*boundary)\b'
        ]

        return any(re.search(pattern, title_text, re.MULTILINE) for pattern in subsystem_patterns)

    def _is_research_candidate(self, unit: AtomicUnit) -> bool:
        """Check if atomic unit is a research candidate using deterministic rules."""
        title_text = (unit.title or "") + " " + unit.content

        # Research detection patterns from specification
        research_patterns = [
            # Spike patterns
            r'(?i)\bspike\b',
            # Research structure patterns
            r'(?i)\b(hypothesis|method|benchmark|findings|limitations|recommendation)\b',
            # Quantitative patterns
            r'(?i)\b(throughput|latency|p99|p95|tps|rps|benchmark)\b',
            # Qualitative patterns
            r'(?i)\b(interview|participant|user study|usability|UX)\b',
            # Standards patterns
            r'(?i)\b(RFC|ISO|standard|specification)\b'
        ]

        return any(re.search(pattern, title_text) for pattern in research_patterns)

    def _generate_feature_id(self, unit: AtomicUnit) -> str:
        """Generate stable feature ID: FEAT-#### pattern."""
        # Use hash of title + content for deterministic IDs
        content_hash = hashlib.sha1((unit.title + unit.content)[:80].encode()).hexdigest()[:4]
        return f"FEAT-{content_hash.upper()}"

    def _generate_component_id(self, unit: AtomicUnit) -> str:
        """Generate stable component ID: COMP-<slug> pattern."""
        if unit.title:
            slug = re.sub(r'[^a-z0-9]+', '-', unit.title.lower()).strip('-')[:20]
        else:
            slug = hashlib.sha1(unit.content[:64].encode()).hexdigest()[:8]
        return f"COMP-{slug}"

    def _generate_subsystem_id(self, unit: AtomicUnit) -> str:
        """Generate stable subsystem ID: SUB-<SLUG> pattern."""
        name = unit.title or "unnamed"
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:15]
        return f"SUB-{slug.upper()}"

    def _generate_research_id(self, unit: AtomicUnit) -> str:
        """Generate stable research ID: RS-<hash> pattern."""
        # Include source URI and line numbers for uniqueness
        unique_content = unit.source_file + str(unit.line_start) + str(unit.line_end)
        content_hash = str(abs(hash(unique_content)))[:8]
        return f"RS-{content_hash}"

    def _grab_research_section(self, content: str, section_keys: str) -> str:
        """Extract content from research sections using heading patterns."""
        pattern = rf'(?i)^#{1,6}.*({section_keys}).*?$([\s\S]*?)(?:^#{1,6}\s|\Z)'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(2).strip() if match else ""

    def _parse_research_metrics(self, content: str) -> List[Dict[str, Any]]:
        """Parse structured metrics from research content."""
        metrics = []

        # Pattern for performance metrics
        metric_patterns = [
            r'(?i)(p99|p95|p50|throughput|tps|rps|error[- ]rate|latency|cpu|memory)\s*[:=]\s*([\d\.]+)\s*(ms|s|rps|tps|%|mb|gb)?',
            r'(?i)(response time|processing time)\s*[:=]\s*([\d\.]+)\s*(ms|s)?'
        ]

        for pattern in metric_patterns:
            for match in re.finditer(pattern, content):
                metric = {
                    "name": match.group(1).lower(),
                    "value": float(match.group(2)),
                    "unit": (match.group(3) or "").lower()
                }
                metrics.append(metric)

        # Parse table-based metrics
        table_metrics = self._parse_table_metrics(content)
        metrics.extend(table_metrics)

        return metrics

    def _parse_table_metrics(self, content: str) -> List[Dict[str, Any]]:
        """Parse metrics from tables with latency/throughput headers."""
        metrics = []

        # Look for markdown tables with metric headers
        table_pattern = r'\|.*?(latency|throughput|error|p99|p95).*?\|'

        for table_match in re.finditer(table_pattern, content, re.IGNORECASE):
            table_text = table_match.group(0)

            # Extract numeric values from the table row
            value_pattern = r'\|\s*([\d\.]+)\s*(ms|s|rps|tps|%)?'
            for value_match in re.finditer(value_pattern, table_text):
                metric = {
                    "name": "table_metric",
                    "value": float(value_match.group(1)),
                    "unit": (value_match.group(2) or "").lower(),
                    "context": "table"
                }
                metrics.append(metric)

        return metrics

    def _classify_research_type(self, unit: AtomicUnit) -> str:
        """Classify research type from content."""
        content = (unit.title or "") + " " + unit.content

        type_patterns = {
            'Tech Spike': r'(?i)\bspike\b',
            'Benchmark': r'(?i)\b(benchmark|performance|throughput|latency)\b',
            'User Interview': r'(?i)\b(interview|participant|user study|usability)\b',
            'Competitor': r'(?i)\b(competitor|competitive|market analysis)\b',
            'Market': r'(?i)\b(market|industry|trend)\b',
            'Standards/Regulatory': r'(?i)\b(RFC|ISO|standard|specification|regulatory)\b'
        }

        for research_type, pattern in type_patterns.items():
            if re.search(pattern, content):
                return research_type

        return "Tech Spike"  # Default

    def _extract_research_date(self, content: str) -> str:
        """Extract research collection date."""
        date_patterns = [
            r'(?i)date collected:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            r'(?i)conducted on:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            r'([0-9]{4}-[0-9]{2}-[0-9]{2})'  # Any date format
        ]

        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return datetime.now().strftime('%Y-%m-%d')  # Default to today

    def _calculate_recency_days(self, date_collected: str) -> int:
        """Calculate days since research was collected."""
        try:
            collected_date = datetime.strptime(date_collected, '%Y-%m-%d')
            return (datetime.now() - collected_date).days
        except:
            return 0

    def _assess_source_quality(self, unit: AtomicUnit) -> str:
        """Assess source quality using heuristics."""
        content = (unit.title or "") + " " + unit.content + " " + unit.source_file

        # High quality indicators
        high_quality_patterns = [
            r'(?i)\b(primary data|reproducible|peer.reviewed|RFC|ISO)\b',
            r'(?i)\b(benchmark|rigorous|controlled)\b'
        ]

        # Low quality indicators
        low_quality_patterns = [
            r'(?i)\b(vendor|marketing|blog|anecdote)\b',
            r'(?i)\b(unverified|rumor|speculation)\b'
        ]

        if any(re.search(pattern, content) for pattern in high_quality_patterns):
            return "High"
        elif any(re.search(pattern, content) for pattern in low_quality_patterns):
            return "Low"
        else:
            return "Medium"

    def _extract_sample_size(self, content: str) -> str:
        """Extract sample size information."""
        sample_patterns = [
            r'(?i)sample size:?\s*([0-9,]+)',
            r'(?i)participants?:?\s*([0-9,]+)',
            r'(?i)n\s*=\s*([0-9,]+)'
        ]

        for pattern in sample_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return ""

    def _extract_author(self, content: str) -> str:
        """Extract research author."""
        author_patterns = [
            r'(?i)author:?\s*([^\n]+)',
            r'(?i)conducted by:?\s*([^\n]+)',
            r'(?i)researcher:?\s*([^\n]+)'
        ]

        for pattern in author_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_research_sources(self, content: str) -> str:
        """Extract research sources and references."""
        source_patterns = [
            r'https?://[^\s\n)]+',
            r'(?i)source:?\s*([^\n]+)',
            r'(?i)reference:?\s*([^\n]+)'
        ]

        sources = set()
        for pattern in source_patterns:
            matches = re.findall(pattern, content)
            sources.update([s.strip() for s in matches if s.strip()])

        return "; ".join(list(sources)[:3])

    def _calculate_use_by_date(self, research_type: str, date_collected: str) -> str:
        """Calculate use-by date based on research type TTL."""
        try:
            collected_date = datetime.strptime(date_collected, '%Y-%m-%d')
            ttl_days = self.research_ttl.get(research_type, 180)
            use_by_date = collected_date + timedelta(days=ttl_days)
            return use_by_date.strftime('%Y-%m-%d')
        except:
            return ""

    def _compute_research_confidence(self):
        """Compute confidence scores for research entries."""
        print("📊 Computing research confidence scores...")

        for research in self.research.values():
            scores = {}

            # Recency score (newer = higher)
            if research.recency_days <= 30:
                scores['recency'] = 1.0
            elif research.recency_days <= 90:
                scores['recency'] = 0.8
            elif research.recency_days <= 180:
                scores['recency'] = 0.6
            else:
                scores['recency'] = 0.3

            # Quality score
            quality_scores = {'High': 1.0, 'Medium': 0.7, 'Low': 0.4}
            scores['quality'] = quality_scores.get(research.source_quality, 0.5)

            # Sample score (based on sample size)
            if research.sample_size:
                try:
                    size = int(research.sample_size.replace(',', ''))
                    if size >= 100:
                        scores['sample'] = 1.0
                    elif size >= 50:
                        scores['sample'] = 0.8
                    elif size >= 10:
                        scores['sample'] = 0.6
                    else:
                        scores['sample'] = 0.4
                except:
                    scores['sample'] = 0.5
            else:
                scores['sample'] = 0.5

            # Method score (based on rigor indicators)
            method_indicators = ['reproducible', 'controlled', 'benchmark', 'protocol']
            method_score = 0.5  # Base score
            for indicator in method_indicators:
                if indicator in research.method.lower():
                    method_score += 0.1
            scores['method'] = min(method_score, 1.0)

            # Compute weighted confidence
            confidence = sum(
                scores[key] * self.quality_weights[key]
                for key in scores
            )

            research.confidence = round(confidence, 2)
            research.score_breakdown = "|".join([
                f"{key}:{scores[key]:.1f}" for key in scores
            ])

    def _generate_evidence_links(self):
        """Generate evidence links between research and other entities."""
        print("🔗 Generating evidence links...")

        for research in self.research.values():
            # Link to ADRs (supports/contradicts)
            for feature in self.features.values():
                if self._should_link_research_to_entity(research, feature, 'feature'):
                    relation = self._determine_relation(research, feature)
                    if relation:
                        self.evidence_links.append(EvidenceLink(
                            from_id=research.research_id,
                            from_type="Research",
                            to_id=feature.feature_id,
                            to_type="Feature",
                            relation=relation,
                            rationale=self._generate_link_rationale(research, feature, relation),
                            confidence=research.confidence
                        ))

            # Link to Components
            for component in self.components.values():
                if self._should_link_research_to_entity(research, component, 'component'):
                    relation = self._determine_relation(research, component)
                    if relation:
                        self.evidence_links.append(EvidenceLink(
                            from_id=research.research_id,
                            from_type="Research",
                            to_id=component.component_id,
                            to_type="Component",
                            relation=relation,
                            rationale=self._generate_link_rationale(research, component, relation),
                            confidence=research.confidence
                        ))

    def _should_link_research_to_entity(self, research: ResearchEntry, entity: Any, entity_type: str) -> bool:
        """Determine if research should be linked to entity."""
        research_content = research.claim_summary + " " + research.key_findings

        if entity_type == 'feature':
            entity_content = entity.title + " " + entity.description
        elif entity_type == 'component':
            entity_content = entity.name + " " + entity.purpose
        else:
            return False

        # Simple keyword overlap check - in production use semantic similarity
        research_words = set(research_content.lower().split())
        entity_words = set(entity_content.lower().split())

        overlap = len(research_words & entity_words)
        return overlap >= 2  # At least 2 words in common

    def _determine_relation(self, research: ResearchEntry, entity: Any) -> Optional[str]:
        """Determine the relation type between research and entity."""
        research_content = research.recommendation + " " + research.key_findings

        # Look for supporting evidence
        if re.search(r'(?i)\b(supports?|confirms?|validates?|proves?)\b', research_content):
            return "supports"

        # Look for contradicting evidence
        if re.search(r'(?i)\b(contradicts?|disproves?|conflicts?|fails?)\b', research_content):
            return "contradicts"

        # Look for risk indicators
        if re.search(r'(?i)\b(risks?|threatens?|compromises?)\b', research_content):
            return "risks"

        # Default to informs
        return "informs"

    def _generate_link_rationale(self, research: ResearchEntry, entity: Any, relation: str) -> str:
        """Generate rationale for evidence link."""
        if relation == "supports":
            return f"Research shows {research.research_type.lower()} supports implementation"
        elif relation == "contradicts":
            return f"Research findings contradict assumptions"
        elif relation == "risks":
            return f"Research identifies risks for implementation"
        else:
            return f"Research provides relevant context"

    # ... (continuing with existing extraction methods from previous implementation)

    def _classify_feature_type(self, unit: AtomicUnit) -> str:
        """Classify feature type from content."""
        content = (unit.title or "") + " " + unit.content

        if re.search(r'(?i)\bepic\b', content):
            return "Epic"
        elif re.search(r'(?i)\bcapability\b', content):
            return "Capability"
        elif re.search(r'(?i)\buser story\b', content):
            return "User Story"
        else:
            return "Feature"

    def _extract_acceptance_criteria(self, content: str) -> str:
        """Extract acceptance criteria using multiple patterns."""
        criteria_patterns = [
            r'(?i)acceptance criteria:?\s*\n(.*?)(?=\n\n|\n#+|$)',
            r'(?i)given\s+.*when\s+.*then\s+.*',
            r'(?i)scenario:?\s*(.*?)(?=\n\n|\n#+|$)',
            r'(?i)criteria:?\s*\n(.*?)(?=\n\n|\n#+|$)'
        ]

        for pattern in criteria_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                result = match.group(1 if match.groups() else 0).strip()
                return result[:500] if result else ""
        return ""

    def _extract_non_goals(self, content: str) -> str:
        """Extract non-goals and out-of-scope items."""
        non_goal_patterns = [
            r'(?i)non[- ]goals?:?\s*\n(.*?)(?=\n\n|\n#+|$)',
            r'(?i)out of scope:?\s*\n(.*?)(?=\n\n|\n#+|$)',
            r'(?i)not included:?\s*\n(.*?)(?=\n\n|\n#+|$)'
        ]

        for pattern in non_goal_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()[:300]
        return ""

    def _extract_priority(self, content: str) -> str:
        """Extract priority information."""
        priority_patterns = [
            r'(?i)priority:?\s*(high|medium|low|critical)',
            r'(?i)(p0|p1|p2|p3|p4)\b',
            r'(?i)(critical|high|medium|low)\s+priority'
        ]

        for pattern in priority_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).title()
        return ""

    def _extract_risk_level(self, content: str) -> str:
        """Extract risk assessment."""
        risk_patterns = [
            r'(?i)risk:?\s*(high|medium|low)',
            r'(?i)(high|medium|low)\s+risk',
            r'(?i)risk level:?\s*(high|medium|low)'
        ]

        for pattern in risk_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).title()
        return ""

    def _extract_level_of_effort(self, content: str) -> str:
        """Extract level of effort estimation."""
        effort_patterns = [
            r'(?i)effort:?\s*(small|medium|large|xl)',
            r'(?i)complexity:?\s*(low|medium|high)',
            r'(?i)(t-shirt size|size):?\s*(xs|s|m|l|xl)'
        ]

        for pattern in effort_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).title()
        return ""

    def _extract_story_points(self, content: str) -> int:
        """Extract story points if present."""
        story_patterns = [
            r'(?i)story points?:?\s*(\d+)',
            r'(?i)points?:?\s*(\d+)',
            r'(?i)sp:?\s*(\d+)'
        ]

        for pattern in story_patterns:
            match = re.search(pattern, content)
            if match:
                return int(match.group(1))
        return 0

    def _extract_target_release(self, content: str) -> str:
        """Extract target release information."""
        release_patterns = [
            r'(?i)target release:?\s*([^\n]+)',
            r'(?i)release:?\s*(\d{4}\.\d+)',
            r'(?i)version:?\s*(\d+\.\d+)'
        ]

        for pattern in release_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_public_interfaces(self, content: str) -> str:
        """Extract public interfaces with detailed patterns."""
        interface_patterns = [
            r'(?i)(REST|GraphQL|gRPC)\s+([^\n]+)',
            r'(?i)API:?\s*([^\n]+)',
            r'(?i)interface:?\s*([^\n]+)',
            r'(?i)endpoint:?\s*([^\n]+)',
            # OpenAPI patterns
            r'(?i)openapi:?\s*([^\n]+)',
            r'(?i)swagger:?\s*([^\n]+)'
        ]

        interfaces = []
        for pattern in interface_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    interfaces.append(f"{match[0]}: {match[1]}")
                else:
                    interfaces.append(match)

        return "; ".join(interfaces[:3])

    def _extract_component_dependencies(self, content: str) -> str:
        """Extract component dependencies with improved patterns."""
        dependency_patterns = [
            r'(?i)depends on:?\s*([^\n]+)',
            r'(?i)dependencies:?\s*([^\n]+)',
            r'(?i)requires:?\s*([^\n]+)',
            # Component ID references - exact specification format
            r'\bCOMP-[A-Z0-9-]+\b',
            # Service references
            r'(?i)calls?\s+([A-Za-z][A-Za-z0-9_-]*Service)',
            r'(?i)uses?\s+([A-Za-z][A-Za-z0-9_-]*(?:API|Client))',
            # Code fence dependencies - from specification
            r'(?i)import\s+([A-Za-z][A-Za-z0-9_.-]*)',
            r'(?i)repo:\s*([^\n\s]+)'
        ]

        deps = set()
        for pattern in dependency_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str) and match.strip():
                    # Clean up common dependency formats
                    clean_dep = match.strip().rstrip(',;')
                    if clean_dep:
                        deps.add(clean_dep)

        return ", ".join(list(deps)[:5])

    def _extract_tech_stack(self, content: str) -> Dict[str, str]:
        """Extract technology stack with comprehensive patterns."""
        tech_patterns = {
            'tech': r'(?i)\b(Python|Java|Go|Rust|JavaScript|TypeScript|C\+\+|C#|Ruby|PHP|Scala|Kotlin)\b',
            'stack': r'(?i)\b(FastAPI|Spring|Express|Django|Flask|React|Vue|Angular|Next\.js|Gin|Echo|ASP\.NET)\b'
        }

        result = {}
        for key, pattern in tech_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                # Take first match, could extend to take all
                result[key] = matches[0]

        return result

    def _extract_repo_info(self, content: str) -> str:
        """Extract repository information."""
        repo_patterns = [
            r'(?i)repo:?\s*([^\s\n]+)',
            r'(?i)repository:?\s*([^\s\n]+)',
            r'(?i)git:?\s*([^\s\n]+)',
            r'https?://github\.com/[^\s\n)]+',
            r'git@[^\s\n):]+'
        ]

        for pattern in repo_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1 if match.groups() else 0).strip()
        return ""

    def _extract_sli_metrics(self, content: str) -> str:
        """Extract SLI metrics information."""
        sli_patterns = [
            r'(?i)sli:?\s*([^\n]+)',
            r'(?i)metrics:?\s*([^\n]+)',
            r'(?i)(req_rate|error_rate|latency|p99|p95|p50)',
            r'(?i)(requests/second|errors/minute|ms|response time)'
        ]

        metrics = set()
        for pattern in sli_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    metrics.add(match.strip())

        return ", ".join(list(metrics)[:3])

    def _extract_security_notes(self, content: str) -> str:
        """Extract security-related information."""
        security_patterns = [
            r'(?i)security:?\s*([^\n]+)',
            r'(?i)(STRIDE|threat model|JWT|mTLS|OAuth)',
            r'(?i)(authentication|authorization|encryption)',
            r'(?i)security notes?:?\s*([^\n]+)'
        ]

        security_info = set()
        for pattern in security_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    security_info.update([m for m in match if m])
                elif isinstance(match, str):
                    security_info.add(match.strip())

        return "; ".join(list(security_info)[:3])

    def _extract_data_owned(self, content: str) -> str:
        """Extract data ownership information."""
        data_patterns = [
            r'(?i)data owned:?\s*([^\n]+)',
            r'(?i)owns:?\s*([^\n]+)',
            r'(?i)manages:?\s*([^\n]+)',
            r'(?i)(table|collection|database):?\s*([^\n]+)'
        ]

        data_items = set()
        for pattern in data_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    data_items.add(f"{match[0]}: {match[1]}" if match[1] else match[0])
                elif isinstance(match, str):
                    data_items.add(match.strip())

        return ", ".join(list(data_items)[:3])

    def _extract_containers(self, content: str) -> str:
        """Extract containers with enhanced patterns."""
        container_patterns = [
            r'Container\(["\']([^"\']+)["\']',
            r'(?i)containers?:?\s*([^\n]+)',
            r'(?i)services?:?\s*([^\n]+)',
            r'(?i)microservices?:?\s*([^\n]+)'
        ]

        containers = set()
        for pattern in container_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.strip():
                    containers.add(match.strip())

        return ", ".join(list(containers)[:5])

    def _extract_data_stores(self, content: str) -> str:
        """Extract data stores with comprehensive patterns."""
        datastore_patterns = [
            r'(?i)(database|db|storage|cache|queue):?\s*([^\n]+)',
            r'(?i)\b(postgres|postgresql|mysql|redis|kafka|s3|dynamodb|mongodb|elasticsearch)\b',
            r'(?i)data store:?\s*([^\n]+)'
        ]

        stores = set()
        for pattern in datastore_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    stores.add(match[1] if match[1] else match[0])
                else:
                    stores.add(match)

        return ", ".join(list(stores)[:4])

    def _extract_events(self, content: str) -> str:
        """Extract event information."""
        event_patterns = [
            r'(?i)events?:?\s*([^\n]+)',
            r'(?i)publishes?:?\s*([^\n]+)',
            r'(?i)emits?:?\s*([^\n]+)',
            r'Event:\s*([^\n]+)'
        ]

        events = set()
        for pattern in event_patterns:
            matches = re.findall(pattern, content)
            events.update([m.strip() for m in matches if m.strip()])

        return ", ".join(list(events)[:3])

    def _extract_external_interfaces(self, content: str) -> str:
        """Extract external interfaces."""
        interface_patterns = [
            r'(?i)external interface:?\s*([^\n]+)',
            r'(?i)public:?\s*(REST|GraphQL|gRPC)',
            r'(?i)exposes?:?\s*([^\n]+)'
        ]

        interfaces = set()
        for pattern in interface_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    interfaces.add(match.strip())

        return "; ".join(list(interfaces)[:3])

    def _extract_domain(self, content: str) -> str:
        """Extract domain information."""
        domain_patterns = [
            r'(?i)domain:?\s*([^\n]+)',
            r'(?i)bounded context:?\s*([^\n]+)',
            r'(?i)business domain:?\s*([^\n]+)'
        ]

        for pattern in domain_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_upstream_dependencies(self, content: str) -> str:
        """Extract upstream dependencies."""
        upstream_patterns = [
            r'(?i)upstream:?\s*([^\n]+)',
            r'(?i)depends on:?\s*([^\n]+)',
            r'(?i)calls:?\s*([^\n]+)'
        ]

        deps = set()
        for pattern in upstream_patterns:
            matches = re.findall(pattern, content)
            deps.update([m.strip() for m in matches if m.strip()])

        return ", ".join(list(deps)[:3])

    def _extract_downstream_dependencies(self, content: str) -> str:
        """Extract downstream dependencies."""
        downstream_patterns = [
            r'(?i)dependent on:?\s*([^\n]+)',
            r'(?i)called by:?\s*([^\n]+)',
            r'(?i)used by:?\s*([^\n]+)'
        ]

        deps = set()
        for pattern in downstream_patterns:
            matches = re.findall(pattern, content)
            deps.update([m.strip() for m in matches if m.strip()])

        return ", ".join(list(deps)[:3])

    def _extract_sla_info(self, content: str) -> Dict[str, str]:
        """Extract SLA, RTO, RPO information."""
        sla_patterns = {
            'sla': r'(?i)sla:?\s*([0-9.]+%?)',
            'rto': r'(?i)rto:?\s*([0-9]+[hm]?)',
            'rpo': r'(?i)rpo:?\s*([0-9]+[hm]?)'
        }

        result = {}
        for key, pattern in sla_patterns.items():
            match = re.search(pattern, content)
            if match:
                result[key] = match.group(1)

        return result

    def _extract_rfc_ids(self, content: str) -> str:
        """Extract RFC IDs with enhanced patterns."""
        rfc_patterns = [
            r'\bRFC-\d+\b',
            r'\bRFC\s*#?\s*(\d+)\b'
        ]

        rfcs = set()
        for pattern in rfc_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    rfcs.add(f"RFC-{match}" if not match.startswith('RFC') else match)
                else:
                    rfcs.add(match)

        return "|".join(list(rfcs)[:5])

    def _extract_adr_ids(self, content: str) -> str:
        """Extract ADR IDs with enhanced patterns."""
        adr_patterns = [
            r'\bADR-\d+\b',
            r'\bADR\s*#?\s*(\d+)\b'
        ]

        adrs = set()
        for pattern in adr_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str):
                    adrs.add(f"ADR-{match}" if not match.startswith('ADR') else match)
                else:
                    adrs.add(match)

        return "|".join(list(adrs)[:5])

    def _deduplicate_entries(self):
        """
        Deduplicate registry entries using similarity thresholds.

        Uses cosine similarity > 0.90 and Jaccard distance for near-duplicates.
        Prefers newer + more specific entries (with tables, interfaces present).
        """
        print(f"🔍 Deduplicating with thresholds: cosine ≥{self.cosine_threshold}, jaccard ≥{self.jaccard_threshold}")

        # Simplified deduplication - in production would use embeddings
        # For now, dedupe by exact title matches and similar content

        # Features deduplication
        self._dedupe_by_similarity(self.features, lambda f: f.title + " " + f.description)

        # Components deduplication
        self._dedupe_by_similarity(self.components, lambda c: c.name + " " + c.purpose)

        # Subsystems deduplication
        self._dedupe_by_similarity(self.subsystems, lambda s: s.name + " " + s.description)

        # Research deduplication - prefer more rigorous studies
        self._dedupe_research_by_quality()

    def _dedupe_by_similarity(self, registry: Dict[str, Any], content_extractor):
        """Helper to deduplicate registry by content similarity."""
        to_remove = set()
        items = list(registry.items())

        for i, (id1, item1) in enumerate(items):
            if id1 in to_remove:
                continue

            content1 = content_extractor(item1).lower()

            for j, (id2, item2) in enumerate(items[i+1:], i+1):
                if id2 in to_remove:
                    continue

                content2 = content_extractor(item2).lower()

                # Simple similarity check - in practice use cosine similarity
                if self._simple_similarity(content1, content2) > 0.8:
                    # Prefer more specific entry (longer content, more details)
                    specificity1 = len(content1) + len(item1.source_uri)
                    specificity2 = len(content2) + len(item2.source_uri)

                    if specificity1 >= specificity2:
                        to_remove.add(id2)
                    else:
                        to_remove.add(id1)
                        break

        # Remove duplicates
        for id_to_remove in to_remove:
            if id_to_remove in registry:
                del registry[id_to_remove]

    def _dedupe_research_by_quality(self):
        """Deduplicate research entries preferring higher quality studies."""
        to_remove = set()
        research_items = list(self.research.items())

        for i, (id1, research1) in enumerate(research_items):
            if id1 in to_remove:
                continue

            content1 = research1.claim_summary.lower()

            for j, (id2, research2) in enumerate(research_items[i+1:], i+1):
                if id2 in to_remove:
                    continue

                content2 = research2.claim_summary.lower()

                if self._simple_similarity(content1, content2) > 0.7:
                    # Prefer higher quality research
                    quality1 = self._calculate_research_quality_score(research1)
                    quality2 = self._calculate_research_quality_score(research2)

                    if quality1 >= quality2:
                        to_remove.add(id2)
                    else:
                        to_remove.add(id1)
                        break

        for id_to_remove in to_remove:
            if id_to_remove in self.research:
                del self.research[id_to_remove]

    def _calculate_research_quality_score(self, research: ResearchEntry) -> float:
        """Calculate quality score for research deduplication."""
        score = 0.0

        # Quality assessment
        quality_scores = {'High': 1.0, 'Medium': 0.7, 'Low': 0.4}
        score += quality_scores.get(research.source_quality, 0.5) * 0.3

        # Recency (newer is better)
        if research.recency_days <= 30:
            score += 0.3
        elif research.recency_days <= 90:
            score += 0.2
        else:
            score += 0.1

        # Method rigor
        if 'reproducible' in research.method.lower():
            score += 0.2
        elif 'controlled' in research.method.lower():
            score += 0.15
        else:
            score += 0.05

        # Sample size
        if research.sample_size:
            try:
                size = int(research.sample_size.replace(',', ''))
                if size >= 100:
                    score += 0.2
                elif size >= 10:
                    score += 0.1
                else:
                    score += 0.05
            except:
                score += 0.05

        return score

    def _simple_similarity(self, content1: str, content2: str) -> float:
        """Simple similarity measure - replace with cosine similarity in production."""
        words1 = set(content1.split())
        words2 = set(content2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _enrich_relationships(self):
        """Enrich entries with cross-references and relationships."""
        print("🔗 Enriching cross-references between registries...")

        # Link components to subsystems
        for component in self.components.values():
            for subsystem in self.subsystems.values():
                # Check if component is mentioned in subsystem containers
                if component.name.lower() in subsystem.containers.lower():
                    component.subsystem_id = subsystem.subsystem_id
                    continue

                # Check for domain/context matches
                component_words = set(component.name.lower().split())
                subsystem_words = set(subsystem.name.lower().split())

                if len(component_words & subsystem_words) >= 1:
                    component.subsystem_id = subsystem.subsystem_id
                    break

        # Link features to components and subsystems
        for feature in self.features.values():
            matching_components = []
            matching_subsystems = []

            feature_words = set(feature.title.lower().split())

            for component in self.components.values():
                component_words = set(component.name.lower().split())
                if len(feature_words & component_words) >= 1:
                    matching_components.append(component.component_id)

            for subsystem in self.subsystems.values():
                subsystem_words = set(subsystem.name.lower().split())
                if len(feature_words & subsystem_words) >= 1:
                    matching_subsystems.append(subsystem.subsystem_id)

            feature.component_ids = "|".join(matching_components[:3])
            feature.subsystem_ids = "|".join(matching_subsystems[:2])

    def _enrich_ownership(self):
        """Enrich with ownership information from CODEOWNERS or metadata."""
        print("👥 Enriching ownership information...")

        # This would read from CODEOWNERS file or repo metadata
        # For now, placeholder implementation
        default_owners = {
            'features': 'Product Team',
            'components': 'Engineering Team',
            'subsystems': 'Architecture Team'
        }

        for feature in self.features.values():
            if not feature.owner:
                feature.owner = default_owners['features']

        for component in self.components.values():
            if not component.owner:
                component.owner = default_owners['components']

        for subsystem in self.subsystems.values():
            if not subsystem.owner:
                subsystem.owner = default_owners['subsystems']

    def _enrich_slo_stubs(self):
        """Enrich with SLO stubs from SRE docs."""
        print("📊 Enriching SLO stubs...")

        # Default SLO templates
        default_slos = {
            'availability': '99.9%',
            'latency': 'P50<50ms; P99<300ms'
        }

        for component in self.components.values():
            if not component.slo_availability:
                component.slo_availability = default_slos['availability']
            if not component.slo_latency:
                component.slo_latency = default_slos['latency']

    def _write_registries(self) -> Dict[str, int]:
        """Write all registries to TSV files following canonical schema."""
        counts = {}

        # Write features.tsv
        if self.features:
            features_file = self.output_dir / "features.tsv"
            with features_file.open('w', newline='', encoding='utf-8') as f:
                fieldnames = list(FeatureEntry.__dataclass_fields__.keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()

                for feature in self.features.values():
                    writer.writerow(asdict(feature))

            counts['features'] = len(self.features)
            print(f"📋 Written {counts['features']} features to features.tsv")
        else:
            counts['features'] = 0

        # Write components.tsv
        if self.components:
            components_file = self.output_dir / "components.tsv"
            with components_file.open('w', newline='', encoding='utf-8') as f:
                fieldnames = list(ComponentEntry.__dataclass_fields__.keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()

                for component in self.components.values():
                    writer.writerow(asdict(component))

            counts['components'] = len(self.components)
            print(f"🏗️  Written {counts['components']} components to components.tsv")
        else:
            counts['components'] = 0

        # Write subsystems.tsv
        if self.subsystems:
            subsystems_file = self.output_dir / "subsystems.tsv"
            with subsystems_file.open('w', newline='', encoding='utf-8') as f:
                fieldnames = list(SubsystemEntry.__dataclass_fields__.keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()

                for subsystem in self.subsystems.values():
                    writer.writerow(asdict(subsystem))

            counts['subsystems'] = len(self.subsystems)
            print(f"🏛️  Written {counts['subsystems']} subsystems to subsystems.tsv")
        else:
            counts['subsystems'] = 0

        # Write research.tsv
        if self.research:
            research_file = self.output_dir / "research.tsv"
            with research_file.open('w', newline='', encoding='utf-8') as f:
                fieldnames = list(ResearchEntry.__dataclass_fields__.keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()

                for research in self.research.values():
                    writer.writerow(asdict(research))

            counts['research'] = len(self.research)
            print(f"🧪 Written {counts['research']} research entries to research.tsv")
        else:
            counts['research'] = 0

        # Write evidence_links.tsv
        if self.evidence_links:
            evidence_file = self.output_dir / "evidence_links.tsv"
            with evidence_file.open('w', newline='', encoding='utf-8') as f:
                fieldnames = ['from_id', 'from_type', 'to_id', 'to_type', 'relation', 'rationale', 'confidence']
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()

                for link in self.evidence_links:
                    writer.writerow(asdict(link))

            counts['evidence_links'] = len(self.evidence_links)
            print(f"🔗 Written {counts['evidence_links']} evidence links to evidence_links.tsv")
        else:
            counts['evidence_links'] = 0

        return counts

    def write_sqlite_db(self, db_path: Path) -> bool:
        """
        Write registries to SQLite database using canonical DDL from specification.

        This is optional - TSV files are the primary output for git versioning.
        SQLite provides relational queries and views for analysis.
        """
        try:
            import sqlite3

            print(f"🗄️ Writing SQLite database to {db_path}")

            # Create database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create tables using exact DDL from specification
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subsystems (
                  subsystem_id TEXT PRIMARY KEY,
                  name TEXT, domain TEXT, description TEXT,
                  containers TEXT, owning_team TEXT,
                  upstream TEXT, dependent_on TEXT,
                  data_stores TEXT, events TEXT,
                  rto TEXT, rpo TEXT, sla TEXT,
                  external_interfaces TEXT, security_posture TEXT,
                  owner TEXT, adr_ids TEXT, rfc_ids TEXT,
                  source_uri TEXT, source_lines TEXT,
                  created_at TEXT, updated_at TEXT, tags TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS components (
                  component_id TEXT PRIMARY KEY,
                  name TEXT, subsystem_id TEXT REFERENCES subsystems(subsystem_id),
                  container_name TEXT, purpose TEXT, public_interfaces TEXT,
                  data_owned TEXT, dependencies TEXT, tech TEXT, stack TEXT,
                  repo TEXT, owner TEXT,
                  slo_availability TEXT, slo_latency TEXT,
                  sli_metrics TEXT, alerts TEXT,
                  security_notes TEXT, threat_model_refs TEXT,
                  adr_ids TEXT, rfc_ids TEXT,
                  source_uri TEXT, source_lines TEXT,
                  created_at TEXT, updated_at TEXT, tags TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS features (
                  feature_id TEXT PRIMARY KEY,
                  title TEXT, type TEXT, status TEXT, priority TEXT,
                  owner TEXT, subsystem_ids TEXT, component_ids TEXT,
                  description TEXT, acceptance_criteria TEXT, non_goals TEXT,
                  risk TEXT, level_of_effort TEXT, story_points INTEGER,
                  target_release TEXT, rfc_ids TEXT, adr_ids TEXT,
                  source_uri TEXT, source_lines TEXT,
                  created_at TEXT, updated_at TEXT, tags TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research (
                  research_id TEXT PRIMARY KEY,
                  title TEXT, research_type TEXT, status TEXT,
                  author TEXT, date_collected TEXT, recency_days INTEGER,
                  source_quality TEXT, sample_size TEXT, method TEXT,
                  claim_summary TEXT, key_findings TEXT, key_metrics TEXT,
                  limitations TEXT, risks TEXT, recommendation TEXT,
                  confidence REAL, score_breakdown TEXT,
                  sources TEXT, source_uri TEXT, source_lines TEXT,
                  use_by TEXT, tags TEXT
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evidence_links (
                  from_id TEXT, from_type TEXT,
                  to_id TEXT, to_type TEXT,
                  relation TEXT, rationale TEXT, confidence REAL,
                  PRIMARY KEY (from_id, to_id, relation)
                );
            """)

            # Insert data
            for subsystem in self.subsystems.values():
                cursor.execute("""
                    INSERT OR REPLACE INTO subsystems VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, tuple(asdict(subsystem).values()))

            for component in self.components.values():
                cursor.execute("""
                    INSERT OR REPLACE INTO components VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, tuple(asdict(component).values()))

            for feature in self.features.values():
                cursor.execute("""
                    INSERT OR REPLACE INTO features VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, tuple(asdict(feature).values()))

            for research in self.research.values():
                cursor.execute("""
                    INSERT OR REPLACE INTO research VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, tuple(asdict(research).values()))

            for link in self.evidence_links:
                cursor.execute("""
                    INSERT OR REPLACE INTO evidence_links VALUES (?, ?, ?, ?, ?, ?, ?)
                """, tuple(asdict(link).values()))

            # Create helpful views from specification
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS features_by_subsystem AS
                SELECT f.feature_id, f.title, c.component_id, c.name, c.subsystem_id
                FROM features f
                JOIN components c
                  ON ','||f.component_ids||',' LIKE '%,'||c.component_id||',%'
                ORDER BY f.priority;
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS component_dependencies AS
                SELECT
                    c.component_id AS from_id,
                    TRIM(dep.value) AS to_id
                FROM components c,
                     json_each('["' || REPLACE(c.dependencies, ',', '","') || '"]') dep
                WHERE c.dependencies IS NOT NULL AND c.dependencies != '';
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS slo_coverage_report AS
                SELECT component_id, name, subsystem_id,
                       CASE WHEN slo_availability IS NULL OR slo_availability = '' THEN 'Missing' ELSE 'Present' END as availability_slo,
                       CASE WHEN slo_latency IS NULL OR slo_latency = '' THEN 'Missing' ELSE 'Present' END as latency_slo
                FROM components;
            """)

            # Additional helpful views
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS research_recent_high_confidence AS
                SELECT research_id, title, research_type, recency_days, source_quality, confidence
                FROM research
                WHERE (recency_days IS NOT NULL AND recency_days <= 90)
                  AND (confidence IS NOT NULL AND confidence >= 0.8)
                ORDER BY recency_days ASC, confidence DESC;
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS components_security_gaps AS
                SELECT component_id, name, subsystem_id, security_notes, threat_model_refs
                FROM components
                WHERE (security_notes IS NULL OR security_notes = '')
                   OR (threat_model_refs IS NULL OR threat_model_refs = '');
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS components_missing_slos AS
                SELECT component_id, name, subsystem_id
                FROM components
                WHERE (slo_availability IS NULL OR slo_availability = '')
                   OR (slo_latency IS NULL OR slo_latency = '');
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS evidence_density_by_component AS
                SELECT c.component_id, c.name, COUNT(el.to_id) AS evidence_incoming
                FROM components c
                LEFT JOIN evidence_links el ON el.to_id = c.component_id
                GROUP BY c.component_id, c.name
                ORDER BY evidence_incoming DESC;
            """)

            cursor.execute("""
                CREATE VIEW IF NOT EXISTS evidence_density_by_feature AS
                SELECT f.feature_id, f.title, COUNT(el.to_id) AS evidence_incoming
                FROM features f
                LEFT JOIN evidence_links el ON el.to_id = f.feature_id
                GROUP BY f.feature_id, f.title
                ORDER BY evidence_incoming DESC;
            """)

            # Helpful indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_subsystem ON components(subsystem_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_name ON components(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_features_priority ON features(priority);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_confidence ON research(confidence);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_recency ON research(recency_days);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_from ON evidence_links(from_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_to ON evidence_links(to_id);")

            conn.commit()
            conn.close()

            print(f"✅ SQLite database written with {len(self.features)} features, {len(self.components)} components, {len(self.subsystems)} subsystems, {len(self.research)} research entries")
            return True

        except Exception as e:
            print(f"❌ Error writing SQLite database: {e}")
            return False
