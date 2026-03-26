// @ts-nocheck
import { expect, test } from 'vitest';
import fs from 'fs';
import path from 'path';

const componentsDir = path.resolve(__dirname, '..');

test('CognitiveLoadGauge.tsx has aria-label for LinearProgress and status Tooltip', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'CognitiveLoadGauge.tsx'), 'utf8');
  expect(content).toContain('aria-label="Cognitive Load Percentage"');
  expect(content).toContain('aria-valuetext');
  expect(content).toContain('<Tooltip title={`Recommendation: ${recommendation}`} arrow>');
  expect(content).toContain('tabIndex={0}');
});

test('PredictionPanel.tsx has aria-label for LinearProgress and loading state', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'PredictionPanel.tsx'), 'utf8');
  expect(content).toContain('aria-label="15-Minute Load Prediction Percentage"');
  expect(content).toContain('aria-valuetext');
  expect(content).toContain('Prediction Loading...');
  // Indeterminate LinearProgress in loading state
  expect(content).toContain('aria-label="Loading prediction data"');
  expect(content).toMatch(/<Tooltip[^>]*title="Predictive LSTM model running on edge device"[^>]*arrow/);
});

test('TeamDashboard.tsx has aria-labels for team and member progress bars and Tooltips', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TeamDashboard.tsx'), 'utf8');
  expect(content).toContain('aria-label="Team Average Cognitive Load Percentage"');
  expect(content).toContain('aria-label={`${member.name}\'s Cognitive Load Percentage`}');
  expect(content).toContain('aria-label={`Profile picture of ${member.name}`}');
  expect(content).toContain('<Tooltip title={statusStyles[member.status].label} arrow>');
  expect(content).toContain('<Tooltip title="Average cognitive load across all team members" arrow>');
  expect(content).toContain('<Tooltip title="Current energy level" arrow>');
  expect(content).toContain('<Tooltip title="Current attention focus" arrow>');
  expect(content).toContain('<Tooltip title="AI-generated team coordination insights" arrow>');
  expect(content).toContain('tabIndex={0}');
  expect(content).toMatch(/<Tooltip title="Current energy level"[\s\S]*tabIndex=\{0\}/);
  expect(content).toMatch(/<Tooltip title="Current attention focus"[\s\S]*tabIndex=\{0\}/);
  expect(content).toMatch(/<Tooltip[^>]*title="AI-generated team coordination insights"[^>]*arrow/);
});

test('App.tsx exposes metric card tooltips with focus indicators and labels', () => {
  const appContent = fs.readFileSync(path.join(componentsDir, '..', 'App.tsx'), 'utf8');
  expect(appContent).toContain('<Tooltip title={metric.tooltip} arrow>');
  expect(appContent).toMatch(/<Tooltip title=\{metric\.tooltip\} arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toContain('aria-label={`${metric.label}: ${metric.value !== null ? (metric.value * 100).toFixed(0) : \'N/A\'}%`}');
  expect(appContent).toContain('&:focus-visible');
});

test('TaskSequencer.tsx has contextual aria-labels and current step indicator', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('aria-label={isTimerRunning ? `Pause task: ${currentTask.title}` : `Start task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Complete task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Skip task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Start task: ${task.title}`}');
  // New LinearProgress for task progress
  expect(content).toContain('aria-label="Current task progress"');
  // Timer accessibility
  expect(content).toContain('aria-label={getTimerAriaLabel(taskTimer)}');
  expect(content).toMatch(/<Tooltip[^>]*title="Real-time task synchronization active"[^>]*arrow/);
  expect(content).toContain('aria-label="Real-time task synchronization active"');
  expect(content).toContain('aria-current={isCurrent ? \'step\' : undefined}');
  // Total remaining duration display
  expect(content).toContain('role="status"');
  expect(content).toContain('aria-label={`Total remaining duration: ${totalRemainingMinutes} minutes`}');
  expect(content).toContain('aria-label="Ritual Complete: All tasks finished"');
});

test('Components have aria-hidden="true" on decorative icons', () => {
  const files = ['CognitiveLoadGauge.tsx', 'PredictionPanel.tsx', 'TeamDashboard.tsx', 'TaskSequencer.tsx'];
  files.forEach(file => {
    const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
    expect(content).toContain('aria-hidden="true"');
  });
});

test('TaskSequencer.tsx has accessible timer with pluralization', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('role="timer"');
  expect(content).toContain('aria-label={getTimerAriaLabel(taskTimer)}');
  expect(content).toContain('const getTimerAriaLabel = (seconds: number): string =>');
});

test('App.tsx has accessible header chips and skip link', () => {
  const appContent = fs.readFileSync(path.resolve(__dirname, '../../App.tsx'), 'utf8');
  expect(appContent).toContain('href="#main-dashboard"');
  expect(appContent).toContain('aria-label={`System is actively monitoring ritual state: ${brandTokens.chips.live} DØPEMÜX Ritual Daemon`}');
  expect(appContent).toContain('<Tooltip title="Current cognitive status and load percentage" arrow>');
  expect(appContent).toContain('<Tooltip title="AI-generated recommendation based on current load" arrow>');
  expect(appContent).toMatch(/<Tooltip title="Current cognitive status and load percentage" arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toMatch(/<Tooltip title="AI-generated recommendation based on current load" arrow>[\s\S]*tabIndex=\{0\}/);
});
