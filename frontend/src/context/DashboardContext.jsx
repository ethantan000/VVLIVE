import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useApi } from '../hooks/useApi';

const DashboardContext = createContext(null);

// Polling intervals (ms)
const HEALTH_POLL_INTERVAL = 5000;
const STATUS_POLL_INTERVAL = 2000;
const METRICS_POLL_INTERVAL = 2000;
const INGEST_POLL_INTERVAL = 1000;
const OBS_POLL_INTERVAL = 2000;
const AGGREGATED_POLL_INTERVAL = 3000;
const SCREENSHOT_POLL_INTERVAL = 5000;

export function DashboardProvider({ children }) {
  // Feature flags from /health
  const [features, setFeatures] = useState({
    obs_enabled: false,
    ingest_enabled: false,
    srt_bonding: false,
    health_score: false,
    dual_metrics: false
  });

  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // API data states
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [ingestStats, setIngestStats] = useState(null);
  const [obsStatus, setObsStatus] = useState(null);
  const [aggregated, setAggregated] = useState(null);
  const [screenshot, setScreenshot] = useState(null);

  // Error tracking
  const [errors, setErrors] = useState({});

  // Health check - get feature flags
  const { data: healthData, error: healthError } = useApi('/health', {
    interval: HEALTH_POLL_INTERVAL,
    enabled: true,
    onSuccess: (data) => {
      setIsConnected(true);
      setFeatures({
        obs_enabled: data.features?.obs_enabled ?? false,
        ingest_enabled: data.features?.ingest_enabled ?? false,
        srt_bonding: data.features?.srtla_transport ?? false,
        health_score: data.features?.health_score ?? false,
        dual_metrics: data.features?.dual_metrics ?? false
      });
    },
    onError: () => {
      setIsConnected(false);
    }
  });

  // Status polling
  const { data: statusData } = useApi('/status', {
    interval: STATUS_POLL_INTERVAL,
    enabled: isConnected,
    onSuccess: setStatus,
    onError: (err) => setErrors(prev => ({ ...prev, status: err.message }))
  });

  // Metrics polling
  const { data: metricsData } = useApi('/metrics', {
    interval: METRICS_POLL_INTERVAL,
    enabled: isConnected,
    onSuccess: setMetrics,
    onError: (err) => setErrors(prev => ({ ...prev, metrics: err.message }))
  });

  // Ingest stats polling (only if ingest enabled)
  const { data: ingestData } = useApi('/ingest/stats', {
    interval: INGEST_POLL_INTERVAL,
    enabled: isConnected && features.ingest_enabled,
    onSuccess: setIngestStats,
    onError: (err) => setErrors(prev => ({ ...prev, ingest: err.message }))
  });

  // OBS status polling (only if OBS enabled)
  const { data: obsData } = useApi('/obs/status', {
    interval: OBS_POLL_INTERVAL,
    enabled: isConnected && features.obs_enabled,
    onSuccess: setObsStatus,
    onError: (err) => setErrors(prev => ({ ...prev, obs: err.message }))
  });

  // Aggregated metrics polling
  const { data: aggregatedData } = useApi('/metrics/aggregated', {
    interval: AGGREGATED_POLL_INTERVAL,
    enabled: isConnected && features.dual_metrics,
    onSuccess: setAggregated,
    onError: (err) => setErrors(prev => ({ ...prev, aggregated: err.message }))
  });

  // Screenshot polling (only if OBS connected)
  const { data: screenshotData } = useApi('/obs/screenshot', {
    interval: SCREENSHOT_POLL_INTERVAL,
    enabled: isConnected && features.obs_enabled && obsStatus?.connected,
    onSuccess: (data) => {
      if (data.success && data.image_data) {
        setScreenshot(data.image_data);
      }
    },
    onError: () => {} // Silently fail screenshot errors
  });

  // WebSocket for real-time updates
  const handleWsMessage = useCallback((data) => {
    switch (data.type) {
      case 'status':
        setStatus(data.payload);
        break;
      case 'metrics':
        setMetrics(data.payload);
        break;
      case 'ingest':
        setIngestStats(data.payload);
        break;
      case 'obs':
        setObsStatus(data.payload);
        break;
      case 'aggregated':
        setAggregated(data.payload);
        break;
      default:
        console.log('Unknown WS message type:', data.type);
    }
  }, []);

  const { isConnected: wsIsConnected } = useWebSocket('/api/ws', {
    enabled: isConnected,
    onMessage: handleWsMessage,
    onConnect: () => setWsConnected(true),
    onDisconnect: () => setWsConnected(false)
  });

  // Update wsConnected state
  useEffect(() => {
    setWsConnected(wsIsConnected);
  }, [wsIsConnected]);

  // Actions
  const switchScene = useCallback(async (sceneName) => {
    try {
      const response = await fetch(`/api/obs/scene?scene_name=${encodeURIComponent(sceneName)}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        setObsStatus(prev => prev ? { ...prev, current_scene: sceneName } : prev);
      }
      return data;
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const startStreaming = useCallback(async () => {
    try {
      const response = await fetch('/api/obs/stream/start', { method: 'POST' });
      return await response.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const stopStreaming = useCallback(async () => {
    try {
      const response = await fetch('/api/obs/stream/stop', { method: 'POST' });
      return await response.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const value = {
    // Connection state
    isConnected,
    wsConnected,

    // Feature flags
    features,

    // Data
    status,
    metrics,
    ingestStats,
    obsStatus,
    aggregated,
    screenshot,

    // Errors
    errors,

    // Actions
    switchScene,
    startStreaming,
    stopStreaming
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
}

export default DashboardContext;
