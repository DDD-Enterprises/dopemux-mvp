import type { ReactNode } from 'react';

export interface PlannerExtension {
  id: string;
  render: () => ReactNode;
}

export interface PlannerExtensionModule {
  default: PlannerExtension;
}

export interface PlannerClaim {
  claimId: string;
  field: string;
  value: string;
  sourceLocator: string;
  sourceSha256: string;
  transformationId: string;
}

export type PlannerStatus = 'ready' | 'blocked' | 'stale' | 'unknown' | 'conflicting';

export interface PlannerConflict {
  field: string;
  values: string[];
  claims: PlannerClaim[];
}

export interface PlannerLane {
  projectId: string;
  laneId: string;
  candidateSha: string;
  observedHead: string;
  fetchedAt: string;
  freshness: 'CURRENT' | 'STALE' | 'UNKNOWN';
  lifecycleState: string;
  recommendation: string;
  states: PlannerStatus[];
  claims: PlannerClaim[];
  conflicts: PlannerConflict[];
}

export interface SourceFixture {
  authority: 'NONE';
  surface_class: 'PROJECTION';
  is_proof: false;
  project_id: string;
  observed_head: string;
  fetched_at: string;
  freshness: 'CURRENT' | 'STALE' | 'UNKNOWN';
  claims: Array<{ claim_id: string; lane_id: string; field: string; value: string; source_locator: string; source_sha256: string; transformation_id: string }>;
  lanes: Array<{ lane_id: string; candidate_sha: string; gate_status: string; audit_status: string; lifecycle_state: string }>;
}
