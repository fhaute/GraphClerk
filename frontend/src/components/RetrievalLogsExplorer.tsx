import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { fetchRetrievalLog, fetchRetrievalLogs } from "../api/retrievalLogs";
import type { RetrievalLogDetailResponse, RetrievalLogSummary } from "../types/retrievalLog";
import type { RetrievalPacket } from "../types/retrievalPacket";
import { RetrievalPacketPanel } from "./RetrievalPacketPanel";

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

/** Minimal structural check before handing stored JSON to RetrievalPacketPanel. */
function parseStoredRetrievalPacket(raw: unknown): RetrievalPacket | null {
  if (raw == null || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  if (o.packet_type !== "retrieval_packet") return null;
  if (typeof o.question !== "string") return null;
  if (!Array.isArray(o.evidence_units)) return null;
  if (!Array.isArray(o.graph_paths)) return null;
  if (!Array.isArray(o.selected_indexes)) return null;
  if (!Array.isArray(o.alternative_interpretations)) return null;
  if (!Array.isArray(o.warnings)) return null;
  if (o.interpreted_intent == null || typeof o.interpreted_intent !== "object") return null;
  if (o.context_budget == null || typeof o.context_budget !== "object") return null;
  if (typeof o.answer_mode !== "string") return null;
  if (typeof o.confidence !== "number") return null;
  return o as unknown as RetrievalPacket;
}

function WarningsInline({ warnings }: { warnings: string[] | null | undefined }) {
  if (warnings == null || warnings.length === 0) {
    return <span className="text-neutral-500">(none)</span>;
  }
  return (
    <ul className="max-h-24 list-inside list-disc overflow-y-auto text-xs text-amber-950">
      {warnings.map((w, i) => (
        <li key={i} className="whitespace-pre-wrap">
          {w}
        </li>
      ))}
    </ul>
  );
}

const MAX_LIMIT = 100;

export function RetrievalLogsExplorer() {
  const [limitStr, setLimitStr] = useState("50");
  const [offsetStr, setOffsetStr] = useState("0");

  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [items, setItems] = useState<RetrievalLogSummary[]>([]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detail, setDetail] = useState<RetrievalLogDetailResponse | null>(null);

  const loadList = useCallback(async () => {
    const limit = Math.min(MAX_LIMIT, Math.max(1, Number.parseInt(limitStr, 10) || 50));
    const offset = Math.max(0, Number.parseInt(offsetStr, 10) || 0);
    setLimitStr(String(limit));
    setOffsetStr(String(offset));
    setListLoading(true);
    setListError(null);
    try {
      const res = await fetchRetrievalLogs({ limit, offset });
      setItems(res.items);
    } catch (e) {
      setListError(formatError(e));
      setItems([]);
    } finally {
      setListLoading(false);
    }
  }, [limitStr, offsetStr]);

  useEffect(() => {
    void loadList();
  }, []);

  const selectLog = useCallback(async (id: string) => {
    setSelectedId(id);
    setDetailLoading(true);
    setDetailError(null);
    setDetail(null);
    try {
      const d = await fetchRetrievalLog(id);
      setDetail(d);
    } catch (e) {
      setDetailError(formatError(e));
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const parsedPacket =
    detail?.retrieval_packet != null
      ? parseStoredRetrievalPacket(detail.retrieval_packet)
      : null;
  const packetPresentButUnreadable =
    detail?.retrieval_packet != null && parsedPacket == null;

  return (
    <section className="space-y-6">
      <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Retrieval logs</h2>
        <p className="mt-1 text-xs text-neutral-500">
          Read-only: <code className="font-mono">GET /retrieval-logs</code>,{" "}
          <code className="font-mono">GET /retrieval-logs/{"{id}"}</code>. Stored packets are shown
          only when returned by the API — never reconstructed from summaries.
        </p>
        <p className="mt-2 text-xs text-neutral-600">
          List summaries do not include a selected-index count; open a log for{" "}
          <code className="font-mono">selected_indexes</code>.
        </p>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="flex flex-col text-xs text-neutral-600">
            limit (1–{MAX_LIMIT})
            <input
              type="number"
              min={1}
              max={MAX_LIMIT}
              className="mt-1 w-24 rounded border border-neutral-300 px-2 py-1 text-sm shadow-sm"
              value={limitStr}
              onChange={(e) => setLimitStr(e.target.value)}
              disabled={listLoading}
            />
          </label>
          <label className="flex flex-col text-xs text-neutral-600">
            offset (≥ 0)
            <input
              type="number"
              min={0}
              className="mt-1 w-24 rounded border border-neutral-300 px-2 py-1 text-sm shadow-sm"
              value={offsetStr}
              onChange={(e) => setOffsetStr(e.target.value)}
              disabled={listLoading}
            />
          </label>
          <button
            type="button"
            className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
            onClick={() => void loadList()}
            disabled={listLoading}
          >
            {listLoading ? "Loading…" : "Apply"}
          </button>
        </div>

        {listError && (
          <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            {listError}
          </p>
        )}

        {!listLoading && !listError && items.length === 0 && (
          <p className="mt-4 text-sm text-neutral-600">No retrieval logs returned for this page.</p>
        )}

        {!listLoading && items.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-neutral-200 text-neutral-600">
                  <th className="py-2 pr-3 font-medium">id</th>
                  <th className="py-2 pr-3 font-medium">question</th>
                  <th className="py-2 pr-3 font-medium" title="Not in list API; open detail">
                    sel. idx#
                  </th>
                  <th className="py-2 pr-3 font-medium">evidence#</th>
                  <th className="py-2 pr-3 font-medium">warnings</th>
                  <th className="py-2 pr-3 font-medium">confidence</th>
                  <th className="py-2 pr-3 font-medium">latency_ms</th>
                  <th className="py-2 pr-3 font-medium">token_est.</th>
                  <th className="py-2 pr-3 font-medium">packet?</th>
                  <th className="py-2 font-medium">created_at</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr
                    key={row.id}
                    className={`cursor-pointer border-b border-neutral-100 hover:bg-neutral-50 ${
                      selectedId === row.id ? "bg-neutral-100" : ""
                    }`}
                    onClick={() => void selectLog(row.id)}
                  >
                    <td className="py-2 pr-3 font-mono align-top text-neutral-700">{row.id}</td>
                    <td className="py-2 pr-3 align-top text-neutral-900">
                      <div className="max-h-20 max-w-xs overflow-y-auto whitespace-pre-wrap">
                        {row.question}
                      </div>
                    </td>
                    <td
                      className="py-2 pr-3 align-top text-neutral-500"
                      title="Use detail view — summary has no selected_indexes count"
                    >
                      —
                    </td>
                    <td className="py-2 pr-3 align-top">{row.evidence_unit_count}</td>
                    <td className="py-2 pr-3 align-top max-w-[12rem]">
                      <WarningsInline warnings={row.warnings} />
                    </td>
                    <td className="py-2 pr-3 align-top">{row.confidence ?? "—"}</td>
                    <td className="py-2 pr-3 align-top">{row.latency_ms ?? "—"}</td>
                    <td className="py-2 pr-3 align-top">{row.token_estimate ?? "—"}</td>
                    <td className="py-2 pr-3 align-top font-mono">
                      {row.has_retrieval_packet ? "yes" : "no"}
                    </td>
                    <td className="py-2 align-top font-mono text-neutral-600">{row.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedId && (
        <div className="space-y-4">
          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Log detail</h3>
            <p className="mt-1 font-mono text-xs text-neutral-500">{selectedId}</p>
            {detailLoading && (
              <p className="mt-4 text-sm text-neutral-600">Loading detail…</p>
            )}
            {detailError && (
              <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
                {detailError}
              </p>
            )}
            {!detailLoading && detail && (
              <>
                <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-[minmax(10rem,auto)_1fr]">
                  <dt className="text-neutral-500">question</dt>
                  <dd className="whitespace-pre-wrap">{detail.question}</dd>
                  <dt className="text-neutral-500">selected_indexes</dt>
                  <dd>
                    {detail.selected_indexes == null ? (
                      "(none)"
                    ) : (
                      <>
                        <span className="font-mono text-xs">
                          count: {detail.selected_indexes.length}
                        </span>
                        <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded border border-neutral-100 bg-neutral-50 p-2 text-xs">
                          {formatJson(detail.selected_indexes)}
                        </pre>
                      </>
                    )}
                  </dd>
                  <dt className="text-neutral-500">graph_path</dt>
                  <dd className="font-mono text-xs whitespace-pre-wrap">
                    {detail.graph_path == null ? "(none)" : formatJson(detail.graph_path)}
                  </dd>
                  <dt className="text-neutral-500">evidence_unit_ids</dt>
                  <dd className="font-mono text-xs break-all">
                    {detail.evidence_unit_ids?.join(", ") ?? "(none)"}
                  </dd>
                  <dt className="text-neutral-500">confidence</dt>
                  <dd>{detail.confidence ?? "(none)"}</dd>
                  <dt className="text-neutral-500">warnings</dt>
                  <dd>
                    {detail.warnings == null || detail.warnings.length === 0 ? (
                      "(none)"
                    ) : (
                      <ul className="list-inside list-disc rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
                        {detail.warnings.map((w, i) => (
                          <li key={i} className="whitespace-pre-wrap">
                            {w}
                          </li>
                        ))}
                      </ul>
                    )}
                  </dd>
                  <dt className="text-neutral-500">latency_ms</dt>
                  <dd>{detail.latency_ms ?? "(none)"}</dd>
                  <dt className="text-neutral-500">token_estimate</dt>
                  <dd>{detail.token_estimate ?? "(none)"}</dd>
                  <dt className="text-neutral-500">metadata</dt>
                  <dd className="font-mono text-xs whitespace-pre-wrap">
                    {detail.metadata == null || Object.keys(detail.metadata).length === 0
                      ? "(none)"
                      : formatJson(detail.metadata)}
                  </dd>
                  <dt className="text-neutral-500">created_at</dt>
                  <dd className="font-mono text-xs">{detail.created_at}</dd>
                </dl>

                <div className="mt-8 border-t border-neutral-200 pt-6">
                  <h4 className="text-sm font-medium text-neutral-800">Stored retrieval_packet</h4>
                  {detail.retrieval_packet == null ? (
                    <p className="mt-3 text-sm text-neutral-700">
                      This log has no stored <code className="font-mono">retrieval_packet</code> in
                      the API response (null or absent). The readable RetrievalPacket view is not
                      available without inventing data.
                    </p>
                  ) : packetPresentButUnreadable ? (
                    <div className="mt-3 space-y-2">
                      <p className="text-sm text-amber-900">
                        A stored packet JSON exists but does not match the expected RetrievalPacket
                        shape for the readable viewer. Raw payload is below only.
                      </p>
                      <pre className="max-h-[min(50vh,480px)] overflow-auto rounded border border-neutral-800 bg-neutral-950 p-3 text-xs text-neutral-100">
                        {formatJson(detail.retrieval_packet)}
                      </pre>
                    </div>
                  ) : (
                    parsedPacket && <RetrievalPacketPanel packet={parsedPacket} />
                  )}
                </div>

                <div className="mt-8 rounded-md border border-neutral-800 bg-neutral-950 p-4">
                  <h4 className="text-sm font-medium text-neutral-300">Raw log detail JSON</h4>
                  <pre className="mt-3 max-h-[min(60vh,560px)] overflow-auto whitespace-pre-wrap break-words text-xs text-neutral-100">
                    {formatJson(detail)}
                  </pre>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
