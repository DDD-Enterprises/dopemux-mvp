/** 24-hour `hh:mm:ss` for operator-facing timestamps; `--:--:--` when the input is not a date. */
export const formatClockTime = (value: string | Date) => {
  const date = typeof value === 'string' ? new Date(value) : value;
  if (isNaN(date.getTime())) return '--:--:--';
  return [date.getHours(), date.getMinutes(), date.getSeconds()]
    .map((part) => part.toString().padStart(2, '0'))
    .join(':');
};
