import type { ReactNode } from 'react';

export interface PlannerExtension {
  id: string;
  render: () => ReactNode;
}

export interface PlannerExtensionModule {
  default: PlannerExtension;
}

export interface PlannerClaim {
  field: string;
  value: string;
  sourceLocator: string;
  sourceSha256: string;
}

export interface PlannerLane {
  projectId: string;
  laneId: string;
  candidateSha: string;
  observedHead: string;
  fetchedAt: string;
  freshness: 'CURRENT' | 'STALE';
  lifecycleState: string;
  recommendation: string;
  status: 'ready' | 'blocked' | 'stale' | 'unknown';
  claims: PlannerClaim[];
  conflicts: string[];
}
