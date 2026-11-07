// A date-time with no `Z` or offset. The backend emits `datetime.utcnow().isoformat()`,
// which looks like this: UTC, but JS would parse it as local time.
const ZONELESS_DATE_TIME = /^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::(\d{2})(?:\.(\d+))?)?$/;

/**
 * Normalizes a zone-less ISO date-time to explicit UTC (`...Z`) with at most 3 fractional
 * digits (Safari rejects more). Strings that carry a zone, or are not date-times, pass through.
 */
export const asUtcIso = (value: string): string => {
  const match = ZONELESS_DATE_TIME.exec(value);
  if (!match) return value;
  const [, day, minutes, seconds = '00', fraction] = match;
  return `${day}T${minutes}:${seconds}${fraction ? `.${fraction.slice(0, 3)}` : ''}Z`;
};

/** 24-hour `hh:mm:ss` for operator-facing timestamps; `--:--:--` when the input is not a date. */
export const formatClockTime = (value: string | Date) => {
  const date = typeof value === 'string' ? new Date(asUtcIso(value)) : value;
  if (isNaN(date.getTime())) return '--:--:--';
  return [date.getHours(), date.getMinutes(), date.getSeconds()]
    .map((part) => part.toString().padStart(2, '0'))
    .join(':');
};
