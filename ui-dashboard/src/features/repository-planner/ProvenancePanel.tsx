import { Box, List, ListItem, ListItemText, Typography } from '@mui/material';

import { CandidateShaChip } from './PortfolioTable';
import type { PlannerLane } from './extensionTypes';

export default function ProvenancePanel({ lane, onError }: { lane: PlannerLane; onError?: (message: string) => void }) {
  return <Box component="section"><Typography variant="h6" component="h3">Provenance</Typography><Box sx={{ display: 'flex', alignItems: 'center', gap: 1, my: 1 }}><Typography><strong>Observed head</strong></Typography><CandidateShaChip sha={lane.observedHead} labelPrefix="observed head SHA" onError={onError} /></Box><Typography><strong>Freshness</strong> {lane.freshness} at {lane.fetchedAt}</Typography><List>{lane.claims.map((claim) => <ListItem key={claim.claimId} disableGutters><ListItemText primary={`${claim.field}: ${claim.value}`} secondary={`${claim.sourceLocator} · SHA-256 ${claim.sourceSha256} · ${claim.materiality} · freshness ${claim.freshness} · transformation ${claim.transformationId}`} /></ListItem>)}</List></Box>;
}
