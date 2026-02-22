// @ts-nocheck
import { expect, test } from 'vitest';
import fs from 'fs';
import path from 'path';

const componentsDir = path.resolve(__dirname, '..');

test('CognitiveLoadGauge.tsx has aria-label for LinearProgress', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'CognitiveLoadGauge.tsx'), 'utf8');
  expect(content).toContain('aria-label="Cognitive Load Percentage"');
  expect(content).toContain('aria-valuetext');
});

test('PredictionPanel.tsx has aria-label for LinearProgress and loading state', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'PredictionPanel.tsx'), 'utf8');
  expect(content).toContain('aria-label="15-Minute Load Prediction Percentage"');
  expect(content).toContain('aria-valuetext');
  expect(content).toContain('Prediction Loading...');
  // Indeterminate LinearProgress in loading state
  expect(content).toContain('aria-label="Loading prediction data"');
});

test('TeamDashboard.tsx has aria-labels for team and member progress bars', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TeamDashboard.tsx'), 'utf8');
  expect(content).toContain('aria-label="Team Average Cognitive Load Percentage"');
  expect(content).toContain('aria-label={`${member.name}\'s Cognitive Load Percentage`}');
});

test('TaskSequencer.tsx has contextual aria-labels for buttons', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('aria-label={isTimerRunning ? `Pause task: ${currentTask.title}` : `Start task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Complete task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Skip task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Start task: ${task.title}`}');
  // New LinearProgress for task progress
  expect(content).toContain('aria-label="Current task progress"');
});

test('Components have aria-hidden="true" on decorative icons', () => {
  const files = ['CognitiveLoadGauge.tsx', 'PredictionPanel.tsx', 'TeamDashboard.tsx', 'TaskSequencer.tsx'];
  files.forEach(file => {
    const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
    expect(content).toContain('aria-hidden="true"');
  });
});

test('App.tsx has skip-to-content link, semantic roles, and decorative icons', () => {
  const appContent = fs.readFileSync(path.resolve(componentsDir, '..', 'App.tsx'), 'utf8');
  expect(appContent).toContain('href="#main-dashboard"');
  expect(appContent).toContain('id="main-dashboard"');
  expect(appContent).toContain('component="main"');
  expect(appContent).toContain('component="header"');
  expect(appContent).toContain('tabIndex={-1}');
  expect(appContent).toContain('Skip to main content');
  expect(appContent).toContain('aria-hidden="true"');
});
