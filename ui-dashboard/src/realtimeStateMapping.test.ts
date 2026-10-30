import { expect, test } from 'vitest';

import { mapAggregateState, mapRealtimeState } from './cognitiveReading';

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

test('ratios round to whole percent so the shown number and the state band agree', () => {
  const state = mapRealtimeState({
    type: 'state_update',
    data: { cognitive_load: 0.604, predicted_load_15min: 0.296 },
  });

  expect(state?.load).toBe(0.6);
  expect(state?.prediction).toBe(0.3);
});

test('non-object envelopes are ignored instead of throwing', () => {
  expect(mapRealtimeState(null)).toBeNull();
  expect(mapRealtimeState(42)).toBeNull();
  expect(mapRealtimeState('state_update')).toBeNull();
});
