import { afterAll, beforeAll, expect, test } from 'vitest';

import { asUtcIso, formatClockTime } from './time';

// October 30 2026 is PDT (UTC-7). Node re-reads TZ when it is assigned, so setting it here
// pins this file's local-time assertions; restoring it keeps the zone out of other suites
// that share the worker.
const originalTz = process.env.TZ;

beforeAll(() => {
  process.env.TZ = 'America/Los_Angeles';
});

afterAll(() => {
  if (originalTz === undefined) {
    delete process.env.TZ;
  } else {
    process.env.TZ = originalTz;
  }
});

test('TZ applies to Dates built after it is set', () => {
  expect(new Date('2026-10-30T14:01:55Z').getHours()).toBe(7);
});

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
