import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { fetchRetrievalLog, fetchRetrievalLogs } from "../api/retrievalLogs";
import { parseStoredRetrievalPacket } from "../lib/parseStoredRetrievalPacket";
import type { RetrievalLogDetailResponse, RetrievalLogSummary } from "../types/retrievalLog";

function formatError(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return String(err);
}

function mean(nums: number[]): number | null {
  if (nums.length === 0) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

function fmtMean(n: number | null): string {
  if (n === null) return "—";
  return String(Math.round(n * 1000) / 1000);
}

const MAX_LIMIT = 100;

function MetricCard({
  title,
  subtitle,
  value,
}: {
  title: string;
  subtitle: string;
  value: string | number;
}) {
  return (
    <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium text-neutral-600">{title}</div>
      <div className="mt-2 text-2xl font-semibold tabular-nums text-neutral-900">{value}</div>
      <p className="mt-2 text-xs text-neutral-500">{subtitle}</p>
    </div>
  );
}

export function EvaluationDashboard() {
  const [limitStr, setLimitStr] = useState("50");
  const [offsetStr, setOffsetStr] = useState("0");

  const [listLoading, setListLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [summaries, setSummaries] = useState<RetrievalLogSummary[]>([]);

  const [detailsById, setDetailsById] = useState<Record<string, RetrievalLogDetailResponse>>({});
  const [detailFetchRejected, setDetailFetchRejected] = useState(0);

  const loadAll = useCallback(async () => {
    const limit = Math.min(MAX_LIMIT, Math.max(1, Number.parseInt(limitStr, 10) || 50));
    const offset = Math.max(0, Number.parseInt(offsetStr, 10) || 0);
    setLimitStr(String(limit));
    setOffsetStr(String(offset));
    setListLoading(true);
    setDetailsLoading(false);
    setListError(null);
    setSummaries([]);
    setDetailsById({});
    setDetailFetchRejected(0);

    try {
      const listRes = await fetchRetrievalLogs({ limit, offset });
      const items = listRes.items;
      setSummaries(items);

      const packetIds = items.filter((r) => r.has_retrieval_packet).map((r) => r.id);
      if (packetIds.length === 0) {
        setListLoading(false);
        return;
      }

      setDetailsLoading(true);
      const settled = await Promise.allSettled(packetIds.map((id) => fetchRetrievalLog(id)));
      const next: Record<string, RetrievalLogDetailResponse> = {};
      let rejected = 0;
      settled.forEach((result, i) => {
        const id = packetIds[i];
        if (result.status === "fulfilled") next[id] = result.value;
        else rejected += 1;
      });
      setDetailsById(next);
      setDetailFetchRejected(rejected);
    } catch (e) {
      setListError(formatError(e));
      setSummaries([]);
    } finally {
      setListLoading(false);
      setDetailsLoading(false);
    }
  }, [limitStr, offsetStr]);

  useEffect(() => {
    void loadAll();
  }, []);

  const honesty = useMemo(() => {
    const totalLoaded = summaries.length;
    const flaggedPacket = summaries.filter((s) => s.has_retrieval_packet).length;
    const noPacketFlag = summaries.filter((s) => !s.has_retrieval_packet).length;

    let missingPayloadAfterDetail = 0;
    let jsonPresentButUnparsed = 0;
    const parsedPackets = [];

    for (const s of summaries) {
      if (!s.has_retrieval_packet) continue;
      const d = detailsById[s.id];
      if (!d) continue;
      if (d.retrieval_packet == null) {
        missingPayloadAfterDetail += 1;
        continue;
      }
      const p = parseStoredRetrievalPacket(d.retrieval_packet);
      if (p == null) {
        jsonPresentButUnparsed += 1;
        continue;
      }
      parsedPackets.push(p);
    }

    return {
      totalLoaded,
      flaggedPacket,
      noPacketFlag,
      missingPayloadAfterDetail,
      jsonPresentButUnparsed,
      parsedPacketCount: parsedPackets.length,
      parsedPackets,
    };
  }, [summaries, detailsById]);

  const listMetrics = useMemo(() => {
    const confidences = summaries
      .map((s) => s.confidence)
      .filter((c): c is number => c != null && typeof c === "number");
    const latencies = summaries
      .map((s) => s.latency_ms)
      .filter((x): x is number => x != null && typeof x === "number");
    const tokens = summaries
      .map((s) => s.token_estimate)
      .filter((x): x is number => x != null && typeof x === "number");
    const evidenceCounts = summaries.map((s) => s.evidence_unit_count);

    const warningFreq = new Map<string, number>();
    for (const row of summaries) {
      for (const w of row.warnings ?? []) {
        warningFreq.set(w, (warningFreq.get(w) ?? 0) + 1);
      }
    }
    const warningRows = Array.from(warningFreq.entries()).sort((a, b) => b[1] - a[1]);

    const answerModeFreq = new Map<string, number>();
    for (const p of honesty.parsedPackets) {
      answerModeFreq.set(p.answer_mode, (answerModeFreq.get(p.answer_mode) ?? 0) + 1);
    }
    const answerModeRows = Array.from(answerModeFreq.entries()).sort((a, b) => b[1] - a[1]);

    const selIdxLens = honesty.parsedPackets.map((p) => p.selected_indexes.length);
    const graphPathLens = honesty.parsedPackets.map((p) => p.graph_paths.length);

    return {
      avgConfidence: mean(confidences),
      avgLatency: mean(latencies),
      avgTokenEstimate: mean(tokens),
      avgEvidenceUnits: mean(evidenceCounts),
      avgSelectedIndexes: mean(selIdxLens),
      avgGraphPaths: mean(graphPathLens),
      warningRows,
      answerModeRows,
      confidenceSampleSize: confidences.length,
      latencySampleSize: latencies.length,
      tokenSampleSize: tokens.length,
      packetMetricsSampleSize: honesty.parsedPackets.length,
    };
  }, [summaries, honesty]);

  const busy = listLoading || detailsLoading;

  return (
    <section className="space-y-6">
      <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-3 text-sm text-amber-950">
        <strong className="font-medium">Limitation</strong>
        <p className="mt-1">
          These are <strong className="font-medium">observability metrics</strong>, not
          answer-quality metrics. There is no accuracy score, no LLM judge, and no benchmark
          comparison in this slice.
        </p>
      </div>

      <div className="rounded-md border border-teal-200 bg-teal-50/90 px-3 py-3 text-sm text-teal-950">
        <strong className="font-medium">Model pipeline (Phase 8)</strong>
        <p className="mt-1">
          Ingest-time model calls are <strong className="font-medium">disabled by default</strong>.
          Configured <code className="font-mono text-xs">evidence_candidate_enricher</code> output is
          stored on{" "}
          <code className="font-mono text-xs">
            EvidenceUnit.metadata_json[&quot;graphclerk_model_pipeline&quot;]
          </code>{" "}
          — use <strong className="font-medium">Artifacts &amp; evidence</strong> for operator notes
          and (when the API includes <code className="font-mono text-xs">metadata_json</code>) a
          readout. A <strong className="font-medium">writable selector</strong> is future Track D{" "}
          <strong>D7b</strong> (this dashboard does not configure models).
        </p>
      </div>

      <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Evaluation (retrieval logs)</h2>
        <p className="mt-1 text-xs text-neutral-500">
          Data from <code className="font-mono">GET /retrieval-logs</code> and, when{" "}
          <code className="font-mono">has_retrieval_packet</code> is true,{" "}
          <code className="font-mono">GET /retrieval-logs/{"{id}"}</code>. Nothing is inferred from
          summaries alone except where labeled. <strong className="text-neutral-700">POST /retrieve</strong>{" "}
          is not called for hidden runs.
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
              disabled={busy}
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
              disabled={busy}
            />
          </label>
          <button
            type="button"
            className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
            onClick={() => void loadAll()}
            disabled={busy}
          >
            {busy ? "Loading…" : "Refresh"}
          </button>
        </div>

        {listError && (
          <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            {listError}
          </p>
        )}

        {!listLoading && !listError && summaries.length === 0 && (
          <p className="mt-4 text-sm text-neutral-600">
            No logs on this page. Adjust limit/offset and refresh, or run retrievals elsewhere first.
          </p>
        )}
      </div>

      {summaries.length > 0 && (
        <>
          <div className="rounded-md border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-neutral-800">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-600">
              Traceability / honesty (this refresh)
            </h3>
            <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
              <li>
                Retrieval log rows loaded (this page):{" "}
                <strong className="font-mono">{honesty.totalLoaded}</strong>
              </li>
              <li>
                Rows with <code className="font-mono">has_retrieval_packet=true</code> in list:{" "}
                <strong className="font-mono">{honesty.flaggedPacket}</strong>
              </li>
              <li>
                Rows without stored packet flag in list:{" "}
                <strong className="font-mono">{honesty.noPacketFlag}</strong> (packets are not
                reconstructed)
              </li>
              <li>
                Detail GET failures (for flagged rows):{" "}
                <strong className="font-mono">{detailFetchRejected}</strong>
              </li>
              <li>
                Flagged in list but detail had null <code className="font-mono">retrieval_packet</code>:{" "}
                <strong className="font-mono">{honesty.missingPayloadAfterDetail}</strong>
              </li>
              <li>
                Non-null packet JSON that failed structural parse for metrics:{" "}
                <strong className="font-mono">{honesty.jsonPresentButUnparsed}</strong>
              </li>
              <li>
                Parsed packets used for packet-field metrics:{" "}
                <strong className="font-mono">{honesty.parsedPacketCount}</strong>
              </li>
            </ul>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <MetricCard
              title="Total logs (page)"
              subtitle="Count of rows returned by GET /retrieval-logs for current limit/offset."
              value={honesty.totalLoaded}
            />
            <MetricCard
              title="Logs with packet flag"
              subtitle="Summaries where has_retrieval_packet is true (list API only)."
              value={summaries.filter((s) => s.has_retrieval_packet).length}
            />
            <MetricCard
              title="Avg confidence"
              subtitle={`Mean of list summary confidence where present (n=${listMetrics.confidenceSampleSize}). Not a quality score.`}
              value={fmtMean(listMetrics.avgConfidence)}
            />
            <MetricCard
              title="Avg evidence_unit_count"
              subtitle="Mean of list summary evidence_unit_count for all rows on this page."
              value={fmtMean(listMetrics.avgEvidenceUnits)}
            />
            <MetricCard
              title="Avg latency_ms"
              subtitle={`Mean of list summary latency_ms where present (n=${listMetrics.latencySampleSize}).`}
              value={fmtMean(listMetrics.avgLatency)}
            />
            <MetricCard
              title="Avg token_estimate"
              subtitle={`Mean of list summary token_estimate where present (n=${listMetrics.tokenSampleSize}).`}
              value={fmtMean(listMetrics.avgTokenEstimate)}
            />
            <MetricCard
              title="Avg selected index count"
              subtitle={`Mean length of selected_indexes inside parsed stored retrieval_packet only (n=${listMetrics.packetMetricsSampleSize}).`}
              value={fmtMean(listMetrics.avgSelectedIndexes)}
            />
            <MetricCard
              title="Avg graph path count"
              subtitle={`Mean length of graph_paths inside parsed stored retrieval_packet only (n=${listMetrics.packetMetricsSampleSize}).`}
              value={fmtMean(listMetrics.avgGraphPaths)}
            />
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Answer mode distribution</h3>
            <p className="mt-1 text-xs text-neutral-500">
              Counts from <code className="font-mono">answer_mode</code> on{" "}
              <strong className="text-neutral-700">parsed</strong> stored retrieval packets only (
              {honesty.parsedPacketCount} packets). Empty if none parsed.
            </p>
            {listMetrics.answerModeRows.length === 0 ? (
              <p className="mt-4 text-sm text-neutral-600">No parsed packets with answer_mode.</p>
            ) : (
              <table className="mt-4 w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 text-neutral-600">
                    <th className="py-2 pr-3 font-medium">answer_mode</th>
                    <th className="py-2 font-medium">count</th>
                  </tr>
                </thead>
                <tbody>
                  {listMetrics.answerModeRows.map(([mode, count]) => (
                    <tr key={mode} className="border-b border-neutral-100">
                      <td className="py-2 pr-3 font-mono text-xs">{mode}</td>
                      <td className="py-2 tabular-nums">{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Warning frequency</h3>
            <p className="mt-1 text-xs text-neutral-500">
              Warning strings aggregated from list summary <code className="font-mono">warnings</code>{" "}
              arrays for logs on this page (each occurrence counted once per log row).
            </p>
            {listMetrics.warningRows.length === 0 ? (
              <p className="mt-4 text-sm text-neutral-600">
                No warnings on list summaries for this page.
              </p>
            ) : (
              <table className="mt-4 w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 text-neutral-600">
                    <th className="py-2 pr-3 font-medium">warning text</th>
                    <th className="py-2 font-medium">count</th>
                  </tr>
                </thead>
                <tbody>
                  {listMetrics.warningRows.map(([text, count]) => (
                    <tr key={text} className="border-b border-neutral-100">
                      <td className="max-w-xl py-2 pr-3 whitespace-pre-wrap font-mono text-xs">
                        {text}
                      </td>
                      <td className="py-2 tabular-nums">{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="rounded-md border border-neutral-300 bg-neutral-100 px-4 py-4 text-sm text-neutral-800">
            <h3 className="text-sm font-medium text-neutral-900">Naive baseline</h3>
            <p className="mt-2 text-neutral-700">
              Naive baseline comparison is not implemented yet. This dashboard currently summarizes
              GraphClerk RetrievalPackets (and log summaries) only.
            </p>
          </div>
        </>
      )}
    </section>
  );
}
