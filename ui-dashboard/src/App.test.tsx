// @vitest-environment jsdom
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import App from './App';

class FakeSocket {
  static instances: FakeSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  constructor(public url: string) {
    FakeSocket.instances.push(this);
  }
  close() {}
}

const livePayload = (load: number) => ({
  energy: { energy_level: 'medium' },
  attention: { attention_state: 'focused' },
  cognitive_load: { cognitive_load: load, predicted_load_15min: 0.71 },
  recommendation: 'Finish the current task, then take a 10-minute break.',
});

beforeEach(() => {
  FakeSocket.instances = [];
  vi.stubGlobal('WebSocket', FakeSocket);
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

async function renderApp() {
  await act(async () => {
    render(<App />);
  });
}

test('backend unreachable: shows unknown state and a precise failure, never invented numbers', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
  await renderApp();
  await act(async () => {
    FakeSocket.instances[0].onerror?.();
    FakeSocket.instances[0].onclose?.();
  });

  expect(screen.getByText('[DEGRADED]')).toBeInTheDocument();
  const alert = screen.getByRole('alert');
  expect(alert).toHaveTextContent('Failed: GET http://localhost:8097/api/adhd-state');
  expect(alert).toHaveTextContent('Next:');
  expect(within(alert).getByRole('button', { name: 'Retry' })).toBeInTheDocument();

  expect(screen.getByText('Unknown')).toBeInTheDocument();
  expect(screen.getByTestId('energy-value')).toHaveTextContent('unknown');
  expect(screen.getByTestId('attention-value')).toHaveTextContent('unknown');
  expect(screen.queryByText('70%')).not.toBeInTheDocument();
  expect(screen.queryByText('60%')).not.toBeInTheDocument();
  expect(screen.getByText(/Socket ws:\/\/localhost:8097\/ws\/state is closed/)).toBeInTheDocument();
  expect(screen.getByText('Load unknown. Sequence order is not adjusted.')).toBeInTheDocument();
  expect(screen.queryByText(/calibrated for OPTIMAL/)).not.toBeInTheDocument();
});

test('state request fails while the socket is open: still explains the failure', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
  await renderApp();
  await act(async () => {
    FakeSocket.instances[0].onopen?.();
  });

  expect(screen.getByText('[LIVE]')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent(
    'Failed: GET http://localhost:8097/api/adhd-state returned HTTP 500.'
  );
  expect(screen.getByText('Unknown')).toBeInTheDocument();
});

test('live reading: renders load, state and attention from the backend payload', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.64) }));
  await renderApp();
  await act(async () => {
    FakeSocket.instances[0].onopen?.();
  });

  expect(screen.getByText('[LIVE]')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByText('64%')).toBeInTheDocument();
  expect(screen.getByText('Pressure Build')).toBeInTheDocument();
  expect(screen.getByTestId('energy-value')).toHaveTextContent('medium');
  expect(screen.getByTestId('attention-value')).toHaveTextContent('focused');
  expect(screen.getByText(/^updated \d{2}:\d{2}:\d{2}$/)).toBeInTheDocument();
});

test('consent is reported as unknown, not verified', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();

  expect(screen.getByText('[CONSENT: UNKNOWN]')).toBeInTheDocument();
  expect(screen.queryByText(/consent verified/i)).not.toBeInTheDocument();
});

test('aftercare button keeps its own name; the tooltip only describes it', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();

  const button = screen.getByRole('button', { name: '[AFTERCARE] Log a sip' });
  fireEvent.click(button);
  expect(screen.getByRole('button', { name: '[AFTERCARE] Sip logged' })).toBeInTheDocument();
});

test('critical load hides secondary panels until the operator asks for them', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.9) }));
  await renderApp();

  expect(screen.getByText('Break. Now.')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Signal Feed' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Attention State' })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Show all panels' }));

  expect(screen.getByRole('heading', { name: 'Signal Feed' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Attention State' })).toBeInTheDocument();
  expect(screen.getByText('Team Signal Board')).toBeInTheDocument();
});

test('show all lasts one critical episode; the next one collapses panels again', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.9) }));
  await renderApp();
  fireEvent.click(screen.getByRole('button', { name: 'Show all panels' }));

  const sendLoad = async (load: number) =>
    act(async () => {
      FakeSocket.instances[0].onmessage?.({
        data: JSON.stringify({ type: 'state_update', data: { cognitive_load: load } }),
      });
    });

  await sendLoad(0.4);
  await sendLoad(0.9);

  expect(screen.getByRole('button', { name: 'Show all panels' })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Signal Feed' })).not.toBeInTheDocument();
});

