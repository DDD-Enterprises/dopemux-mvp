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

export const EMPTY_READING: CognitiveReading = {
  energyLevel: null,
  attentionState: null,
  load: null,
  prediction: null,
  recommendation: null,
};

const asText = (value: unknown): string | null =>
  typeof value === 'string' && value.trim() !== '' ? value : null;

const asRatio = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) ? Math.min(Math.max(value, 0), 1) : null;

export function mapAggregateState(payload: AggregateDashboardState): CognitiveReading {
  return {
    energyLevel: asText(payload.energy?.energy_level),
    attentionState: asText(payload.attention?.attention_state),
    load: asRatio(payload.cognitive_load?.cognitive_load),
    prediction: asRatio(payload.cognitive_load?.predicted_load_15min),
    recommendation: asText(payload.recommendation),
  };
}

/** Maps a `/ws/state` message; returns `null` for anything that is not a `state_update`. */
export function mapRealtimeState(message: Record<string, unknown>): CognitiveReading | null {
  if (message.type !== 'state_update') {
    return null;
  }

  const data = (message.data || {}) as Record<string, unknown>;
  return {
    energyLevel: asText(data.energy_level),
    attentionState: asText(data.attention_state),
    load: asRatio(data.cognitive_load),
    prediction: asRatio(data.predicted_load_15min),
    recommendation: asText(data.recommendation),
  };
}
