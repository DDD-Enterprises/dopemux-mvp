// @ts-nocheck
import { expect, test } from 'vitest';
import fs from 'fs';
import path from 'path';

const componentsDir = path.resolve(__dirname, '..');

test('CognitiveLoadGauge.tsx has aria-label for LinearProgress and status Tooltip', () => {
  const filePath = path.join(componentsDir, 'CognitiveLoadGauge.tsx');
  if (!fs.existsSync(filePath)) {
    console.warn(`Skipping: Required component missing for accessibility test: ${filePath}`);
    return;
  }
  const content = fs.readFileSync(filePath, 'utf8');
  expect(content).toContain('aria-label="Cognitive Load Percentage"');
  expect(content).toContain('aria-valuetext');
  expect(content).toContain('<Tooltip title={`Recommendation: ${recommendation}`} arrow>');
  expect(content).toContain('tabIndex={0}');
});

test('PredictionPanel.tsx has aria-label for LinearProgress and loading state', () => {
  const filePath = path.join(componentsDir, 'PredictionPanel.tsx');
  if (!fs.existsSync(filePath)) {
    console.warn(`Skipping: Required component missing for accessibility test: ${filePath}`);
    return;
  }
  const content = fs.readFileSync(filePath, 'utf8');
  expect(content).toContain('aria-label="15-Minute Load Prediction Percentage"');
  expect(content).toContain('aria-valuetext');
  expect(content).toContain('Prediction Loading...');
  // Indeterminate LinearProgress in loading state
  expect(content).toContain('aria-label="Loading prediction data"');
  expect(content).toMatch(/<Tooltip[^>]*title="Predictive LSTM model running on edge device"[^>]*arrow/);
});

test('TeamDashboard.tsx has aria-labels for team and member progress bars and Tooltips', () => {
  const filePath = path.join(componentsDir, 'TeamDashboard.tsx');
  if (!fs.existsSync(filePath)) {
    console.warn(`Skipping: Required component missing for accessibility test: ${filePath}`);
    return;
  }
  const content = fs.readFileSync(filePath, 'utf8');
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
  expect(appContent).toContain('<Tooltip title={metric.tooltip} arrow describeChild>');
  expect(appContent).toMatch(/<Tooltip title=\{metric\.tooltip\} arrow describeChild>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toContain('aria-label={`${metric.label}: ${metric.value !== null ? (metric.value * 100).toFixed(0) : \'N/A\'}%`}');
  expect(appContent).toContain('&:focus-visible');
});

test('TaskSequencer.tsx has contextual aria-labels and current step indicator', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('aria-label={isTimerRunning ? `Pause task: ${currentTask.title}` : `Start task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={`Complete task: ${currentTask.title}`}');
  expect(content).toContain('aria-label={');
  expect(content).toContain('nextTask');
  expect(content).toContain('? `Skip ${currentTask.title}, proceed to ${nextTask.title}`');
  expect(content).toContain(': `Skip task: ${currentTask.title}`');
  expect(content).toContain('aria-label={`Start task: ${task.title}`}');
  // New LinearProgress for task progress
  expect(content).toContain('aria-label={`Progress for task: ${currentTask.title}`}');
  // Timer accessibility
  expect(content).toContain('aria-label={getTimerAriaLabel(taskTimer)}');
  // Total remaining duration
  expect(content).toContain('role="status"');
  expect(content).toMatch(/aria-label=\{\s*isComplete\s*\?\s*'Task sequence complete'\s*:\s*`\$\{completedCount\}\/\$\{totalCount\} tasks completed\. \$\{getDurationAriaLabel\(displayRemainingMinutes\)\}\.\$\{finishTimeLabel\s*\?\s*` Estimated completion: \$\{finishTimeLabel\}`\s*:\s*''\}`\s*\}/);
  expect(content).toContain('title={');
  expect(content).toContain('optimizedTasks.length <= 1');
  expect(content).toContain("? 'No other tasks to skip to'");
  expect(content).toContain(": `Skip to: ${nextTask?.title || 'next ritual'}`");
  expect(content).toMatch(/<Tooltip[^>]*title="Real-time task synchronization active"[^>]*arrow/);
  expect(content).toContain('aria-label="Real-time task synchronization active"');
  expect(content).toContain('aria-current={isCurrent ? \'step\' : undefined}');
  // Total remaining duration display and completed-state accessibility
  expect(content).toContain('role="status"');
  expect(content).toMatch(/aria-label=\{\s*isComplete\s*\?\s*'Task sequence complete'\s*:\s*`\$\{completedCount\}\/\$\{totalCount\} tasks completed\. \$\{getDurationAriaLabel\(displayRemainingMinutes\)\}\.\$\{finishTimeLabel\s*\?\s*` Estimated completion: \$\{finishTimeLabel\}`\s*:\s*''\}`\s*\}/);
  expect(content).toContain('aria-label="Ritual Complete: All tasks finished"');
  expect(content).toContain('const headerRef = useRef<HTMLHeadingElement>(null);');
  expect(content).toContain('ref={headerRef}');
  expect(content).toContain('tabIndex={-1}');
  expect(content).toContain('headerRef.current?.focus();');
});