test('a live state_update clears a stale state-request failure', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
  await renderApp();
  expect(screen.getByRole('alert')).toHaveTextContent('Failed: GET');

  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: 'state_update', data: { cognitive_load: 0.4 } }),
    });
  });

  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByText('40%')).toBeInTheDocument();
});

test('a 200 response with a non-object body is reported as an unexpected payload', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => null }));
  await renderApp();

  expect(screen.getByRole('alert')).toHaveTextContent(
    'Failed: GET http://localhost:8097/api/adhd-state returned an unexpected payload.'
  );
});

test('a 200 response with invalid JSON is reported as such, not as a network error', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: true, json: async () => Promise.reject(new SyntaxError('bad json')) })
  );
  await renderApp();

  expect(screen.getByRole('alert')).toHaveTextContent(
    'Failed: GET http://localhost:8097/api/adhd-state returned invalid JSON.'
  );
});

test('a malformed state_update is reported and does not replace the reading', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();

  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({ data: JSON.stringify({ type: 'state_update', data: 'invalid' }) });
  });

  expect(screen.getByRole('alert')).toHaveTextContent('Failed: malformed state_update from ws://localhost:8097/ws/state.');
  expect(screen.getByText('40%')).toBeInTheDocument();
});

test('the empty feed says connecting while the socket is connecting', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();

  expect(screen.getByText('Connecting to ws://localhost:8097/ws/state.')).toBeInTheDocument();
  expect(screen.queryByText(/is closed/)).not.toBeInTheDocument();
});

test('a slow GET does not overwrite a newer live state_update', async () => {
  let resolveFetch: (value: unknown) => void = () => {};
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValue(new Promise((resolve) => (resolveFetch = resolve)))
  );
  await renderApp();

  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: 'state_update', data: { cognitive_load: 0.9 } }),
    });
  });
  expect(screen.getByText('Break. Now.')).toBeInTheDocument();

  await act(async () => {
    resolveFetch({ ok: true, json: async () => livePayload(0.4) });
  });

  expect(screen.getByText('Break. Now.')).toBeInTheDocument();
  expect(screen.queryByText('40%')).not.toBeInTheDocument();
});

test('a GET that fails after a live update does not bring back a stale failure banner', async () => {
  let rejectFetch: (reason: unknown) => void = () => {};
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValue(new Promise((_resolve, reject) => (rejectFetch = reject)))
  );
  await renderApp();

  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: 'state_update', data: { cognitive_load: 0.4 } }),
    });
  });
  await act(async () => {
    rejectFetch(new TypeError('Failed to fetch'));
  });

  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(screen.getByText('40%')).toBeInTheDocument();
});

test('a null socket message is reported, not thrown', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();

  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({ data: 'null' });
  });

  expect(screen.getByRole('alert')).toHaveTextContent('Failed: unexpected message from ws://localhost:8097/ws/state.');
});

test('signal feed lists notifications as log rows that can be dismissed', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();
  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({
      data: JSON.stringify({
        type: 'dashboard_notification',
        id: 'n1',
        notification_type: 'decision',
        message: 'Logged decision 212',
        timestamp: '2026-10-30T14:01:55Z',
      }),
    });
  });

  const log = screen.getByRole('log');
  expect(within(log).getByText('Logged decision 212')).toBeInTheDocument();
  expect(within(log).getByText('decision')).toBeInTheDocument();

  fireEvent.click(within(log).getByRole('button', { name: /Dismiss decision signal/ }));
  expect(screen.queryByText('Logged decision 212')).not.toBeInTheDocument();
});

test('a 200 response with nested upstream errors keeps the partial reading and shows a retryable banner', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        health: { status: 'ok' },
        energy: { error: 'engine down', detail: 'timeout' },
        attention: { error: 'engine down', detail: 'timeout' },
        cognitive_load: { cognitive_load: 0.4, predicted_load_15min: 0.5 },
        recommendation: 'Take a break.',
        task_recommendations: [],
      }),
    })
  );
  await renderApp();

  const alert = screen.getByRole('alert');
  expect(alert).toHaveTextContent(
    'Failed: GET http://localhost:8097/api/adhd-state returned upstream errors for energy, attention.'
  );
  expect(within(alert).getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  expect(screen.getByText('40%')).toBeInTheDocument();
  expect(screen.getByTestId('energy-value')).toHaveTextContent('unknown');
  expect(screen.getByTestId('attention-value')).toHaveTextContent('unknown');
});

