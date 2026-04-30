import { useEffect, useState } from "react";
import { ApiError, getApiBaseUrl } from "./api/client";
import { fetchHealth } from "./api/health";
import { ArtifactsExplorer } from "./components/ArtifactsExplorer";
import { QueryPlayground } from "./components/QueryPlayground";
import type { HealthResponse } from "./types/health";

type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

type MainTab = "playground" | "artifacts";

export default function App() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [tab, setTab] = useState<MainTab>("playground");

  useEffect(() => {
    let cancelled = false;
    setState({ kind: "loading" });
    fetchHealth()
      .then((data) => {
        if (!cancelled) setState({ kind: "ok", data });
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        if (e instanceof ApiError) {
          setState({
            kind: "error",
            message: `${e.message} (status ${e.status})`,
          });
        } else if (e instanceof Error) {
          setState({ kind: "error", message: e.message });
        } else {
          setState({ kind: "error", message: String(e) });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-semibold text-neutral-900">GraphClerk</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Phase 6 UI — live backend contracts only (no mock artifacts or evidence).
      </p>

      <section className="mt-8 rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Backend health</h2>
        <p className="mt-1 text-xs text-neutral-500 break-all">
          API base: <code>{getApiBaseUrl()}</code>
        </p>
        <div className="mt-3 text-sm">
          {state.kind === "loading" && (
            <p className="text-neutral-600">Loading…</p>
          )}
          {state.kind === "ok" && (
            <p className="text-green-700">
              Status: <code className="font-mono">{state.data.status}</code>
            </p>
          )}
          {state.kind === "error" && (
            <p className="text-red-700 whitespace-pre-wrap">{state.message}</p>
          )}
        </div>
      </section>

      <nav
        className="mt-8 flex gap-2 border-b border-neutral-200"
        aria-label="Main sections"
      >
        <button
          type="button"
          onClick={() => setTab("playground")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "playground"
              ? "border-neutral-900 text-neutral-900"
              : "border-transparent text-neutral-600 hover:text-neutral-900"
          }`}
        >
          Query playground
        </button>
        <button
          type="button"
          onClick={() => setTab("artifacts")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "artifacts"
              ? "border-neutral-900 text-neutral-900"
              : "border-transparent text-neutral-600 hover:text-neutral-900"
          }`}
        >
          Artifacts &amp; evidence
        </button>
      </nav>

      <div className="mt-6">
        {tab === "playground" && <QueryPlayground />}
        {tab === "artifacts" && <ArtifactsExplorer />}
      </div>
    </div>
  );
}
