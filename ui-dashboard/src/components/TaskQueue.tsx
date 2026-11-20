import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Button, Paper, Typography } from '@mui/material';

import { dashboardApiHeaders, dashboardApiUrl } from '../config';
import { parseTaskQueue, type TaskQueueItem, type TaskQueueReading } from '../taskQueue';
import { brandTokens } from '../theme';
import { formatClockTime } from '../time';

const TASKS_ENDPOINT = `${dashboardApiUrl}/api/tasks`;

type View = { kind: 'waiting' } | { kind: 'failed'; message: string } | { kind: 'read'; reading: TaskQueueReading };

// Cockpit status colors: cyan = a real read, yellow = waiting or degraded, red = failed or blocked.
const { ritualCyan, giltEdge, errorRed } = brandTokens.colors;

const chipFor = (view: View): { label: string; color: string } => {
  if (view.kind === 'waiting') return { label: '[WAITING]', color: giltEdge };
  if (view.kind === 'failed') return { label: '[FAILED]', color: errorRed };
  if (view.reading.status === 'wrong_project') return { label: '[BLOCKED]', color: errorRed };
  if (view.reading.status === 'unavailable') return { label: '[UNAVAILABLE]', color: giltEdge };
  return { label: '[READ]', color: ritualCyan };
};

const statusLines = (view: View): string[] => {
  if (view.kind === 'waiting') return [`Reading GET ${TASKS_ENDPOINT}.`];
  if (view.kind === 'failed') {
    return [view.message, `Next: check that the adhd-dashboard service is running at ${dashboardApiUrl}, then refresh.`];
  }
  const { reading } = view;
  if (reading.status === 'wrong_project') {
    return [
      `Blocked: ${reading.reason ?? 'the orchestrator is serving another project'}.`,
      `Next: run dopemux mcp switch-project in ${reading.projectName ?? 'this project'}, then refresh.`,
    ];
  }
  if (reading.status === 'unavailable') {
    return [
      `Task queue unavailable: ${reading.reason ?? 'no reason given'}.`,
      `Source ${reading.sourceEndpoint ?? 'unknown'}, read through GET ${TASKS_ENDPOINT}.`,
    ];
  }
  const readAt = reading.fetchedAt ? formatClockTime(reading.fetchedAt) : 'an unknown time';
  return [`task-orchestrator · ${reading.projectName ?? 'project unknown'} · read at ${readAt}.`];
};

const itemMeta = (item: TaskQueueItem): string =>
  [
    `priority ${item.priority ?? 'unknown'}`,
    `complexity ${item.complexity ?? 'unknown'}`,
    ...(item.tags && item.tags.length > 0 ? [item.tags.join(', ')] : []),
  ].join(' · ');

const countLine = (reading: TaskQueueReading): string | null => {
  const shown = reading.items.length;
  if (reading.total === null) return `Showing ${shown}; total unknown.`;
  return reading.total > shown ? `Showing ${shown} of ${reading.total}.` : null;
};

const monoSx = { fontFamily: brandTokens.fonts.mono } as const;

const TaskQueue: React.FC = () => {
  const [view, setView] = useState<View>({ kind: 'waiting' });
  // Only the newest request may set the view; an unmounted panel sets nothing.
  const latestRequest = useRef(0);

  const read = useCallback(async () => {
    const request = ++latestRequest.current;
    const settle = (next: View) => {
      if (latestRequest.current === request) setView(next);
    };
    const fail = (detail: string) => settle({ kind: 'failed', message: `Failed: GET ${TASKS_ENDPOINT}${detail}` });

    let response: Response;
    try {
      response = await fetch(TASKS_ENDPOINT, { headers: dashboardApiHeaders });
    } catch {
      fail(', no response (network error).');
      return;
    }
    if (!response.ok) {
      fail(` returned HTTP ${response.status}.`);
      return;
    }
    let raw: unknown;
    try {
      raw = await response.json();
    } catch {
      fail(' returned invalid JSON.');
      return;
    }
    const reading = parseTaskQueue(raw);
    if (!reading) {
      fail(' returned an unexpected payload.');
      return;
    }
    settle({ kind: 'read', reading });
  }, []);

  // The first read starts from the initial 'waiting' view, so the effect sets no state itself.
  useEffect(() => {
    void read();
    return () => {
      latestRequest.current += 1;
    };
  }, [read]);

  const refresh = () => {
    setView({ kind: 'waiting' });
    void read();
  };

  const chip = chipFor(view);
  const reading = view.kind === 'read' ? view.reading : null;
  const count = reading?.status === 'ok' ? countLine(reading) : null;

  return (
    <Paper sx={{ p: 3, borderRadius: 3, background: brandTokens.gradients.focusCard, height: '100%' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1.5, mb: 2 }}>
        <Typography variant="h6" component="h2" sx={{ letterSpacing: '0.16em' }}>
          Task Queue
        </Typography>
        <Typography
          component="span"
          data-testid="task-queue-chip"
          sx={{
            ...monoSx,
            fontSize: '0.6875rem',
            letterSpacing: '0.08em',
            color: chip.color,
            border: `1px solid ${chip.color}`,
            borderRadius: '999px',
            px: 1,
            py: 0.25,
          }}
        >
          {chip.label}
        </Typography>
        {/* Never disabled: a read that hangs must not leave the panel without a way to read again. */}
        <Button size="small" variant="outlined" onClick={refresh} sx={{ ml: 'auto' }}>
          Refresh queue
        </Button>
      </Box>

      <Box role="status" sx={{ display: 'grid', gap: 0.5, mb: 2 }}>
        {statusLines(view).map((line) => (
          <Typography key={line} variant="body2" sx={{ ...monoSx, color: brandTokens.text.secondary, overflowWrap: 'anywhere' }}>
            {line}
          </Typography>
        ))}
      </Box>

      {reading?.status === 'empty' && (
        <Typography variant="body2">{`No work or queue items for ${reading.projectName ?? 'this project'}.`}</Typography>
      )}

      {reading?.status === 'ok' && (
        <>
          <Box component="ul" aria-label="Work and queue items" sx={{ listStyle: 'none', p: 0, m: 0, display: 'grid', gap: 1 }}>
            {reading.items.map((item) => (
              <Box
                component="li"
                key={`${item.role}:${item.id}`}
                sx={{ p: 1.5, borderRadius: 2, border: `1px solid ${brandTokens.borders.strong}` }}
              >
                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                  <Typography
                    component="span"
                    sx={{
                      ...monoSx,
                      fontSize: '0.6875rem',
                      color: item.role === 'work' ? ritualCyan : brandTokens.text.secondary,
                    }}
                  >
                    {item.role === 'work' ? '[WORK]' : '[QUEUE]'}
                  </Typography>
                  <Typography variant="body1" sx={{ overflowWrap: 'anywhere' }}>
                    {item.title}
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ ...monoSx, color: brandTokens.text.secondary }}>
                  {itemMeta(item)}
                </Typography>
              </Box>
            ))}
          </Box>
          {count && (
            <Typography variant="caption" sx={{ ...monoSx, display: 'block', mt: 1.5, color: brandTokens.text.secondary }}>
              {count}
            </Typography>
          )}
        </>
      )}

      {reading && reading.status !== 'unavailable' && reading.status !== 'wrong_project' && (
        <Typography variant="caption" sx={{ display: 'block', mt: 2, color: brandTokens.text.muted }}>
          Read-only: start, finish and skip are not wired to the orchestrator.
        </Typography>
      )}
    </Paper>
  );
};

export default TaskQueue;
