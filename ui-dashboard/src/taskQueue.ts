// The cockpit's reading of GET /api/tasks (services/adhd-dashboard/orchestrator_tasks.py).
// A field the source did not supply is null and renders as unknown. A payload this module does
// not recognise is not a queue at all: parseTaskQueue returns null and the panel reports a failure.

export type TaskQueueStatus = 'ok' | 'empty' | 'unavailable' | 'wrong_project';
export type TaskQueueRole = 'work' | 'queue';

export interface TaskQueueItem {
  id: string;
  title: string;
  role: TaskQueueRole;
  priority: string | null;
  complexity: number | null;
  tags: string[] | null;
}

export interface TaskQueueReading {
  status: TaskQueueStatus;
  reason: string | null;
  /** The orchestrator endpoint the backend read, as the backend reports it. */
  sourceEndpoint: string | null;
  /** The project this backend runs from. Never the port's owner. */
  projectName: string | null;
  items: TaskQueueItem[];
  total: number | null;
  fetchedAt: string | null;
}

const STATUSES: readonly TaskQueueStatus[] = ['ok', 'empty', 'unavailable', 'wrong_project'];
const ROLES: readonly TaskQueueRole[] = ['work', 'queue'];

type Json = Record<string, unknown>;

const isObject = (value: unknown): value is Json => typeof value === 'object' && value !== null && !Array.isArray(value);
const asText = (value: unknown): string | null => (typeof value === 'string' && value.trim() ? value : null);
const asNumber = (value: unknown): number | null => (typeof value === 'number' && Number.isFinite(value) ? value : null);
const asTags = (value: unknown): string[] | null =>
  Array.isArray(value) && value.every((tag) => typeof tag === 'string') ? (value as string[]) : null;

const parseItem = (raw: unknown): TaskQueueItem | null => {
  if (!isObject(raw)) return null;
  const id = asText(raw.id);
  const title = asText(raw.title);
  const role = ROLES.find((candidate) => candidate === raw.role);
  if (!id || !title || !role) return null;
  return { id, title, role, priority: asText(raw.priority), complexity: asNumber(raw.complexity), tags: asTags(raw.tags) };
};

export const parseTaskQueue = (raw: unknown): TaskQueueReading | null => {
  if (!isObject(raw)) return null;
  const status = STATUSES.find((candidate) => candidate === raw.status);
  if (!status) return null;

  // Items are shown for ok only. Any other status drops them, whatever the payload holds.
  let items: TaskQueueItem[] = [];
  if (status === 'ok') {
    if (!Array.isArray(raw.items)) return null;
    const parsed = raw.items.map(parseItem);
    if (parsed.some((item) => item === null)) return null;
    items = parsed as TaskQueueItem[];
  }

  const expected = isObject(raw.project) && isObject(raw.project.expected) ? raw.project.expected : null;
  return {
    status: status === 'ok' && items.length === 0 ? 'empty' : status,
    reason: asText(raw.reason),
    sourceEndpoint: asText(raw.endpoint),
    projectName: expected ? asText(expected.name) : null,
    items,
    total: asNumber(raw.total),
    fetchedAt: asText(raw.fetched_at),
  };
};
