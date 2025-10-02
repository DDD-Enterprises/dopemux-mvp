/**
 * HTTP Client for CONPORT-KG-2025 Integration Bridge API
 *
 * Base URL: http://localhost:${PORT_BASE+16}/kg
 * Default: http://localhost:3016/kg
 */

import type {
  DecisionCard,
  DecisionSummary,
  DecisionNeighborhood,
  FullDecisionContext,
  RecentDecisionsResponse,
  NeighborhoodResponse,
  ContextResponse
} from '../types';

const BASE_URL = process.env.KG_API_URL || 'http://localhost:3016/kg';

export class KGClient {
  private baseUrl: string;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async getRecentDecisions(limit: number = 3): Promise<DecisionCard[]> {
    const response = await fetch(`${this.baseUrl}/decisions/recent?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: RecentDecisionsResponse = await response.json();
    return data.decisions;
  }

  async getDecisionSummary(id: number): Promise<DecisionSummary> {
    const response = await fetch(`${this.baseUrl}/decisions/${id}/summary`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  async getNeighborhood(
    id: number,
    maxHops: number = 1,
    limitPerHop: number = 10
  ): Promise<DecisionNeighborhood> {
    const url = `${this.baseUrl}/decisions/${id}/neighborhood?max_hops=${maxHops}&limit_per_hop=${limitPerHop}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: NeighborhoodResponse = await response.json();
    return {
      center: data.center,
      hop_1_neighbors: data.hop_1_neighbors,
      hop_2_neighbors: data.hop_2_neighbors,
      total_neighbors: data.total_neighbors,
      is_expanded: data.is_expanded
    };
  }

  async getFullContext(id: number): Promise<FullDecisionContext> {
    const response = await fetch(`${this.baseUrl}/decisions/${id}/context`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: ContextResponse = await response.json();
    return {
      decision: data.decision,
      direct_relationships: data.direct_relationships,
      related_decisions: data.related_decisions,
      total_related: data.total_related,
      cognitive_load: data.cognitive_load
    };
  }

  async searchByTag(tag: string, limit: number = 3): Promise<DecisionCard[]> {
    const response = await fetch(`${this.baseUrl}/decisions/search?tag=${tag}&limit=${limit}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.decisions;
  }

  async searchFullText(text: string, limit: number = 20): Promise<DecisionCard[]> {
    const response = await fetch(`${this.baseUrl}/decisions/search?text=${text}&limit=${limit}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.decisions;
  }
}

// Singleton instance
export const kgClient = new KGClient();
