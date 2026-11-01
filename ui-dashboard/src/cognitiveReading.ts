// Enums from services/adhd_engine/core/models.py (EnergyLevel, AttentionState). Energy is
// ordered as the engine reports it; the energy meter lights one step per level.
export const ENERGY_LEVELS = ['very_low', 'low', 'medium', 'high', 'hyperfocus'] as const;
export const ATTENTION_STATES = ['scattered', 'transitioning', 'focused', 'hyperfocused', 'overwhelmed'] as const;
export type EnergyLevel = (typeof ENERGY_LEVELS)[number];
export type AttentionState = (typeof ATTENTION_STATES)[number];

/**
 * One ADHD-engine reading as the cockpit shows it. Every field is `null` until the
 * backend reports it: the cockpit renders `unknown` rather than inventing a value.
 */
export interface CognitiveReading {
  energyLevel: EnergyLevel | null;
  attentionState: AttentionState | null;
  /** 0..1 */
  load: number | null;
  /** 0..1, backend 15-minute forecast */
  prediction: number | null;
  recommendation: string | null;
}

/** `GET /api/adhd-state` payload from services/adhd-dashboard/backend.py. */
export interface AggregateDashboardState {
  energy?: { energy_level?: string };
  attention?: { attention_state?: string };
  cognitive_load?: { cognitive_load?: number; predicted_load_15min?: number };
  recommendation?: string;
}

export const isMessageObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

export const EMPTY_READING: CognitiveReading = {
  energyLevel: null,
  attentionState: null,
  load: null,
  prediction: null,
  recommendation: null,
};

const asText = (value: unknown): string | null =>
  typeof value === 'string' && value.trim() !== '' ? value : null;

// Anything outside the engine's enum is not a reading: it stays unknown.
const asOneOf = <T extends string>(allowed: readonly T[], value: unknown): T | null =>
  typeof value === 'string' && (allowed as readonly string[]).includes(value) ? (value as T) : null;

// Out-of-range values are invalid input, not a reading: they stay unknown rather than
// being clamped into a plausible 0% or 100%. In-range values pass through unrounded so
// thresholds (critical > 0.8) see the real value; display rounding is LoadInstrument's job.
const asRatio = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;

const hasUpstreamError = (section: unknown): boolean => isMessageObject(section) && Boolean(section.error);

// backend.py answers HTTP 200 even when an upstream call failed, putting `{error, detail}`
// in that section. `health` is not shown by the cockpit, so it is not checked.
const UPSTREAM_SECTIONS = [
  ['energy', 'energy'],
  ['attention', 'attention'],
  ['cognitive_load', 'cognitive load'],
  ['task_recommendations', 'recommendation'],
] as const;

/** Readable names of the `GET /api/adhd-state` sections that carry an upstream `error`. */
export function upstreamErrorSections(raw: unknown): string[] {
  if (!isMessageObject(raw)) {
    return [];
  }
  return UPSTREAM_SECTIONS.filter(([key]) => hasUpstreamError(raw[key])).map(([, name]) => name);
}

export function mapAggregateState(raw: unknown): CognitiveReading {
  if (!isMessageObject(raw)) {
    return { ...EMPTY_READING };
  }
  const payload = raw as AggregateDashboardState;
  return {
    energyLevel: asOneOf(ENERGY_LEVELS, payload.energy?.energy_level),
    attentionState: asOneOf(ATTENTION_STATES, payload.attention?.attention_state),
    load: asRatio(payload.cognitive_load?.cognitive_load),
    prediction: asRatio(payload.cognitive_load?.predicted_load_15min),
    // On recommender failure backend.py copies the error text into `recommendation`.
    recommendation: hasUpstreamError(raw.task_recommendations) ? null : asText(payload.recommendation),
  };
}

/**
 * Maps a `/ws/state` message. Returns `null` for anything that is not a well-formed
 * `state_update`, including one whose `data` is missing or not an object.
 */
export function mapRealtimeState(message: unknown): CognitiveReading | null {
  if (!isMessageObject(message) || message.type !== 'state_update' || !isMessageObject(message.data)) {
    return null;
  }

  const data = message.data;
  return {
    energyLevel: asOneOf(ENERGY_LEVELS, data.energy_level),
    attentionState: asOneOf(ATTENTION_STATES, data.attention_state),
    load: asRatio(data.cognitive_load),
    prediction: asRatio(data.predicted_load_15min),
    recommendation: asText(data.recommendation),
  };
}

/** The engine's `predicted_load_15min` describes the next 15 minutes, so it expires after them. */
export const FORECAST_TTL_MS = 15 * 60 * 1000;

/**
 * A `state_update` that omits `predicted_load_15min` (the engine never sends it) keeps the
 * previous forecast while it is under 15 minutes old; an older one is unknown. When the key
 * is present, the snapshot's own mapped value wins, even if that is `null`.
 */
export function carryForecast(
  next: CognitiveReading,
  message: unknown,
  previous: CognitiveReading,
  forecastReceivedAt: number | null,
  now: number
): CognitiveReading {
  if (!isMessageObject(message) || !isMessageObject(message.data) || 'predicted_load_15min' in message.data) {
    return next;
  }
  const isFresh = forecastReceivedAt !== null && now - forecastReceivedAt < FORECAST_TTL_MS;
  return isFresh && previous.prediction !== null ? { ...next, prediction: previous.prediction } : next;
}

/**
 * Which failed GET sections a reading does not yet cover: a section is superseded only
 * when the reading has a value for it.
 */
export function remainingUpstreamSections(failed: readonly string[], reading: CognitiveReading): string[] {
  const covered: Record<string, boolean> = {
    energy: reading.energyLevel !== null,
    attention: reading.attentionState !== null,
    'cognitive load': reading.load !== null,
    recommendation: reading.recommendation !== null,
  };
  return failed.filter((section) => !covered[section]);
}