test('TaskSequencer.tsx implements overtime visual cues', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('const isOvertime = useMemo(() =>');
  expect(content).toContain('color: isOvertime ? brandTokens.colors.gremlinPink : \'inherit\'');
  expect(content).toContain('OVERTIME +{overtimeMinutes}M');
  expect(content).toContain('bgcolor: alpha(isOvertime ? brandTokens.colors.gremlinPink : brandTokens.colors.saintGold, 0.1)');
});

test('Components have aria-hidden="true" on decorative icons', () => {
  const files = ['CognitiveLoadGauge.tsx', 'PredictionPanel.tsx', 'TeamDashboard.tsx', 'TaskSequencer.tsx'];
  files.forEach(file => {
    const filePath = path.join(componentsDir, file);
    if (!fs.existsSync(filePath)) {
      console.warn(`Skipping icon check for missing component: ${file}`);
      return;
    }
    const content = fs.readFileSync(filePath, 'utf8');
    expect(content).toContain('aria-hidden="true"');
  });
});

test('TaskSequencer.tsx has accessible timer with pluralization', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('role="timer"');
  expect(content).toContain('aria-label={getTimerAriaLabel(taskTimer)}');
  expect(content).toContain('const getTimerAriaLabel = (seconds: number): string =>');
});

test('TaskSequencer.tsx displays total remaining duration with accessibility', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('const totalRemainingMinutes = useMemo(() =>');
  expect(content).toMatch(/aria-label=\{\s*isComplete\s*\?\s*'Task sequence complete'\s*:\s*`\$\{completedCount\}\/\$\{totalCount\} tasks completed\. \$\{getDurationAriaLabel\(displayRemainingMinutes\)\}\.\$\{finishTimeLabel\s*\?\s*` Estimated completion: \$\{finishTimeLabel\}`\s*:\s*''\}`\s*\}/);
  expect(content).toContain('tabIndex={0}');
  expect(content).toMatch(/<Tooltip\s+title=\{\s*isComplete\s*\?\s*'Task sequence complete'\s*:\s*`\$\{completedCount\}\/\$\{totalCount\} tasks • \$\{getDurationAriaLabel\(displayRemainingMinutes\)\}\$\{finishTimeLabel\s*\?\s*` \(\$\{finishTimeLabel\}\)`\s*:\s*''\}`\s*\}\s+arrow\s*>/);
});

test('App.tsx has accessible header chips and skip link', () => {
  const appContent = fs.readFileSync(path.resolve(__dirname, '../../App.tsx'), 'utf8');
  const themeContent = fs.readFileSync(path.resolve(__dirname, '../../theme.ts'), 'utf8');
  expect(appContent).toContain('href="#main-dashboard"');
  expect(appContent).toContain('aria-label={`System is actively monitoring ritual state: ${connectionLabel} DØPEMÜX Ritual Daemon`}');
  expect(appContent).toContain('<Tooltip title="Current cognitive status and load percentage" arrow>');
  expect(appContent).toContain('<Tooltip title="AI-generated recommendation based on current load" arrow>');
  expect(appContent).toMatch(/<Tooltip title="Current cognitive status and load percentage" arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toMatch(/<Tooltip title="AI-generated recommendation based on current load" arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toContain('aria-label={`System is actively monitoring ritual state: ${connectionLabel} DØPEMÜX Ritual Daemon`}');
  expect(appContent).toContain('aria-label={isConfirmingClear ? \'Confirm clear all notifications\' : \'Clear all notifications\'}');
  expect(appContent).toMatch(/<Tooltip title=\{isConfirmingClear \? 'Confirm to clear all notifications' : 'Clear all notifications to reduce visual noise'\} arrow>/);
  expect(appContent).toContain('Listening for ConPort and ADHD event traffic');
  expect(appContent).toContain('animation: \'listeningPulse 1.4s infinite ease-in-out both\'');
  expect(appContent).toContain('severity="error"');
  expect(themeContent).toContain('MuiChip');
  expect(themeContent).toContain('&:focus-visible');
  expect(appContent).toContain('ref={feedHeadingRef}');
  expect(appContent).toContain('tabIndex={-1}');
});
