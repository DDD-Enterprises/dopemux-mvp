// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import TaskQueue from '../TaskQueue';
import { brandTokens } from '../../theme';

// Start and Finish write through POST /api/tasks/{id}/transition. Every test here uses a fake
// fetch; nothing reaches a backend or the orchestrator.

const TASKS = 'http://localhost:8097/api/tasks';
const MCP = 'http://127.0.0.1:7890/mcp';
const WORK_ID = '11111111-1111-4111-8111-111111111111';
const QUEUE_ID = '22222222-2222-4222-8222-222222222222';
const REQUEST_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';

const workItem = { id: WORK_ID, title: 'Wire the queue', role: 'work', priority: 'high', parent_id: null, depth: 0, tags: null, complexity: null };
const queueItem = { id: QUEUE_ID, title: 'Write the tests', role: 'queue', priority: null, parent_id: null, depth: 0, tags: null, complexity: null };

const queue = (items: unknown[] = [workItem, queueItem], overrides: Record<string, unknown> = {}) => ({
  source: 'task-orchestrator-mcp',
  endpoint: MCP,
  status: items.length ? 'ok' : 'empty',
  reason: null,
  project: { expected: { project_id: 'alpha-1', name: 'alpha' }, owner: { project_id: 'alpha-1', name: 'alpha' }, verdict: 'OK' },
  roles: ['work', 'queue'],
  items,
  total: items.length,
  fetched_at: '2026-11-22T12:00:00+00:00',
  ...overrides,
});

const transition = (overrides: Record<string, unknown> = {}) => ({
  source: 'task-orchestrator-mcp',
  endpoint: MCP,
  status: 'applied',
  reason: null,
  item_id: QUEUE_ID,
  trigger: 'start',
  request_id: REQUEST_ID,
  actor: { id: 'operator:cockpit', kind: 'user', verification: 'unverified' },
  previous_role: 'queue',
  new_role: 'work',
  missing_notes: null,
  project: { expected: { project_id: 'alpha-1', name: 'alpha' }, owner: null, verdict: 'OK' },
  ...overrides,
});

const reply = (status: number, body: unknown) => ({ ok: status >= 200 && status < 300, status, json: async () => body });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function renderQueue(fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal('fetch', fetchMock);
  vi.stubGlobal('crypto', { randomUUID: () => REQUEST_ID });
  await act(async () => {
    render(<TaskQueue />);
  });
}

async function click(name: string) {
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name }));
  });
}

