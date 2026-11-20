import { expect, test } from 'vitest';

import { parseTaskQueue } from './taskQueue';

const base = {
  source: 'task-orchestrator-mcp',
  endpoint: 'http://127.0.0.1:7890/mcp',
  status: 'ok',
  reason: null,
  project: {
    expected: { project_id: 'alpha-1', name: 'alpha' },
    owner: { project_id: 'alpha-1', name: 'alpha' },
    verdict: 'OK',
  },
  roles: ['work', 'queue'],
  items: [
    { id: 'w1', title: 'Wire the queue', role: 'work', priority: 'high', parent_id: null, depth: 0, tags: ['cockpit'], complexity: 3 },
    { id: 'q1', title: 'Write the tests', role: 'queue', priority: null, parent_id: 'w1', depth: 1, tags: null, complexity: null },
  ],
  total: 9,
  fetched_at: '2026-11-16T12:00:00+00:00',
};

test('an ok payload keeps its items in order, with nulls for what the source did not supply', () => {
  const reading = parseTaskQueue(base);

  expect(reading).toEqual({
    status: 'ok',
    reason: null,
    sourceEndpoint: 'http://127.0.0.1:7890/mcp',
    projectName: 'alpha',
    items: [
      { id: 'w1', title: 'Wire the queue', role: 'work', priority: 'high', complexity: 3, tags: ['cockpit'] },
      { id: 'q1', title: 'Write the tests', role: 'queue', priority: null, complexity: null, tags: null },
    ],
    total: 9,
    fetchedAt: '2026-11-16T12:00:00+00:00',
  });
});

test('missing or wrongly typed optional fields become null, never a default', () => {
  const reading = parseTaskQueue({
    status: 'ok',
    items: [{ id: 'x1', title: 'Bare', role: 'queue', priority: 5, complexity: '3', tags: 'a,b' }],
  });

  expect(reading?.items).toEqual([{ id: 'x1', title: 'Bare', role: 'queue', priority: null, complexity: null, tags: null }]);
  expect(reading?.total).toBeNull();
  expect(reading?.sourceEndpoint).toBeNull();
  expect(reading?.projectName).toBeNull();
  expect(reading?.fetchedAt).toBeNull();
});

test('ok with no items reads as empty', () => {
  expect(parseTaskQueue({ ...base, items: [], total: 0 })?.status).toBe('empty');
});

test.each(['empty', 'unavailable', 'wrong_project'])('%s never carries items, whatever the payload holds', (status) => {
  const reading = parseTaskQueue({ ...base, status, reason: 'because' });

  expect(reading?.status).toBe(status);
  expect(reading?.items).toEqual([]);
  expect(reading?.reason).toBe('because');
});

test('wrong_project keeps this project as projectName, not the owner', () => {
  const reading = parseTaskQueue({
    ...base,
    status: 'wrong_project',
    reason: 'port 7890 is serving project beta (container to-beta), not this one',
    project: { expected: { project_id: 'alpha-1', name: 'alpha' }, owner: { project_id: 'beta', name: 'beta' }, verdict: 'WRONG_PROJECT' },
  });

  expect(reading?.projectName).toBe('alpha');
});

test.each([
  ['null', null],
  ['an array', []],
  ['a string', 'ok'],
  ['no status', { items: [] }],
  ['an unknown status', { ...base, status: 'live' }],
  ['ok without an items array', { ...base, items: 'many' }],
  ['an item that is not an object', { ...base, items: ['w1'] }],
  ['an item without an id', { ...base, items: [{ title: 'No id', role: 'work' }] }],
  ['an item without a title', { ...base, items: [{ id: 'x1', role: 'work' }] }],
  ['an item in a role the cockpit does not list', { ...base, items: [{ id: 'x1', title: 'Done', role: 'terminal' }] }],
  // The /api/adhd-state payload must not be mistaken for a queue.
  ['another endpoint\'s payload', { energy: { energy_level: 'medium' }, recommendation: 'Rest.' }],
])('%s is not a task queue', (_label, raw) => {
  expect(parseTaskQueue(raw)).toBeNull();
});
