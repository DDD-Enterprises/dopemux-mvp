"""
Design-First Prompting Detector - Enhancement E2

Detects substantial feature work that warrants formal design (ADR/RFC)
before implementation. Uses heuristics like file count, directory spread,
architecture keywords, and new service creation.

Part of F001 Enhancement E2: Design-First Prompting
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DesignFirstDetector:
    """
    Detect when uncommitted work warrants formal design (ADR/RFC).

    ADHD benefit: Reduces false-starts by encouraging upfront planning
    for substantial features. Prevents "dive in and discover complexity later"
    pattern that leads to abandoned work.
    """

    # Architecture/system keywords that suggest design needed
    ARCHITECTURE_KEYWORDS = [
        'architecture', 'system', 'core', 'engine',
        'orchestrator', 'coordinator', 'manager',
        'integration', 'bridge', 'gateway', 'adapter',
        'pipeline', 'workflow', 'strategy', 'framework'
    ]

    # New service/component indicators
    SERVICE_PATHS = [
        'services/', 'components/', 'modules/', 'packages/',
        'engines/', 'orchestrators/', 'coordinators/'
    ]

    def __init__(self, workspace: Path):
        """
        Initialize design-first detector.

        Args:
            workspace: Workspace path for file analysis
        """
        self.workspace = workspace

    def should_prompt_for_design(self, git_detection: Dict) -> Dict:
        """
        Determine if work warrants formal design (ADR/RFC).

        Args:
            git_detection: Detection result from GitWorkDetector

        Returns:
            {
                "should_prompt": bool,
                "confidence": float (0.0-1.0),
                "reasons": List[str],
                "heuristics_matched": List[str],
                "suggested_document_type": "ADR" | "RFC" | "Design Doc",
                "complexity_indicators": Dict
            }
        """
        try:
            files = git_detection.get("files", [])
            new_files = git_detection.get("new_files_created", [])

            if not files:
                return self._no_design_needed()

            reasons = []
            heuristics_matched = []
            confidence_score = 0.0

            # Heuristic 1: Significant code volume (5+ files)
            if len(files) >= 5:
                reasons.append(f"{len(files)} files modified - substantial change")
                heuristics_matched.append("significant_file_count")
                confidence_score += 0.3

            # Heuristic 2: Multiple directories (cross-cutting change)
            unique_dirs = set(Path(f).parent for f in files)
            if len(unique_dirs) >= 3:
                reasons.append(f"{len(unique_dirs)} directories affected - cross-cutting concern")
                heuristics_matched.append("multi_directory")
                confidence_score += 0.25

            # Heuristic 3: Architecture/core files
            files_str = ' '.join(files).lower()
            matched_keywords = [
                kw for kw in self.ARCHITECTURE_KEYWORDS
                if kw in files_str
            ]
            if matched_keywords:
                reasons.append(f"Architecture keywords detected: {', '.join(matched_keywords[:3])}")
                heuristics_matched.append("architecture_keywords")
                confidence_score += 0.35

            # Heuristic 4: New service or major component
            service_dirs_created = set()
            for file in new_files:
                for service_path in self.SERVICE_PATHS:
                    if service_path in file:
                        service_dirs_created.add(str(Path(file).parent))

            if len(service_dirs_created) >= 2:
                reasons.append(f"Creating new service/component structure: {len(service_dirs_created)} dirs")
                heuristics_matched.append("new_service_creation")
                confidence_score += 0.4

            # Heuristic 5: Database schema changes
            schema_files = [f for f in files if 'schema' in f.lower() or 'migration' in f.lower()]
            if schema_files:
                reasons.append(f"Database schema/migration changes detected")
                heuristics_matched.append("schema_changes")
                confidence_score += 0.3

            # Heuristic 6: API/interface changes
            api_files = [f for f in files if 'api' in f.lower() or 'interface' in f.lower() or 'contract' in f.lower()]
            if api_files:
                reasons.append("API/interface changes - affects contracts")
                heuristics_matched.append("api_changes")
                confidence_score += 0.25

            # Cap confidence at 1.0
            confidence_score = min(confidence_score, 1.0)

            # Decide if should prompt (threshold: 0.5)
            should_prompt = confidence_score >= 0.5

            # Suggest document type based on heuristics
            doc_type = self._suggest_document_type(heuristics_matched)

            # Complexity indicators for ADHD assessment
            complexity_indicators = {
                "file_count": len(files),
                "directory_count": len(unique_dirs),
                "new_dirs_created": len(service_dirs_created),
                "architecture_keywords_found": len(matched_keywords),
                "schema_changes": len(schema_files) > 0,
                "api_changes": len(api_files) > 0
            }

            result = {
                "should_prompt": should_prompt,
                "confidence": round(confidence_score, 2),
                "reasons": reasons,
                "heuristics_matched": heuristics_matched,
                "suggested_document_type": doc_type,
                "complexity_indicators": complexity_indicators
            }

            if should_prompt:
                logger.info(
                    f"🏗️ Design-first recommended (confidence: {confidence_score:.2f}): "
                    f"{', '.join(heuristics_matched)}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to detect design-first need: {e}")
            return self._no_design_needed()

    def _suggest_document_type(self, heuristics: List[str]) -> str:
        """
        Suggest ADR vs RFC vs Design Doc based on matched heuristics.

        ADR: Architectural decisions (system-level, cross-cutting)
        RFC: Request for Comments (API/interface changes, needs discussion)
        Design Doc: General design (new features, substantial changes)
        """
        # ADR for architectural and schema changes
        if any(h in heuristics for h in ['architecture_keywords', 'schema_changes', 'multi_directory']):
            return "ADR"

        # RFC for API changes and new services (need team input)
        if any(h in heuristics for h in ['api_changes', 'new_service_creation']):
            return "RFC"

        # Design Doc for everything else
        return "Design Doc"

    def _no_design_needed(self) -> Dict:
        """Return result indicating no design needed."""
        return {
            "should_prompt": False,
            "confidence": 0.0,
            "reasons": [],
            "heuristics_matched": [],
            "suggested_document_type": None,
            "complexity_indicators": {}
        }

    def format_design_prompt_message(self, detection_result: Dict, work_name: str) -> str:
        """
        Format the design-first prompting message.

        ADHD-optimized: Clear structure, actionable steps, explains WHY.

        Args:
            detection_result: Result from should_prompt_for_design
            work_name: Name of detected work

        Returns:
            Formatted message string
        """
        if not detection_result["should_prompt"]:
            return ""

        doc_type = detection_result["suggested_document_type"]
        confidence = detection_result["confidence"]
        reasons = detection_result["reasons"]

        lines = ["📐 DESIGN-FIRST RECOMMENDATION"]
        lines.append("─" * 45)
        lines.append("")
        lines.append(f"Work detected: '{work_name}'")
        lines.append(f"Confidence: {confidence:.0%} this needs design")
        lines.append("")

        # Why design is recommended
        lines.append("Why formal design helps:")
        for reason in reasons:
            lines.append(f"  • {reason}")
        lines.append("")

        # Suggested document type
        lines.append(f"📝 Suggested: Create {doc_type} first")
        lines.append("")

        # Document type explanation
        if doc_type == "ADR":
            lines.append("ADR (Architecture Decision Record):")
            lines.append("  → For architectural/system-level decisions")
            lines.append("  → Documents context, decision, consequences")
            lines.append("  → Template: docs/templates/adr-template.md")
        elif doc_type == "RFC":
            lines.append("RFC (Request for Comments):")
            lines.append("  → For API/interface changes needing discussion")
            lines.append("  → Gets team feedback before implementation")
            lines.append("  → Template: docs/templates/rfc-template.md")
        else:
            lines.append("Design Document:")
            lines.append("  → For substantial features and components")
            lines.append("  → Clarifies scope, approach, dependencies")
            lines.append("  → Template: docs/templates/design-doc-template.md")

        lines.append("")
        lines.append("💡 Benefits: Reduces false-starts, clarifies scope,")
        lines.append("   prevents mid-work complexity surprises")

        return "\n".join(lines)
