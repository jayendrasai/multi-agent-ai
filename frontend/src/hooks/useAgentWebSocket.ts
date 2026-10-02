import { useEffect, useRef, useState } from 'react';
import { config } from '@/lib/config';
import { useEventStore } from '@/store';
import { useAuthStore } from '@/store/auth';

export const useAgentWebSocket = (taskId: string | null) => {
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const { addEvent } = useEventStore();
  const { user, isLoading: isAuthLoading } = useAuthStore();

  useEffect(() => {
    if (!taskId || isAuthLoading || !user) return;

    let stopped = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      if (stopped) return;
      const wsUrl = `${config.wsBaseUrl}/ws/tasks/${taskId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setReconnectAttempt(0);
        // Start ping interval to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
        
        ws.addEventListener('close', () => clearInterval(pingInterval), { once: true });
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong' || event.data === 'ping') return;
        try {
          const data = JSON.parse(event.data);
          addEvent(taskId, data);
        } catch (err) {
          console.error("Failed to parse websocket message", err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (stopped) return;
        setReconnectAttempt((attempt) => {
          const nextAttempt = attempt + 1;
          if (nextAttempt <= config.wsReconnectMaxAttempts) {
            const delay = Math.min(1000 * 2 ** Math.min(nextAttempt, 5), 15000);
            reconnectTimer = setTimeout(connect, delay);
          }
          return nextAttempt;
        });
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [taskId, addEvent, isAuthLoading, user]);

  return { isConnected, reconnectAttempt };
};
