"""
Multi-angle document extraction for Dopemux analysis.

Extracts features, components, subsystems, and research patterns from
atomic document units with comprehensive evidence linking.
"""

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class EntityPattern:
    """Pattern definition for entity extraction."""

    name: str
    regex: str
    description: str
    examples: List[str]


@dataclass
class AtomicUnit:
    """Normalized atomic unit of documentation."""

    id: str
    content: str
    title: str
    source_file: str
    doc_type: str
    metadata: Dict[str, Any]


class MultiAngleExtractor:
    """
    Multi-angle entity extraction for comprehensive codebase analysis.

    Implements 11 distinct extraction patterns to capture features,
    components, architectural decisions, and research insights.
    """

    def __init__(self, output_dir: Path):
        """Initialize extractor with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize extraction patterns
        self._init_patterns()

        # Storage for extracted entities
        self.registries = {
            "features": [],
            "components": [],
            "subsystems": [],
            "research": [],
            "evidence_links": [],
        }

    def _init_patterns(self):
        """Initialize all extraction patterns."""
        self.patterns = {
            "features": EntityPattern(
                name="Feature",
                regex=r"(?:feature|capability|functionality):\s*([^.\n]+)",
                description="User-facing features and capabilities",
                examples=["Authentication", "File Upload", "Real-time Chat"],
            ),
            "components": EntityPattern(
                name="Component",
                regex=r"(?:component|module|class|service):\s*([^.\n]+)",
                description="Technical components and modules",
                examples=["UserService", "DatabaseConnector", "APIRouter"],
            ),
            "subsystems": EntityPattern(
                name="Subsystem",
                regex=r"(?:subsystem|system|domain|layer):\s*([^.\n]+)",
                description="Architectural subsystems and domains",
                examples=["Authentication System", "Data Layer", "API Gateway"],
            ),
            "requirements": EntityPattern(
                name="Requirement",
                regex=r"(?:requirement|must|should|shall):\s*([^.\n]+)",
                description="Functional and non-functional requirements",
                examples=[
                    "Must support 1000+ concurrent users",
                    "Should respond within 200ms",
                ],
            ),
            "decisions": EntityPattern(
                name="Decision",
                regex=r"(?:decision|chosen|selected|opted):\s*([^.\n]+)",
                description="Architectural and design decisions",
                examples=[
                    "Chose PostgreSQL over MongoDB",
                    "Selected React for frontend",
                ],
            ),
            "constraints": EntityPattern(
                name="Constraint",
                regex=r"(?:constraint|limitation|restriction):\s*([^.\n]+)",
                description="Technical and business constraints",
                examples=["Budget limited to $10k", "Must use existing infrastructure"],
            ),
            "patterns": EntityPattern(
                name="Pattern",
                regex=r"(?:pattern|approach|strategy|method):\s*([^.\n]+)",
                description="Design patterns and approaches",
                examples=["Factory Pattern", "Event Sourcing", "Microservices"],
            ),
            "technologies": EntityPattern(
                name="Technology",
                regex=r"(?:using|with|technology|framework|library):\s*([A-Za-z0-9.-]+)",
                description="Technologies, frameworks, and libraries",
                examples=["React", "PostgreSQL", "Docker", "AWS"],
            ),
            "interfaces": EntityPattern(
                name="Interface",
                regex=r"(?:interface|API|endpoint):\s*([^.\n]+)",
                description="System interfaces and APIs",
                examples=["/api/v1/users", "UserRepository", "EventBus"],
            ),
            "processes": EntityPattern(
                name="Process",
                regex=r"(?:process|workflow|procedure|steps):\s*([^.\n]+)",
                description="Business processes and workflows",
                examples=["User Registration", "Order Processing", "CI/CD Pipeline"],
            ),
            "metrics": EntityPattern(
                name="Metric",
                regex=r"(?:metric|measure|KPI|target):\s*([^.\n]+)",
                description="Performance metrics and targets",
                examples=["Response time < 200ms", "99.9% uptime", "10k DAU"],
            ),
        }

    def extract_all_entities(
        self, atomic_units: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all entity types from atomic units.

        Args:
            atomic_units: List of normalized atomic units

        Returns:
            Dictionary containing all extracted registries
        """
        console.print("[bold blue]🔍 Starting multi-angle extraction...[/bold blue]")

        # Convert to AtomicUnit objects
        units = [
            AtomicUnit(**unit) if isinstance(unit, dict) else unit
            for unit in atomic_units
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Extract entities by pattern
            task = progress.add_task("Extracting entities...", total=len(self.patterns))

            for i, (pattern_name, pattern) in enumerate(self.patterns.items()):
                entities = self._extract_pattern(units, pattern)

                if pattern_name in ["features", "components", "subsystems"]:
                    self.registries[pattern_name] = entities
                else:
                    # Add to research registry
                    for entity in entities:
                        entity["entity_type"] = pattern_name
                    self.registries["research"].extend(entities)

                progress.update(
                    task,
                    description=f"Extracted {len(entities)} {pattern_name}",
                    completed=i + 1,
                )

            # Generate evidence links
            progress.add_task("Generating evidence links...", total=None)
            self._generate_evidence_links(units)

        # Save registries to files
        self._save_registries()

        # Display summary
        self._display_extraction_summary()

        return self.registries

    def _extract_pattern(
        self, units: List[AtomicUnit], pattern: EntityPattern
    ) -> List[Dict[str, Any]]:
        """Extract entities matching a specific pattern."""
        entities = []
        seen_entities = set()

        for unit in units:
            matches = re.finditer(
                pattern.regex, unit.content, re.IGNORECASE | re.MULTILINE
            )

            for match in matches:
                entity_text = match.group(1).strip()

                # Skip duplicates and too short/long entities
                if (
                    entity_text in seen_entities
                    or len(entity_text) < 3
                    or len(entity_text) > 200
                ):
                    continue

                seen_entities.add(entity_text)

                # Create entity record
                entity = {
                    "id": f"{pattern.name.lower()}_{len(entities)}",
                    "name": entity_text,
                    "description": self._generate_description(
                        entity_text, unit.content
                    ),
                    "source_file": unit.source_file,
                    "source_unit": unit.id,
                    "doc_type": unit.doc_type,
                    "confidence": self._calculate_confidence(entity_text, unit.content),
                    "context": self._extract_context(
                        unit.content, match.start(), match.end()
                    ),
                    "metadata": {
                        "pattern_type": pattern.name,
                        "extraction_method": "regex",
                        "file_path": unit.source_file,
                        "unit_title": unit.title,
                    },
                }

                entities.append(entity)

        return entities

    def _generate_description(self, entity_text: str, content: str) -> str:
        """Generate a description for an extracted entity."""
        # Extract surrounding sentences for context
        sentences = content.split(".")
        entity_sentence = None

        for sentence in sentences:
            if entity_text.lower() in sentence.lower():
                entity_sentence = sentence.strip()
                break

        if entity_sentence and len(entity_sentence) > len(entity_text) + 10:
            return entity_sentence[:200]  # Limit description length

        # Fallback to entity text
        return f"Extracted {entity_text} from documentation"

    def _calculate_confidence(self, entity_text: str, content: str) -> float:
        """Calculate confidence score for extracted entity."""
        base_confidence = 0.7

        # Boost confidence based on context
        if any(
            keyword in content.lower()
            for keyword in ["important", "critical", "key", "main"]
        ):
            base_confidence += 0.1

        # Boost if entity appears multiple times
        occurrence_count = content.lower().count(entity_text.lower())
        if occurrence_count > 1:
            base_confidence += min(0.2, occurrence_count * 0.05)

        # Penalize if entity is very short or generic
        if len(entity_text) < 5 or entity_text.lower() in [
            "test",
            "data",
            "info",
            "item",
        ]:
            base_confidence -= 0.2

        return max(0.1, min(1.0, base_confidence))

    def _extract_context(
        self, content: str, start: int, end: int, window: int = 100
    ) -> str:
        """Extract surrounding context for an entity match."""
        context_start = max(0, start - window)
        context_end = min(len(content), end + window)

        context = content[context_start:context_end]

        # Clean up context
        context = " ".join(context.split())  # Normalize whitespace
        if len(context) > 200:
            context = context[:197] + "..."

        return context

    def _generate_evidence_links(self, units: List[AtomicUnit]):
        """Generate evidence links between entities and their sources."""
        evidence_links = []

        # Link entities to atomic units
        for registry_name, entities in self.registries.items():
            if registry_name == "evidence_links":
                continue

            for entity in entities:
                # Find source unit
                source_unit = next(
                    (unit for unit in units if unit.id == entity.get("source_unit")),
                    None,
                )

                if source_unit:
                    link = {
                        "id": f"evidence_{len(evidence_links)}",
                        "entity_type": registry_name,
                        "entity_id": entity["id"],
                        "entity_name": entity["name"],
                        "source_type": "atomic_unit",
                        "source_id": source_unit.id,
                        "source_file": source_unit.source_file,
                        "link_type": "extraction_source",
                        "confidence": entity.get("confidence", 0.5),
                        "metadata": {
                            "extraction_method": entity.get("metadata", {}).get(
                                "extraction_method", "unknown"
                            ),
                            "doc_type": source_unit.doc_type,
                        },
                    }
                    evidence_links.append(link)

        # Cross-reference entities (find co-occurrences)
        self._create_cross_references(evidence_links)

        self.registries["evidence_links"] = evidence_links

    def _create_cross_references(self, evidence_links: List[Dict[str, Any]]):
        """Create cross-references between related entities."""
        # Group entities by source file
        file_entities = defaultdict(list)
        for link in evidence_links:
            file_entities[link["source_file"]].append(link)

        # Create co-occurrence links
        for file_path, file_links in file_entities.items():
            if len(file_links) < 2:
                continue

            for i, link1 in enumerate(file_links):
                for link2 in file_links[i + 1 :]:
                    # Create cross-reference
                    cross_ref = {
                        "id": f"cross_ref_{len(evidence_links)}",
                        "entity_type": "cross_reference",
                        "entity_id": f"{link1['entity_id']}_to_{link2['entity_id']}",
                        "entity_name": f"{link1['entity_name']} <-> {link2['entity_name']}",
                        "source_type": "file_cooccurrence",
                        "source_id": file_path,
                        "source_file": file_path,
                        "link_type": "co_occurrence",
                        "confidence": min(link1["confidence"], link2["confidence"])
                        * 0.8,
                        "metadata": {
                            "entity1_id": link1["entity_id"],
                            "entity1_type": link1["entity_type"],
                            "entity2_id": link2["entity_id"],
                            "entity2_type": link2["entity_type"],
                            "relationship": "co_occurrence",
                        },
                    }
                    evidence_links.append(cross_ref)

    def _save_registries(self):
        """Save all registries to TSV files."""
        registry_files = {
            "features": "features_registry.tsv",
            "components": "components_registry.tsv",
            "subsystems": "subsystems_registry.tsv",
            "research": "research_registry.tsv",
            "evidence_links": "evidence_links.tsv",
        }

        for registry_name, filename in registry_files.items():
            file_path = self.output_dir / filename
            entities = self.registries[registry_name]

            if not entities:
                continue

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                if entities:
                    writer = csv.DictWriter(
                        f, fieldnames=entities[0].keys(), delimiter="\t"
                    )
                    writer.writeheader()
                    writer.writerows(entities)

            console.print(
                f"[green]📁 Saved {len(entities)} {registry_name} to {filename}[/green]"
            )

    def _display_extraction_summary(self):
        """Display extraction summary with ADHD-friendly formatting."""
        from rich.table import Table

        table = Table(title="🔍 Entity Extraction Summary")
        table.add_column("Registry", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Status", style="yellow")

        for registry_name, entities in self.registries.items():
            count = len(entities)
            status = "✅" if count > 0 else "⚪"
            display_name = registry_name.replace("_", " ").title()
            table.add_row(display_name, str(count), status)

        console.print(table)

        # Encouraging feedback
        total_entities = sum(len(entities) for entities in self.registries.values())
        console.print(
            f"[bold green]🎉 Extracted {total_entities} total entities with full traceability![/bold green]"
        )
