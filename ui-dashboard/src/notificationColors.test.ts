import { expect, test } from 'vitest';

import { getNotificationColor } from './notificationColors';
import { brandTokens } from './theme';

test('maps backend notification types to intended severity colors', () => {
  expect(getNotificationColor('decision')).toBe(brandTokens.colors.serumMint);
  expect(getNotificationColor('progress')).toBe(brandTokens.colors.serumMint);
  expect(getNotificationColor('break')).toBe(brandTokens.colors.serumMint);
  expect(getNotificationColor('session')).toBe(brandTokens.colors.serumMint);
  expect(getNotificationColor('info')).toBe(brandTokens.colors.serumMint);
  expect(getNotificationColor('hyperfocus')).toBe(brandTokens.colors.saintGold);
  expect(getNotificationColor('warning')).toBe(brandTokens.colors.saintGold);
  expect(getNotificationColor('error')).toBe(brandTokens.colors.gremlinPink);
  expect(getNotificationColor('unknown')).toBe(brandTokens.colors.ritualCyan);
});
