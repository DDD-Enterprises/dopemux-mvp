"""
Document builder for generating comprehensive documents using Jinja2 templates.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)


class DocumentBuilder:
    """
    Builds comprehensive documents from extracted fields using Jinja2 templates.

    Supports adaptive document generation with rich content organization
    and formatting.
    """

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the document builder with Jinja2 environment."""
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self._add_custom_filters()

        # Initialize templates
        self._initialize_templates()

    def _add_custom_filters(self):
        """Add custom Jinja2 filters for document generation."""

        def format_confidence(confidence: float) -> str:
            """Format confidence as percentage with icon."""
            percentage = confidence * 100
            if percentage >= 80:
                return f"🟢 {percentage:.0f}%"
            elif percentage >= 60:
                return f"🟡 {percentage:.0f}%"
            else:
                return f"🔴 {percentage:.0f}%"

        def format_priority(priority: str) -> str:
            """Format priority with appropriate icon."""
            priority_icons = {
                'critical': '🔴 Critical',
                'high': '🟠 High',
                'medium': '🟡 Medium',
                'low': '🟢 Low'
            }
            return priority_icons.get(priority.lower(), priority.title())

        def group_by_type(fields: List[Dict], field_key: str = 'field_type') -> Dict[str, List]:
            """Group fields by a specified key."""
            groups = {}
            for field in fields:
                key = field.get(field_key, 'unknown')
                if key not in groups:
                    groups[key] = []
                groups[key].append(field)
            return groups

        def format_stakeholders(stakeholders: List[str]) -> str:
            """Format stakeholder list with proper grammar."""
            if not stakeholders:
                return "TBD"
            elif len(stakeholders) == 1:
                return stakeholders[0]
            elif len(stakeholders) == 2:
                return f"{stakeholders[0]} and {stakeholders[1]}"
            else:
                return f"{', '.join(stakeholders[:-1])}, and {stakeholders[-1]}"

        def format_date(timestamp: Optional[str]) -> str:
            """Format timestamp for document display."""
            if not timestamp:
                return datetime.now().strftime("%Y-%m-%d")
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d")
            except:
                return datetime.now().strftime("%Y-%m-%d")

        def sort_by_confidence(fields: List[Dict]) -> List[Dict]:
            """Sort fields by confidence score descending."""
            return sorted(fields, key=lambda x: x.get('confidence', 0), reverse=True)

        def extract_content(fields: List[Dict], max_length: int = 200) -> str:
            """Extract and concatenate content from fields with length limit."""
            content_parts = []
            total_length = 0

            for field in sorted(fields, key=lambda x: x.get('confidence', 0), reverse=True):
                content = field.get('content', '').strip()
                if content and total_length + len(content) <= max_length:
                    content_parts.append(content)
                    total_length += len(content)

            return '. '.join(content_parts)

        # Register filters
        self.env.filters['format_confidence'] = format_confidence
        self.env.filters['format_priority'] = format_priority
        self.env.filters['group_by_type'] = group_by_type
        self.env.filters['format_stakeholders'] = format_stakeholders
        self.env.filters['format_date'] = format_date
        self.env.filters['sort_by_confidence'] = sort_by_confidence
        self.env.filters['extract_content'] = extract_content

    def _initialize_templates(self):
        """Initialize default templates if they don't exist."""
        templates_to_create = [
            'prd.md.j2',
            'adr.md.j2',
            'design_spec.md.j2',
            'business_plan.md.j2',
            'implementation_plan.md.j2',
            'architecture_doc.md.j2',
            'security_assessment.md.j2',
            'risk_register.md.j2',
            'stakeholder_map.md.j2',
            'research_summary.md.j2'
        ]

        for template_name in templates_to_create:
            template_path = self.template_dir / template_name
            if not template_path.exists():
                logger.info(f"Creating default template: {template_name}")
                self._create_default_template(template_name)

    def build_documents(self, extracted_fields: List[Dict[str, Any]],
                       selected_templates: List[str],
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Build documents using selected templates and extracted fields.

        Args:
            extracted_fields: List of extracted field dictionaries
            selected_templates: List of template names to generate
            metadata: Optional metadata for document generation

        Returns:
            Dictionary mapping document names to generated content
        """
        logger.info(f"Building {len(selected_templates)} documents from {len(extracted_fields)} fields")

        # Prepare context data
        context = self._prepare_context(extracted_fields, metadata)

        documents = {}

        for template_name in selected_templates:
            try:
                content = self._build_single_document(template_name, context)
                documents[template_name] = content
                logger.info(f"Generated {template_name} document ({len(content)} chars)")
            except Exception as e:
                logger.error(f"Failed to generate {template_name}: {e}")
                documents[template_name] = f"Error generating document: {e}"

        return documents

    def _prepare_context(self, extracted_fields: List[Dict[str, Any]],
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare context data for template rendering."""
        # Group fields by type
        fields_by_type = {}
        for field in extracted_fields:
            field_type = field.get('field_type', 'unknown')
            if field_type not in fields_by_type:
                fields_by_type[field_type] = []
            fields_by_type[field_type].append(field)

        # Calculate statistics
        total_fields = len(extracted_fields)
        avg_confidence = sum(f.get('confidence', 0) for f in extracted_fields) / total_fields if total_fields > 0 else 0

        # Extract unique stakeholders
        all_stakeholders = set()
        for field in extracted_fields:
            all_stakeholders.update(field.get('stakeholders', []))

        # Prepare context
        context = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime("%Y-%m-%d"),
            'fields': extracted_fields,
            'fields_by_type': fields_by_type,
            'total_fields': total_fields,
            'avg_confidence': avg_confidence,
            'unique_stakeholders': sorted(list(all_stakeholders)),
            'metadata': metadata or {},

            # Convenient field accessors
            'decisions': fields_by_type.get('decision', []),
            'features': fields_by_type.get('feature', []),
            'research': fields_by_type.get('research', []),
            'constraints': fields_by_type.get('constraint', []),
            'stakeholders': fields_by_type.get('stakeholder', []),
            'risks': fields_by_type.get('risk', []),
            'security': fields_by_type.get('security', []),
        }

        return context

    def _build_single_document(self, template_name: str, context: Dict[str, Any]) -> str:
        """Build a single document using the specified template."""
        template_filename = f"{template_name}.md.j2"

        try:
            template = self.env.get_template(template_filename)
            content = template.render(**context)
            return content.strip()
        except Exception as e:
            logger.error(f"Error rendering template {template_filename}: {e}")
            return self._generate_fallback_document(template_name, context)

    def _generate_fallback_document(self, template_name: str, context: Dict[str, Any]) -> str:
        """Generate a fallback document when template rendering fails."""
        title = template_name.replace('_', ' ').title()

        fallback = f"""# {title}

**Generated:** {context['date']}
**Total Fields:** {context['total_fields']}
**Average Confidence:** {context['avg_confidence']:.2f}

## Error

Template rendering failed for {template_name}. This is a fallback document.

## Extracted Information

"""

        # Add basic field information
        for field_type, fields in context['fields_by_type'].items():
            if fields:
                fallback += f"\n### {field_type.title()} ({len(fields)} items)\n\n"
                for field in fields[:5]:  # Limit to first 5 items
                    content = field.get('content', 'No content')
                    confidence = field.get('confidence', 0)
                    fallback += f"- **{content[:100]}{'...' if len(content) > 100 else ''}** (Confidence: {confidence:.2f})\n"

        return fallback

    def _create_default_template(self, template_name: str):
        """Create a default template file."""
        template_path = self.template_dir / template_name
        document_type = template_name.replace('.md.j2', '')

        # Template content based on document type
        templates = {
            'prd': self._get_prd_template(),
            'adr': self._get_adr_template(),
            'design_spec': self._get_design_spec_template(),
            'business_plan': self._get_business_plan_template(),
            'implementation_plan': self._get_implementation_plan_template(),
            'architecture_doc': self._get_architecture_doc_template(),
            'security_assessment': self._get_security_assessment_template(),
            'risk_register': self._get_risk_register_template(),
            'stakeholder_map': self._get_stakeholder_map_template(),
            'research_summary': self._get_research_summary_template()
        }

        content = templates.get(document_type, self._get_generic_template(document_type))

        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _get_prd_template(self) -> str:
        """Get PRD template content."""
        return '''# Product Requirements Document

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}
**Stakeholders:** {{ unique_stakeholders | format_stakeholders }}

## Executive Summary

{{ features | extract_content(300) }}

## Features & Requirements

{% for feature in features | sort_by_confidence %}
### {{ loop.index }}. {{ feature.content | title }}

**Confidence:** {{ feature.confidence | format_confidence }}
**Stakeholders:** {{ feature.stakeholders | format_stakeholders }}

{% if feature.metadata.user_story.persona %}
**User Story:** As a {{ feature.metadata.user_story.persona }}, I want {{ feature.metadata.user_story.goal }} so that {{ feature.metadata.user_story.benefit }}.
{% endif %}

{% if feature.metadata.acceptance_criteria %}
**Acceptance Criteria:**
{% for criteria in feature.metadata.acceptance_criteria %}
- {{ criteria }}
{% endfor %}
{% endif %}

{% if feature.metadata.priority %}
**Priority:** {{ feature.metadata.priority | format_priority }}
{% endif %}

---

{% endfor %}

## Constraints

{% if constraints %}
{% for constraint in constraints | sort_by_confidence %}
- **{{ constraint.content }}** ({{ constraint.metadata.constraint_type | title }}, {{ constraint.metadata.severity | format_priority }})
{% endfor %}
{% else %}
No constraints identified.
{% endif %}

## Research & Data

{% if research %}
{% for item in research | sort_by_confidence %}
- {{ item.content }} {% if item.metadata.source %}(Source: {{ item.metadata.source }}){% endif %}
{% endfor %}
{% else %}
No research data available.
{% endif %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_adr_template(self) -> str:
        """Get ADR template content."""
        return '''# Architecture Decision Record