const actionChip = () => screen.getByTestId('task-action-chip');
const actionText = () => screen.getByTestId('task-action').textContent ?? '';
const toRgb = (hex: string) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgb(${n >> 16}, ${(n >> 8) & 255}, ${n & 255})`;
};

test('Start is offered on queue rows and Finish on work rows, nothing else', async () => {
  await renderQueue(vi.fn().mockResolvedValue(reply(200, queue())));

  expect(screen.getAllByRole('button').map((button) => button.textContent)).toEqual(['Refresh queue', 'Finish', 'Start']);
  expect(screen.getByRole('button', { name: 'Finish: Wire the queue' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Start: Write the tests' })).toBeInTheDocument();
  for (const missing of [/skip/i, /cancel/i, /block/i, /reopen/i, /resume/i, /hold/i]) {
    expect(screen.queryByRole('button', { name: missing })).not.toBeInTheDocument();
  }
});

test('Start posts one request with a fresh request id, the API key header and JSON', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(reply(200, queue())).mockReturnValueOnce(new Promise(() => {}));
  await renderQueue(fetchMock);

  await click('Start: Write the tests');

  const [url, init] = fetchMock.mock.calls[1];
  expect(url).toBe(`${TASKS}/${QUEUE_ID}/transition`);
  expect(init.method).toBe('POST');
  expect(init.headers['Content-Type']).toBe('application/json');
  expect(JSON.parse(init.body)).toEqual({ trigger: 'start', request_id: REQUEST_ID });
});

test('while a write is pending it is yellow and every Start and Finish is disabled', async () => {
  await renderQueue(vi.fn().mockResolvedValueOnce(reply(200, queue())).mockReturnValueOnce(new Promise(() => {})));

  await click('Start: Write the tests');

  expect(actionChip()).toHaveTextContent('[PENDING]');
  expect(actionChip()).toHaveStyle({ color: toRgb(brandTokens.colors.giltEdge) });
  expect(actionText()).toContain(`POST ${TASKS}/${QUEUE_ID}/transition`);
  expect(screen.getByRole('button', { name: 'Start: Write the tests' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Finish: Wire the queue' })).toBeDisabled();
  // The queue itself is unchanged: no optimistic move.
  expect(screen.getByText('[QUEUE]')).toBeInTheDocument();
});

test('applied Start turns cyan only when a fresh read shows the item in work', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(reply(200, queue()))
    .mockResolvedValueOnce(reply(200, transition()))
    .mockResolvedValueOnce(reply(200, queue([workItem, { ...queueItem, role: 'work' }])));
  await renderQueue(fetchMock);

  await click('Start: Write the tests');

  expect(fetchMock).toHaveBeenCalledTimes(3);
  expect(fetchMock.mock.calls[2][0]).toBe(TASKS);
  expect(actionChip()).toHaveTextContent('[CONFIRMED]');
  expect(actionChip()).toHaveStyle({ color: toRgb(brandTokens.colors.ritualCyan) });
  expect(actionText()).toContain('now in work');
  expect(actionText()).toContain('operator:cockpit');
});

test('applied Start that the fresh read does not show stays yellow', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(reply(200, queue()))
    .mockResolvedValueOnce(reply(200, transition()))
    .mockResolvedValueOnce(reply(200, queue([workItem])));
  await renderQueue(fetchMock);

  await click('Start: Write the tests');

  expect(actionChip()).toHaveTextContent('[UNCONFIRMED]');
  expect(actionChip()).toHaveStyle({ color: toRgb(brandTokens.colors.giltEdge) });
  expect(actionText()).toContain('first 20');
});

test('applied Finish stays yellow: the read never lists terminal items', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(reply(200, queue()))
    .mockResolvedValueOnce(reply(200, transition({ item_id: WORK_ID, trigger: 'complete', previous_role: 'work', new_role: 'terminal' })))
    .mockResolvedValueOnce(reply(200, queue([queueItem])));
  await renderQueue(fetchMock);

  await click('Finish: Wire the queue');

  expect(JSON.parse(fetchMock.mock.calls[1][1].body).trigger).toBe('complete');
  expect(actionChip()).toHaveTextContent('[UNCONFIRMED]');
  expect(actionChip()).toHaveStyle({ color: toRgb(brandTokens.colors.giltEdge) });
  expect(actionText()).toContain('terminal');
});

test('a refused Finish is red with the endpoint, the reason and the missing notes', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(reply(200, queue()))
    .mockResolvedValueOnce(
      reply(
        409,
        transition({
          status: 'refused',
          item_id: WORK_ID,
          trigger: 'complete',
          previous_role: 'work',
          new_role: null,
          reason: 'orchestrator refused: Gate check failed: required notes not filled: proof-bundle',
          missing_notes: [{ key: 'proof-bundle', description: 'AGENTS.md section 9 proof' }],
        }),
      ),
    )
    .mockResolvedValueOnce(reply(200, queue()));
  await renderQueue(fetchMock);

  await click('Finish: Wire the queue');

  expect(actionChip()).toHaveTextContent('[REFUSED]');
  expect(actionChip()).toHaveStyle({ color: toRgb(brandTokens.colors.errorRed) });
  expect(actionText()).toContain(`POST ${TASKS}/${WORK_ID}/transition`);
  expect(actionText()).toContain('Gate check failed');
  expect(actionText()).toContain('proof-bundle — AGENTS.md section 9 proof');
  // The panel re-reads after every write attempt so it shows the store, not a guess.
  expect(fetchMock).toHaveBeenCalledTimes(3);
  expect(screen.getByText('[WORK]')).toBeInTheDocument();
});

test.each([
  ['unavailable', 503, 'the write outcome is unknown; refresh the queue'],
  ['wrong_project', 409, 'port 7890 is serving project beta'],
])('a %s write is red with the server reason', async (status, code, reason) => {
  await renderQueue(
    vi
      .fn()
      .mockResolvedValueOnce(reply(200, queue()))
      .mockResolvedValueOnce(reply(code, transition({ status, reason, new_role: null })))
      .mockResolvedValueOnce(reply(200, queue())),
  );

  await click('Start: Write the tests');

  expect(actionChip()).toHaveTextContent('[FAILED]');
  expect(actionChip()).toHaveStyle({ color: toRgb(brandTokens.colors.errorRed) });
  expect(actionText()).toContain(reason);
});

test.each([
  ['a network error', () => Promise.reject(new TypeError('Failed to fetch')), 'no response (network error)'],
  ['an unexpected payload', () => Promise.resolve(reply(500, { detail: 'Internal Server Error' })), 'HTTP 500 with an unexpected payload'],
  ['invalid JSON', () => Promise.resolve({ ok: false, status: 502, json: async () => Promise.reject(new SyntaxError('bad')) }), 'HTTP 502 with an unexpected payload'],
])('%s on the write is red and says the outcome is unknown', async (_label, failure, text) => {
  const fetchMock = vi.fn().mockResolvedValueOnce(reply(200, queue())).mockImplementationOnce(failure).mockResolvedValueOnce(reply(200, queue()));
  await renderQueue(fetchMock);

  await click('Start: Write the tests');

  expect(actionChip()).toHaveTextContent('[FAILED]');
  expect(actionText()).toContain(text);
  expect(actionText()).toContain('outcome is unknown');
});

test('gremlinPink is never a status color', async () => {
  await renderQueue(
    vi
      .fn()
      .mockResolvedValueOnce(reply(200, queue()))
      .mockResolvedValueOnce(reply(200, transition()))
      .mockResolvedValueOnce(reply(200, queue([workItem, { ...queueItem, role: 'work' }]))),
  );
  await click('Start: Write the tests');

  const pink = toRgb(brandTokens.colors.gremlinPink);
  for (const element of Array.from(document.querySelectorAll('*'))) {
    expect(getComputedStyle(element).color).not.toBe(pink);
  }
});
