// @vitest-environment jsdom
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
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
