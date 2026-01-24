import { useState, useEffect, useRef, useCallback } from 'react';

const RECONNECT_DELAY = 3000;
const PING_INTERVAL = 30000;

export function useWebSocket(url, options = {}) {
  const { onMessage, onConnect, onDisconnect, enabled = true } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = url.startsWith('ws') ? url : `${protocol}//${window.location.host}${url}`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        setError(null);
        onConnect?.();

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, PING_INTERVAL);
      };

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type !== 'pong') {
            setLastMessage(data);
            onMessage?.(data);
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };

      wsRef.current.onclose = () => {
        if (!mountedRef.current) return;
        setIsConnected(false);
        onDisconnect?.();
        clearInterval(pingIntervalRef.current);

        // Auto-reconnect
        reconnectTimeoutRef.current = setTimeout(connect, RECONNECT_DELAY);
      };

      wsRef.current.onerror = (err) => {
        if (!mountedRef.current) return;
        setError('WebSocket connection error');
        console.error('WebSocket error:', err);
      };
    } catch (err) {
      setError(err.message);
    }
  }, [url, enabled, onMessage, onConnect, onDisconnect]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(pingIntervalRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    error,
    send,
    disconnect,
    reconnect: connect
  };
}

export default useWebSocket;
