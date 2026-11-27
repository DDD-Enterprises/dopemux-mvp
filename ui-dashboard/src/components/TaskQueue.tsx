import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Button, Paper, Typography } from '@mui/material';

import { dashboardApiHeaders, dashboardApiUrl } from '../config';
import {
  parseTaskQueue,
  parseTransitionResult,
  triggerFor,
  type MissingNote,
  type TaskQueueItem,
  type TaskQueueReading,
  type TransitionResult,
  type TransitionTrigger,
} from '../taskQueue';
import { brandTokens } from '../theme';
import { formatClockTime } from '../time';

const TASKS_ENDPOINT = `${dashboardApiUrl}/api/tasks`;

type View = { kind: 'waiting' } | { kind: 'failed'; message: string } | { kind: 'read'; reading: TaskQueueReading };

// A Start or Finish click. Nothing is shown as moved until a fresh GET /api/tasks shows it.
type Action =
  | { phase: 'pending'; title: string; url: string }
  | { phase: 'confirmed'; title: string; url: string; result: TransitionResult }
  | { phase: 'unconfirmed'; title: string; url: string; result: TransitionResult; why: string }
  | { phase: 'refused' | 'failed'; title: string; url: string; message: string; missingNotes: MissingNote[] | null };

// What a read returns to the code that started it. 'superseded' when a newer read started meanwhile:
// its result was not shown, so it must not confirm anything either.
type ReadOutcome = TaskQueueReading | null | 'superseded';

const transitionUrl = (itemId: string) => `${TASKS_ENDPOINT}/${encodeURIComponent(itemId)}/transition`;
const LABELS: Record<TransitionTrigger, string> = { start: 'Start', complete: 'Finish' };

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

const actionChipFor = (action: Action): { label: string; color: string } => {
  if (action.phase === 'pending') return { label: '[PENDING]', color: giltEdge };
  if (action.phase === 'confirmed') return { label: '[CONFIRMED]', color: ritualCyan };
  if (action.phase === 'unconfirmed') return { label: '[UNCONFIRMED]', color: giltEdge };
  if (action.phase === 'refused') return { label: '[REFUSED]', color: errorRed };
  return { label: '[FAILED]', color: errorRed };
};

const actor = (result: TransitionResult) => `written as ${result.actorId ?? 'an unknown actor'}, unverified`;

const actionLines = (action: Action): string[] => {
  if (action.phase === 'pending') return [`Writing "${action.title}": POST ${action.url}.`];
  if (action.phase === 'confirmed') {
    return [`"${action.title}" is now in ${action.result.newRole}: the fresh read shows it (${actor(action.result)}).`];
  }
  if (action.phase === 'unconfirmed') {
    return [
      `The orchestrator applied it: "${action.title}" moved from ${action.result.previousRole ?? 'unknown'} to ${action.result.newRole} (${actor(action.result)}).`,
      `Not confirmed: ${action.why}`,
      ...(action.result.reason ? [`Note: ${action.result.reason}.`] : []),
    ];
  }
  const lead = action.phase === 'refused' ? 'Refused' : 'Failed';
  return [
    `${lead}: POST ${action.url}: ${action.message}`,
    ...(action.missingNotes ?? []).map((note) => `Missing note: ${note.key}${note.description ? ` — ${note.description}` : ''}`),
  ];
};

// Cyan needs the fresh read to list the item in its new role. The read lists only work and queue,
// the first 20 of each, so Finish (terminal) can never be confirmed this way.
const confirm = (reading: ReadOutcome, itemId: string, result: TransitionResult): string | null => {
  if (reading === 'superseded') return 'a newer read replaced the one that would have confirmed it; refresh to see the item.';
  if (!reading || (reading.status !== 'ok' && reading.status !== 'empty')) return 'the fresh read failed, so the new role is not shown.';
  if (result.newRole !== 'work' && result.newRole !== 'queue') {
    return `the queue lists only work and queue items, so it cannot show ${result.newRole}.`;
  }
  const listed = reading.items.find((item) => item.id === itemId);
  if (listed?.role === result.newRole) return null;
  return `the fresh read does not show it in ${result.newRole} (it lists the first 20 work and 20 queue items).`;
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

  const [action, setAction] = useState<Action | null>(null);
  const writing = useRef(false);

  const read = useCallback(async (): Promise<ReadOutcome> => {
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
      return null;
    }
    if (!response.ok) {
      fail(` returned HTTP ${response.status}.`);
      return null;
    }
    let raw: unknown;
    try {
      raw = await response.json();
    } catch {
      fail(' returned invalid JSON.');
      return null;
    }
    const reading = parseTaskQueue(raw);
    if (!reading) {
      fail(' returned an unexpected payload.');
      return null;
    }
    if (latestRequest.current !== request) return 'superseded';
    settle({ kind: 'read', reading });
    return reading;
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

  const transition = async (item: TaskQueueItem) => {
    if (writing.current) return;
    writing.current = true;
    const url = transitionUrl(item.id);
    const trigger = triggerFor(item.role);
    const title = item.title;
    setAction({ phase: 'pending', title, url });

    let result: TransitionResult | null = null;
    let failure: string | null = null;
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { ...(dashboardApiHeaders as Record<string, string>), 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger, request_id: crypto.randomUUID() }),
      });
      let raw: unknown = null;
      try {
        raw = await response.json();
      } catch {
        raw = null;
      }
      result = parseTransitionResult(raw);
      if (!result) failure = `returned HTTP ${response.status} with an unexpected payload; the write outcome is unknown, refresh the queue.`;
    } catch {
      failure = 'no response (network error); the write outcome is unknown, refresh the queue.';
    }

    // Always re-read: the panel shows the store, never a guess about the write.
    const reading = await read();
    writing.current = false;

    if (!result) {
      setAction({ phase: 'failed', title, url, message: failure ?? 'unknown failure.', missingNotes: null });
      return;
    }
    if (result.status === 'applied') {
      const why = confirm(reading, item.id, result);
      setAction(why === null ? { phase: 'confirmed', title, url, result } : { phase: 'unconfirmed', title, url, result, why });
      return;
    }
    setAction({
      phase: result.status === 'refused' ? 'refused' : 'failed',
      title,
      url,
      message: result.reason ?? 'no reason given.',
      missingNotes: result.missingNotes,
    });
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

      {action && (
        <Box data-testid="task-action" aria-live="polite" sx={{ display: 'grid', gap: 0.5, mb: 2 }}>
          <Typography
            component="span"
            data-testid="task-action-chip"
            sx={{ ...monoSx, fontSize: '0.6875rem', letterSpacing: '0.08em', color: actionChipFor(action).color }}
          >
            {actionChipFor(action).label}
          </Typography>
          {actionLines(action).map((line) => (
            <Typography key={line} variant="body2" sx={{ ...monoSx, color: brandTokens.text.secondary, overflowWrap: 'anywhere' }}>
              {line}
            </Typography>
          ))}
        </Box>
      )}

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
                <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                  <Typography variant="caption" sx={{ ...monoSx, color: brandTokens.text.secondary }}>
                    {itemMeta(item)}
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    aria-label={`${LABELS[triggerFor(item.role)]}: ${item.title}`}
                    disabled={action?.phase === 'pending'}
                    onClick={() => void transition(item)}
                    sx={{ ml: 'auto' }}
                  >
                    {LABELS[triggerFor(item.role)]}
                  </Button>
                </Box>
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
          Start moves a queue item to work; Finish completes a work item. Writes are recorded as operator:cockpit, unverified until Wave 2C. Skip is not offered.
        </Typography>
      )}
    </Paper>
  );
};

export default TaskQueue;
