// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import TaskQueue from '../TaskQueue';
import { brandTokens } from '../../theme';

const TASKS = 'http://localhost:8097/api/tasks';
const MCP = 'http://127.0.0.1:7890/mcp';

const payload = (overrides: Record<string, unknown> = {}) => ({
  source: 'task-orchestrator-mcp',
  endpoint: MCP,
  status: 'ok',
  reason: null,
  project: { expected: { project_id: 'alpha-1', name: 'alpha' }, owner: { project_id: 'alpha-1', name: 'alpha' }, verdict: 'OK' },
  roles: ['work', 'queue'],
  items: [
    { id: 'w1', title: 'Wire the queue', role: 'work', priority: 'high', parent_id: null, depth: 0, tags: ['cockpit', 'backend'], complexity: 3 },
    { id: 'q1', title: 'Write the tests', role: 'queue', priority: null, parent_id: 'w1', depth: 1, tags: null, complexity: null },
  ],
  total: 2,
  fetched_at: '2026-11-16T12:00:00+00:00',
  ...overrides,
});

const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function renderQueue(fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal('fetch', fetchMock);
  await act(async () => {
    render(<TaskQueue />);
  });
}

const chip = () => screen.getByTestId('task-queue-chip');
const toRgb = (hex: string) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgb(${n >> 16}, ${(n >> 8) & 255}, ${n & 255})`;
};

test('while the request is pending it says what it is waiting for, in yellow', async () => {
  await renderQueue(vi.fn().mockReturnValue(new Promise(() => {})));

  expect(chip()).toHaveTextContent('[WAITING]');
  expect(chip()).toHaveStyle({ color: toRgb(brandTokens.colors.giltEdge) });
  expect(screen.getByRole('status')).toHaveTextContent(`Reading GET ${TASKS}.`);
  expect(screen.queryByRole('list')).not.toBeInTheDocument();
});

test('ok: lists real items in the order received, with unknown shown as unknown', async () => {
  const fetchMock = vi.fn().mockResolvedValue(ok(payload()));
  await renderQueue(fetchMock);

  expect(fetchMock).toHaveBeenCalledWith(TASKS, expect.anything());
  expect(chip()).toHaveTextContent('[READ]');
  expect(chip()).toHaveStyle({ color: toRgb(brandTokens.colors.ritualCyan) });
  expect(screen.getByRole('status')).toHaveTextContent(/^task-orchestrator · alpha · read at \d\d:\d\d:\d\d\.$/);

  const rows = within(screen.getByRole('list', { name: 'Work and queue items' })).getAllByRole('listitem');
  expect(rows).toHaveLength(2);
  expect(rows[0]).toHaveTextContent('[WORK]');
  expect(rows[0]).toHaveTextContent('Wire the queue');
  expect(rows[0]).toHaveTextContent('priority high · complexity 3 · cockpit, backend');
  expect(rows[1]).toHaveTextContent('[QUEUE]');
  expect(rows[1]).toHaveTextContent('Write the tests');
  expect(rows[1]).toHaveTextContent('priority unknown · complexity unknown');

  expect(screen.queryByText(/SAMPLE/)).not.toBeInTheDocument();
  expect(screen.queryByText(/Showing/)).not.toBeInTheDocument();
});

test('ok: says so when the source holds more than it returned, or does not say how many', async () => {
  await renderQueue(vi.fn().mockResolvedValue(ok(payload({ total: 31 }))));
  expect(screen.getByText('Showing 2 of 31.')).toBeInTheDocument();
  cleanup();

  await renderQueue(vi.fn().mockResolvedValue(ok(payload({ total: null }))));
  expect(screen.getByText('Showing 2; total unknown.')).toBeInTheDocument();
});

test('the panel is read-only: no control changes a task', async () => {
  await renderQueue(vi.fn().mockResolvedValue(ok(payload())));

  expect(screen.getAllByRole('button').map((button) => button.textContent)).toEqual(['Refresh queue']);
  expect(screen.getByText('Read-only: start, finish and skip are not wired to the orchestrator.')).toBeInTheDocument();
});

test('empty is a result, not a failure', async () => {
  await renderQueue(vi.fn().mockResolvedValue(ok(payload({ status: 'empty', items: [], total: 0 }))));

  expect(chip()).toHaveTextContent('[READ]');
  expect(screen.getByText('No work or queue items for alpha.')).toBeInTheDocument();
  expect(screen.queryByRole('list')).not.toBeInTheDocument();
});

test('unavailable renders as unavailable with the reason and both endpoints, never as an empty list', async () => {
  const reason = 'port 7890 owner could not be proven (UNKNOWN): docker ps unavailable: docker ps timed out';
  await renderQueue(vi.fn().mockResolvedValue(ok(payload({ status: 'unavailable', reason, items: [], total: null }))));

  expect(chip()).toHaveTextContent('[UNAVAILABLE]');
  expect(chip()).toHaveStyle({ color: toRgb(brandTokens.colors.giltEdge) });
  expect(screen.getByRole('status')).toHaveTextContent(`Task queue unavailable: ${reason}.`);
  expect(screen.getByRole('status')).toHaveTextContent(`Source ${MCP}, read through GET ${TASKS}.`);
  expect(screen.queryByText(/No work or queue items/)).not.toBeInTheDocument();
  expect(screen.queryByRole('list')).not.toBeInTheDocument();
});

test('wrong_project is blocked in red, names the owner and the next action, and shows no tasks', async () => {
  const reason = 'port 7890 is serving project beta (container to-beta), not this one';
  const body = payload({ status: 'wrong_project', reason });
  await renderQueue(vi.fn().mockResolvedValue(ok(body)));

  expect(chip()).toHaveTextContent('[BLOCKED]');
  expect(chip()).toHaveStyle({ color: toRgb(brandTokens.colors.errorRed) });
  expect(screen.getByRole('status')).toHaveTextContent(`Blocked: ${reason}.`);
  expect(screen.getByRole('status')).toHaveTextContent('Next: run dopemux mcp switch-project in alpha, then refresh.');
  expect(screen.queryByText('Wire the queue')).not.toBeInTheDocument();
  expect(screen.queryByRole('list')).not.toBeInTheDocument();
});

test.each([
  ['a network error', () => vi.fn().mockRejectedValue(new TypeError('Failed to fetch')), `Failed: GET ${TASKS}, no response (network error).`],
  ['an HTTP error', () => vi.fn().mockResolvedValue({ ok: false, status: 502, json: async () => ({}) }), `Failed: GET ${TASKS} returned HTTP 502.`],
  ['invalid JSON', () => vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => Promise.reject(new SyntaxError('bad')) }), `Failed: GET ${TASKS} returned invalid JSON.`],
  ['an unexpected payload', () => vi.fn().mockResolvedValue(ok({ energy: { energy_level: 'medium' } })), `Failed: GET ${TASKS} returned an unexpected payload.`],
])('%s is failed in red and names the endpoint', async (_label, makeFetch, message) => {
  await renderQueue(makeFetch());

  expect(chip()).toHaveTextContent('[FAILED]');
  expect(chip()).toHaveStyle({ color: toRgb(brandTokens.colors.errorRed) });
  expect(screen.getByRole('status')).toHaveTextContent(message);
  expect(screen.getByRole('status')).toHaveTextContent('Next: check that the adhd-dashboard service is running at http://localhost:8097, then refresh.');
  expect(screen.queryByRole('list')).not.toBeInTheDocument();
});

test('Refresh reads again and replaces what was shown', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
    .mockResolvedValueOnce(ok(payload()));
  await renderQueue(fetchMock);
  expect(chip()).toHaveTextContent('[FAILED]');

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Refresh queue' }));
  });

  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(chip()).toHaveTextContent('[READ]');
  expect(screen.getByText('Wire the queue')).toBeInTheDocument();
});

test('a slow earlier read cannot overwrite a newer one', async () => {
  let resolveFirst: (value: unknown) => void = () => {};
  const fetchMock = vi
    .fn()
    .mockReturnValueOnce(new Promise((resolve) => (resolveFirst = resolve)))
    .mockResolvedValueOnce(ok(payload({ status: 'empty', items: [], total: 0 })));
  await renderQueue(fetchMock);

  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Refresh queue' }));
  });
  await act(async () => {
    resolveFirst(ok(payload()));
  });

  expect(screen.getByText('No work or queue items for alpha.')).toBeInTheDocument();
  expect(screen.queryByText('Wire the queue')).not.toBeInTheDocument();
});

test('nothing in the panel is a tab stop except the refresh button', async () => {
  await renderQueue(vi.fn().mockResolvedValue(ok(payload())));

  expect(document.querySelectorAll('[tabindex]')).toHaveLength(1);
});
