const DEFAULT_DASHBOARD_API_URL = 'http://localhost:8097';

function deriveWebSocketUrl(httpUrl: string): string {
  if (httpUrl.startsWith('https://')) {
    return `wss://${httpUrl.slice('https://'.length)}`;
  }
  if (httpUrl.startsWith('http://')) {
    return `ws://${httpUrl.slice('http://'.length)}`;
  }
  return `ws://${httpUrl}`;
}

export const dashboardApiUrl =
  import.meta.env.VITE_DASHBOARD_API_URL || DEFAULT_DASHBOARD_API_URL;

export const dashboardWsUrl =
  import.meta.env.VITE_DASHBOARD_WS_URL || deriveWebSocketUrl(dashboardApiUrl);

export const dashboardApiHeaders: HeadersInit = import.meta.env.VITE_DASHBOARD_API_KEY
  ? { 'X-API-Key': import.meta.env.VITE_DASHBOARD_API_KEY }
  : {};
