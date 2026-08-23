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
  materiality: 'BLOCKING' | 'NON_BLOCKING';
  freshness: 'CURRENT' | 'STALE' | 'UNKNOWN';
}

export type PlannerStatus = 'ready' | 'blocked' | 'stale' | 'unknown' | 'conflicting';

export interface PlannerConflict {
  field: string;
  values: string[];
  claims: PlannerClaim[];
  materiality: 'BLOCKING' | 'NON_BLOCKING';
}

export interface PlannerDependency {
  project_id: string;
  lane_id: string;
  candidate_sha: string;
}

export interface PlannerLane {
  projectId: string;
  laneId: string;
  candidateSha: string;
  observedHead: string;
  fetchedAt: string;
  freshness: 'CURRENT' | 'STALE' | 'UNKNOWN';
  lifecycleState: string;
  dependencies: PlannerDependency[];
  gateStatus: 'PASS' | 'FAIL' | 'UNKNOWN';
  auditStatus: 'PASS' | 'FAIL' | 'UNKNOWN';
  recommendation: string;
  states: PlannerStatus[];
  claims: PlannerClaim[];
  conflicts: PlannerConflict[];
}

export interface SourceFixture {
  schema_version: 'pcp.repository_planner_source.v1';
  authority: 'NONE';
  surface_class: 'PROJECTION';
  is_proof: false;
  evidence_class: string;
  project_id: string;
  observed_head: string;
  fetched_at: string;
  freshness: 'CURRENT' | 'STALE' | 'UNKNOWN';
  claims: Array<{ claim_id: string; lane_id: string; field: string; value: string; materiality: 'BLOCKING' | 'NON_BLOCKING'; source_locator: string; source_sha256: string; transformation_id: string }>;
  lanes: Array<{ lane_id: string; candidate_sha: string; dependencies: PlannerDependency[]; gate_status: 'PASS' | 'FAIL' | 'UNKNOWN'; audit_status: 'PASS' | 'FAIL' | 'UNKNOWN'; lifecycle_state: string }>;
}
