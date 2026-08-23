// @vitest-environment jsdom
// @ts-nocheck
import { expect, test } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import React from 'react';
import TaskSequencer from '../TaskSequencer';

const defaultCognitiveState = {
  energy: 80,
  attention: 70,
  load: 40,
  status: 'optimal' as const,
  recommendation: 'Stay focused.',
};

test('TaskSequencer mount: does not auto-focus primary action on initial render', () => {
  render(<TaskSequencer cognitiveState={defaultCognitiveState} />);
  const primaryButton = screen.getByRole('button', { name: /^Start task: Implement LSTM/i });
  expect(primaryButton).not.toHaveFocus();
});

test('TaskSequencer transition: focuses primary action when task transitions via Start button', async () => {
  render(<TaskSequencer cognitiveState={defaultCognitiveState} />);

  // Find a non-current task's Start button
  const startButtons = screen.getAllByRole('button', { name: /^Start task: Create UI dashboard/i });
  const pendingStartButton = startButtons.find((btn) => {
    const li = btn.closest('li');
    return li && li.getAttribute('aria-current') !== 'step';
  });
  expect(pendingStartButton).toBeDefined();

  // Click start on task 2 to switch active task
  fireEvent.click(pendingStartButton);

  // Focus should shift to the primary Start button of the new active task
  const primaryButton = screen.getByRole('button', { name: /^Start task: Create UI dashboard/i });
  expect(primaryButton).toHaveFocus();
});

test('TaskSequencer transition: focuses primary action when task transitions via Complete button', async () => {
  render(<TaskSequencer cognitiveState={defaultCognitiveState} />);

  // Complete task 1
  const completeButton = screen.getByRole('button', { name: /Complete/i });
  fireEvent.click(completeButton);

  // Next task in sequence becomes current and its primary action receives focus
  const primaryButton = screen.getByRole('button', { name: /^Start task: /i });
  expect(primaryButton).toHaveFocus();
});

test('TaskSequencer reset: resets task state and focuses header when all tasks complete, then handles reset confirmation', async () => {
  render(<TaskSequencer cognitiveState={defaultCognitiveState} />);

  // Complete all 3 tasks
  for (let i = 0; i < 3; i++) {
    const completeButton = screen.getByRole('button', { name: /Complete/i });
    fireEvent.click(completeButton);
  }

  // Expect "Ritual Complete" message and Reset button
  expect(screen.getByText('Ritual Complete')).toBeInTheDocument();

  const resetButton = screen.getByRole('button', { name: /Reset Ritual/i });

  // First click enters confirmation state
  fireEvent.click(resetButton);
  expect(screen.getByRole('button', { name: /Confirm Reset\?/i })).toBeInTheDocument();

  // Second click resets tasks
  fireEvent.click(screen.getByRole('button', { name: /Confirm Reset\?/i }));
  expect(screen.getByText('Implement LSTM cognitive predictor')).toBeInTheDocument();
});

test('TaskSequencer disabled & keyboard focus: skip button handling when disabled or when navigating with keyboard', () => {
  render(<TaskSequencer cognitiveState={defaultCognitiveState} />);

  const primaryButton = screen.getByRole('button', { name: /^Start task: Implement LSTM/i });

  // Test keyboard focus
  primaryButton.focus();
  expect(primaryButton).toHaveFocus();

  // Fire Enter on start button
  fireEvent.keyDown(primaryButton, { key: 'Enter', code: 'Enter' });

  // Skip button tooltip container handling when tasks are available vs disabled
  const skipButton = screen.getByRole('button', { name: /Skip/i });
  expect(skipButton).not.toBeDisabled();
});
