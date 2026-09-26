import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip } from '@mui/material';
import { Check, Copy } from 'lucide-react';

import type { PlannerLane } from './extensionTypes';

const statusColor = { ready: 'success', blocked: 'error', stale: 'warning', unknown: 'default', conflicting: 'warning' } as const;
const statusLabel = { ready: 'Ready evidence', blocked: 'Blocked evidence', stale: 'Stale evidence', unknown: 'Unknown: audit', conflicting: 'Conflicting evidence' } as const;

function CandidateShaChip({ sha }: { sha: string }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = useCallback(() => {
    if (!navigator.clipboard?.writeText) return;
    void navigator.clipboard
      .writeText(sha)
      .then(() => {
        setCopied(true);
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => {
          setCopied(false);
          timeoutRef.current = null;
        }, 2000);
      })
      .catch(() => {});
  }, [sha]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <Tooltip title={copied ? 'SHA copied!' : 'Click to copy full candidate SHA'} arrow>
      <Chip
        size="small"
        variant="outlined"
        icon={copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
        label={<code>{sha.slice(0, 12)}</code>}
        onClick={handleCopy}
        aria-label={copied ? `Candidate SHA ${sha} copied` : `Copy candidate SHA: ${sha}`}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          '&:hover, &:focus-visible': {
            transform: 'translateY(-1px)',
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
              <TableCell><CandidateShaChip sha={lane.candidateSha} /></TableCell>
              <TableCell><Button onClick={(event) => onInspect(lane, event.currentTarget)} aria-label={`Inspect ${lane.projectId} ${lane.laneId} ${lane.candidateSha}`}>Inspect</Button></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
