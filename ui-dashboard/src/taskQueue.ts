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

// The cockpit's reading of POST /api/tasks/{id}/transition (services/adhd-dashboard/orchestrator_transitions.py).
// Start and Finish only (operator ruling 2026-11-22). A payload this module does not recognise
// returns null and the panel reports the write's outcome as unknown.

export type TransitionTrigger = 'start' | 'complete';
export type TransitionStatus = 'applied' | 'refused' | 'unavailable' | 'wrong_project';

export interface MissingNote {
  key: string;
  description: string | null;
}

export interface TransitionResult {
  status: TransitionStatus;
  reason: string | null;
  previousRole: string | null;
  newRole: string | null;
  /** Required notes the orchestrator's gate found missing; null when it named none. */
  missingNotes: MissingNote[] | null;
  /** The actor the backend wrote as. The orchestrator records it unverified until Wave 2C. */
  actorId: string | null;
}

const TRANSITION_STATUSES: readonly TransitionStatus[] = ['applied', 'refused', 'unavailable', 'wrong_project'];

export const triggerFor = (role: TaskQueueRole): TransitionTrigger => (role === 'queue' ? 'start' : 'complete');

const parseMissingNotes = (raw: unknown): MissingNote[] | null | undefined => {
  if (raw === null || raw === undefined) return null;
  if (!Array.isArray(raw)) return undefined;
  const notes: MissingNote[] = [];
  for (const note of raw) {
    if (!isObject(note) || !asText(note.key)) return undefined;
    notes.push({ key: note.key as string, description: asText(note.description) });
  }
  return notes;
};

export const parseTransitionResult = (raw: unknown): TransitionResult | null => {
  if (!isObject(raw)) return null;
  const status = TRANSITION_STATUSES.find((candidate) => candidate === raw.status);
  if (!status) return null;
  const newRole = asText(raw.new_role);
  if (status === 'applied' && !newRole) return null;
  const missingNotes = parseMissingNotes(raw.missing_notes);
  if (missingNotes === undefined) return null;
  return {
    status,
    reason: asText(raw.reason),
    previousRole: asText(raw.previous_role),
    newRole,
    missingNotes,
    actorId: isObject(raw.actor) ? asText(raw.actor.id) : null,
  };
};
