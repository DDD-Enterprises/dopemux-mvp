"""
Field extractors for comprehensive chatlog analysis.

This package contains specialized extractors that analyze conversation data
to extract specific types of information needed for document synthesis.
"""

from .base_extractor import BaseExtractor, ExtractedField
from .decision_extractor import DecisionExtractor
from .feature_extractor import FeatureExtractor
from .research_extractor import ResearchExtractor
from .constraint_extractor import ConstraintExtractor
from .stakeholder_extractor import StakeholderExtractor
from .risk_extractor import RiskExtractor
from .security_extractor import SecurityExtractor

__all__ = [
    'BaseExtractor',
    'ExtractedField',
    'DecisionExtractor',
    'FeatureExtractor',
    'ResearchExtractor',
    'ConstraintExtractor',
    'StakeholderExtractor',
    'RiskExtractor',
    'SecurityExtractor',
]