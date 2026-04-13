"""
Main synthesis engine that orchestrates template selection and document building.
"""

from typing import Dict, List, Any, Optional
import logging
from .template_selector import TemplateSelector
from .document_builder import DocumentBuilder

logger = logging.getLogger(__name__)


class SynthesisEngine:
    """
    Main synthesis engine that coordinates template selection and document generation.

    Provides a unified interface for adaptive document synthesis from extracted fields.
    """

    def __init__(self, template_dir: Optional[str] = None, max_documents: int = 6):
        """
        Initialize the synthesis engine.

        Args:
            template_dir: Directory containing Jinja2 templates
            max_documents: Maximum number of documents to generate
        """
        self.template_selector = TemplateSelector()
        self.document_builder = DocumentBuilder(template_dir)
        self.max_documents = max_documents

    def synthesize_documents(self, extracted_fields: List[Dict[str, Any]],
                           metadata: Optional[Dict[str, Any]] = None,
                           force_templates: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive documents from extracted fields.

        Args:
            extracted_fields: List of extracted field dictionaries
            metadata: Optional metadata for document generation
            force_templates: Optional list of templates to force generation

        Returns:
            Dictionary containing generated documents and analysis data
        """
        logger.info(f"Starting document synthesis for {len(extracted_fields)} fields")

        # Convert ExtractedField objects to dictionaries if needed
        field_dicts = []
        for field in extracted_fields:
            if hasattr(field, 'to_dict'):
                field_dicts.append(field.to_dict())
            elif isinstance(field, dict):
                field_dicts.append(field)
            else:
                logger.warning(f"Unknown field type: {type(field)}")
                continue

        # Select templates (unless forced)
        if force_templates:
            selected_templates = force_templates
            template_recommendations = None
            logger.info(f"Using forced templates: {selected_templates}")
        else:
            selected_templates = self.template_selector.select_templates(
                field_dicts, self.max_documents
            )
            template_recommendations = self.template_selector.get_template_recommendations(field_dicts)
            logger.info(f"Selected templates: {selected_templates}")

        # Generate documents
        documents = self.document_builder.build_documents(
            field_dicts, selected_templates, metadata
        )

        # Prepare analysis data
        analysis = {
            'total_fields': len(field_dicts),
            'selected_templates': selected_templates,
            'template_recommendations': template_recommendations,
            'document_count': len(documents),
            'field_summary': self._analyze_fields(field_dicts),
            'generation_metadata': metadata or {}
        }

        logger.info(f"Generated {len(documents)} documents successfully")

        return {
            'documents': documents,
            'analysis': analysis
        }

    def _analyze_fields(self, field_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze field composition and quality."""
        if not field_dicts:
            return {}

        field_types = {}
        total_confidence = 0
        high_confidence_count = 0

        for field in field_dicts:
            field_type = field.get('field_type', 'unknown')
            confidence = field.get('confidence', 0.0)

            field_types[field_type] = field_types.get(field_type, 0) + 1
            total_confidence += confidence

            if confidence >= 0.7:
                high_confidence_count += 1

        avg_confidence = total_confidence / len(field_dicts)

        return {
            'field_types': field_types,
            'avg_confidence': avg_confidence,
            'high_confidence_count': high_confidence_count,
            'high_confidence_ratio': high_confidence_count / len(field_dicts)
        }

    def get_available_templates(self) -> List[str]:
        """Get list of available document templates."""
        return list(self.template_selector.template_criteria.keys())

    def preview_template_selection(self, extracted_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Preview which templates would be selected without generating documents.

        Args:
            extracted_fields: List of extracted field dictionaries

        Returns:
            Template selection analysis
        """
        field_dicts = []
        for field in extracted_fields:
            if hasattr(field, 'to_dict'):
                field_dicts.append(field.to_dict())
            elif isinstance(field, dict):
                field_dicts.append(field)

        return self.template_selector.get_template_recommendations(field_dicts)

    def generate_single_document(self, template_name: str,
                                extracted_fields: List[Dict[str, Any]],
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a single document using the specified template.

        Args:
            template_name: Name of the template to use
            extracted_fields: List of extracted field dictionaries
            metadata: Optional metadata for document generation

        Returns:
            Generated document content
        """
        field_dicts = []
        for field in extracted_fields:
            if hasattr(field, 'to_dict'):
                field_dicts.append(field.to_dict())
            elif isinstance(field, dict):
                field_dicts.append(field)

        documents = self.document_builder.build_documents(
            field_dicts, [template_name], metadata
        )

        return documents.get(template_name, '')

    def update_max_documents(self, max_documents: int):
        """Update the maximum number of documents to generate."""
        self.max_documents = max_documents
        logger.info(f"Updated max documents to {max_documents}")

    def get_synthesis_summary(self, extracted_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a comprehensive summary of what would be synthesized.

        Args:
            extracted_fields: List of extracted field dictionaries

        Returns:
            Synthesis summary with field analysis and template recommendations
        """
        field_dicts = []
        for field in extracted_fields:
            if hasattr(field, 'to_dict'):
                field_dicts.append(field.to_dict())
            elif isinstance(field, dict):
                field_dicts.append(field)

        template_recommendations = self.template_selector.get_template_recommendations(field_dicts)
        field_analysis = self._analyze_fields(field_dicts)

        return {
            'field_analysis': field_analysis,
            'template_recommendations': template_recommendations,
            'available_templates': self.get_available_templates(),
            'max_documents': self.max_documents
        }