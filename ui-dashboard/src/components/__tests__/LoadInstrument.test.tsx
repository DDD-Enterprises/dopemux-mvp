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

test('rounds away from a zone edge when one decimal still lands on it', () => {
  const { rerender } = render(<LoadInstrument load={0.8001} prediction={null} recommendation={null} />);
  expect(screen.getByText('80.1%')).toBeInTheDocument();
  expect(screen.getByText('Break. Now.')).toBeInTheDocument();
  expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '80.1');

  rerender(<LoadInstrument load={0.6001} prediction={null} recommendation={null} />);
  expect(screen.getByText('60.1%')).toBeInTheDocument();
  expect(screen.getByText('Pressure Build')).toBeInTheDocument();
  expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '60.1');

  rerender(<LoadInstrument load={0.29999} prediction={null} recommendation={null} />);
  expect(screen.getByText('29.9%')).toBeInTheDocument();
  expect(screen.getByText('Gentle Glide')).toBeInTheDocument();
  expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '29.9');
});

test('keeps whole percents on the exact zone edges, in the band deriveStatus gives them', () => {
  const { rerender } = render(<LoadInstrument load={0.8} prediction={null} recommendation={null} />);
  expect(screen.getByText('80%')).toBeInTheDocument();
  expect(screen.getByText('Pressure Build')).toBeInTheDocument();
  expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '80');

  rerender(<LoadInstrument load={0.6} prediction={null} recommendation={null} />);
  expect(screen.getByText('60%')).toBeInTheDocument();
  expect(screen.getByText('Flow Ritual')).toBeInTheDocument();
  expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '60');

  rerender(<LoadInstrument load={0.3} prediction={null} recommendation={null} />);
  expect(screen.getByText('30%')).toBeInTheDocument();
  expect(screen.getByText('Flow Ritual')).toBeInTheDocument();
  expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '30');
});

test('draws the needle fully inside the band deriveStatus gives an exact zone edge', () => {
  const { rerender } = render(<LoadInstrument load={0.6} prediction={null} recommendation={null} />);
  expect(screen.getByTestId('load-needle')).toHaveStyle({ left: '60%', transform: 'translateX(-100%)' });

  rerender(<LoadInstrument load={0.8} prediction={null} recommendation={null} />);
  expect(screen.getByTestId('load-needle')).toHaveStyle({ left: '80%', transform: 'translateX(-100%)' });

  rerender(<LoadInstrument load={0.3} prediction={null} recommendation={null} />);
  expect(screen.getByTestId('load-needle')).toHaveStyle({ left: '30%', transform: 'translateX(0)' });

  rerender(<LoadInstrument load={0.45} prediction={null} recommendation={null} />);
  expect(screen.getByTestId('load-needle')).toHaveStyle({ left: '45%', transform: 'translateX(-50%)' });
});

test('draws the forecast marker fully inside the band deriveStatus gives an exact zone edge', () => {
  const { rerender } = render(<LoadInstrument load={0.5} prediction={0.6} recommendation={null} />);
  expect(screen.getByTestId('forecast-marker')).toHaveStyle({ left: '60%', transform: 'translateX(-100%)' });

  rerender(<LoadInstrument load={0.5} prediction={0.8} recommendation={null} />);
  expect(screen.getByTestId('forecast-marker')).toHaveStyle({ left: '80%', transform: 'translateX(-100%)' });

  rerender(<LoadInstrument load={0.5} prediction={0.3} recommendation={null} />);
  // 30 belongs to the upper zone and the marker's border already starts at the edge: unchanged.
  expect(screen.getByTestId('forecast-marker')).toHaveStyle({ left: '30%' });
  expect(screen.getByTestId('forecast-marker')).not.toHaveStyle({ transform: 'translateX(-100%)' });

  rerender(<LoadInstrument load={0.5} prediction={0.45} recommendation={null} />);
  expect(screen.getByTestId('forecast-marker')).toHaveStyle({ left: '45%' });
  expect(screen.getByTestId('forecast-marker')).not.toHaveStyle({ transform: 'translateX(-100%)' });
});

test('applies the same edge-safe rounding to the forecast and its delta', () => {
  render(<LoadInstrument load={0.62} prediction={0.8001} recommendation={null} />);

  expect(screen.getByTestId('forecast-value')).toHaveTextContent('80.1%');
  expect(screen.getByTestId('forecast-value')).toHaveTextContent('+18.1 pts');
  expect(screen.getByRole('meter').getAttribute('aria-valuetext')).toContain('forecast 80.1%');
});
