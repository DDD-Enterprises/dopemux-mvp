import { useMemo, useRef, useState } from 'react';
import { Alert, Box, CircularProgress, Container, CssBaseline, Paper, Stack, ThemeProvider, Typography } from '@mui/material';

import dopemuxFixture from '../../../../tests/fixtures/repository_planner/foundation/dopemux.json';
import adopsFixture from '../../../../tests/fixtures/repository_planner/foundation/adops.json';
import dnhFixture from '../../../../tests/fixtures/repository_planner/foundation/dnh_crm.json';
import theme from '../../theme';
import LaneDetails from './LaneDetails';
import PortfolioTable from './PortfolioTable';
import { plannerExtensions } from './extensionRegistry';
import type { PlannerClaim, PlannerConflict, PlannerLane, PlannerStatus, SourceFixture } from './extensionTypes';

const fixtures = [dopemuxFixture, adopsFixture, dnhFixture] as unknown as SourceFixture[];
const stateOrder: PlannerStatus[] = ['ready', 'blocked', 'stale', 'unknown', 'conflicting'];
const shaPattern = /^[0-9a-f]{40}([0-9a-f]{24})?$/;
const hashPattern = /^[0-9a-f]{64}$/;

function validateFixture(source: SourceFixture) {
  if (source.authority !== 'NONE' || source.surface_class !== 'PROJECTION' || source.is_proof !== false) throw new Error('Fixture attempted authority promotion');
  if (!source.project_id || !shaPattern.test(source.observed_head) || Number.isNaN(Date.parse(source.fetched_at))) throw new Error('Fixture identity is malformed');
  if (!['CURRENT', 'STALE', 'UNKNOWN'].includes(source.freshness) || !Array.isArray(source.claims) || !Array.isArray(source.lanes)) throw new Error('Fixture state is malformed');
  const laneIds = new Set(source.lanes.map((lane) => lane.lane_id));
  for (const claim of source.claims) {
    if (!claim.claim_id || !laneIds.has(claim.lane_id) || !claim.source_locator || !hashPattern.test(claim.source_sha256) || !claim.transformation_id) throw new Error('Fixture claim provenance is malformed');
  }
}

export function buildFoundationLanes(sources: readonly SourceFixture[]): readonly PlannerLane[] {
  return sources.flatMap((source) => {
    validateFixture(source);
    return source.lanes.map((lane) => {
    const claims: PlannerClaim[] = source.claims.filter((claim) => claim.lane_id === lane.lane_id).map((claim) => ({
      claimId: claim.claim_id,
      field: claim.field,
      value: claim.value,
      sourceLocator: claim.source_locator,
      sourceSha256: claim.source_sha256,
      transformationId: claim.transformation_id,
    }));
    const conflicts: PlannerConflict[] = [...new Set(claims.map((claim) => claim.field))].flatMap((field) => {
      const matching = claims.filter((claim) => claim.field === field);
      const values = [...new Set(matching.map((claim) => claim.value))].sort();
      return values.length > 1 ? [{ field, values, claims: matching }] : [];
    });
    const states = new Set<PlannerStatus>();
    if (source.freshness === 'STALE') states.add('stale');
    if (source.freshness === 'UNKNOWN' || lane.gate_status === 'UNKNOWN' || lane.audit_status === 'UNKNOWN') states.add('unknown');
    if (lane.lifecycle_state === 'REMOTE_COMMIT_ABSENT' || lane.gate_status === 'FAIL' || lane.audit_status === 'FAIL') states.add('blocked');
    if (conflicts.length) states.add('conflicting');
    if (!states.size) states.add('ready');
    const orderedStates = stateOrder.filter((state) => states.has(state));
    const recommendation = states.has('conflicting') ? 'Blocked: conflicting evidence'
      : states.has('blocked') ? 'Blocked: failed readiness gate'
        : states.has('stale') ? 'Deferred: stale evidence'
          : states.has('unknown') ? 'Unknown readiness'
            : 'Ready for Control Tower review';
    return {
      projectId: source.project_id,
      laneId: lane.lane_id,
      candidateSha: lane.candidate_sha,
      observedHead: source.observed_head,
      fetchedAt: source.fetched_at,
      freshness: source.freshness,
      lifecycleState: lane.lifecycle_state,
      recommendation,
      states: orderedStates,
      claims,
      conflicts,
    };
    });
  }).sort((left, right) => {
    const a = new TextEncoder().encode(`${left.projectId}\0${left.laneId}\0${left.candidateSha}`);
    const b = new TextEncoder().encode(`${right.projectId}\0${right.laneId}\0${right.candidateSha}`);
    for (let index = 0; index < Math.min(a.length, b.length); index += 1) if (a[index] !== b[index]) return a[index] - b[index];
    return a.length - b.length;
  });
}

interface RepositoryPlannerPageProps {
  state?: 'loading' | 'ready' | 'error';
  errorMessage?: string;
  sources?: readonly SourceFixture[];
}

export default function RepositoryPlannerPage({ state = 'ready', errorMessage = 'Unable to load planner fixtures', sources = fixtures }: RepositoryPlannerPageProps) {
  const [selected, setSelected] = useState<PlannerLane | null>(null);
  const returnFocus = useRef<HTMLButtonElement | null>(null);
  const projection = useMemo(() => {
    try { return { lanes: buildFoundationLanes(sources), error: null }; }
    catch (error) { return { lanes: [], error: error instanceof Error ? error.message : 'Fixture validation failed' }; }
  }, [sources]);
  const effectiveState = projection.error ? 'error' : state;
  const inspect = (lane: PlannerLane, trigger: HTMLButtonElement) => { returnFocus.current = trigger; setSelected(lane); };
  const close = () => { setSelected(null); window.setTimeout(() => returnFocus.current?.focus(), 0); };

  return <ThemeProvider theme={theme}><CssBaseline /><Container maxWidth="xl" component="main" sx={{ py: 4 }}><Stack spacing={3}><Box><Typography variant="h3" component="h1">Repository merge planner</Typography><Typography color="text.secondary">Deterministic projection generated from checked-in foundation fixtures</Typography></Box><Alert severity="info"><strong>Projection only.</strong> Authority: NONE · is_proof: false. Control Tower and repository governance retain all terminal decisions.</Alert>{effectiveState === 'loading' && <Stack role="status" aria-label="Loading repository planner fixtures" alignItems="center"><CircularProgress /><Typography>Loading checked-in fixtures…</Typography></Stack>}{effectiveState === 'error' && <Alert severity="error">{projection.error ?? errorMessage}</Alert>}{effectiveState === 'ready' && <Paper><PortfolioTable lanes={projection.lanes} onInspect={inspect} /></Paper>}{effectiveState === 'ready' && plannerExtensions.map((extension) => <Box key={extension.id}>{extension.render()}</Box>)}</Stack><LaneDetails lane={selected} onClose={close} /></Container></ThemeProvider>;
}
