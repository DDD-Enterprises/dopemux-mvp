import { Alert, Box, List, ListItem, ListItemText, Typography } from '@mui/material';
import type { PlannerConflict } from './extensionTypes';

export default function ConflictPanel({ conflicts }: { conflicts: readonly PlannerConflict[] }) {
  if (!conflicts.length) return null;
  return <Box component="section"><Typography variant="h6" component="h3">Evidence conflicts</Typography>{conflicts.map((conflict) => <Alert severity={conflict.materiality === 'BLOCKING' ? 'error' : 'warning'} key={conflict.field}><Typography>{conflict.materiality === 'BLOCKING' ? 'Blocking' : 'Non-blocking'} · {conflict.field}: {conflict.values.join(' versus ')}. No winner selected.</Typography><List dense>{conflict.claims.map((claim) => <ListItem key={claim.claimId}><ListItemText primary={`${claim.value} — ${claim.sourceLocator}`} secondary={`SHA-256 ${claim.sourceSha256} · ${claim.materiality} · transformation ${claim.transformationId}`} /></ListItem>)}</List></Alert>)}</Box>;
}
