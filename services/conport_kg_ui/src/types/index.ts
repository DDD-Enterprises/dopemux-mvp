/**
 * TypeScript interfaces for CONPORT-KG-2025 API responses
 * Matches Integration Bridge /kg/* endpoint schemas
 */

export interface DecisionCard {
  id: number;
  summary: string;
  timestamp: string;
  related_count?: number;
  tags?: string[];
}

export interface DecisionSummary extends DecisionCard {
  rationale?: string;
  implementation?: string;
  relationship_types?: string[];
  cognitive_load: 'low' | 'medium' | 'high';
}

export interface DecisionNeighborhood {
  center: DecisionCard;
  hop_1_neighbors: DecisionCard[];
  hop_2_neighbors: DecisionCard[];
  total_neighbors: number;
  is_expanded: boolean;
}

export interface Relationship {
  source_id: number;
  target_id: number;
  type: string;
  description?: string;
  timestamp: string;
  direction: 'incoming' | 'outgoing';
}

export interface FullDecisionContext {
  decision: DecisionSummary;
  direct_relationships: Relationship[];
  related_decisions: DecisionCard[];
  total_related: number;
  cognitive_load: string;
}

// API response wrappers
export interface RecentDecisionsResponse {
  decisions: DecisionCard[];
  count: number;
  tier: number;
}

export interface NeighborhoodResponse extends DecisionNeighborhood {
  tier: number;
}

export interface ContextResponse extends FullDecisionContext {
  tier: number;
}
