// @vitest-environment jsdom
import { afterEach, expect, test } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import AttentionStatePanel from '../AttentionStatePanel';

afterEach(cleanup);

test('renders unknown states with accessibility attributes and tooltips', () => {
  render(<AttentionStatePanel energyLevel={null} attentionState={null} />);

  const energyBox = screen.getByLabelText('Energy level: unknown');
  expect(energyBox).toBeInTheDocument();
  expect(energyBox).toHaveAttribute('tabIndex', '0');

  const attentionBox = screen.getByLabelText('Attention state: unknown');
  expect(attentionBox).toBeInTheDocument();
  expect(attentionBox).toHaveAttribute('tabIndex', '0');
});

test('renders known energy level and attention state with descriptive aria-label and step context', () => {
  render(<AttentionStatePanel energyLevel="medium" attentionState="focused" />);

  const energyBox = screen.getByLabelText('Energy level: medium, step 3 of 5');
  expect(energyBox).toBeInTheDocument();
  expect(energyBox).toHaveAttribute('tabIndex', '0');
  expect(energyBox).toHaveTextContent('medium');

  const attentionBox = screen.getByLabelText('Attention state: focused');
  expect(attentionBox).toBeInTheDocument();
  expect(attentionBox).toHaveAttribute('tabIndex', '0');
  expect(attentionBox).toHaveTextContent('focused');
});

test('renders tooltip on keyboard focus for energy level', async () => {
  render(<AttentionStatePanel energyLevel="high" attentionState="overwhelmed" />);

  const energyBox = screen.getByLabelText('Energy level: high, step 4 of 5');
  fireEvent.keyDown(document, { key: 'Tab' });
  energyBox.focus();
  fireEvent.focus(energyBox);

  expect(await screen.findByRole('tooltip', {}, { timeout: 2000 })).toHaveTextContent(
    'Energy level: high (4/5)'
  );
});

test('renders tooltip on keyboard focus for attention state', async () => {
  render(<AttentionStatePanel energyLevel="high" attentionState="overwhelmed" />);

  const attentionBox = screen.getByLabelText('Attention state: overwhelmed');
  fireEvent.keyDown(document, { key: 'Tab' });
  attentionBox.focus();
  fireEvent.focus(attentionBox);

  expect(await screen.findByRole('tooltip', {}, { timeout: 2000 })).toHaveTextContent(
    'Attention state: overwhelmed'
  );
});
