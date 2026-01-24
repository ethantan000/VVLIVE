import { useState, useEffect, useCallback, useRef } from 'react';

export function useApi(endpoint, options = {}) {
  const {
    interval = null,
    enabled = true,
    initialData = null,
    onSuccess,
    onError
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    setLoading(true);
    try {
      const response = await fetch(`/api${endpoint}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const result = await response.json();

      if (mountedRef.current) {
        setData(result);
        setError(null);
        onSuccess?.(result);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        onError?.(err);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [endpoint, enabled, onSuccess, onError]);

  const refetch = useCallback(() => {
    return fetchData();
  }, [fetchData]);

  useEffect(() => {
    mountedRef.current = true;

    if (enabled) {
      fetchData();

      if (interval) {
        intervalRef.current = setInterval(fetchData, interval);
      }
    }

    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, interval, fetchData]);

  return { data, loading, error, refetch };
}

export function useApiPost(endpoint) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const post = useCallback(async (body) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  return { post, loading, error };
}

export default useApi;
