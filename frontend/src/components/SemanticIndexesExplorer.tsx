import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import {
  fetchSemanticIndex,
  fetchSemanticIndexEntryPoints,
  fetchSemanticIndexes,
  searchSemanticIndexes,
} from "../api/semanticIndexes";
import type {
  SemanticIndexResponse,
  SemanticIndexSearchResult,
} from "../types/semanticIndex";

function formatError(err: unknown): string {
  if (err instanceof ApiError) return `${err.message} (status ${err.status})`;
  if (err instanceof Error) return err.message;
  return String(err);
}

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function VectorStatusBadge({ status }: { status: string }) {
  const cls =
    status === "indexed"
      ? "bg-green-100 text-green-900"
      : status === "pending"
        ? "bg-amber-100 text-amber-900"
        : status === "failed"
          ? "bg-red-100 text-red-900"
          : "bg-neutral-100 text-neutral-800";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>
  );
}

export function SemanticIndexesExplorer() {
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [listUnavailable, setListUnavailable] = useState(false);
  const [indexes, setIndexes] = useState<SemanticIndexResponse[]>([]);

  const [manualId, setManualId] = useState("");
  const [manualLoading, setManualLoading] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detail, setDetail] = useState<SemanticIndexResponse | null>(null);

  const [epLoading, setEpLoading] = useState(false);
  const [epError, setEpError] = useState<string | null>(null);
  const [entryPointIds, setEntryPointIds] = useState<string[] | null>(null);

  const [searchQ, setSearchQ] = useState("");
  const [searchLimit, setSearchLimit] = useState(10);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SemanticIndexSearchResult[] | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;
    setListLoading(true);
    setListError(null);
    setListUnavailable(false);
    fetchSemanticIndexes({ limit: 500 })
      .then((res) => {
        if (!cancelled) setIndexes(res.items ?? []);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 404) {
          setListUnavailable(true);
          setIndexes([]);
          setListError(null);
        } else {
          setListError(formatError(e));
          setIndexes([]);
        }
      })
      .finally(() => {
        if (!cancelled) setListLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadSelected = useCallback(async (semanticIndexId: string) => {
    setSelectedId(semanticIndexId);
    setDetailError(null);
    setEpError(null);
    setDetailLoading(true);
    setEpLoading(true);
    setDetail(null);
    setEntryPointIds(null);
    try {
      const [d, ep] = await Promise.all([
        fetchSemanticIndex(semanticIndexId),
        fetchSemanticIndexEntryPoints(semanticIndexId),
      ]);
      setDetail(d);
      setEntryPointIds(ep.entry_node_ids);
    } catch (e) {
      const msg = formatError(e);
      setDetailError(msg);
      setEpError(msg);
    } finally {
      setDetailLoading(false);
      setEpLoading(false);
    }
  }, []);

  const openByManualId = useCallback(async () => {
    const id = manualId.trim();
    if (!id) {
      setManualError("Enter a semantic index UUID.");
      return;
    }
    setManualLoading(true);
    setManualError(null);
    try {
      await loadSelected(id);
    } finally {
      setManualLoading(false);
    }
  }, [manualId, loadSelected]);

  const runSearch = useCallback(async () => {
    const q = searchQ.trim();
    if (!q) {
      setSearchError("Enter a non-empty search query.");
      setSearchResults(null);
      return;
    }
    setSearchLoading(true);
    setSearchError(null);
    setSearchResults(null);
    try {
      const res = await searchSemanticIndexes(q, searchLimit);
      setSearchResults(res.results);
    } catch (e) {
      setSearchError(formatError(e));
    } finally {
      setSearchLoading(false);
    }
  }, [searchQ, searchLimit]);

  return (
    <section className="space-y-6">
      <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Semantic search</h2>
        <p className="mt-2 text-xs text-neutral-600">
          <code className="font-mono">GET /semantic-indexes/search</code> ranks semantic indexes
          using the configured embedding + vector backend. Only rows with{" "}
          <strong className="font-medium text-neutral-800">vector_status=indexed</strong> can appear
          in results — pending or failed indexes are excluded by the backend (they are not
          searchable).
        </p>
        <p className="mt-2 text-xs text-neutral-600">
          If the vector backend or embedding adapter is unavailable, the API may return{" "}
          <strong className="font-medium">503</strong> or other errors; those responses are shown
          below without fabrication.
        </p>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="flex min-w-[12rem] flex-1 flex-col text-xs text-neutral-600">
            Query <span className="font-normal text-neutral-500">(q)</span>
            <input
              type="text"
              className="mt-1 rounded border border-neutral-300 px-3 py-2 text-sm text-neutral-900 shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              placeholder="Natural language to compare against embedding_text…"
              disabled={searchLoading}
            />
          </label>
          <label className="flex flex-col text-xs text-neutral-600">
            limit (1–50)
            <input
              type="number"
              min={1}
              max={50}
              className="mt-1 w-24 rounded border border-neutral-300 px-3 py-2 text-sm shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
              value={searchLimit}
              onChange={(e) => {
                const n = Number.parseInt(e.target.value, 10);
                if (Number.isNaN(n)) return;
                setSearchLimit(Math.min(50, Math.max(1, n)));
              }}
              disabled={searchLoading}
            />
          </label>
          <button
            type="button"
            className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
            onClick={() => void runSearch()}
            disabled={searchLoading}
          >
            {searchLoading ? "Searching…" : "Search"}
          </button>
        </div>

        {searchError && (
          <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            {searchError}
          </p>
        )}

        {!searchLoading && searchResults && searchResults.length === 0 && (
          <p className="mt-4 text-sm text-neutral-700">
            No indexed semantic indexes matched this query in the vector backend (empty result set).
          </p>
        )}

        {searchResults && searchResults.length > 0 && (
          <ul className="mt-4 space-y-3">
            {searchResults.map((r) => (
              <li
                key={r.id}
                className="rounded border border-neutral-200 bg-neutral-50 p-3 text-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-mono text-xs text-neutral-600">{r.id}</div>
                  <div className="text-xs text-neutral-700">
                    score:{" "}
                    <span className="font-semibold text-neutral-900">{r.score}</span>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <VectorStatusBadge status={r.vector_status} />
                  <span className="text-neutral-800">{r.meaning}</span>
                </div>
                {r.summary && (
                  <p className="mt-2 text-xs text-neutral-600">{r.summary}</p>
                )}
                <button
                  type="button"
                  className="mt-3 text-xs font-medium text-neutral-800 underline hover:text-neutral-950"
                  onClick={() => void loadSelected(r.id)}
                >
                  Inspect this index (detail + entry points)
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Semantic indexes list</h2>
        <p className="mt-1 text-xs text-neutral-500">
          <code className="font-mono">GET /semantic-indexes</code>
        </p>

        {listLoading && <p className="mt-4 text-sm text-neutral-600">Loading indexes…</p>}
        {listError && (
          <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            {listError}
          </p>
        )}
        {listUnavailable && (
          <div className="mt-4 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
            This API returned <strong>404</strong> for{" "}
            <code className="font-mono text-xs">GET /semantic-indexes</code> — there is no list
            route on this deployment. Use semantic search above or open a known UUID below.
          </div>
        )}
        {!listLoading && !listError && !listUnavailable && indexes.length === 0 && (
          <p className="mt-4 text-sm text-neutral-600">No semantic indexes returned from the API.</p>
        )}
        {!listLoading && indexes.length > 0 && (
          <ul className="mt-4 max-h-56 divide-y divide-neutral-100 overflow-y-auto rounded border border-neutral-100">
            {indexes.map((idx) => (
              <li key={idx.id}>
                <button
                  type="button"
                  onClick={() => void loadSelected(idx.id)}
                  className={`flex w-full flex-col items-start gap-1 px-3 py-2 text-left text-sm hover:bg-neutral-50 ${
                    selectedId === idx.id ? "bg-neutral-100" : ""
                  }`}
                >
                  <span className="font-mono text-xs text-neutral-500">{idx.id}</span>
                  <span className="font-medium text-neutral-900">{idx.meaning}</span>
                  <span className="flex items-center gap-2 text-xs text-neutral-600">
                    <VectorStatusBadge status={idx.vector_status} />
                    {idx.summary ? idx.summary.slice(0, 120) : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="mt-6 border-t border-neutral-100 pt-4">
          <h3 className="text-xs font-medium text-neutral-700">Open by semantic index id</h3>
          <p className="mt-1 text-xs text-neutral-500">
            Loads <code className="font-mono">GET /semantic-indexes/{"{id}"}</code> and{" "}
            <code className="font-mono">…/entry-points</code>.
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <input
              type="text"
              className="min-w-[16rem] flex-1 rounded border border-neutral-300 px-3 py-2 font-mono text-xs text-neutral-900 shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
              placeholder="semantic_index UUID"
              value={manualId}
              onChange={(e) => setManualId(e.target.value)}
              disabled={manualLoading}
            />
            <button
              type="button"
              className="rounded border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-800 hover:bg-neutral-50 disabled:opacity-50"
              onClick={() => void openByManualId()}
              disabled={manualLoading}
            >
              {manualLoading ? "Loading…" : "Load"}
            </button>
          </div>
          {manualError && (
            <p className="mt-2 text-sm text-red-800">{manualError}</p>
          )}
        </div>
      </div>

      {selectedId && (
        <div className="space-y-4">
          <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-950">
            Selected semantic index{" "}
            <code className="rounded bg-blue-100 px-1 font-mono text-xs">{selectedId}</code>.
            Entry points below are graph node ids returned by the API only (no invented labels).
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Detail</h3>
            {detailLoading && (
              <p className="mt-3 text-sm text-neutral-600">Loading detail…</p>
            )}
            {detailError && (
              <p className="mt-3 whitespace-pre-wrap text-sm text-red-800">{detailError}</p>
            )}
            {!detailLoading && detail && (
              <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-[minmax(9rem,auto)_1fr]">
                <dt className="text-neutral-500">id</dt>
                <dd className="font-mono text-xs">{detail.id}</dd>
                <dt className="text-neutral-500">meaning</dt>
                <dd>{detail.meaning}</dd>
                <dt className="text-neutral-500">summary</dt>
                <dd>{detail.summary ?? "(none)"}</dd>
                <dt className="text-neutral-500">embedding_text</dt>
                <dd className="whitespace-pre-wrap font-mono text-xs text-neutral-800">
                  {detail.embedding_text ?? "(none)"}
                </dd>
                <dt className="text-neutral-500">vector_status</dt>
                <dd>
                  <VectorStatusBadge status={detail.vector_status} />
                  <span className="ml-2 text-xs text-neutral-600">
                    Pending/failed rows are not returned by semantic search until indexed.
                  </span>
                </dd>
                <dt className="text-neutral-500">entry_node_ids (from detail)</dt>
                <dd className="font-mono text-xs break-all">
                  {detail.entry_node_ids.length
                    ? detail.entry_node_ids.join(", ")
                    : "(none)"}
                </dd>
                <dt className="text-neutral-500">metadata</dt>
                <dd className="whitespace-pre-wrap font-mono text-xs">
                  {detail.metadata == null || Object.keys(detail.metadata).length === 0
                    ? "(none)"
                    : formatJson(detail.metadata)}
                </dd>
                <dt className="text-neutral-500">created_at</dt>
                <dd className="font-mono text-xs">{detail.created_at}</dd>
                <dt className="text-neutral-500">updated_at</dt>
                <dd className="font-mono text-xs">{detail.updated_at}</dd>
              </dl>
            )}
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">
              Entry points{" "}
              <span className="font-normal text-neutral-500">
                (<code className="font-mono text-xs">GET …/entry-points</code>)
              </span>
            </h3>
            {epLoading && (
              <p className="mt-3 text-sm text-neutral-600">Loading entry points…</p>
            )}
            {epError && !detailLoading && (
              <p className="mt-3 whitespace-pre-wrap text-sm text-red-800">{epError}</p>
            )}
            {!epLoading && entryPointIds && (
              <>
                {entryPointIds.length === 0 ? (
                  <p className="mt-3 text-sm text-neutral-600">
                    API returned no entry node ids for this index.
                  </p>
                ) : (
                  <ul className="mt-3 list-inside list-disc font-mono text-xs text-neutral-900">
                    {entryPointIds.map((nid) => (
                      <li key={nid} className="break-all">
                        {nid}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
