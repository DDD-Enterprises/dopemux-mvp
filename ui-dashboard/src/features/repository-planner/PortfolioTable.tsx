import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Chip, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tooltip } from '@mui/material';
import { Check, AlertTriangle } from 'lucide-react';

import type { PlannerLane } from './extensionTypes';

const statusColor = { ready: 'success', blocked: 'error', stale: 'warning', unknown: 'default', conflicting: 'warning' } as const;
const statusLabel = { ready: 'Ready evidence', blocked: 'Blocked evidence', stale: 'Stale evidence', unknown: 'Unknown: audit', conflicting: 'Conflicting evidence' } as const;

export interface CandidateShaChipProps {
  sha: string;
  onError?: (message: string) => void;
  labelPrefix?: string;
}

export function CandidateShaChip({ sha, onError, labelPrefix = 'candidate SHA' }: CandidateShaChipProps) {
  const shortSha = sha.slice(0, 12);
  const [isCopied, setIsCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const copyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activeShaRef = useRef(sha);
  activeShaRef.current = sha;

  useEffect(() => {
    setIsCopied(false);
    setCopyFailed(false);
    if (copyTimeoutRef.current) {
      clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = null;
    }
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current);
        copyTimeoutRef.current = null;
      }
    };
  }, [sha]);

  const handleCopy = useCallback(async () => {
    const currentSha = activeShaRef.current;
    if (!navigator.clipboard?.writeText) {
      setCopyFailed(true);
      onError?.('Clipboard API is not supported in this browser or context.');
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setCopyFailed(false);
        copyTimeoutRef.current = null;
      }, 2000);
      return;
    }

    try {
      await navigator.clipboard.writeText(currentSha);
      if (activeShaRef.current !== currentSha) return;
      setIsCopied(true);
      setCopyFailed(false);
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setIsCopied(false);
        copyTimeoutRef.current = null;
      }, 2000);
    } catch (err) {
      if (activeShaRef.current !== currentSha) return;
      const errorMsg = err instanceof Error ? err.message : String(err);
      setCopyFailed(true);
      onError?.(`Failed to copy ${labelPrefix}: ${errorMsg}`);
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = setTimeout(() => {
        setCopyFailed(false);
        copyTimeoutRef.current = null;
      }, 2000);
    }
  }, [labelPrefix, onError]);

  const tooltipTitle = isCopied
    ? 'SHA copied!'
    : copyFailed
      ? `Failed to copy ${labelPrefix}`
      : `Copy ${labelPrefix} ${shortSha}`;

  const chipLabel = isCopied
    ? `${labelPrefix.charAt(0).toUpperCase() + labelPrefix.slice(1)} ${shortSha} copied`
    : copyFailed
      ? `Copy failed: ${shortSha}`
      : shortSha;

  const ariaLabel = isCopied
    ? `${labelPrefix.charAt(0).toUpperCase() + labelPrefix.slice(1)} ${shortSha} copied`
    : copyFailed
      ? `Failed to copy ${labelPrefix} ${shortSha}`
      : `Copy ${labelPrefix} ${shortSha}`;

  return (
    <Tooltip title={tooltipTitle} arrow describeChild>
      <Chip
        size="small"
        variant="outlined"
        onClick={handleCopy}
        icon={isCopied ? <Check size={14} aria-hidden="true" /> : copyFailed ? <AlertTriangle size={14} aria-hidden="true" /> : undefined}
        label={chipLabel}
        aria-label={ariaLabel}
        color={isCopied ? 'success' : copyFailed ? 'error' : 'default'}
        sx={{
          fontFamily: 'monospace',
          cursor: 'pointer',
          '@media (prefers-reduced-motion: reduce)': {
            transition: 'none',
            animation: 'none',
          },
        }}
      />
    </Tooltip>
  );
}

export default function PortfolioTable({
  lanes,
  onInspect,
  onError,
}: {
  lanes: readonly PlannerLane[];
  onInspect: (lane: PlannerLane, trigger: HTMLButtonElement) => void;
  onError?: (message: string) => void;
}) {
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
              <TableCell><CandidateShaChip sha={lane.candidateSha} onError={onError} /></TableCell>
              <TableCell><Button onClick={(event) => onInspect(lane, event.currentTarget)} aria-label={`Inspect ${lane.projectId} ${lane.laneId} ${lane.candidateSha}`}>Inspect</Button></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
