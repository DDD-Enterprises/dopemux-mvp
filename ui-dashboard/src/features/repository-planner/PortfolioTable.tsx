import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Check, Copy } from 'lucide-react';

import { brandTokens } from '../../theme';
import type { PlannerLane } from './extensionTypes';

const statusColor = { ready: 'success', blocked: 'error', stale: 'warning', unknown: 'default', conflicting: 'warning' } as const;
const statusLabel = { ready: 'Ready evidence', blocked: 'Blocked evidence', stale: 'Stale evidence', unknown: 'Unknown: audit', conflicting: 'Conflicting evidence' } as const;

function CandidateShaChip({ sha }: { sha: string }) {
  const [copied, setCopied] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleCopy = useCallback(async () => {
    if (!navigator.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(sha);
      setCopied(true);
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setCopied(false);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch {
      // ignore copy failures
    }
  }, [sha]);

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
    };
  }, []);

  const shortSha = sha.slice(0, 12);

  return (
    <Tooltip title={copied ? 'SHA copied!' : 'Click to copy full candidate SHA'} arrow>
      <Chip
        size="small"
        variant="outlined"
        icon={copied ? <Check size={14} color={brandTokens.colors.serumMint} aria-hidden="true" /> : <Copy size={14} color={brandTokens.colors.ritualCyan} aria-hidden="true" />}
        label={shortSha}
        onClick={handleCopy}
        aria-label={copied ? `Candidate SHA ${shortSha} copied to clipboard` : `Candidate SHA ${shortSha}. Click to copy full SHA`}
        sx={{
          fontFamily: 'monospace',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          borderColor: copied ? alpha(brandTokens.colors.serumMint, 0.6) : alpha(brandTokens.colors.ritualCyan, 0.4),
          color: copied ? brandTokens.colors.serumMint : brandTokens.colors.ritualCyan,
          bgcolor: alpha(copied ? brandTokens.colors.serumMint : brandTokens.colors.ritualCyan, 0.08),
          '&:hover': {
            borderColor: copied ? brandTokens.colors.serumMint : brandTokens.colors.ritualCyan,
            bgcolor: alpha(copied ? brandTokens.colors.serumMint : brandTokens.colors.ritualCyan, 0.16),
            transform: 'translateY(-1px)',
          },
          ...(copied && {
            animation: 'sha-copy-pulse 0.4s ease-out',
            '@keyframes sha-copy-pulse': {
              '0%': { transform: 'scale(1)' },
              '50%': { transform: 'scale(1.05)', boxShadow: `0 0 12px ${alpha(brandTokens.colors.serumMint, 0.4)}` },
              '100%': { transform: 'scale(1)' },
            },
          }),
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
