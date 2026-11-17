import { errorMessage } from "./errors";

const BASE = "/api"; // proxied to the FastAPI backend by next.config.mjs

export type ApiResult<T> = {
  ok: boolean;
  status: number;
  data: T | null;
  error: string | null;
};

type Options = { method?: string; body?: unknown; csrf?: string };

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {};
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  if (opts.csrf) headers["X-CSRF-Token"] = opts.csrf;
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: opts.method ?? "GET",
      credentials: "include",
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
    let data: unknown = null;
    if (res.status !== 204) {
      try {
        data = await res.json();
      } catch {
        data = null;
      }
    }
    return {
      ok: res.ok,
      status: res.status,
      data: res.ok ? (data as T) : null,
      error: res.ok ? null : errorMessage(data, res.status),
    };
  } catch {
    return {
      ok: false,
      status: 0,
      data: null,
      error: "We could not reach the server. Check your connection and try again.",
    };
  }
}
