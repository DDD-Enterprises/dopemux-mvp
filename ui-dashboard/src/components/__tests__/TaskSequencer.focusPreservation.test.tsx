// @vitest-environment jsdom
import { expect, test } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import React from 'react';
import fs from 'fs';
import path from 'path';
import TaskSequencer from '../TaskSequencer';

const cognitiveState = {
  energy: 80,
  attention: 70,
  load: 40,
  status: 'optimal' as const,
  recommendation: 'Stay focused.',
};

test('TaskSequencer does not steal focus on initial mount', () => {
  render(
    <React.StrictMode>
      <TaskSequencer cognitiveState={cognitiveState} />
    </React.StrictMode>,
  );

  const ritualStart = screen.getByRole('button', {
    name: 'Start task: Implement LSTM cognitive predictor',
  });
  expect(ritualStart).toBeInTheDocument();
  expect(document.activeElement).not.toBe(ritualStart);
});

test('TaskSequencer moves focus to the new current task Start control after a list transition', () => {
  render(<TaskSequencer cognitiveState={cognitiveState} />);

  const listStarts = screen.getAllByRole('button', {
    name: 'Start task: Create UI dashboard components',
  });
  expect(listStarts.length).toBeGreaterThan(0);
  fireEvent.click(listStarts[0]);

  const ritualStart = document.querySelector(
    'button.MuiButton-contained[aria-label="Start task: Create UI dashboard components"]',
  );
  expect(ritualStart).not.toBeNull();
  expect(ritualStart).toHaveFocus();
});

test('TaskSequencer keeps primaryActionRef on the ritual Start/Pause button', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '..', 'TaskSequencer.tsx'),
    'utf8',
  );

  expect(source).toContain('primaryActionRef');
  expect(source).toContain('previousTaskIdRef');
  expect(source).toMatch(/<Button[\s\S]*ref=\{primaryActionRef\}/);
});
