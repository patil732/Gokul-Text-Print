/**
 * frontend/lib/api/client.ts
 * --------------------------
 * Base typed fetch wrapper for the Gokul Text Print Flask API.
 *
 * All API modules in this directory build on top of `apiFetch<T>()`.
 * The backend base URL is supplied via `NEXT_PUBLIC_API_BASE_URL`
 * (defaults to http://localhost:5001 for local development).
 */

/** Resolved from the Next.js public env variable — set in .env.local */
export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5001";

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly body: unknown,
    message?: string,
  ) {
    super(message ?? `API error ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface FetchOptions {
  method?: HttpMethod;
  /** JSON-serialisable request body (POST / PUT / PATCH) */
  body?: unknown;
  /** Extra headers merged into the default set */
  headers?: Record<string, string>;
  /** URL query-string params appended to the path */
  params?: Record<string, string | number | boolean | undefined | null>;
  /** Passed straight through to native `fetch` */
  cache?: RequestCache;
  /** Next.js extended fetch options */
  next?: NextFetchRequestConfig;
}

/**
 * Generic fetch wrapper.
 *
 * @example
 * const data = await apiFetch<KpiResponse>("/api/dashboard/kpis");
 */
export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    headers: extraHeaders = {},
    params,
    cache,
    next,
  } = options;

  // Build URL
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...extraHeaders,
  };

  const init: RequestInit = {
    method,
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    ...(cache !== undefined ? { cache } : {}),
    ...(next !== undefined ? { next } : {}),
    credentials: "include", // Required for flask-cors supports_credentials
  };

  const response = await fetch(url.toString(), init);

  if (!response.ok) {
    let errorBody: unknown;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = await response.text();
    }
    throw new ApiError(response.status, response.statusText, errorBody);
  }

  // Handle responses with no body (e.g. 204 No Content)
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Convenience helpers
// ---------------------------------------------------------------------------

export const apiGet = <T>(path: string, options?: Omit<FetchOptions, "method" | "body">) =>
  apiFetch<T>(path, { ...options, method: "GET" });

export const apiPost = <T>(path: string, body: unknown, options?: Omit<FetchOptions, "method" | "body">) =>
  apiFetch<T>(path, { ...options, method: "POST", body });