test('a failed task recommender does not render its error text as the recommendation', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        ...livePayload(0.4),
        recommendation: 'recommender exploded',
        task_recommendations: { error: 'recommender exploded' },
      }),
    })
  );
  await renderApp();

  expect(screen.getByText('40%')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('upstream errors for recommendation');
  expect(screen.queryByText(/recommender exploded/)).not.toBeInTheDocument();
});

test('a later good state_update clears a socket error banner', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.4) }));
  await renderApp();

  await act(async () => {
    FakeSocket.instances[0].onopen?.();
    FakeSocket.instances[0].onmessage?.({ data: '{not json' });
  });
  expect(screen.getByRole('alert')).toHaveTextContent(
    'Failed: could not parse a message from ws://localhost:8097/ws/state.'
  );

  await act(async () => {
    FakeSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: 'state_update', data: { cognitive_load: 0.55 } }),
    });
  });

  // The alert sits in a Collapse, so it leaves the DOM after its exit transition.
  await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  expect(screen.getByText('55%')).toBeInTheDocument();
});

const sendStateUpdate = async (data: Record<string, unknown>) =>
  act(async () => {
    FakeSocket.instances[0].onmessage?.({ data: JSON.stringify({ type: 'state_update', data }) });
  });

const forecastGet = (predicted: number) => ({
  ok: true,
  json: async () => ({ ...livePayload(0.4), cognitive_load: { cognitive_load: 0.4, predicted_load_15min: predicted } }),
});

test('a state_update without a forecast keeps a GET forecast that is under 15 minutes old', async () => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-31T10:00:00Z'));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('50%');

  vi.setSystemTime(new Date('2026-10-31T10:14:59Z'));
  await sendStateUpdate({ cognitive_load: 0.45 });

  expect(screen.getByText('45%')).toBeInTheDocument();
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('50%');
});

test('a carried forecast is not refreshed by later snapshots: it expires 15 minutes after it arrived', async () => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-31T10:00:00Z'));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();

  vi.setSystemTime(new Date('2026-10-31T10:10:00Z'));
  await sendStateUpdate({ cognitive_load: 0.45 });
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('50%');

  vi.setSystemTime(new Date('2026-10-31T10:15:00Z'));
  await sendStateUpdate({ cognitive_load: 0.46 });
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
});

test('a state_update after 15 minutes drops the old forecast to unknown', async () => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-31T10:00:00Z'));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();

  vi.setSystemTime(new Date('2026-10-31T10:16:00Z'));
  await sendStateUpdate({ cognitive_load: 0.45 });

  expect(screen.getByText('45%')).toBeInTheDocument();
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
});

test('a GET that lands after a live update supplies its forecast and nothing else', async () => {
  let resolveFetch: (value: unknown) => void = () => {};
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValue(new Promise((resolve) => (resolveFetch = resolve)))
  );
  await renderApp();
  await sendStateUpdate({ cognitive_load: 0.45 });
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');

  await act(async () => {
    resolveFetch(forecastGet(0.5));
  });

  expect(screen.getByTestId('forecast-value')).toHaveTextContent('50%');
  expect(screen.getByText('45%')).toBeInTheDocument();
  expect(screen.getByTestId('energy-value')).toHaveTextContent('unknown');
  expect(screen.getByTestId('attention-value')).toHaveTextContent('unknown');
});

test('a late GET does not replace a forecast the socket already sent', async () => {
  let resolveFetch: (value: unknown) => void = () => {};
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValue(new Promise((resolve) => (resolveFetch = resolve)))
  );
  await renderApp();
  await sendStateUpdate({ cognitive_load: 0.45, predicted_load_15min: 0.7 });

  await act(async () => {
    resolveFetch(forecastGet(0.5));
  });

  expect(screen.getByTestId('forecast-value')).toHaveTextContent('70%');
});

test('a late GET does not bring back a forecast the socket cleared', async () => {
  let resolveFetch: (value: unknown) => void = () => {};
  vi.stubGlobal(
    'fetch',
    vi.fn().mockReturnValue(new Promise((resolve) => (resolveFetch = resolve)))
  );
  await renderApp();
  // The key is present, so this snapshot says "no forecast", not "forecast not sent".
  await sendStateUpdate({ cognitive_load: 0.45, predicted_load_15min: null });

  await act(async () => {
    resolveFetch(forecastGet(0.5));
  });

  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
});

const clickRetry = async () =>
  act(async () => {
    fireEvent.click(within(screen.getByRole('alert')).getByRole('button', { name: 'Retry' }));
  });

