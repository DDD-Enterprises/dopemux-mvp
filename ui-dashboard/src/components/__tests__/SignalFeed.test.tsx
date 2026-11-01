// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import SignalFeed, { DashboardNotification } from '../SignalFeed';

afterEach(cleanup);

const socketUrl = 'ws://localhost:8000/ws';
const notification: DashboardNotification = {
  id: 'n1',
  message: 'Break suggested',
  notificationType: 'break_reminder',
  timestamp: '2026-10-31T10:00:00Z',
};

const renderFeed = (notifications: DashboardNotification[]) => (
  <SignalFeed notifications={notifications} socketUrl={socketUrl} socketState="open" onDismiss={vi.fn()} onClear={vi.fn()} />
);

test('keeps an empty labelled log mounted, with the empty-state text outside it', () => {
  render(renderFeed([]));

  const log = screen.getByRole('log', { name: 'Signal Feed' });
  expect(log).toHaveAttribute('aria-live', 'polite');
  expect(within(log).queryAllByRole('listitem')).toHaveLength(0);

  const emptyText = screen.getByText(`No signals received yet. Listening on ${socketUrl}.`);
  expect(emptyText).toBeInTheDocument();
  expect(log).not.toContainElement(emptyText);
});

test('adds the first notification to the same log node, so it is announced', () => {
  const { rerender } = render(renderFeed([]));
  const initialLog = screen.getByRole('log');

  rerender(renderFeed([notification]));

  expect(screen.getByRole('log')).toBe(initialLog);
  expect(within(initialLog).getByText('Break suggested')).toBeInTheDocument();
  expect(within(initialLog).getAllByRole('listitem')).toHaveLength(1);
  expect(screen.queryByText(/No signals received yet/)).not.toBeInTheDocument();
});
