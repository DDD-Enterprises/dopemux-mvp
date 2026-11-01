import { expect, test } from 'vitest';

import {
  carryForecast,
  EMPTY_READING,
  FORECAST_TTL_MS,
  mapAggregateState,
  mapRealtimeState,
  remainingUpstreamSections,
  upstreamErrorSections,
} from './cognitiveReading';

test('state_update messages map into a cognitive reading', () => {
  const state = mapRealtimeState({
    type: 'state_update',
    data: {
      energy_level: 'low',
      attention_state: 'scattered',
      cognitive_load: 0.84,
      predicted_load_15min: 0.91,
      recommendation: 'Pause and take a recovery break.',
    },
  });

  expect(state).toEqual({
    energyLevel: 'low',
    attentionState: 'scattered',
    load: 0.84,
    prediction: 0.91,
    recommendation: 'Pause and take a recovery break.',
  });
});

test('missing fields stay unknown instead of defaulting to a mid value', () => {
  expect(mapRealtimeState({ type: 'state_update', data: {} })).toEqual({
    energyLevel: null,
    attentionState: null,
    load: null,
    prediction: null,
    recommendation: null,
  });
  expect(mapAggregateState({})).toEqual({
    energyLevel: null,
    attentionState: null,
    load: null,
    prediction: null,
    recommendation: null,
  });
});

test('non-state messages do not update the reading', () => {
  expect(mapRealtimeState({ type: 'dashboard_notification' })).toBeNull();
});

test('out-of-range ratios are unknown, not clamped into a plausible value', () => {
  const state = mapRealtimeState({
    type: 'state_update',
    data: { cognitive_load: 1.4, predicted_load_15min: -0.2, energy_level: 'medium' },
  });

  expect(state?.load).toBeNull();
  expect(state?.prediction).toBeNull();
  expect(state?.energyLevel).toBe('medium');
});

test('a state_update whose data is not an object is malformed, not an empty reading', () => {
  expect(mapRealtimeState({ type: 'state_update', data: 'invalid' })).toBeNull();
  expect(mapRealtimeState({ type: 'state_update' })).toBeNull();
});

test('a non-object state payload maps to an all-unknown reading', () => {
  expect(mapAggregateState(null)).toEqual({
    energyLevel: null,
    attentionState: null,
    load: null,
    prediction: null,
    recommendation: null,
  });
});

test('in-range ratios pass through unrounded so thresholds see the real value', () => {
  const state = mapRealtimeState({
    type: 'state_update',
    data: { cognitive_load: 0.804, predicted_load_15min: 0.296 },
  });

  expect(state?.load).toBe(0.804);
  expect(state?.prediction).toBe(0.296);
});

test('non-object envelopes are ignored instead of throwing', () => {
  expect(mapRealtimeState(null)).toBeNull();
  expect(mapRealtimeState(42)).toBeNull();
  expect(mapRealtimeState('state_update')).toBeNull();
});

test('energy and attention outside the engine enums are unknown, in both mappers', () => {
  const realtime = mapRealtimeState({
    type: 'state_update',
    data: { energy_level: 'invalid', attention_state: 'invalid' },
  });
  expect(realtime?.energyLevel).toBeNull();
  expect(realtime?.attentionState).toBeNull();

  const aggregate = mapAggregateState({
    energy: { energy_level: 'invalid' },
    attention: { attention_state: 'invalid' },
  });
  expect(aggregate.energyLevel).toBeNull();
  expect(aggregate.attentionState).toBeNull();
});

test('every engine enum value is accepted', () => {
  for (const energy of ['very_low', 'low', 'medium', 'high', 'hyperfocus']) {
    expect(mapAggregateState({ energy: { energy_level: energy } }).energyLevel).toBe(energy);
  }
  for (const attention of ['scattered', 'transitioning', 'focused', 'hyperfocused', 'overwhelmed']) {
    expect(mapRealtimeState({ type: 'state_update', data: { attention_state: attention } })?.attentionState).toBe(
      attention
    );
  }
});

test('upstreamErrorSections names the sections whose upstream call failed', () => {
  expect(upstreamErrorSections({})).toEqual([]);
  expect(upstreamErrorSections(null)).toEqual([]);
  expect(
    upstreamErrorSections({
      health: { error: 'ignored' },
      energy: { error: 'down', detail: 'x' },
      attention: { error: 'down' },
      cognitive_load: { cognitive_load: 0.4 },
      task_recommendations: { error: 'boom' },
    })
  ).toEqual(['energy', 'attention', 'recommendation']);
  expect(upstreamErrorSections({ cognitive_load: { error: 'down' } })).toEqual(['cognitive load']);
  expect(upstreamErrorSections({ energy: { error: '' }, attention: 'error' })).toEqual([]);
});

test('a failed task recommender never leaks its error text as the recommendation', () => {
  const state = mapAggregateState({
    recommendation: 'boom',
    task_recommendations: { error: 'boom' },
  });
  expect(state.recommendation).toBeNull();
  expect(
    mapAggregateState({ recommendation: 'Take a break.', task_recommendations: [] }).recommendation
  ).toBe('Take a break.');
});

test('carryForecast keeps a fresh forecast only when the snapshot omits the key', () => {
  const previous = { ...EMPTY_READING, load: 0.4, prediction: 0.5 };
  const withoutKey = { type: 'state_update', data: { cognitive_load: 0.45 } };
  const next = mapRealtimeState(withoutKey)!;

  expect(carryForecast(next, withoutKey, previous, 1000, 1000 + FORECAST_TTL_MS - 1).prediction).toBe(0.5);
  expect(carryForecast(next, withoutKey, previous, 1000, 1000 + FORECAST_TTL_MS).prediction).toBeNull();
  expect(carryForecast(next, withoutKey, previous, null, 1000).prediction).toBeNull();
  expect(carryForecast(next, withoutKey, EMPTY_READING, 1000, 1001).prediction).toBeNull();

  const withKey = { type: 'state_update', data: { cognitive_load: 0.45, predicted_load_15min: 0.9 } };
  expect(carryForecast(mapRealtimeState(withKey)!, withKey, previous, 1000, 1001).prediction).toBe(0.9);
  const invalidKey = { type: 'state_update', data: { predicted_load_15min: 2 } };
  expect(carryForecast(mapRealtimeState(invalidKey)!, invalidKey, previous, 1000, 1001).prediction).toBeNull();
});

test('remainingUpstreamSections drops only the sections the reading has a value for', () => {
  const failed = ['energy', 'attention', 'cognitive load', 'recommendation'];
  expect(remainingUpstreamSections(failed, EMPTY_READING)).toEqual(failed);
  expect(
    remainingUpstreamSections(failed, { ...EMPTY_READING, energyLevel: 'low', load: 0.2 })
  ).toEqual(['attention', 'recommendation']);
  expect(
    remainingUpstreamSections(failed, { energyLevel: 'low', attentionState: 'focused', load: 0.2, prediction: null, recommendation: 'x' })
  ).toEqual([]);
});
