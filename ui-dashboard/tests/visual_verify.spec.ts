import { test, expect } from '@playwright/test';

test('TaskSequencer renders with enhancements', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // Wait for Task Sequencer to render
  const sequencer = page.locator('.dopemux-panel').filter({ hasText: 'Task Sequencer' });
  await expect(sequencer).toBeVisible();

  // Check for the new progress bar
  const progressBar = sequencer.locator('span[role="progressbar"]');
  await expect(progressBar).toBeVisible();

  // Check for tooltips (hover over start button)
  const startButton = sequencer.getByLabel(/Start task:/).first();
  await startButton.hover();

  // Wait for tooltip to appear
  const tooltip = page.getByRole('tooltip');
  await expect(tooltip).toBeVisible();

  // Take a screenshot of the sequencer
  await sequencer.screenshot({ path: 'task-sequencer-enhanced.png' });
});
