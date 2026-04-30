/**
 * Typed HTTP client for the GraphClerk API.
 * Base URL: `VITE_API_BASE_URL`, else `http://localhost:8010` (Docker Compose host port for the API).
 * For local `uvicorn` on another port, set `VITE_API_BASE_URL` (see `frontend/.env.example`).
 */

const DEFAULT_BASE = "http://localhost:8010";

const NETWORK_HINT =
  " If the API is running, check browser vs API origin (CORS allowlist GRAPHCLERK_CORS_ORIGINS or loopback regex), VITE_API_BASE_URL, and mixed HTTP/HTTPS.";

export function getApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL?.trim();
  return raw && raw.length > 0 ? raw.replace(/\/$/, "") : DEFAULT_BASE;
}

/** Pull FastAPI-style `detail` from JSON body when present. */
function parseBackendDetail(text: string): string | null {
  const trimmed = text.trim();
  if (!trimmed.startsWith("{")) return null;
  try {
    const j = JSON.parse(trimmed) as { detail?: unknown };
    if (j.detail === undefined || j.detail === null) return null;
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) {
      return j.detail
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            const msg = (item as { msg?: unknown }).msg;
            return typeof msg === "string" ? msg : JSON.stringify(item);
          }
          return JSON.stringify(item);
        })
        .join("; ");
    }
    return JSON.stringify(j.detail);
  } catch {
    return null;
  }
}

function httpErrorMessage(status: number, statusText: string, bodyText: string): string {
  const detail = parseBackendDetail(bodyText);
  const head = `HTTP ${status}${statusText ? ` ${statusText}` : ""}`;
  if (detail) return `${head} — ${detail}`;
  if (bodyText.trim()) return `${head} — ${bodyText.trim()}`;
  return head;
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
    throw new ApiError(
      `Network error (HTTP status unavailable) calling ${url}: ${msg}.${NETWORK_HINT}`,
      0,
    );
  }

  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(httpErrorMessage(res.status, res.statusText, text), res.status, text || undefined);
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
    throw new ApiError(
      `Network error (HTTP status unavailable) calling ${url}: ${msg}.${NETWORK_HINT}`,
      0,
    );
  }

  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(httpErrorMessage(res.status, res.statusText, text), res.status, text || undefined);
  }

  return res.json() as Promise<T>;
}
