// @vitest-environment jsdom
import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import React from 'react';
import fs from 'fs';
import path from 'path';
import TaskSequencer from '../TaskSequencer';
import { brandTokens } from '../../theme';

const cognitiveState = {
  energy: 80,
  attention: 70,
  load: 40,
  status: 'optimal' as const,
  recommendation: 'Stay focused.',
};

test('TaskSequencer ListItemText does not nest a div under a p', () => {
  const { container } = render(<TaskSequencer cognitiveState={cognitiveState} />);

  expect(container.querySelectorAll('p div').length).toBe(0);
  expect(container.querySelectorAll('p p').length).toBe(0);
  expect(container.querySelectorAll('.MuiTypography-root .MuiBox-root').length).toBe(0);
});

test('TaskSequencer preserves secondary caption tokens after disableTypography', () => {
  render(<TaskSequencer cognitiveState={cognitiveState} />);

  const durationHosts = screen.getAllByLabelText('Estimated duration: 90 minutes');
  expect(durationHosts.length).toBeGreaterThan(0);
  for (const host of durationHosts) {
    const durationCaption = host.querySelector('.MuiTypography-caption');
    expect(durationCaption).not.toBeNull();
    expect(durationCaption).toHaveStyle({ color: brandTokens.text.secondary });
  }

  const indexCaptions = screen.getAllByText('#2');
  expect(indexCaptions.length).toBeGreaterThan(0);
  for (const indexCaption of indexCaptions) {
    expect(indexCaption).toHaveStyle({ color: brandTokens.text.secondary });
  }

  const titles = screen.getAllByText('Create UI dashboard components');
  expect(titles.length).toBeGreaterThan(0);
  for (const title of titles) {
    expect(title).toHaveStyle({ color: brandTokens.text.primary });
  }
});

test('TaskSequencer ListItemText keeps disableTypography and explicit token colors', () => {
  const source = fs.readFileSync(
    path.resolve(__dirname, '..', 'TaskSequencer.tsx'),
    'utf8',
  );

  expect(source).toMatch(/<ListItemText[\s\S]*disableTypography/);
  expect(source).toContain('color: brandTokens.text.primary');
  expect(source).toContain('color: brandTokens.text.secondary');
});
