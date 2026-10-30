/**
 * One ADHD-engine reading as the cockpit shows it. Every field is `null` until the
 * backend reports it: the cockpit renders `unknown` rather than inventing a value.
 */
export interface CognitiveReading {
  energyLevel: string | null;
  attentionState: string | null;
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

// Out-of-range values are invalid input, not a reading: they stay unknown rather than
// being clamped into a plausible 0% or 100%. In-range values round to whole percent
// here, once, so the number shown and the load band derived from it always agree.
const asRatio = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
    ? Math.round(value * 100) / 100
    : null;

export function mapAggregateState(raw: unknown): CognitiveReading {
  if (!isMessageObject(raw)) {
    return { ...EMPTY_READING };
  }
  const payload = raw as AggregateDashboardState;
  return {
    energyLevel: asText(payload.energy?.energy_level),
    attentionState: asText(payload.attention?.attention_state),
    load: asRatio(payload.cognitive_load?.cognitive_load),
    prediction: asRatio(payload.cognitive_load?.predicted_load_15min),
    recommendation: asText(payload.recommendation),
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
    energyLevel: asText(data.energy_level),
    attentionState: asText(data.attention_state),
    load: asRatio(data.cognitive_load),
    prediction: asRatio(data.predicted_load_15min),
    recommendation: asText(data.recommendation),
  };
}
