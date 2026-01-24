import { useState, useCallback, useRef, useEffect } from 'react';

const MAX_SAMPLES = 60; // 60 seconds of history

export function useBitrateHistory(currentBitrate) {
  const [history, setHistory] = useState(() => {
    // Initialize with empty data points
    return Array(MAX_SAMPLES).fill(null).map((_, i) => ({
      time: Date.now() - (MAX_SAMPLES - i) * 1000,
      bitrate: 0
    }));
  });

  const lastUpdateRef = useRef(Date.now());

  const addSample = useCallback((bitrate) => {
    const now = Date.now();
    setHistory(prev => {
      const newHistory = [...prev.slice(1), {
        time: now,
        bitrate: bitrate || 0
      }];
      return newHistory;
    });
    lastUpdateRef.current = now;
  }, []);

  // Auto-update when currentBitrate changes
  useEffect(() => {
    if (currentBitrate !== undefined) {
      const interval = setInterval(() => {
        addSample(currentBitrate);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [currentBitrate, addSample]);

  const getStats = useCallback(() => {
    const validSamples = history.filter(h => h.bitrate > 0);
    if (validSamples.length === 0) {
      return { avg: 0, min: 0, max: 0, current: 0 };
    }

    const bitrates = validSamples.map(h => h.bitrate);
    return {
      avg: Math.round(bitrates.reduce((a, b) => a + b, 0) / bitrates.length),
      min: Math.min(...bitrates),
      max: Math.max(...bitrates),
      current: bitrates[bitrates.length - 1] || 0
    };
  }, [history]);

  const clear = useCallback(() => {
    setHistory(Array(MAX_SAMPLES).fill(null).map((_, i) => ({
      time: Date.now() - (MAX_SAMPLES - i) * 1000,
      bitrate: 0
    })));
  }, []);

  return {
    history,
    addSample,
    getStats,
    clear
  };
}

export default useBitrateHistory;
