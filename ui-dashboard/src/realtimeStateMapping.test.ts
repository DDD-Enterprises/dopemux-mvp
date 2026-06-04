import { expect, test } from 'vitest';

import { mapRealtimeState } from './App';

test('state_update messages map into the critical dashboard band state', () => {
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
    energy: 0.4,
    attention: 0.3,
    load: 0.84,
    prediction: 0.91,
    status: 'critical',
    recommendation: 'Pause and take a recovery break.',
  });
});

test('non-state messages do not update the dashboard band', () => {
  expect(mapRealtimeState({ type: 'dashboard_notification' })).toBeNull();
});
