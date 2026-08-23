import { Alert, Box, Typography } from '@mui/material';

export default function ConflictPanel({ conflicts }: { conflicts: readonly string[] }) {
  if (!conflicts.length) return null;
  return <Box component="section"><Typography variant="h6" component="h3">Blocking conflicts</Typography>{conflicts.map((conflict) => <Alert severity="error" key={conflict}>{conflict}</Alert>)}</Box>;
}
