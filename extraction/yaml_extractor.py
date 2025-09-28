"""
YAML Configuration Extractor for Dopemux Documentation

Extracts semantic entities from YAML configuration files, specifically
designed for .dopemux/config.yaml and similar structured configuration.
"""

import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path


@dataclass
class YamlEntity:
    """Extracted entity from YAML configuration."""
    type: str
    key_path: str  # Dot-notation path like "adhd_profile.focus_duration_avg"
    value: Any
    category: str
    description: Optional[str] = None
    confidence: float = 0.0


class YamlExtractor:
    """Extract semantic entities from YAML configuration files."""

    def __init__(self):
        """Initialize YAML extractor with domain mappings."""
        self._init_category_mappings()

    def _init_category_mappings(self):
        """Initialize category mappings for YAML keys."""

        # ADHD-specific configuration categories
        self.adhd_categories = {
            'focus_settings': [
                'focus_duration_avg', 'focus_duration', 'attention_span',
                'concentration_time', 'deep_work_duration'
            ],
            'break_settings': [
                'break_interval', 'break_duration', 'rest_time',
                'pause_frequency', 'break_reminder'
            ],
            'notification_settings': [
                'notification_style', 'alert_type', 'reminder_style',
                'gentle_notifications', 'notification_frequency'
            ],
            'accommodation_settings': [
                'attention_monitoring', 'context_preservation',
                'task_decomposition', 'hyperfocus_tendency',
                'distraction_sensitivity', 'visual_complexity'
            ],
            'session_settings': [
                'auto_save_interval', 'session_timeout', 'max_sessions',
                'compression', 'session_persistence'
            ]
        }

        # General configuration categories
        self.general_categories = {
            'project_metadata': [
                'project_type', 'project_name', 'version',
                'initialized_at', 'created_date'
            ],
            'feature_flags': [
                'active_features', 'enabled_features', 'feature_toggles',
                'experimental_features'
            ],
            'system_settings': [
                'system_config', 'performance_settings',
                'resource_limits', 'optimization_settings'
            ]
        }

        # Value type mappings for better categorization
        self.value_types = {
            'duration': ['duration', 'interval', 'timeout', 'time'],
            'boolean_flag': ['enabled', 'active', 'monitoring', 'tendency'],
            'threshold': ['sensitivity', 'limit', 'max', 'min'],
            'style': ['style', 'type', 'complexity', 'mode']
        }

    def extract_entities(self, yaml_content: str, filename: str = "") -> List[YamlEntity]:
        """Extract entities from YAML content."""
        try:
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                return []

            entities = []
            self._extract_recursive(data, "", entities, filename)

            # Calculate confidence scores
            for entity in entities:
                entity.confidence = self._calculate_confidence(entity, filename)

            return entities

        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
            return []

    def _extract_recursive(self, data: Dict[str, Any], path_prefix: str,
                          entities: List[YamlEntity], filename: str):
        """Recursively extract entities from nested YAML structure."""

        for key, value in data.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key

            if isinstance(value, dict):
                # Nested structure - create a container entity and recurse
                entity = YamlEntity(
                    type='configuration_section',
                    key_path=current_path,
                    value=value,
                    category=self._categorize_key(key, current_path),
                    description=f"Configuration section: {key}"
                )
                entities.append(entity)

                # Recurse into nested structure
                self._extract_recursive(value, current_path, entities, filename)

            elif isinstance(value, list):
                # List of values
                entity = YamlEntity(
                    type='configuration_list',
                    key_path=current_path,
                    value=value,
                    category=self._categorize_key(key, current_path),
                    description=f"Configuration list: {key} ({len(value)} items)"
                )
                entities.append(entity)

                # Extract individual list items if they're meaningful
                for i, item in enumerate(value):
                    if isinstance(item, (str, int, float, bool)):
                        item_entity = YamlEntity(
                            type='configuration_value',
                            key_path=f"{current_path}[{i}]",
                            value=item,
                            category=self._categorize_key(key, current_path),
                            description=f"List item from {key}"
                        )
                        entities.append(item_entity)

            else:
                # Simple value (string, int, float, bool)
                entity = YamlEntity(
                    type='configuration_value',
                    key_path=current_path,
                    value=value,
                    category=self._categorize_key(key, current_path),
                    description=self._generate_description(key, value, current_path)
                )
                entities.append(entity)

    def _categorize_key(self, key: str, full_path: str) -> str:
        """Categorize a YAML key based on its name and path."""
        key_lower = key.lower()
        path_lower = full_path.lower()

        # Check ADHD-specific categories first
        for category, keywords in self.adhd_categories.items():
            if any(keyword in key_lower or keyword in path_lower for keyword in keywords):
                return category

        # Check general categories
        for category, keywords in self.general_categories.items():
            if any(keyword in key_lower or keyword in path_lower for keyword in keywords):
                return category

        # Path-based categorization
        if 'adhd' in path_lower:
            return 'adhd_configuration'
        if 'session' in path_lower:
            return 'session_configuration'
        if 'feature' in path_lower:
            return 'feature_configuration'

        return 'general_configuration'

    def _generate_description(self, key: str, value: Any, path: str) -> str:
        """Generate human-readable description for a configuration value."""
        key_readable = key.replace('_', ' ').title()

        # Value-specific descriptions
        if isinstance(value, bool):
            status = "enabled" if value else "disabled"
            return f"{key_readable}: {status}"
        elif isinstance(value, (int, float)):
            # Check if it's a duration/time value
            if any(time_word in key.lower() for time_word in ['duration', 'interval', 'timeout']):
                return f"{key_readable}: {value} (time setting)"
            else:
                return f"{key_readable}: {value}"
        elif isinstance(value, str):
            return f"{key_readable}: '{value}'"
        else:
            return f"{key_readable}: {value}"

    def _calculate_confidence(self, entity: YamlEntity, filename: str) -> float:
        """Calculate confidence score for extracted entity."""
        base_confidence = 0.8  # YAML is structured, so higher base confidence

        # Boost for ADHD-related configurations
        if 'adhd' in entity.category or 'focus' in entity.category or 'break' in entity.category:
            base_confidence += 0.15

        # Boost for well-known configuration patterns
        if entity.type == 'configuration_value' and isinstance(entity.value, (bool, int, float)):
            base_confidence += 0.05

        # Boost for dopemux-related files
        if 'dopemux' in filename.lower() or 'config' in filename.lower():
            base_confidence += 0.05

        # Boost for structured paths (nested configurations)
        if '.' in entity.key_path:
            base_confidence += 0.05

        return max(0.1, min(1.0, base_confidence))

    def extract_to_dict(self, yaml_content: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities and return as categorized dictionary."""
        entities = self.extract_entities(yaml_content, filename)

        # Group by category
        categorized = {}
        for entity in entities:
            if entity.category not in categorized:
                categorized[entity.category] = []

            categorized[entity.category].append({
                'type': entity.type,
                'key_path': entity.key_path,
                'value': entity.value,
                'description': entity.description,
                'confidence': entity.confidence
            })

        return categorized

    def extract_adhd_profile(self, yaml_content: str) -> Dict[str, Any]:
        """Extract specifically ADHD profile settings from YAML."""
        try:
            data = yaml.safe_load(yaml_content)
            adhd_profile = {}

            # Extract adhd_profile section if it exists
            if 'adhd_profile' in data:
                adhd_profile['profile'] = data['adhd_profile']

            # Extract active_features if it exists
            if 'active_features' in data:
                adhd_profile['features'] = data['active_features']

            # Extract session_settings if relevant to ADHD
            if 'session_settings' in data:
                session_settings = data['session_settings']
                adhd_session = {}

                adhd_keys = ['auto_save_interval', 'max_sessions', 'compression']
                for key in adhd_keys:
                    if key in session_settings:
                        adhd_session[key] = session_settings[key]

                if adhd_session:
                    adhd_profile['session_settings'] = adhd_session

            return adhd_profile

        except yaml.YAMLError:
            return {}


def extract_yaml_entities(yaml_content: str, filename: str = "") -> Dict[str, List[Dict[str, Any]]]:
    """Convenience function to extract entities from YAML content."""
    extractor = YamlExtractor()
    return extractor.extract_to_dict(yaml_content, filename)


# Test function
def test_with_sample_yaml():
    """Test the extractor with sample YAML content."""
    sample_yaml = '''
active_features:
  attention_monitoring: true
  context_preservation: true
  gentle_notifications: true
  task_decomposition: true

adhd_profile:
  break_interval: 5
  distraction_sensitivity: 0.5
  focus_duration_avg: 30
  hyperfocus_tendency: false
  notification_style: gentle
  visual_complexity: minimal

initialized_at: '2024-01-15T10:30:00Z'
project_type: python

session_settings:
  auto_save_interval: 30
  compression: true
  max_sessions: 50

version: '1.0'
'''

    extractor = YamlExtractor()
    entities = extractor.extract_entities(sample_yaml, "config.yaml")

    print("Extracted YAML entities:")
    for entity in entities:
        print(f"  {entity.category}: {entity.key_path}")
        print(f"    Value: {entity.value}")
        print(f"    Description: {entity.description}")
        print(f"    Confidence: {entity.confidence:.2f}")
        print()

    # Test ADHD profile extraction
    print("\nADHD Profile extraction:")
    adhd_profile = extractor.extract_adhd_profile(sample_yaml)
    for section, data in adhd_profile.items():
        print(f"  {section}: {data}")

    return entities


if __name__ == "__main__":
    test_with_sample_yaml()