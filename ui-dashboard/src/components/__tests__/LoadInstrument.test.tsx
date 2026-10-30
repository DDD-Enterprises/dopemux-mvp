// @vitest-environment jsdom
import { afterEach, expect, test } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import LoadInstrument from '../LoadInstrument';

afterEach(cleanup);

test('shows unknown instead of a number when there is no reading', () => {
  render(<LoadInstrument load={null} prediction={null} recommendation={null} />);

  expect(screen.getByText('Unknown')).toBeInTheDocument();
  expect(screen.queryByText(/%$/)).not.toBeInTheDocument();
  expect(screen.queryByRole('meter')).not.toBeInTheDocument();
  expect(screen.getByText('No reading received.')).toBeInTheDocument();
});

test('shows load, state name and a meter for a live reading', () => {
  render(<LoadInstrument load={0.64} prediction={0.71} recommendation="Finish the current task, then take a break." />);

  expect(screen.getByText('64%')).toBeInTheDocument();
  expect(screen.getByText('Pressure Build')).toBeInTheDocument();

  const meter = screen.getByRole('meter');
  expect(meter).toHaveAttribute('aria-valuenow', '64');
  expect(meter).toHaveAttribute('aria-valuemin', '0');
  expect(meter).toHaveAttribute('aria-valuemax', '100');
  expect(meter.getAttribute('aria-valuetext')).toContain('forecast 71%');

  expect(screen.getByText('71%')).toBeInTheDocument();
  expect(screen.getByText('+7 pts')).toBeInTheDocument();
  expect(screen.getByText('Finish the current task, then take a break.')).toBeInTheDocument();
});

test('labels the forecast unknown when the backend sends none', () => {
  render(<LoadInstrument load={0.4} prediction={null} recommendation={null} />);

  expect(screen.getByText('Flow Ritual')).toBeInTheDocument();
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('unknown');
  expect(screen.queryByText('NEXT:')).not.toBeInTheDocument();
});

test('shows a decimal only where a whole number would cross a zone edge', () => {
  const { rerender } = render(<LoadInstrument load={0.804} prediction={null} recommendation={null} />);
  expect(screen.getByText('80.4%')).toBeInTheDocument();
  expect(screen.getByText('Break. Now.')).toBeInTheDocument();

  rerender(<LoadInstrument load={0.296} prediction={null} recommendation={null} />);
  expect(screen.getByText('29.6%')).toBeInTheDocument();
  expect(screen.getByText('Gentle Glide')).toBeInTheDocument();

  rerender(<LoadInstrument load={0.62} prediction={null} recommendation={null} />);
  expect(screen.getByText('62%')).toBeInTheDocument();
});

test('uses the same thresholds as deriveStatus at the zone edges', () => {
  const { rerender } = render(<LoadInstrument load={0.29} prediction={null} recommendation={null} />);
  expect(screen.getByText('Gentle Glide')).toBeInTheDocument();

  rerender(<LoadInstrument load={0.81} prediction={null} recommendation={null} />);
  expect(screen.getByText('Break. Now.')).toBeInTheDocument();
});
