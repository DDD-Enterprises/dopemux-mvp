import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip } from '@mui/material';
import { Check, Copy } from 'lucide-react';

import type { PlannerLane } from './extensionTypes';

const statusColor = { ready: 'success', blocked: 'error', stale: 'warning', unknown: 'default', conflicting: 'warning' } as const;
const statusLabel = { ready: 'Ready evidence', blocked: 'Blocked evidence', stale: 'Stale evidence', unknown: 'Unknown: audit', conflicting: 'Conflicting evidence' } as const;

export default function PortfolioTable({ lanes, onInspect }: { lanes: readonly PlannerLane[]; onInspect: (lane: PlannerLane, trigger: HTMLButtonElement) => void }) {
  const [copiedSha, setCopiedSha] = useState<string | null>(null);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopySha = useCallback(async (sha: string) => {
    if (!navigator.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(sha);
      setCopiedSha(sha);
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setCopiedSha(null);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    };
  }, []);

  return (
    <TableContainer>
      <Table aria-label="Repository planning portfolio">
        <TableHead><TableRow><TableCell>Repository</TableCell><TableCell>Lane</TableCell><TableCell>Status</TableCell><TableCell>Candidate</TableCell><TableCell>Evidence</TableCell></TableRow></TableHead>
        <TableBody>
          {lanes.map((lane) => {
            const isCopied = copiedSha === lane.candidateSha;
            return (
              <TableRow key={`${lane.projectId}\0${lane.laneId}\0${lane.candidateSha}`}>
                <TableCell component="th" scope="row">{lane.projectId}</TableCell>
                <TableCell>{lane.laneId}</TableCell>
                <TableCell><Stack spacing={0.5} alignItems="flex-start"><Chip color={lane.states.includes('blocked') ? 'error' : lane.states.includes('stale') || lane.states.includes('conflicting') ? 'warning' : lane.states.includes('unknown') ? 'default' : 'success'} label={lane.recommendation} />{lane.states.map((state) => <Chip size="small" variant="outlined" color={statusColor[state]} label={statusLabel[state]} key={state} />)}</Stack></TableCell>
                <TableCell>
                  <Tooltip title={isCopied ? 'SHA copied!' : 'Click to copy full candidate SHA'} arrow>
                    <Chip
                      size="small"
                      variant="outlined"
                      icon={isCopied ? <Check size={12} aria-hidden="true" /> : <Copy size={12} aria-hidden="true" />}
                      label={lane.candidateSha.slice(0, 12)}
                      onClick={() => void handleCopySha(lane.candidateSha)}
                      aria-label={isCopied ? `Candidate SHA ${lane.candidateSha} copied` : `Copy full candidate SHA ${lane.candidateSha}`}
                      sx={{ fontFamily: 'monospace', cursor: 'copy' }}
                    />
                  </Tooltip>
                </TableCell>
                <TableCell><Button onClick={(event) => onInspect(lane, event.currentTarget)} aria-label={`Inspect ${lane.projectId} ${lane.laneId} ${lane.candidateSha}`}>Inspect</Button></TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
