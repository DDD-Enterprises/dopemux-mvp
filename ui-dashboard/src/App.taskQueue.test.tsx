// @vitest-environment jsdom
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { act, cleanup, render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import App from './App';

class FakeSocket {
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  constructor(public url: string) {}
  close() {}
}

const STATE = 'http://localhost:8097/api/adhd-state';
const TASKS = 'http://localhost:8097/api/tasks';

const statePayload = {
  energy: { energy_level: 'medium' },
  attention: { attention_state: 'focused' },
  cognitive_load: { cognitive_load: 0.4, predicted_load_15min: 0.5 },
  recommendation: 'Finish the current task.',
};

const queuePayload = {
  source: 'task-orchestrator-mcp',
  endpoint: 'http://127.0.0.1:7890/mcp',
  status: 'ok',
  reason: null,
  project: { expected: { project_id: 'alpha-1', name: 'alpha' }, owner: { project_id: 'alpha-1', name: 'alpha' }, verdict: 'OK' },
  roles: ['work', 'queue'],
  items: [{ id: 'w1', title: 'Wire the queue', role: 'work', priority: 'high', parent_id: null, depth: 0, tags: null, complexity: null }],
  total: 1,
  fetched_at: '2026-11-16T12:00:00+00:00',
};

const byUrl = (responses: Record<string, unknown>) =>
  vi.fn(async (url: string) => {
    if (!(url in responses)) throw new TypeError('Failed to fetch');
    return { ok: true, status: 200, json: async () => responses[url] };
  });

beforeEach(() => {
  vi.stubGlobal('WebSocket', FakeSocket);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function renderApp(fetchMock: ReturnType<typeof byUrl>) {
  vi.stubGlobal('fetch', fetchMock);
  await act(async () => {
    render(<App />);
  });
}

test('the cockpit shows the real task queue where the seeded sequencer used to be', async () => {
  const fetchMock = byUrl({ [STATE]: statePayload, [TASKS]: queuePayload });
  await renderApp(fetchMock);

  expect(fetchMock.mock.calls.map(([url]) => url).sort()).toEqual([STATE, TASKS]);
  const list = screen.getByRole('list', { name: 'Work and queue items' });
  expect(within(list).getByText('Wire the queue')).toBeInTheDocument();
  expect(screen.getByTestId('task-queue-chip')).toHaveTextContent('[READ]');

  // The seeded tasks and their local controls are gone from the screen.
  expect(screen.queryByText('Implement LSTM cognitive predictor')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /skip/i })).not.toBeInTheDocument();
});

test('a task queue failure stays in its own panel and does not raise the state alert', async () => {
  await renderApp(byUrl({ [STATE]: statePayload }));

  expect(screen.getByTestId('task-queue-chip')).toHaveTextContent('[FAILED]');
  expect(screen.getByText(`Failed: GET ${TASKS}, no response (network error).`)).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByText('40%')).toBeInTheDocument();
});

test('a state failure does not hide a task queue that was read', async () => {
  await renderApp(byUrl({ [TASKS]: queuePayload }));

  expect(screen.getByRole('alert')).toHaveTextContent(`Failed: GET ${STATE}`);
  expect(screen.getByText('Wire the queue')).toBeInTheDocument();
});
