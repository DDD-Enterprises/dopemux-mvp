import { Button, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';

import type { PlannerLane } from './extensionTypes';

const statusColor = { ready: 'success', blocked: 'error', stale: 'warning', unknown: 'default' } as const;

export default function PortfolioTable({ lanes, onInspect }: { lanes: readonly PlannerLane[]; onInspect: (lane: PlannerLane, trigger: HTMLButtonElement) => void }) {
  return (
    <TableContainer>
      <Table aria-label="Repository planning portfolio">
        <TableHead><TableRow><TableCell>Repository</TableCell><TableCell>Lane</TableCell><TableCell>Status</TableCell><TableCell>Candidate</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead>
        <TableBody>
          {lanes.map((lane) => (
            <TableRow key={`${lane.projectId}:${lane.laneId}`}>
              <TableCell component="th" scope="row">{lane.projectId}</TableCell>
              <TableCell>{lane.laneId}</TableCell>
              <TableCell><Stack spacing={0.5} alignItems="flex-start"><Chip color={statusColor[lane.status]} label={lane.recommendation} />{lane.claims.filter((claim) => claim.value === 'UNKNOWN').map((claim) => <Typography variant="caption" key={claim.field}>Unknown evidence: {claim.field}</Typography>)}</Stack></TableCell>
              <TableCell><code>{lane.candidateSha.slice(0, 12)}</code></TableCell>
              <TableCell><Button onClick={(event) => onInspect(lane, event.currentTarget)} aria-label={`Inspect ${lane.projectId} ${lane.laneId}`}>Inspect</Button></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
