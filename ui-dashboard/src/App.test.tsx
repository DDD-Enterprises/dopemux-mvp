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

test('critical load hides secondary panels until the operator asks for them', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => livePayload(0.9) }));
  await renderApp();

  expect(screen.getByText('Break. Now.')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Signal Feed' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Attention State' })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Show all panels' }));

  expect(screen.getByRole('heading', { name: 'Signal Feed' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Attention State' })).toBeInTheDocument();
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
