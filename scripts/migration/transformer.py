#!/usr/bin/env python3
"""
ConPort Data Transformer
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Transforms old ConPort schema to new AGE-compatible schema:
- UUID → INTEGER mapping (sequential by created_at)
- TEXT[] → JSONB conversion
- confidence_level → status derivation
- alternatives → implementation extraction
- 4 relationship types → 8 types mapping
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class DecisionTransformer:
    """Transforms decisions from old schema to new schema"""

    def __init__(self):
        self.uuid_to_id_map: Dict[str, int] = {}

        # Confidence level → status mapping
        self.status_map = {
            'certain': 'accepted',
            'high': 'accepted',
            'medium': 'proposed',
            'low': 'proposed'
        }

        # Old relationship types → new relationship types
        self.relationship_type_map = {
            'implements': 'IMPLEMENTS',      # Direct match
            'relates_to': 'RELATES_TO',      # Direct match
            'blocks': 'DEPENDS_ON',          # Semantic: blocking = dependency
            'caused_by': 'BUILDS_UPON'       # Semantic: reverse causality
        }

    def transform_decision(self, old_decision: Dict, new_id: int) -> Dict:
        """
        Transform single decision from old → new schema

        Args:
            old_decision: Row from old decisions table
            new_id: Sequential INTEGER ID to assign

        Returns:
            Transformed decision ready for decisions_v2 insertion
        """

        # Derive status from confidence_level
        status = self.status_map.get(
            old_decision.get('confidence_level', 'medium'),
            'proposed'
        )

        # Derive implementation from alternatives
        implementation = self._extract_implementation(old_decision.get('alternatives'))

        # Convert TEXT[] → JSONB
        tags_jsonb = self._convert_tags(old_decision.get('tags', []))
        alternatives_jsonb = self._convert_alternatives(old_decision.get('alternatives', []))

        # Create transformed decision
        transformed = {
            'workspace_id': old_decision['workspace_id'],
            'summary': old_decision['summary'],
            'rationale': old_decision.get('rationale') or f"[Auto-generated from: {old_decision['summary']}]",
            'status': status,
            'implementation': implementation,
            'tags': tags_jsonb,
            'alternatives': alternatives_jsonb,
            'confidence_level': old_decision.get('confidence_level', 'medium'),
            'decision_type': old_decision.get('decision_type', 'implementation'),
            'graph_version': 1,
            'hop_distance': None,  # Computed post-migration
            'created_at': old_decision['created_at'],
            'updated_at': old_decision['updated_at'],
            'old_uuid': old_decision['id']  # For relationship migration
        }

        # Track UUID → ID mapping
        self.uuid_to_id_map[old_decision['id']] = new_id

        return transformed

    def _extract_implementation(self, alternatives) -> Optional[str]:
        """
        Derive implementation field from alternatives array

        If alternatives exist, create implementation summary.
        Otherwise return None (will be NULL in database).
        """
        if not alternatives or len(alternatives) == 0:
            return None

        # Format alternatives as implementation context
        alt_list = ', '.join(alternatives[:3])  # Limit to first 3
        if len(alternatives) > 3:
            alt_list += f" (+{len(alternatives) - 3} more)"

        return f"Alternatives considered: {alt_list}"

    def _convert_tags(self, tags_array) -> str:
        """Convert PostgreSQL TEXT[] to JSONB string"""
        if not tags_array:
            return '[]'
        return json.dumps(tags_array)

    def _convert_alternatives(self, alternatives_array) -> str:
        """Convert alternatives to JSONB string"""
        if not alternatives_array:
            return '[]'
        return json.dumps(alternatives_array)

    def transform_relationship(self, old_relationship: Dict) -> Dict:
        """
        Transform relationship from old → new schema

        Maps 4 old relationship types to 8 new types.
        Uses UUID→ID map to convert foreign keys.
        """

        source_uuid = old_relationship['source_id']
        target_uuid = old_relationship['target_id']

        # Lookup new INTEGER IDs
        source_id = self.uuid_to_id_map.get(source_uuid)
        target_id = self.uuid_to_id_map.get(target_uuid)

        if source_id is None or target_id is None:
            raise ValueError(
                f"Orphaned relationship: {source_uuid} → {target_uuid}. "
                f"Source mapped: {source_id is not None}, Target mapped: {target_id is not None}"
            )

        # Map relationship type
        old_type = old_relationship['relationship_type']
        new_type = self.relationship_type_map.get(old_type, 'RELATES_TO')

        # Create properties JSON (preserve original type for audit)
        properties = {
            'original_type': old_type,
            'migrated_at': datetime.now().isoformat()
        }

        return {
            'workspace_id': old_relationship['workspace_id'],
            'source_type': 'decision',
            'source_id': source_id,
            'target_type': 'decision',
            'target_id': target_id,
            'relationship_type': new_type,
            'strength': float(old_relationship.get('strength', 1.0)),
            'properties': json.dumps(properties),
            'created_at': old_relationship['created_at']
        }

    def get_statistics(self) -> Dict:
        """Return transformation statistics"""
        return {
            'uuid_mappings': len(self.uuid_to_id_map),
            'relationship_type_mappings': self.relationship_type_map
        }


if __name__ == "__main__":
    # Example usage
    print("DecisionTransformer - ConPort Schema Upgrade")
    print("=" * 60)
    print("\nMapping rules:")
    print("  UUID → INTEGER: Sequential by created_at")
    print("  confidence_level → status:")
    for old, new in DecisionTransformer().status_map.items():
        print(f"    {old} → {new}")
    print("  Relationship types (4 → 8):")
    for old, new in DecisionTransformer().relationship_type_map.items():
        print(f"    {old} → {new}")
    print("\nUse in conjunction with export_conport.py and reingest.py")