test('Retry after a failed GET keeps an open socket', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });
  vi.stubGlobal('fetch', fetchMock);
  await renderApp();
  await act(async () => {
    FakeSocket.instances[0].onopen?.();
  });
  expect(screen.getByText('[LIVE]')).toBeInTheDocument();

  await clickRetry();

  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(FakeSocket.instances).toHaveLength(1);
  expect(screen.getByText('[LIVE]')).toBeInTheDocument();
});

test('Retry reopens a closed socket', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();
  await act(async () => {
    FakeSocket.instances[0].onclose?.();
  });

  await clickRetry();

  expect(FakeSocket.instances).toHaveLength(2);
  expect(screen.getByText('[CONNECTING]')).toBeInTheDocument();
});

const FIFTEEN_MINUTES_MS = 15 * 60 * 1000;

const advance = async (ms: number) =>
  act(async () => {
    vi.advanceTimersByTime(ms);
  });

test('a quiet socket does not keep the forecast past 15 minutes', async () => {
  vi.useFakeTimers({ toFake: ['Date', 'setTimeout', 'clearTimeout'] });
  vi.setSystemTime(new Date('2026-10-31T10:00:00Z'));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();
  const updated = screen.getByText(/^updated /).textContent;

  await advance(FIFTEEN_MINUTES_MS - 1);
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('50%');

  await advance(1);
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
  // Expiry is the clock, not new data: the last-received time and the load stay as they were.
  expect(screen.getByText(/^updated /).textContent).toBe(updated);
  expect(screen.getByText('40%')).toBeInTheDocument();
});

test('a snapshot that only carries the forecast does not postpone its expiry', async () => {
  vi.useFakeTimers({ toFake: ['Date', 'setTimeout', 'clearTimeout'] });
  vi.setSystemTime(new Date('2026-10-31T10:00:00Z'));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();

  await advance(10 * 60 * 1000);
  await sendStateUpdate({ cognitive_load: 0.45 });
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('50%');

  await advance(5 * 60 * 1000);
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
  expect(screen.getByText('45%')).toBeInTheDocument();
});

test('a new forecast restarts the 15-minute expiry', async () => {
  vi.useFakeTimers({ toFake: ['Date', 'setTimeout', 'clearTimeout'] });
  vi.setSystemTime(new Date('2026-10-31T10:00:00Z'));
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();

  await advance(10 * 60 * 1000);
  await sendStateUpdate({ cognitive_load: 0.45, predicted_load_15min: 0.7 });

  await advance(5 * 60 * 1000);
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('70%');

  await advance(10 * 60 * 1000);
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
});

test('a state_update that carries a forecast replaces the previous one', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(forecastGet(0.5)));
  await renderApp();

  await sendStateUpdate({ cognitive_load: 0.45, predicted_load_15min: 0.7 });
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('70%');

  // An invalid forecast is unknown, not the previous value.
  await sendStateUpdate({ cognitive_load: 0.45, predicted_load_15min: 7 });
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
});

const upstreamGet = (overrides: Record<string, unknown> = {}) => ({
  ok: true,
  json: async () => ({
    health: { status: 'ok' },
    energy: { error: 'engine down' },
    attention: { attention_state: 'focused' },
    cognitive_load: { cognitive_load: 0.4 },
    task_recommendations: { error: 'recommender down' },
    ...overrides,
  }),
});

test('a snapshot that covers only some failed GET sections keeps a warning naming the rest', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(upstreamGet()));
  await renderApp();
  expect(screen.getByRole('alert')).toHaveTextContent('upstream errors for energy, recommendation.');

  await sendStateUpdate({ cognitive_load: 0.45, energy_level: 'medium' });

  const alert = screen.getByRole('alert');
  expect(alert).toHaveTextContent('Failed: GET http://localhost:8097/api/adhd-state returned upstream errors for recommendation.');
  expect(alert).not.toHaveTextContent('energy');
  expect(screen.getByTestId('energy-value')).toHaveTextContent('medium');
});

test('a snapshot that covers every failed GET section clears the warning', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(upstreamGet()));
  await renderApp();

  await sendStateUpdate({ cognitive_load: 0.45, energy_level: 'medium', recommendation: 'Take a break.' });

  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

test('a GET transport failure is cleared by any valid snapshot', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));
  await renderApp();
  expect(screen.getByRole('alert')).toHaveTextContent('returned HTTP 500.');

  await sendStateUpdate({ cognitive_load: 0.4 });

  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
