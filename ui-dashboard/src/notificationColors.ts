import { brandTokens } from './theme';

export type NotificationType =
  | 'decision'
  | 'progress'
  | 'break'
  | 'session'
  | 'info'
  | 'hyperfocus'
  | 'warning'
  | 'error';

export const getNotificationColor = (type: NotificationType | string) => {
  switch (type) {
    case 'decision':
    case 'progress':
    case 'break':
    case 'session':
    case 'info':
      return brandTokens.colors.serumMint;
    case 'hyperfocus':
    case 'warning':
      return brandTokens.colors.saintGold;
    case 'error':
      return brandTokens.colors.gremlinPink;
    default:
      return brandTokens.colors.ritualCyan;
  }
};
