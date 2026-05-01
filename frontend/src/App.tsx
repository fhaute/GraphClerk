import { useEffect, useState } from "react";
import { ApiError, getApiBaseUrl } from "./api/client";
import { fetchHealth } from "./api/health";
import { fetchVersion } from "./api/version";
import { ArtifactsExplorer } from "./components/ArtifactsExplorer";
import { QueryPlayground } from "./components/QueryPlayground";
import { EvaluationDashboard } from "./components/EvaluationDashboard";
import { GraphExplorer } from "./components/GraphExplorer";
import { RetrievalLogsExplorer } from "./components/RetrievalLogsExplorer";
import { SemanticIndexesExplorer } from "./components/SemanticIndexesExplorer";
import type { HealthResponse } from "./types/health";
import type { VersionResponse } from "./types/version";

type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

type MainTab = "playground" | "artifacts" | "semantic" | "graph" | "logs" | "eval";

export default function App() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [tab, setTab] = useState<MainTab>("playground");
  const [backendVersion, setBackendVersion] = useState<VersionResponse | null>(null);

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
            message: e.message,
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

  useEffect(() => {
    let cancelled = false;
    fetchVersion()
      .then((v) => {
        if (!cancelled) setBackendVersion(v);
      })
      .catch(() => {
        if (!cancelled) setBackendVersion(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-semibold text-neutral-900">GraphClerk</h1>
      <p className="mt-2 text-sm text-neutral-600">
        Phase 6 UI — live backend contracts only (no mock data).
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
        className="mt-8 flex flex-wrap gap-2 border-b border-neutral-200"
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
        <button
          type="button"
          onClick={() => setTab("semantic")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "semantic"
              ? "border-neutral-900 text-neutral-900"
              : "border-transparent text-neutral-600 hover:text-neutral-900"
          }`}
        >
          Semantic indexes
        </button>
        <button
          type="button"
          onClick={() => setTab("graph")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "graph"
              ? "border-neutral-900 text-neutral-900"
              : "border-transparent text-neutral-600 hover:text-neutral-900"
          }`}
        >
          Graph explorer
        </button>
        <button
          type="button"
          onClick={() => setTab("logs")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "logs"
              ? "border-neutral-900 text-neutral-900"
              : "border-transparent text-neutral-600 hover:text-neutral-900"
          }`}
        >
          Retrieval logs
        </button>
        <button
          type="button"
          onClick={() => setTab("eval")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "eval"
              ? "border-neutral-900 text-neutral-900"
              : "border-transparent text-neutral-600 hover:text-neutral-900"
          }`}
        >
          Evaluation
        </button>
      </nav>

      <div className="mt-6">
        {tab === "playground" && <QueryPlayground />}
        {tab === "artifacts" && <ArtifactsExplorer />}
        {tab === "semantic" && <SemanticIndexesExplorer />}
        {tab === "graph" && <GraphExplorer />}
        {tab === "logs" && <RetrievalLogsExplorer />}
        {tab === "eval" && <EvaluationDashboard />}
      </div>

      {backendVersion ? (
        <p
          className="mt-12 border-t border-neutral-100 pt-4 text-xs text-neutral-500"
          aria-live="polite"
        >
          Backend{" "}
          <span className="font-mono">
            {backendVersion.name} {backendVersion.version}
          </span>{" "}
          · <span className="font-mono">{backendVersion.phase}</span>
        </p>
      ) : null}
    </div>
  );
}