**Date:** {{ date }}
**Status:** Proposed
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Context

{% if decisions %}
{{ decisions | extract_content(400) }}
{% else %}
No specific context identified from conversation analysis.
{% endif %}

## Decisions

{% for decision in decisions | sort_by_confidence %}
### {{ loop.index }}. {{ decision.content }}

**Type:** {{ decision.metadata.decision_type | title }}
**Urgency:** {{ decision.metadata.urgency | format_priority }}
**Scope:** {{ decision.metadata.scope | title }}

{% if decision.metadata.rationale %}
**Rationale:**
{% for reason in decision.metadata.rationale %}
- {{ reason }}
{% endfor %}
{% endif %}

{% if decision.metadata.alternatives %}
**Alternatives Considered:**
{% for alt in decision.metadata.alternatives %}
- {{ alt }}
{% endfor %}
{% endif %}

---

{% endfor %}

## Consequences

### Positive
{% for decision in decisions %}
{% if decision.metadata.rationale %}
{% for reason in decision.metadata.rationale %}
- {{ reason }}
{% endfor %}
{% endif %}
{% endfor %}

### Negative
{% for risk in risks %}
- {{ risk.content }}
{% endfor %}

## Compliance

{% for constraint in constraints %}
{% if constraint.metadata.constraint_type == 'regulatory' %}
- {{ constraint.content }}
{% endif %}
{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_design_spec_template(self) -> str:
        """Get Design Specification template content."""
        return '''# Technical Design Specification

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}
**Stakeholders:** {{ unique_stakeholders | format_stakeholders }}

## Overview

This document outlines the technical design based on conversation analysis.

## System Architecture

{% for decision in decisions %}
{% if 'architecture' in decision.content.lower() or 'system' in decision.content.lower() %}
### {{ decision.content }}

**Rationale:** {{ decision.metadata.rationale | join(', ') }}
{% if decision.metadata.dependencies %}
**Dependencies:** {{ decision.metadata.dependencies | join(', ') }}
{% endif %}

{% endif %}
{% endfor %}

## Components

{% for feature in features %}
### {{ feature.content | title }}

{% if feature.metadata.technical_requirements %}
**Technical Requirements:**
{% for req in feature.metadata.technical_requirements %}
- {{ req }}
{% endfor %}
{% endif %}

{% if feature.metadata.dependencies %}
**Dependencies:**
{% for dep in feature.metadata.dependencies %}
- {{ dep }}
{% endfor %}
{% endif %}

---

{% endfor %}

## Security Considerations

{% for sec in security | sort_by_confidence %}
### {{ sec.content }}

**Type:** {{ sec.metadata.security_type | title }}
**Threat Level:** {{ sec.metadata.threat_level | format_priority }}

{% if sec.metadata.compliance_framework %}
**Compliance:** {{ sec.metadata.compliance_framework | join(', ') }}
{% endif %}

---

{% endfor %}

## Constraints & Limitations

{% for constraint in constraints %}
- **{{ constraint.content }}** ({{ constraint.metadata.constraint_type | title }})
{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_business_plan_template(self) -> str:
        """Get Business Plan template content."""
        return '''# Business Plan

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Executive Summary

{{ features | extract_content(300) }}

## Market Opportunity

{% for research in research %}
{% if 'market' in research.content.lower() or 'opportunity' in research.content.lower() %}
- {{ research.content }}
{% endif %}
{% endfor %}

## Product Features

{% for feature in features %}
### {{ feature.content | title }}

{% if feature.metadata.business_value %}
**Business Value:**
{% for value in feature.metadata.business_value %}
- {{ value }}
{% endfor %}
{% endif %}

**Priority:** {{ feature.metadata.priority | format_priority }}

{% endfor %}

## Stakeholder Analysis

{% for stakeholder in stakeholders %}
### {{ stakeholder.content }}

**Role:** {{ stakeholder.metadata.role }}
**Influence:** {{ stakeholder.metadata.influence_level | format_priority }}

{% if stakeholder.metadata.responsibilities %}
**Responsibilities:**
{% for resp in stakeholder.metadata.responsibilities %}
- {{ resp }}
{% endfor %}
{% endif %}

{% endfor %}

## Risk Assessment

{% for risk in risks %}
### {{ risk.content }}

**Type:** {{ risk.metadata.risk_type | title }}
**Probability:** {{ risk.metadata.probability | title }}
**Impact:** {{ risk.metadata.impact_level | format_priority }}

{% if risk.metadata.mitigation %}
**Mitigation:**
{% for mit in risk.metadata.mitigation %}
- {{ mit }}
{% endfor %}
{% endif %}

{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_implementation_plan_template(self) -> str:
        """Get Implementation Plan template content."""
        return '''# Implementation Plan

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Overview

Implementation plan derived from conversation analysis.

## Implementation Phases

{% for feature in features %}
### Phase {{ loop.index }}: {{ feature.content | title }}

**Complexity:** {{ feature.metadata.complexity | title }}
**Priority:** {{ feature.metadata.priority | format_priority }}

{% if feature.metadata.dependencies %}
**Prerequisites:**
{% for dep in feature.metadata.dependencies %}
- {{ dep }}
{% endfor %}
{% endif %}

{% if feature.metadata.acceptance_criteria %}
**Success Criteria:**
{% for criteria in feature.metadata.acceptance_criteria %}
- {{ criteria }}
{% endfor %}
{% endif %}

---

{% endfor %}

## Technical Decisions

{% for decision in decisions %}
### {{ decision.content }}

**Implementation Impact:** {{ decision.metadata.scope | title }}
**Dependencies:** {{ decision.metadata.dependencies | join(', ') }}

{% endfor %}

## Risk Mitigation

{% for risk in risks %}
### {{ risk.content }}

**Severity:** {{ risk.metadata.severity | format_priority }}
**Owner:** {{ risk.metadata.owner }}

{% if risk.metadata.mitigation %}
**Mitigation Plan:**
{% for mit in risk.metadata.mitigation %}
- {{ mit }}
{% endfor %}
{% endif %}

{% endfor %}

## Resource Requirements

{% for constraint in constraints %}
{% if constraint.metadata.constraint_type in ['resource', 'financial', 'temporal'] %}
- **{{ constraint.metadata.constraint_type | title }}:** {{ constraint.content }}
{% endif %}
{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_architecture_doc_template(self) -> str:
        """Get Architecture Document template content."""
        return '''# Architecture Document

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Architectural Decisions

{% for decision in decisions %}
{% if decision.metadata.decision_type == 'technical' %}
### {{ decision.content }}

**Rationale:**
{% for reason in decision.metadata.rationale %}
- {{ reason }}
{% endfor %}

**Alternatives:**
{% for alt in decision.metadata.alternatives %}
- {{ alt }}
{% endfor %}

---

{% endif %}
{% endfor %}

## System Constraints

{% for constraint in constraints %}
{% if constraint.metadata.constraint_type == 'technical' %}
### {{ constraint.content }}

**Impact:** {{ constraint.metadata.impact }}
**Severity:** {{ constraint.metadata.severity | format_priority }}

{% endif %}
{% endfor %}

## Security Architecture

{% for sec in security %}
### {{ sec.content }}

**Type:** {{ sec.metadata.security_type | title }}
**Implementation:** {{ sec.metadata.implementation | items | join(', ') }}

{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_security_assessment_template(self) -> str:
        """Get Security Assessment template content."""
        return '''# Security Assessment

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Security Requirements

{% for sec in security | sort_by_confidence %}
### {{ sec.content }}

**Type:** {{ sec.metadata.security_type | title }}
**Threat Level:** {{ sec.metadata.threat_level | format_priority }}
**Data Classification:** {{ sec.metadata.data_classification | title }}

{% if sec.metadata.compliance_framework %}
**Compliance Requirements:** {{ sec.metadata.compliance_framework | join(', ') }}
{% endif %}

---

{% endfor %}

## Risk Analysis

{% for risk in risks %}
{% if risk.metadata.risk_type == 'security' %}
### {{ risk.content }}

**Probability:** {{ risk.metadata.probability | title }}
**Impact:** {{ risk.metadata.impact_level | format_priority }}
**Severity:** {{ risk.metadata.severity | format_priority }}

{% endif %}
{% endfor %}

## Compliance Framework

{% for constraint in constraints %}
{% if constraint.metadata.constraint_type == 'regulatory' %}
- {{ constraint.content }}
{% endif %}
{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_risk_register_template(self) -> str:
        """Get Risk Register template content."""
        return '''# Risk Register

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Risk Summary

| Risk | Type | Probability | Impact | Severity | Owner |
|------|------|-------------|--------|----------|-------|
{% for risk in risks | sort_by_confidence %}
| {{ risk.content[:50] }}... | {{ risk.metadata.risk_type | title }} | {{ risk.metadata.probability | title }} | {{ risk.metadata.impact_level | title }} | {{ risk.metadata.severity | format_priority }} | {{ risk.metadata.owner }} |
{% endfor %}

## Detailed Risk Analysis

{% for risk in risks | sort_by_confidence %}
### Risk {{ loop.index }}: {{ risk.content }}

**Category:** {{ risk.metadata.risk_type | title }}
**Probability:** {{ risk.metadata.probability | title }}
**Impact Level:** {{ risk.metadata.impact_level | format_priority }}
**Overall Severity:** {{ risk.metadata.severity | format_priority }}
**Risk Owner:** {{ risk.metadata.owner }}

{% if risk.metadata.mitigation %}
**Mitigation Strategies:**
{% for mit in risk.metadata.mitigation %}
- {{ mit }}
{% endfor %}
{% endif %}

**Timeline:** {{ risk.metadata.timeline }}

---

{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_stakeholder_map_template(self) -> str:
        """Get Stakeholder Map template content."""
        return '''# Stakeholder Map

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Stakeholder Overview

{% for stakeholder in stakeholders | sort_by_confidence %}
### {{ stakeholder.content }}

**Type:** {{ stakeholder.metadata.stakeholder_type | title }}
**Role:** {{ stakeholder.metadata.role }}
**Department:** {{ stakeholder.metadata.department }}
**Influence Level:** {{ stakeholder.metadata.influence_level | format_priority }}

{% if stakeholder.metadata.responsibilities %}
**Responsibilities:**
{% for resp in stakeholder.metadata.responsibilities %}
- {{ resp }}
{% endfor %}
{% endif %}

{% if stakeholder.metadata.contact_info %}
**Contact Information:**
{% for key, value in stakeholder.metadata.contact_info.items() %}
- {{ key | title }}: {{ value }}
{% endfor %}
{% endif %}

---

{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_research_summary_template(self) -> str:
        """Get Research Summary template content."""
        return '''# Research Summary

**Date:** {{ date }}
**Confidence Score:** {{ avg_confidence | format_confidence }}

## Research Findings

{% for item in research | sort_by_confidence %}
### {{ item.content }}

**Research Type:** {{ item.metadata.research_type | title }}
**Source:** {{ item.metadata.source }}
**Methodology:** {{ item.metadata.methodology }}

{% if item.metadata.sample_size %}
**Sample Size:** {{ item.metadata.sample_size }}
{% endif %}

{% if item.metadata.confidence_level %}
**Statistical Confidence:** {{ item.metadata.confidence_level }}
{% endif %}

{% if item.metadata.limitations %}
**Limitations:**
{% for limitation in item.metadata.limitations %}
- {{ limitation }}
{% endfor %}
{% endif %}

---

{% endfor %}

---
*Generated from {{ total_fields }} extracted fields*
'''

    def _get_generic_template(self, document_type: str) -> str:
        """Get generic template for unknown document types."""
        return f'''# {document_type.replace('_', ' ').title()}

**Date:** {{{{ date }}}}
**Confidence Score:** {{{{ avg_confidence | format_confidence }}}}

## Overview

This document was generated from conversation analysis.

## Content

{{{{ fields | extract_content(500) }}}}

## Field Summary

{{% for field_type, field_list in fields_by_type.items() %}}
### {{{{ field_type.title() }}}} ({{{{ field_list | length }}}} items)

{{% for field in field_list[:5] %}}
- **{{{{ field.content[:100] }}}}...** (Confidence: {{{{ field.confidence | format_confidence }}}})
{{% endfor %}}

{{% endfor %}}

---
*Generated from {{{{ total_fields }}}} extracted fields*
'''