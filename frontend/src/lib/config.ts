export const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  wsBaseUrl: process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000',
  wsReconnectMaxAttempts: Number(process.env.NEXT_PUBLIC_WS_RECONNECT_MAX_ATTEMPTS || '10'),
  enableObservability: process.env.NEXT_PUBLIC_ENABLE_OBSERVABILITY === 'true',
};
