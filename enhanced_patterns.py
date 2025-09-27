"""
Enhanced Pattern System for DocuXtractor - Natural Language Matching

Extends the rigid patterns to match natural writing style in documentation.
"""

import re
from typing import Dict, Pattern

# Enhanced patterns that match natural language
ENHANCED_EXTRACTION_PATTERNS: Dict[str, str] = {
    # Features - match natural descriptions
    "features": r"(?:this\s+feature|the\s+feature|feature\s+(?:provides|enables|supports|allows)|(?:provides|enables|supports|allows|includes)\s+(?:the\s+)?(?:ability\s+to|capability\s+to|functionality\s+(?:for|to))|(?:key|main|primary)\s+features?)\s*[:\-]?\s*([^.\n]{10,100})",

    # Components - match system descriptions
    "components": r"(?:this\s+component|the\s+component|component\s+(?:handles|manages|provides)|(?:service|module|class|system)\s+(?:handles|manages|provides|is\s+responsible\s+for)|(?:the\s+)?(?:main|primary|key)\s+(?:service|module|component))\s*[:\-]?\s*([^.\n]{10,100})",

    # Subsystems - match architectural descriptions
    "subsystems": r"(?:this\s+subsystem|the\s+subsystem|subsystem\s+(?:handles|manages)|(?:domain|layer|system)\s+(?:handles|manages|is\s+responsible\s+for)|architecture\s+(?:consists\s+of|includes))\s*[:\-]?\s*([^.\n]{10,100})",

    # Requirements - match natural requirement language
    "requirements": r"(?:(?:we|the\s+system|application)\s+(?:must|should|shall|will|needs?\s+to)|(?:requirement|req)\s*[:\-]?\s*(?:the\s+system|we)\s+(?:must|should|shall)|(?:it\s+is\s+)?required\s+(?:that|to))\s*([^.\n]{10,150})",

    # Decisions - match decision language
    "decisions": r"(?:(?:we|the\s+team|I)\s+(?:decided|chose|selected|opted)\s+(?:to|for)|decision\s*[:\-]?\s*(?:to|we)|(?:after\s+(?:consideration|analysis)|based\s+on)\s+.*?(?:decided|chose|selected))\s*([^.\n]{10,150})",

    # Constraints - match limitation language
    "constraints": r"(?:(?:constraint|limitation|restriction)\s*[:\-]?\s*|(?:limited\s+by|constrained\s+by|restricted\s+to)|(?:cannot|can't|unable\s+to|won't|will\s+not)\s+(?:support|handle|allow))\s*([^.\n]{10,100})",

    # Patterns - match approach descriptions
    "patterns": r"(?:(?:pattern|approach|strategy|method|technique)\s*[:\-]?\s*(?:we\s+use|using|used|involves)|(?:we|the\s+system)\s+(?:use|uses|follow|follows)\s+(?:the\s+)?(?:pattern|approach|strategy|method))\s*([^.\n]{10,150})",

    # Technologies - match tech stack mentions
    "technologies": r"(?:(?:using|with|built\s+(?:with|on)|powered\s+by|based\s+on)\s+([A-Za-z0-9.-]+(?:\s+[A-Za-z0-9.-]+)*)|(?:technology|framework|library|database|stack)\s*[:\-]?\s*([A-Za-z0-9.-]+(?:\s+[A-Za-z0-9.-]+)*))",

    # Interfaces - match API/interface descriptions
    "interfaces": r"(?:(?:interface|API|endpoint)\s*[:\-]?\s*|(?:exposes?|provides?)\s+(?:an?\s+)?(?:interface|API|endpoint)\s*(?:for|to)?)\s*([^.\n]{10,100})",

    # Processes - match workflow descriptions
    "processes": r"(?:(?:process|workflow|procedure|steps?)\s*[:\-]?\s*|(?:the\s+)?(?:following\s+)?(?:process|workflow|procedure|steps?)\s+(?:involves?|includes?|are|is))\s*([^.\n]{10,200})",

    # Metrics - match measurement descriptions
    "metrics": r"(?:(?:metric|measure|KPI|target|goal)\s*[:\-]?\s*|(?:performance|speed|throughput|latency|response\s+time|availability|uptime)\s*[:\-]?\s*([0-9]+[^\.\n]*)|(?:must\s+(?:handle|support|achieve))\s*([0-9]+[^\.\n]*))"
}

# Domain-specific patterns for ADHD/Dopemux context
DOPEMUX_PATTERNS: Dict[str, str] = {
    "adhd_features": r"(?:ADHD|neurodivergent|executive\s+function|attention|focus|cognitive\s+load)\s+(?:accommodation|feature|support|optimization|friendly)\s*[:\-]?\s*([^.\n]{10,150})",

    "mcp_components": r"(?:MCP|Model\s+Context\s+Protocol)\s+(?:server|client|tool|integration|component)\s*[:\-]?\s*([^.\n]{10,100})",

    "session_patterns": r"(?:session|context)\s+(?:management|persistence|restoration|saving)\s*[:\-]?\s*([^.\n]{10,150})",

    "task_features": r"(?:task|todo|work)\s+(?:decomposition|breakdown|management|tracking)\s*[:\-]?\s*([^.\n]{10,150})"
}

# Combine all patterns
ALL_ENHANCED_PATTERNS = {**ENHANCED_EXTRACTION_PATTERNS, **DOPEMUX_PATTERNS}

# Compiled patterns for performance
COMPILED_ENHANCED_PATTERNS: Dict[str, Pattern[str]] = {
    name: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    for name, pattern in ALL_ENHANCED_PATTERNS.items()
}

def enhanced_calculate_confidence(entity_text: str, content: str) -> float:
    """Enhanced confidence calculation for natural language patterns."""
    base_confidence = 0.75  # Higher base for natural language

    # Boost for ADHD/domain-specific content
    domain_keywords = ["adhd", "neurodivergent", "mcp", "dopemux", "claude", "session", "task"]
    if any(keyword in content.lower() for keyword in domain_keywords):
        base_confidence += 0.15

    # Boost for important context keywords
    important_keywords = ["important", "critical", "key", "main", "core", "essential"]
    if any(keyword in content.lower() for keyword in important_keywords):
        base_confidence += 0.1

    # Boost for architectural terms
    arch_keywords = ["architecture", "design", "system", "component", "interface", "api"]
    if any(keyword in content.lower() for keyword in arch_keywords):
        base_confidence += 0.05

    # Length-based confidence (natural language tends to be longer)
    if len(entity_text) > 30:
        base_confidence += 0.05
    if len(entity_text) > 50:
        base_confidence += 0.05

    return max(0.1, min(1.0, base_confidence))