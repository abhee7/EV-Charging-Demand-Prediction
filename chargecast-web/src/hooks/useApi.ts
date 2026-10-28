import { useCallback, useEffect, useRef, useState } from "react";

import { apiGet, type QueryValue } from "@/api/client";

interface State<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

/**
 * Fetch one endpoint.
 *
 * Responses are cached per (path, params) for the session, so navigating
 * between pages does not re-request artefacts that have not changed.
 */
const cache = new Map<string, unknown>();

function keyOf(path: string, params?: Record<string, QueryValue>): string {
  return params ? `${path}?${JSON.stringify(params)}` : path;
}

export function useApi<T>(
  path: string | null,
  params?: Record<string, QueryValue>,
  options: { skip?: boolean } = {},
): State<T> & { refetch: () => void } {
  const [state, setState] = useState<State<T>>({
    data: null,
    error: null,
    loading: !options.skip && !!path,
  });
  const nonce = useRef(0);
  const serialised = params ? JSON.stringify(params) : "";

  const run = useCallback(() => {
    if (!path || options.skip) {
      setState({ data: null, error: null, loading: false });
      return () => undefined;
    }

    const parsed = serialised ? (JSON.parse(serialised) as Record<string, QueryValue>) : undefined;
    const cacheKey = keyOf(path, parsed);
    const hit = cache.get(cacheKey);
    if (hit !== undefined) {
      setState({ data: hit as T, error: null, loading: false });
      return () => undefined;
    }

    const controller = new AbortController();
    const current = ++nonce.current;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    apiGet<T>(path, parsed, controller.signal)
      .then((data) => {
        if (current !== nonce.current) return;
        cache.set(cacheKey, data);
        setState({ data, error: null, loading: false });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || current !== nonce.current) return;
        const message = error instanceof Error ? error.message : "Request failed";
        setState({ data: null, error: message, loading: false });
      });

    return () => controller.abort();
  }, [path, serialised, options.skip]);

  useEffect(() => run(), [run]);

  const refetch = useCallback(() => {
    if (!path) return;
    const parsed = serialised ? (JSON.parse(serialised) as Record<string, QueryValue>) : undefined;
    cache.delete(keyOf(path, parsed));
    run();
  }, [path, serialised, run]);

  return { ...state, refetch };
}

export function clearApiCache() {
  cache.clear();
}
