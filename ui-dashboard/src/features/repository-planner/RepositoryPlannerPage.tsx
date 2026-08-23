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
const timestampPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/;
const encoder = new TextEncoder();

function byteCompare(left: string, right: string) {
  const a = encoder.encode(left);
  const b = encoder.encode(right);
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) if (a[index] !== b[index]) return a[index] - b[index];
  return a.length - b.length;
}

function exactKeys(value: object, expected: readonly string[], label: string) {
  const actual = Object.keys(value).sort(byteCompare);
  const wanted = [...expected].sort(byteCompare);
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) throw new Error(`Fixture ${label} fields are malformed`);
}

function nonEmpty(value: unknown) { return typeof value === 'string' && value.length > 0; }

function isCanonicalTimestamp(value: string) {
  const match = timestampPattern.exec(value);
  if (!match) return false;
  const [datePart, timePart] = value.slice(0, 19).split('T');
  const [year, month, day] = datePart.split('-').map(Number);
  const [hour, minute, second] = timePart.split(':').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
    && date.getUTCHours() === hour && date.getUTCMinutes() === minute && date.getUTCSeconds() === second;
}

function validateFixture(source: SourceFixture) {
  exactKeys(source, ['schema_version', 'project_id', 'authority', 'surface_class', 'is_proof', 'evidence_class', 'observed_head', 'fetched_at', 'freshness', 'claims', 'lanes'], 'source');
  if (source.schema_version !== 'pcp.repository_planner_source.v1' || !nonEmpty(source.evidence_class)) throw new Error('Fixture schema is malformed');
  if (source.authority !== 'NONE' || source.surface_class !== 'PROJECTION' || source.is_proof !== false) throw new Error('Fixture attempted authority promotion');
  if (!nonEmpty(source.project_id) || !shaPattern.test(source.observed_head) || !isCanonicalTimestamp(source.fetched_at)) throw new Error('Fixture identity is malformed');
  if (!['CURRENT', 'STALE', 'UNKNOWN'].includes(source.freshness) || !Array.isArray(source.claims) || !Array.isArray(source.lanes)) throw new Error('Fixture state is malformed');
  const laneIds = new Set<string>();
  const laneKeys = new Set<string>();
  for (const lane of source.lanes) {
    exactKeys(lane, ['lane_id', 'candidate_sha', 'dependencies', 'gate_status', 'audit_status', 'lifecycle_state'], 'lane');
    if (!nonEmpty(lane.lane_id) || !shaPattern.test(lane.candidate_sha) || !nonEmpty(lane.lifecycle_state) || !['PASS', 'FAIL', 'UNKNOWN'].includes(lane.gate_status) || !['PASS', 'FAIL', 'UNKNOWN'].includes(lane.audit_status) || !Array.isArray(lane.dependencies)) throw new Error('Fixture lane is malformed');
    const laneKey = `${lane.lane_id}\0${lane.candidate_sha}`;
    if (laneKeys.has(laneKey)) throw new Error('Fixture duplicate candidate identity');
    laneKeys.add(laneKey);
    laneIds.add(lane.lane_id);
    const dependencyKeys = new Set<string>();
    for (const dependency of lane.dependencies) {
      if (!dependency || typeof dependency !== 'object') throw new Error('Fixture dependency is malformed');
      exactKeys(dependency, ['project_id', 'lane_id', 'candidate_sha'], 'dependency');
      if (!nonEmpty(dependency.project_id) || !nonEmpty(dependency.lane_id) || !shaPattern.test(dependency.candidate_sha)) throw new Error('Fixture dependency is malformed');
      const key = `${dependency.project_id}\0${dependency.lane_id}\0${dependency.candidate_sha}`;
      if (dependencyKeys.has(key)) throw new Error('Fixture duplicate dependency');
      dependencyKeys.add(key);
    }
  }
  const claimIds = new Set<string>();
  for (const claim of source.claims) {
    exactKeys(claim, ['claim_id', 'lane_id', 'field', 'value', 'materiality', 'transformation_id', 'source_locator', 'source_sha256'], 'claim');
    if (!nonEmpty(claim.claim_id) || claimIds.has(claim.claim_id)) throw new Error('Fixture duplicate claim identity');
    claimIds.add(claim.claim_id);
    if (!laneIds.has(claim.lane_id) || !nonEmpty(claim.field) || !nonEmpty(claim.value) || !['BLOCKING', 'NON_BLOCKING'].includes(claim.materiality) || !nonEmpty(claim.source_locator) || !hashPattern.test(claim.source_sha256) || !nonEmpty(claim.transformation_id)) throw new Error('Fixture claim provenance is malformed');
  }
}

export function buildFoundationLanes(sources: readonly SourceFixture[]): readonly PlannerLane[] {
  const globalClaimIds = new Set<string>();
  const globalLaneKeys = new Set<string>();
  for (const source of sources) {
    validateFixture(source);
    for (const claim of source.claims) {
      if (globalClaimIds.has(claim.claim_id)) throw new Error(`Fixture duplicate claim identity: ${claim.claim_id}`);
      globalClaimIds.add(claim.claim_id);
    }
    for (const lane of source.lanes) {
      const key = `${source.project_id}\0${lane.lane_id}\0${lane.candidate_sha}`;
      if (globalLaneKeys.has(key)) throw new Error('Fixture duplicate candidate identity');
      globalLaneKeys.add(key);
    }
  }
  return sources.flatMap((source) => {
    return source.lanes.map((lane) => {
    const claims: PlannerClaim[] = source.claims.filter((claim) => claim.lane_id === lane.lane_id).map((claim) => ({
      claimId: claim.claim_id,
      field: claim.field,
      value: claim.value,
      sourceLocator: claim.source_locator,
      sourceSha256: claim.source_sha256,
      transformationId: claim.transformation_id,
      materiality: claim.materiality,
      freshness: source.freshness,
    }));
    const conflicts: PlannerConflict[] = [...new Set(claims.map((claim) => claim.field))].flatMap((field) => {
      const matching = claims.filter((claim) => claim.field === field);
      const values = [...new Set(matching.map((claim) => claim.value))].sort(byteCompare);
      const materiality = matching.some((claim) => claim.materiality === 'BLOCKING') ? 'BLOCKING' : 'NON_BLOCKING';
      return values.length > 1 ? [{ field, values, claims: matching, materiality }] : [];
    });
    const hasBlockingConflict = conflicts.some((conflict) => conflict.materiality === 'BLOCKING');
    const states = new Set<PlannerStatus>();
    if (source.freshness === 'STALE') states.add('stale');
    if (source.freshness === 'UNKNOWN' || lane.gate_status === 'UNKNOWN' || lane.audit_status === 'UNKNOWN') states.add('unknown');
    if (lane.lifecycle_state === 'REMOTE_COMMIT_ABSENT' || lane.gate_status === 'FAIL' || lane.audit_status === 'FAIL') states.add('blocked');
    if (conflicts.length) states.add('conflicting');
    if (!hasBlockingConflict && !states.has('blocked') && !states.has('stale') && !states.has('unknown')) states.add('ready');
    const orderedStates = stateOrder.filter((state) => states.has(state));
    const recommendation = hasBlockingConflict ? 'Blocked: conflicting evidence'
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
      dependencies: lane.dependencies,
      gateStatus: lane.gate_status,
      auditStatus: lane.audit_status,
      recommendation,
      states: orderedStates,
      claims,
      conflicts,
    };
    });
  }).sort((left, right) => {
    return byteCompare(`${left.projectId}\0${left.laneId}\0${left.candidateSha}`, `${right.projectId}\0${right.laneId}\0${right.candidateSha}`);
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
