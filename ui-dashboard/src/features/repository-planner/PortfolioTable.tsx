import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip } from '@mui/material';
import { Check, Copy } from 'lucide-react';

import type { PlannerLane } from './extensionTypes';

const statusColor = { ready: 'success', blocked: 'error', stale: 'warning', unknown: 'default', conflicting: 'warning' } as const;
const statusLabel = { ready: 'Ready evidence', blocked: 'Blocked evidence', stale: 'Stale evidence', unknown: 'Unknown: audit', conflicting: 'Conflicting evidence' } as const;

function CandidateShaChip({ candidateSha }: { candidateSha: string }) {
  const [isCopied, setIsCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = useCallback(async () => {
    if (!navigator.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(candidateSha);
      setIsCopied(true);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        setIsCopied(false);
        timeoutRef.current = null;
      }, 2000);
    } catch {
      // ignore
    }
  }, [candidateSha]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const shortSha = candidateSha.slice(0, 12);

  return (
    <Tooltip title={isCopied ? 'SHA copied!' : 'Click to copy full candidate SHA'} arrow>
      <Chip
        size="small"
        variant="outlined"
        icon={isCopied ? <Check size={12} aria-hidden="true" /> : <Copy size={12} aria-hidden="true" />}
        label={shortSha}
        onClick={handleCopy}
        aria-label={
          isCopied
            ? 'Candidate SHA copied to clipboard'
            : `Candidate SHA ${shortSha}. Click to copy full candidate SHA`
        }
        sx={{
          fontFamily: 'monospace',
          cursor: 'copy',
          transition: 'all 0.2s ease',
          '&:hover, &:focus-visible': {
            borderColor: 'primary.main',
            backgroundColor: (theme) => `${theme.palette.primary.main}14`,
          },
        }}
      />
    </Tooltip>
  );
}

export default function PortfolioTable({ lanes, onInspect }: { lanes: readonly PlannerLane[]; onInspect: (lane: PlannerLane, trigger: HTMLButtonElement) => void }) {
  return (
    <TableContainer>
      <Table aria-label="Repository planning portfolio">
        <TableHead><TableRow><TableCell>Repository</TableCell><TableCell>Lane</TableCell><TableCell>Status</TableCell><TableCell>Candidate</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead>
        <TableBody>
          {lanes.map((lane) => (
            <TableRow key={`${lane.projectId}\0${lane.laneId}\0${lane.candidateSha}`}>
              <TableCell component="th" scope="row">{lane.projectId}</TableCell>
              <TableCell>{lane.laneId}</TableCell>
              <TableCell><Stack spacing={0.5} alignItems="flex-start"><Chip color={lane.states.includes('blocked') ? 'error' : lane.states.includes('stale') || lane.states.includes('conflicting') ? 'warning' : lane.states.includes('unknown') ? 'default' : 'success'} label={lane.recommendation} />{lane.states.map((state) => <Chip size="small" variant="outlined" color={statusColor[state]} label={statusLabel[state]} key={state} />)}</Stack></TableCell>
              <TableCell><CandidateShaChip candidateSha={lane.candidateSha} /></TableCell>
              <TableCell><Button onClick={(event) => onInspect(lane, event.currentTarget)} aria-label={`Inspect ${lane.projectId} ${lane.laneId} ${lane.candidateSha}`}>Inspect</Button></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
