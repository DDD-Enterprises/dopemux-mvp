import { expect, test } from 'vitest';

import { asUtcIso, formatClockTime } from './time';

// Must run before the first Date is built; October 30 2026 is PDT (UTC-7).
process.env.TZ = 'America/Los_Angeles';

test('asUtcIso marks a zone-less date-time as UTC and truncates the fraction to milliseconds', () => {
  expect(asUtcIso('2026-10-30T14:01:55.123456')).toBe('2026-10-30T14:01:55.123Z');
  expect(asUtcIso('2026-10-30T14:01:55.5')).toBe('2026-10-30T14:01:55.5Z');
  expect(asUtcIso('2026-10-30T14:01:55')).toBe('2026-10-30T14:01:55Z');
  expect(asUtcIso('2026-10-30T14:01')).toBe('2026-10-30T14:01:00Z');
  expect(asUtcIso('2026-10-30 14:01:55.123456')).toBe('2026-10-30T14:01:55.123Z');
});

test('asUtcIso leaves zoned and non-date-time strings unchanged', () => {
  expect(asUtcIso('2026-10-30T14:01:55Z')).toBe('2026-10-30T14:01:55Z');
  expect(asUtcIso('2026-10-30T14:01:55.123456Z')).toBe('2026-10-30T14:01:55.123456Z');
  expect(asUtcIso('2026-10-30T14:01:55+02:00')).toBe('2026-10-30T14:01:55+02:00');
  expect(asUtcIso('2026-10-30T14:01:55-07:00')).toBe('2026-10-30T14:01:55-07:00');
  expect(asUtcIso('2026-10-30')).toBe('2026-10-30');
  expect(asUtcIso('garbage')).toBe('garbage');
  expect(asUtcIso('')).toBe('');
});

test('formatClockTime reads a zone-less backend timestamp as UTC', () => {
  expect(formatClockTime('2026-10-30T14:01:55.123456')).toBe(formatClockTime(new Date('2026-10-30T14:01:55Z')));
});

test('formatClockTime shows UTC signals in local time', () => {
  expect(formatClockTime('2026-10-30T14:01:55')).toBe('07:01:55');
  expect(formatClockTime('2026-10-30T14:01:55+02:00')).toBe('05:01:55');
});
