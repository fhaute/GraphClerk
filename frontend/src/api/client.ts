/**
 * Typed HTTP client for the GraphClerk API.
 * Base URL: `VITE_API_BASE_URL`, else `http://localhost:8000` (typical uvicorn/Docker).
 * If port 8000 is already taken on your machine, run the API on another port and set
 * `VITE_API_BASE_URL` (see `frontend/.env.example`).
 */

const DEFAULT_BASE = "http://localhost:8000";

export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL?.trim();
  return raw && raw.length > 0 ? raw.replace(/\/$/, "") : DEFAULT_BASE;
}

export class ApiError extends Error {
  readonly status: number;
  readonly responseBody?: string;

  constructor(message: string, status: number, responseBody?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.responseBody = responseBody;
  }
}

export async function apiGetJson<T>(path: string): Promise<T> {
  const base = getApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${base}${normalizedPath}`;

  let res: Response;
  try {
    res = await fetch(url);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new ApiError(`Network error calling ${url}: ${msg}`, 0);
  }

  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(
      `HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ""}`,
      res.status,
      text || undefined,
    );
  }

  return res.json() as Promise<T>;
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const base = getApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${base}${normalizedPath}`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new ApiError(`Network error calling ${url}: ${msg}`, 0);
  }

  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(
      `HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ""}`,
      res.status,
      text || undefined,
    );
  }

  return res.json() as Promise<T>;
}
