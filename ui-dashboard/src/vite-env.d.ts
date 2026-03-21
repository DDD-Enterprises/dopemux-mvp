/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DASHBOARD_API_URL?: string;
  readonly VITE_DASHBOARD_WS_URL?: string;
  readonly VITE_DASHBOARD_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
