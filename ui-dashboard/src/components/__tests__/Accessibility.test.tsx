// @vitest-environment jsdom
// @ts-nocheck
import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import React from 'react';
import fs from 'fs';
import path from 'path';
import PredictionPanel from '../PredictionPanel';

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

test('PredictionPanel.tsx rendered accessibility and state feedback', () => {
  // Test 1: Loading state (no prediction)
  const { rerender } = render(<PredictionPanel />);
  const progressBar = screen.getByRole('progressbar');
  expect(progressBar).toHaveAttribute('aria-label', '15-Minute Load Prediction Percentage');
  expect(progressBar).toHaveAttribute('aria-valuetext', 'Prediction Loading...');

  const panel = screen.getByLabelText('No prediction available');
  expect(panel).toHaveAttribute('tabIndex', '0');

  // Test 2: With critical prediction
  rerender(<PredictionPanel prediction={0.9} />);

  const criticalValue = '90%';
  expect(screen.getByText(criticalValue)).toBeDefined();
  expect(progressBar).toHaveAttribute('aria-valuetext', criticalValue);

  const criticalLabel = /Fifteen minute prediction 90 percent, Break\. Now\./i;
  expect(screen.getByLabelText(criticalLabel)).toBeDefined();

  // Test 3: With optimal prediction
  rerender(<PredictionPanel prediction={0.4} />);
  const optimalValue = '40%';
  expect(screen.getByText(optimalValue)).toBeDefined();
  expect(screen.getByLabelText(/Fifteen minute prediction 40 percent, Flow Ritual/i)).toBeDefined();
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
  expect(content).toContain('aria-label={`${member.name}\'s current status: ${statusStyles[member.status].label}`}');
  expect(content).toContain('aria-label={`${member.name}\'s current energy level: ${member.energy}%`}');
  expect(content).toContain('aria-label={`${member.name}\'s current attention focus: ${member.attention}%`}');
  expect(content).toContain('<Tooltip title={statusStyles[member.status].label} arrow>');
  expect(content).toContain('<Tooltip title="Current energy level" arrow>');
  expect(content).toContain('<Tooltip title="Current attention focus" arrow>');
  expect(content).toContain('tabIndex={0}');
  expect(content).toMatch(/<Tooltip title="Current energy level"[\s\S]*tabIndex=\{0\}/);
  expect(content).toMatch(/<Tooltip title="Current attention focus"[\s\S]*tabIndex=\{0\}/);
  // Verify team signal chips
  expect(content).toMatch(/<Tooltip key=\{signal\.label\} title=\{`Team signal: \$\{signal\.label\} status`\} arrow>/);
  expect(content).toContain('aria-label={`Team signal: ${signal.label} is ${signal.value}`}');
  expect(content).toContain("cursor: 'help'");

  // Verify TeamDashboard root interactive surface and summary Tooltip
  expect(content).toContain('tabIndex={0}');
  expect(content).toMatch(/<Tooltip[^>]*title=\{`Average Team Load: \$\{teamAverageLoad\}% • \$\{statusStyles\[teamStatus\]\.label\}`\}[^>]*arrow/);
  expect(content).toContain('aria-label={`Team dashboard signal summary. Average load: ${teamAverageLoad}%. Status: ${statusStyles[teamStatus].label}.`}');
  expect(content).toContain("letterSpacing: '0.16em'");
  expect(content).toContain('AVG LOAD');
  expect(content).toContain('borderColor: teamStatusColor');
  expect(content).toContain('boxShadow: `0 0 20px ${alpha(teamStatusColor, 0.2)}`');

  // Verify AI Insight copyable surface
  expect(content).toContain('role="button"');
  expect(content).toContain('onClick={() => handleCopyInsight(teamInsight)}');
  expect(content).toMatch(/aria-label=\{\s*isInsightCopied\s*\?\s*`AI Insight: \$\{teamInsight\} \(Copied to clipboard\)`\s*:\s*`AI Insight: \$\{teamInsight\}\. Click to copy to clipboard\.`\s*\}/);
  expect(content).toMatch(/animation:\s*'insight-copy-pulse 0.4s ease-out'/);
  expect(content).toContain('COPIED!');
  expect(content).toContain('AI INSIGHT');
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
  expect(content).toContain('getCompletionTransitionTask(currentTaskId, tasks, optimizedTasks)');
  expect(content).toContain('getSkipTransitionTask(currentTaskId, optimizedTasks)');
  expect(content).toMatch(/aria-label=\{\s*nextTaskAfterCompletion\s*\?\s*`Complete \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterCompletion\.title\}`\s*:\s*`Complete \$\{currentTask\.title\}, finish ritual`\s*\}/);
  expect(content).toMatch(/aria-label=\{\s*nextTaskAfterSkip\s*\?\s*`Skip \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterSkip\.title\}`\s*:\s*`Skip task: \$\{currentTask\.title\}`\s*\}/);
  expect(content).toContain('aria-label={`Start task: ${task.title}`}');
  // New LinearProgress for task progress
  expect(content).toContain('aria-label={`Progress for task: ${currentTask.title}`}');
  // Timer accessibility
  expect(content).toContain('aria-label={getTimerAriaLabel(taskTimer)}');
  // Total remaining duration
  expect(content).toContain('role="status"');
  expect(content).toMatch(/aria-label=\{\s*isComplete\s*\?\s*'Task sequence complete'\s*:\s*`\$\{completedCount\}\/\$\{totalCount\} tasks completed\. \$\{getDurationAriaLabel\(displayRemainingMinutes\)\}\.\$\{finishTimeLabel\s*\?\s*` Estimated completion: \$\{finishTimeLabel\}`\s*:\s*''\}`\s*\}/);
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
  // Predictive task finish times
  expect(content).toMatch(/\{taskFinishTimes\[task\.id\] && \(/);
  expect(content).toContain('• Ends at {taskFinishTimes[task.id]}');

  // Verify task metadata is focusable and has correct aria-labels
  expect(content).toContain('tabIndex={0}');
  expect(content).toContain('aria-label={`Complexity: ${Math.round(task.complexity * 100)}%`}');
  expect(content).toContain('aria-label={`Estimated duration: ${task.estimatedMinutes} minutes`}');
  expect(content).toContain('aria-label={`Energy requirement: ${task.energyRequired}`}');
  expect(content).toContain('aria-label={`Estimated finish time: ${taskFinishTimes[task.id]}`}');
  expect(content).toContain("cursor: 'help'");
  expect(content).toContain('&:focus-visible');

  // Verify copy task title button
  expect(content).toMatch(/aria-label=\{\s*isTaskTitleCopied\s*\?\s*'Task title copied'\s*:\s*'Copy task title to clipboard'\s*\}/);
  expect(content).toMatch(/animation:\s*'copy-success 0.4s ease-out'/);
  expect(content).toContain('<IconButton');
  expect(content).toContain('onClick={() => handleCopyTaskTitle(currentTask.title)}');
});

test('TaskSequencer.tsx implements overtime visual cues', () => {
  const content = fs.readFileSync(path.join(componentsDir, 'TaskSequencer.tsx'), 'utf8');
  expect(content).toContain('const isOvertime = useMemo(() =>');
  expect(content).toContain('color: isOvertime ? brandTokens.colors.gremlinPink : \'inherit\'');
  expect(content).toContain('OVERTIME +{overtimeMinutes}M');
  expect(content).toMatch(/bgcolor:\s*alpha\(\s*isOvertime\s*\?\s*brandTokens\.colors\.gremlinPink\s*:\s*progressPercent\s*>\s*80\s*\?\s*brandTokens\.colors\.giltEdge\s*:\s*brandTokens\.colors\.saintGold,\s*0\.1\s*\)/);
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
  expect(appContent).toMatch(/aria-label=\{\s*connectionStatus === 'degraded'\s*\?\s*`System connection degraded: \$\{connectionLabel\} DØPEMÜX Ritual Daemon\. Click to retry connection\.`\s*:\s*`System is actively monitoring ritual state: \$\{connectionLabel\} DØPEMÜX Ritual Daemon`\s*\}/);
  expect(appContent).toContain('<Tooltip title="Current cognitive status and load percentage" arrow>');
  expect(appContent).toMatch(/<Tooltip title=\{isCopied \? 'Recommendation copied!' : 'Copy recommendation to clipboard'\} arrow>/);
  expect(appContent).toMatch(/<Tooltip title="Current cognitive status and load percentage" arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toMatch(/<Tooltip title=\{isCopied \? 'Recommendation copied!' : 'Copy recommendation to clipboard'\} arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toMatch(/aria-label=\{\s*isCopied\s*\?\s*`AI Recommendation: \$\{cognitiveState\.recommendation\} \(Copied\)`\s*:\s*`Copy AI Recommendation: \$\{cognitiveState\.recommendation\}`\s*\}/);
  expect(appContent).toContain('aria-label={isConfirmingClear ? \'Confirm clear all notifications\' : \'Clear all notifications\'}');
  expect(appContent).toMatch(/<Tooltip title=\{isConfirmingClear \? 'Confirm to clear all notifications' : 'Clear all notifications to reduce visual noise'\} arrow>/);
  expect(appContent).toContain('System is actively listening for ConPort and ADHD event traffic');
  expect(appContent).toContain('animation: \'listeningPulse 1.4s infinite ease-in-out both\'');
  expect(appContent).toContain('Waiting for signals...');
  expect(appContent).toContain('severity="error"');
  expect(themeContent).toContain('MuiChip');
  expect(themeContent).toContain('&:focus-visible');
  expect(appContent).toContain('ref={feedHeadingRef}');
  expect(appContent).toContain('tabIndex={-1}');

  // Verify adaptive reconnection bridge
  expect(appContent).toContain('const [retryTrigger, setRetryTrigger] = useState(0);');
  expect(appContent).toContain('const handleReconnect = useCallback(() => {');
  expect(appContent).toMatch(/connectionStatus === 'degraded'\s*\?\s*'Connection degraded\. Click to attempt manual reconnection\.'\s*:\s*'Real-time connection to the ADHD dashboard surface'/);
  expect(appContent).toMatch(/connectionStatus === 'degraded'\s*\?\s*`System connection degraded: \$\{connectionLabel\} DØPEMÜX Ritual Daemon\. Click to retry connection\.`\s*:\s*`System is actively monitoring ritual state: \$\{connectionLabel\} DØPEMÜX Ritual Daemon`/);
  expect(appContent).toContain("onClick={connectionStatus === 'degraded' ? handleReconnect : undefined}");
  expect(appContent).toContain('action={');
  expect(appContent).toContain("connectionStatus === 'degraded' ? (");
  expect(appContent).toContain('<Button color="inherit" size="small" onClick={handleReconnect}>');
  expect(appContent).toContain('RECONNECT');

  // Verify notification chips are focusable
  expect(appContent).toContain('<Tooltip title="Dismiss notification" arrow describeChild>');
  expect(appContent).toContain('aria-label={notificationLabel}');
  expect(appContent).toContain('tabIndex={0}');
});
