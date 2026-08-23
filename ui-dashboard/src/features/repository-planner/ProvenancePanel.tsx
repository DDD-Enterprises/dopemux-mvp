import { Box, List, ListItem, ListItemText, Typography } from '@mui/material';

import type { PlannerLane } from './extensionTypes';

export default function ProvenancePanel({ lane }: { lane: PlannerLane }) {
  return <Box component="section"><Typography variant="h6" component="h3">Provenance</Typography><Typography><strong>Observed head</strong> <code>{lane.observedHead}</code></Typography><Typography><strong>Freshness</strong> {lane.freshness} at {lane.fetchedAt}</Typography><List>{lane.claims.map((claim) => <ListItem key={claim.claimId} disableGutters><ListItemText primary={`${claim.field}: ${claim.value}`} secondary={`${claim.sourceLocator} · SHA-256 ${claim.sourceSha256} · transformation ${claim.transformationId}`} /></ListItem>)}</List></Box>;
}
