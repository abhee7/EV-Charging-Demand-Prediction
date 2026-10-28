/**
 * API client.
 *
 * The base URL comes from VITE_API_URL. Endpoint paths are fixed in
 * endpoints.ts: the frontend never constructs a filesystem path and never asks
 * the backend for an arbitrary file.
 */

const BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type QueryValue = string | number | boolean | null | undefined;

export function buildUrl(path: string, params?: Record<string, QueryValue>): string {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === null || value === undefined || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, QueryValue>,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(buildUrl(path, params), {
    signal,
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { reason?: string; detail?: unknown };
      if (body?.reason) detail = body.reason;
      else if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* response had no JSON body */
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const API_BASE = BASE;
