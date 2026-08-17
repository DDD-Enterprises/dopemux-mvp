// @vitest-environment jsdom
// @ts-nocheck
import { expect, test } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import React from 'react';
import fs from 'fs';
import path from 'path';
import PredictionPanel from '../PredictionPanel';
import TaskSequencer from '../TaskSequencer';

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
  expect(content).toMatch(/<Tooltip title=\{\s*copied\s*\?\s*'Copied!'\s*:\s*`AI Recommendation: \$\{recommendation\}\. Click to copy\.`\s*\}\s*arrow\s*>/);
  expect(content).toContain('getDynamicRoast');
  expect(content).toContain('load-pulse');
  expect(content).toContain('prefers-reduced-motion');
  expect(content).toContain('tabIndex={0}');
  expect(content).toContain('role="button"');
  expect(content).toMatch(/aria-label=\{\s*copied\s*\?\s*'Copied'\s*:\s*`Load \$\{val\}%, \$\{statusMeta\.label\}\. AI Recommendation: \$\{recommendation\}\. Click to copy\.`\s*\}/);
  expect(content).toContain('onClick={onCopy}');
  expect(content).toContain("cursor: 'copy'");
  expect(content).toContain('copy-glow');
});

test('PredictionPanel.tsx rendered accessibility and state feedback', () => {
  // Test 1: Loading state (no prediction)
  const { rerender } = render(<PredictionPanel />);
  const progressBar = screen.getByRole('progressbar');
  expect(progressBar).toHaveAttribute('aria-label', '15-Minute Load Prediction Percentage');

  const paper = screen.getByLabelText('No prediction');
  expect(paper).toHaveAttribute('tabIndex', '0');
  // Root paper no longer has role=button (dedicated copy control pattern)
  expect(paper).not.toHaveAttribute('role', 'button');

  const roastBox = screen.getByLabelText('No forecast available');
  expect(roastBox).not.toHaveAttribute('role', 'button');
  expect(roastBox).toHaveAttribute('tabIndex', '-1');

  // Test 2: With critical prediction
  rerender(<PredictionPanel prediction={0.9} />);

  const criticalValue = '90%';
  expect(screen.getByText(criticalValue)).toBeDefined();

  const criticalLabel = /15-min prediction 90%, Break\. Now\./i;
  expect(screen.getByLabelText(criticalLabel)).toBeDefined();

  const activeRoastBox = screen.getAllByRole('button').find(el => el.getAttribute('aria-label')?.includes('Click to copy'));
  expect(activeRoastBox).toBeDefined();
  expect(activeRoastBox).toHaveAttribute('tabIndex', '0');

  // Test 3: With optimal prediction
  rerender(<PredictionPanel prediction={0.4} />);
  const optimalValue = '40%';
  expect(screen.getByText(optimalValue)).toBeDefined();
  expect(screen.getByLabelText(/15-min prediction 40%, Flow Ritual/i)).toBeDefined();

  // Test 4: Verify dynamic trend icon (TrendingUp when prediction > currentLoad)
  const { container: containerUp } = render(<PredictionPanel prediction={0.8} currentLoad={0.4} />);
  expect(containerUp.querySelector('.lucide-trending-up')).not.toBeNull();
  expect(containerUp.querySelector('.lucide-trending-down')).toBeNull();

  // Test 5: Verify dynamic trend icon (TrendingDown when prediction < currentLoad)
  const { container: containerDown } = render(<PredictionPanel prediction={0.3} currentLoad={0.7} />);
  expect(containerDown.querySelector('.lucide-trending-down')).not.toBeNull();
  expect(containerDown.querySelector('.lucide-trending-up')).toBeNull();
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
  // Verify team signal chips
  expect(content).toMatch(/<Tooltip key=\{signal\.label\} title=\{`Team signal: \$\{signal\.label\} status`\} arrow>/);
  expect(content).toContain('aria-label={`Team signal: ${signal.label} is ${signal.value}`}');
  expect(content).toContain("cursor: 'help'");

  // Verify TeamDashboard root interactive surface and summary Tooltip
  expect(content).toContain('tabIndex={0}');
  expect(content).toMatch(/<Tooltip[^>]*title=\{`Average Team Load: \$\{teamAverageLoad\}% • \$\{statusStyles\[teamStatus\]\.label\}\. AI Insight: \$\{teamInsight\}`\}[^>]*arrow/);
  expect(content).toContain('aria-label={`Team dashboard signal summary. Average load: ${teamAverageLoad}%. Status: ${statusStyles[teamStatus].label}. AI Insight: ${teamInsight}`}');
  expect(content).toContain("letterSpacing: '0.16em'");
  expect(content).toContain('AVG LOAD');
  expect(content).toContain('borderColor: teamStatusColor');
  expect(content).toContain('boxShadow: `0 0 20px ${alpha(teamStatusColor, 0.2)}`');

  // Verify Member Card consolidation
  expect(content).toMatch(/aria-label=\{\s*`\$\{member\.name\}: \$\{statusStyles\[member\.status\]\.label\}, \$\{member\.load\}% load, \$\{member\.energy\}% energy, \$\{member\.attention\}% attention`\s*\}/);

  // Verify AI Insight Copyable Surface
  expect(content).toMatch(/<Tooltip title=\{isCopied \? 'Copied!' : 'Copy team insight'\} arrow>/);
  expect(content).toMatch(/aria-label=\{\s*isCopied \? `Team insight: \$\{teamInsight\} \(Copied\)` : `Copy team insight: \$\{teamInsight\}`\s*\}/);
  expect(content).toContain('role="button"');
  expect(content).toContain('onKeyDown=');
  expect(content).toContain("animation: 'insight-copy-pulse 0.4s ease-out'");
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
  expect(content).toMatch(/aria-label=\{\s*nextTaskAfterCompletion\s*[\s\S]*\?\s*`Complete \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterCompletion\.title\}`\s*[\s\S]*:\s*`Complete \$\{currentTask\.title\}, finish ritual`\s*\}/);
  expect(content).toMatch(/aria-label=\{\s*isSkipConfirming\s*[\s\S]*nextTaskAfterSkip\s*[\s\S]*`Confirm skip \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterSkip\.title\}`\s*[\s\S]*:\s*`Confirm skip task: \$\{currentTask\.title\}`\s*[\s\S]*:\s*nextTaskAfterSkip\s*[\s\S]*`Skip \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterSkip\.title\}`\s*[\s\S]*:\s*`Skip task: \$\{currentTask\.title\}`\s*\}/);
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

  // Verify start button tooltip
  expect(content).toMatch(/<Tooltip\s+title=\{\s*`Start task and switch active focus to: \$\{task\.title\}`\s*\}\s*arrow\s*>/);

  // Verify disableTypography on ListItemText to prevent DOM nesting validation warning
  expect(content).toContain('disableTypography');

  // Verify Predictive Skip and Soft Confirmation
  expect(content).toContain('const [isSkipConfirming, setIsSkipConfirming] = useState(false);');
  expect(content).toContain('const skipConfirmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);');
  expect(content).toContain("animation: 'skip-pulse 1.5s infinite'");
  expect(content).toMatch(/aria-label=\{\s*isSkipConfirming\s*[\s\S]*nextTaskAfterSkip\s*[\s\S]*`Confirm skip \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterSkip\.title\}`\s*[\s\S]*:\s*`Confirm skip task: \$\{currentTask\.title\}`\s*[\s\S]*:\s*nextTaskAfterSkip\s*[\s\S]*`Skip \$\{currentTask\.title\}, proceed to \$\{nextTaskAfterSkip\.title\}`\s*[\s\S]*:\s*`Skip task: \$\{currentTask\.title\}`\s*\}/);
  expect(content).toContain('{isSkipConfirming ? \'Confirm Skip?\' : \'Skip\'}');
  expect(content).toContain('<AlertTriangle aria-hidden="true" size={16} />');
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
  expect(appContent).toMatch(/<Tooltip title={isCopied \? 'Recommendation copied!' : 'Copy recommendation to clipboard'\} arrow>/);
  expect(appContent).toMatch(/<Tooltip title="Current cognitive status and load percentage" arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toMatch(/<Tooltip title={isCopied \? 'Recommendation copied!' : 'Copy recommendation to clipboard'\} arrow>[\s\S]*tabIndex=\{0\}/);
  expect(appContent).toMatch(/aria-label=\{\s*isCopied\s*\?\s*`AI Recommendation: \$\{cognitiveState\.recommendation\} \(Copied\)`\s*:\s*`Copy AI Recommendation: \$\{cognitiveState\.recommendation\}`\s*\}/);
  expect(appContent).toContain('aria-label={isConfirmingClear ? \'Confirm clear all notifications\' : \'Clear all notifications\'}');
  expect(appContent).toMatch(/<Tooltip title={isConfirmingClear \? 'Confirm to clear all notifications' : 'Clear all notifications to reduce visual noise'\} arrow>/);
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

  // Verify hydration aftercare sip logger interactive states
  expect(appContent).toContain('const [isHydrated, setIsHydrated] = useState(false);');
  expect(appContent).toContain('const handleHydrate = useCallback(() => {');
  expect(appContent).toContain("isHydrated ? 'Sip Logged!' : 'Health and hydration status: Click to log a hydration sip.'");
  expect(appContent).toContain('onClick={handleHydrate}');

  // Verify onKeyDown handlers for connection, hydration, and recommendation chips
  expect(appContent).toContain('onKeyDown={');
  expect(appContent).toContain('handleReconnect();');
  expect(appContent).toContain('handleHydrate();');
  expect(appContent).toContain('void handleCopyRecommendation();');

  // Verify focus-visible overrides for buttons and icon buttons in theme
  expect(themeContent).toContain('MuiIconButton');
  expect(themeContent).toContain('&:focus-visible');
});

test('PredictionPanel.tsx has TrendIcon based on load and prediction', () => {
  const filePath = path.join(componentsDir, 'PredictionPanel.tsx');
  if (!fs.existsSync(filePath)) {
    console.warn(`Skipping: Required component missing: ${filePath}`);
    return;
  }
  const content = fs.readFileSync(filePath, 'utf8');
  expect(content).toContain("const isTrendingUp = hasPrediction && typeof currentLoad === 'number' ? prediction > currentLoad : true;");
  expect(content).toContain('const TrendIcon = isTrendingUp ? TrendingUp : TrendingDown;');
  expect(content).toContain('aria-hidden="true"');
  expect(content).toContain('TrendingDown');
});

test('TaskSequencer pending Start button renders tooltip on hover and keyboard focus', async () => {
  const cognitiveState = {
    energy: 80,
    attention: 70,
    load: 40,
    status: 'optimal' as const,
    recommendation: 'Stay focused.',
  };

  const getPendingListStartButton = () => {
    // List pending/non-current Start controls use "Start task: {title}" and live on
    // list items without aria-current="step". Exclude the primary ritual Start control
    // (tooltip "Start Ritual") which shares the same accessible-name pattern.
    const candidates = screen.getAllByRole('button', { name: /^Start task: / });
    const pending = candidates.find((btn) => {
      const listItem = btn.closest('li');
      return Boolean(listItem) && listItem.getAttribute('aria-current') !== 'step';
    });
    expect(pending).toBeTruthy();
    return pending as HTMLElement;
  };

  const titleFromStartButton = (button: HTMLElement) => {
    const accessibleName = button.getAttribute('aria-label') ?? '';
    const taskTitle = accessibleName.replace(/^Start task:\s*/, '');
    expect(taskTitle.length).toBeGreaterThan(0);
    return taskTitle;
  };

  render(<TaskSequencer cognitiveState={cognitiveState} />);

  const startButton = getPendingListStartButton();
  const taskTitle = titleFromStartButton(startButton);
  const expectedTooltip = `Start task and switch active focus to: ${taskTitle}`;

  // Keyboard focus path first: MUI Tooltip opens only on focus-visible.
  // Use real .focus() so jsdom :focus-visible matches; fireEvent.focus alone may not.
  fireEvent.keyDown(document, { key: 'Tab' });
  startButton.focus();
  fireEvent.focus(startButton);
  expect(await screen.findByRole('tooltip', {}, { timeout: 2000 })).toHaveTextContent(expectedTooltip);

  startButton.blur();
  fireEvent.blur(startButton);
  // Remount for a clean hover path (pointer modality must not poison keyboard assert above).
  cleanup();
  render(<TaskSequencer cognitiveState={cognitiveState} />);

  const hoverStartButton = getPendingListStartButton();
  const hoverTitle = titleFromStartButton(hoverStartButton);
  const hoverExpected = `Start task and switch active focus to: ${hoverTitle}`;

  // Hover path — MUI Tooltip portals title text after enter delay.
  fireEvent.mouseOver(hoverStartButton);
  expect(await screen.findByRole('tooltip', {}, { timeout: 2000 })).toHaveTextContent(hoverExpected);
});
