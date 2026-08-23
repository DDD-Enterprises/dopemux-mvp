import { useRef, useState } from 'react';
import { Alert, Box, Container, CssBaseline, Paper, Stack, ThemeProvider, Typography } from '@mui/material';

import theme from '../../theme';
import LaneDetails from './LaneDetails';
import PortfolioTable from './PortfolioTable';
import { plannerExtensions } from './extensionRegistry';
import type { PlannerLane } from './extensionTypes';

const sourceHash = 'a9a7263d779d879b06e39b012136697eac2b52ad34e11cf8496357b0e3d6358d';
const lanes: readonly PlannerLane[] = [
  { projectId: 'dopemux-mvp', laneId: 'pcp-planner-foundation', candidateSha: '7accb2aab3423f32e751640af2b3de130c68567a', observedHead: '7accb2aab3423f32e751640af2b3de130c68567a', fetchedAt: '2026-08-23T00:00:00Z', freshness: 'CURRENT', lifecycleState: 'DESIGN_ACCEPTED', recommendation: 'Ready for Control Tower review', status: 'ready', conflicts: [], claims: [{ field: 'gate_state', value: 'PASS', sourceLocator: 'task-packets/TP-DMX-REPOSITORY-MERGE-PLANNER-DESIGN-001.json', sourceSha256: sourceHash }] },
  { projectId: 'adOps', laneId: 'legacy-corpus-rating-002', candidateSha: '4ce6b644afa72231c24b3cdac58f251e1ca03321', observedHead: '864915b9cc8ff254eaa877627df1e510dc49dbec', fetchedAt: '2026-08-23T00:00:00Z', freshness: 'CURRENT', lifecycleState: 'REMOTE_COMMIT_ABSENT', recommendation: 'Blocked: conflicting evidence', status: 'blocked', conflicts: ['acceptance_state has incompatible values: DRAFT_NOT_ACCEPTED and FINALITY_EVIDENCE_PRESENT. No winner selected; resolution belongs to source repository authority.'], claims: [{ field: 'acceptance_state', value: 'DRAFT_NOT_ACCEPTED', sourceLocator: 'PROJECT_INSTRUCTIONS.md', sourceSha256: 'f85f1003500f16b754424afa0c0aa6a83af291d7ca9ec2f2749f1deda1276437' }] },
  { projectId: 'dnh-crm', laneId: 'rdcp-evidence-bridge', candidateSha: '92eb632bb07426ae5159c02bf9da549888e7caf1', observedHead: '92eb632bb07426ae5159c02bf9da549888e7caf1', fetchedAt: '2026-08-23T00:00:00Z', freshness: 'STALE', lifecycleState: 'STALE_EVIDENCE', recommendation: 'Deferred: stale evidence', status: 'stale', conflicts: [], claims: [{ field: 'audit_state', value: 'UNKNOWN', sourceLocator: 'AGENTS.md', sourceSha256: '6f8703ec09fc3e593edd5e9b878483fd889ae46977e0780e6b3139a3c8035e8d' }] },
];

export default function RepositoryPlannerPage() {
  const [selected, setSelected] = useState<PlannerLane | null>(null);
  const returnFocus = useRef<HTMLButtonElement | null>(null);
  const inspect = (lane: PlannerLane, trigger: HTMLButtonElement) => { returnFocus.current = trigger; setSelected(lane); };
  const close = () => { setSelected(null); window.setTimeout(() => returnFocus.current?.focus(), 0); };
  return <ThemeProvider theme={theme}><CssBaseline /><Container maxWidth="xl" component="main" sx={{ py: 4 }}><Stack spacing={3}><Box><Typography variant="h3" component="h1">Repository merge planner</Typography><Typography color="text.secondary">Deterministic, fixture-backed portfolio projection</Typography></Box><Alert severity="info"><strong>Projection only.</strong> Authority: NONE · is_proof: false. Control Tower and repository governance retain all terminal decisions.</Alert><Paper><PortfolioTable lanes={lanes} onInspect={inspect} /></Paper>{plannerExtensions.map((extension) => <Box key={extension.id}>{extension.render()}</Box>)}</Stack><LaneDetails lane={selected} onClose={close} /></Container></ThemeProvider>;
}
