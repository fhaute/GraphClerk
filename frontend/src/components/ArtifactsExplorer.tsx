import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { fetchArtifact, fetchArtifacts } from "../api/artifacts";
import { fetchArtifactEvidence, fetchEvidenceUnit } from "../api/evidenceUnits";
import type { ArtifactResponse } from "../types/artifact";
import type { EvidenceUnitResponse } from "../types/evidenceUnit";

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

const TEXT_PREVIEW = 240;

function EvidenceTextBlock({
  text,
  unitId,
  showFull,
  onToggle,
}: {
  text: string | null;
  unitId: string;
  showFull: boolean;
  onToggle: (id: string) => void;
}) {
  if (text == null || text === "") {
    return <span className="text-neutral-500">(no text)</span>;
  }
  const needsToggle = text.length > TEXT_PREVIEW;
  const shown = showFull || !needsToggle ? text : `${text.slice(0, TEXT_PREVIEW)}…`;
  return (
    <div className="space-y-1">
      <p className="whitespace-pre-wrap text-neutral-800">{shown}</p>
      {needsToggle && (
        <button
          type="button"
          className="text-xs font-medium text-neutral-700 underline hover:text-neutral-900"
          onClick={() => onToggle(unitId)}
        >
          {showFull ? "Show preview" : "Show full text"}
        </button>
      )}
    </div>
  );
}

export function ArtifactsExplorer() {
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactResponse[]>([]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [artifactDetail, setArtifactDetail] = useState<ArtifactResponse | null>(null);

  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [evidenceItems, setEvidenceItems] = useState<EvidenceUnitResponse[]>([]);

  const [modalityFilter, setModalityFilter] = useState("");
  const [contentTypeFilter, setContentTypeFilter] = useState("");
  const [sourceFidelityFilter, setSourceFidelityFilter] = useState("");

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedLoading, setExpandedLoading] = useState(false);
  const [expandedError, setExpandedError] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<EvidenceUnitResponse | null>(null);

  const [fullTextRows, setFullTextRows] = useState<Record<string, boolean>>({});

  const toggleFullText = useCallback((id: string) => {
    setFullTextRows((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setListLoading(true);
    setListError(null);
    fetchArtifacts({ limit: 200 })
      .then((res) => {
        if (!cancelled) setArtifacts(res.items);
      })
      .catch((e) => {
        if (!cancelled) setListError(formatError(e));
      })
      .finally(() => {
        if (!cancelled) setListLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectArtifact = useCallback(async (artifactId: string) => {
    setSelectedId(artifactId);
    setDetailError(null);
    setEvidenceError(null);
    setExpandedId(null);
    setExpandedDetail(null);
    setExpandedError(null);
    setModalityFilter("");
    setContentTypeFilter("");
    setSourceFidelityFilter("");
    setFullTextRows({});
    setDetailLoading(true);
    setEvidenceLoading(true);
    try {
      const [detail, ev] = await Promise.all([
        fetchArtifact(artifactId),
        fetchArtifactEvidence(artifactId, { limit: 1000 }),
      ]);
      setArtifactDetail(detail);
      setEvidenceItems(ev.items);
    } catch (e) {
      const msg = formatError(e);
      setDetailError(msg);
      setEvidenceError(msg);
      setArtifactDetail(null);
      setEvidenceItems([]);
    } finally {
      setDetailLoading(false);
      setEvidenceLoading(false);
    }
  }, []);

  const toggleExpand = useCallback(async (unitId: string) => {
    if (expandedId === unitId) {
      setExpandedId(null);
      setExpandedDetail(null);
      setExpandedError(null);
      return;
    }
    setExpandedId(unitId);
    setExpandedDetail(null);
    setExpandedError(null);
    setExpandedLoading(true);
    try {
      const d = await fetchEvidenceUnit(unitId);
      setExpandedDetail(d);
    } catch (e) {
      setExpandedError(formatError(e));
    } finally {
      setExpandedLoading(false);
    }
  }, [expandedId]);

  const modalityOptions = useMemo(() => {
    const s = new Set<string>();
    evidenceItems.forEach((e) => s.add(e.modality));
    return ["", ...Array.from(s).sort()];
  }, [evidenceItems]);

  const contentTypeOptions = useMemo(() => {
    const s = new Set<string>();
    evidenceItems.forEach((e) => s.add(e.content_type));
    return ["", ...Array.from(s).sort()];
  }, [evidenceItems]);

  const sourceFidelityOptions = useMemo(() => {
    const s = new Set<string>();
    evidenceItems.forEach((e) => s.add(e.source_fidelity));
    return ["", ...Array.from(s).sort()];
  }, [evidenceItems]);

  const filteredEvidence = useMemo(() => {
    return evidenceItems.filter((e) => {
      if (modalityFilter && e.modality !== modalityFilter) return false;
      if (contentTypeFilter && e.content_type !== contentTypeFilter) return false;
      if (sourceFidelityFilter && e.source_fidelity !== sourceFidelityFilter) return false;
      return true;
    });
  }, [evidenceItems, modalityFilter, contentTypeFilter, sourceFidelityFilter]);

  const selectedArtifactSummary = artifacts.find((a) => a.id === selectedId);

  return (
    <section className="space-y-6">
      <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Artifacts</h2>
        <p className="mt-1 text-xs text-neutral-500">
          Read-only: <code className="font-mono">GET /artifacts</code>,{" "}
          <code className="font-mono">GET /artifacts/{"{id}"}</code>,{" "}
          <code className="font-mono">GET /artifacts/{"{id}"}/evidence</code>,{" "}
          <code className="font-mono">GET /evidence-units/{"{id}"}</code>.
        </p>

        {listLoading && <p className="mt-4 text-sm text-neutral-600">Loading artifacts…</p>}
        {listError && (
          <p className="mt-4 whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            {listError}
          </p>
        )}
        {!listLoading && !listError && artifacts.length === 0 && (
          <p className="mt-4 text-sm text-neutral-600">No artifacts returned from the API.</p>
        )}
        {!listLoading && !listError && artifacts.length > 0 && (
          <ul className="mt-4 max-h-56 divide-y divide-neutral-100 overflow-y-auto rounded border border-neutral-100">
            {artifacts.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  onClick={() => void selectArtifact(a.id)}
                  className={`flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left text-sm hover:bg-neutral-50 ${
                    selectedId === a.id ? "bg-neutral-100" : ""
                  }`}
                >
                  <span className="font-mono text-xs text-neutral-500">{a.id}</span>
                  <span className="font-medium text-neutral-900">{a.filename}</span>
                  <span className="text-xs text-neutral-600">
                    {a.artifact_type}
                    {a.title ? ` · ${a.title}` : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {selectedId && (
        <div className="space-y-4">
          <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-950">
            <strong className="font-medium">Traceability</strong>
            <p className="mt-1">
              Evidence units below belong to artifact{" "}
              <code className="rounded bg-blue-100 px-1 font-mono text-xs">{selectedId}</code>
              {selectedArtifactSummary ? (
                <>
                  {" "}
                  (<span className="font-medium">{selectedArtifactSummary.filename}</span>)
                </>
              ) : null}
              . Expanded rows load{" "}
              <code className="font-mono text-xs">GET /evidence-units/{"{id}"}</code> for inspection.
            </p>
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Artifact detail</h3>
            {detailLoading && <p className="mt-3 text-sm text-neutral-600">Loading artifact…</p>}
            {detailError && (
              <p className="mt-3 whitespace-pre-wrap text-sm text-red-800">{detailError}</p>
            )}
            {!detailLoading && artifactDetail && (
              <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-[minmax(8rem,auto)_1fr]">
                <dt className="text-neutral-500">artifact id</dt>
                <dd className="font-mono text-xs text-neutral-900">{artifactDetail.id}</dd>
                <dt className="text-neutral-500">filename</dt>
                <dd>{artifactDetail.filename}</dd>
                <dt className="text-neutral-500">title</dt>
                <dd>{artifactDetail.title ?? "(none)"}</dd>
                <dt className="text-neutral-500">artifact_type</dt>
                <dd>{artifactDetail.artifact_type}</dd>
                <dt className="text-neutral-500">mime_type</dt>
                <dd>{artifactDetail.mime_type ?? "(none)"}</dd>
                <dt className="text-neutral-500">checksum</dt>
                <dd className="font-mono text-xs break-all">{artifactDetail.checksum ?? "(none)"}</dd>
                <dt className="text-neutral-500">storage_uri</dt>
                <dd className="font-mono text-xs break-all">{artifactDetail.storage_uri}</dd>
                <dt className="text-neutral-500">size_bytes</dt>
                <dd>{artifactDetail.size_bytes}</dd>
                <dt className="text-neutral-500">created_at</dt>
                <dd className="font-mono text-xs">{artifactDetail.created_at}</dd>
                <dt className="text-neutral-500">updated_at</dt>
                <dd className="font-mono text-xs">{artifactDetail.updated_at}</dd>
                <dt className="text-neutral-500">metadata</dt>
                <dd className="font-mono text-xs whitespace-pre-wrap">
                  {artifactDetail.metadata == null || Object.keys(artifactDetail.metadata).length === 0
                    ? "(none)"
                    : formatJson(artifactDetail.metadata)}
                </dd>
              </dl>
            )}
          </div>

          <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-medium text-neutral-700">Evidence units</h3>
            <p className="mt-1 text-xs text-neutral-500">
              Filters apply client-side to the evidence returned for this artifact.{" "}
              <span className="font-medium text-neutral-700">source_fidelity</span> is always shown.
            </p>

            {evidenceLoading && (
              <p className="mt-4 text-sm text-neutral-600">Loading evidence…</p>
            )}
            {evidenceError && !detailLoading && (
              <p className="mt-4 whitespace-pre-wrap text-sm text-red-800">{evidenceError}</p>
            )}
            {!evidenceLoading && !evidenceError && evidenceItems.length === 0 && (
              <p className="mt-4 text-sm text-amber-800">
                This artifact has no evidence units in the API response (empty list).
              </p>
            )}
            {!evidenceLoading && !evidenceError && evidenceItems.length > 0 && (
              <>
                <div className="mt-4 flex flex-wrap gap-3">
                  <label className="flex flex-col text-xs text-neutral-600">
                    modality
                    <select
                      className="mt-1 rounded border border-neutral-300 px-2 py-1 text-sm text-neutral-900"
                      value={modalityFilter}
                      onChange={(e) => setModalityFilter(e.target.value)}
                    >
                      {modalityOptions.map((v) => (
                        <option key={v || "all"} value={v}>
                          {v === "" ? "All" : v}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="flex flex-col text-xs text-neutral-600">
                    content_type
                    <select
                      className="mt-1 rounded border border-neutral-300 px-2 py-1 text-sm text-neutral-900"
                      value={contentTypeFilter}
                      onChange={(e) => setContentTypeFilter(e.target.value)}
                    >
                      {contentTypeOptions.map((v) => (
                        <option key={v || "all"} value={v}>
                          {v === "" ? "All" : v}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="flex flex-col text-xs text-neutral-600">
                    source_fidelity
                    <select
                      className="mt-1 rounded border border-neutral-300 px-2 py-1 text-sm text-neutral-900"
                      value={sourceFidelityFilter}
                      onChange={(e) => setSourceFidelityFilter(e.target.value)}
                    >
                      {sourceFidelityOptions.map((v) => (
                        <option key={v || "all"} value={v}>
                          {v === "" ? "All" : v}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                {filteredEvidence.length === 0 ? (
                  <p className="mt-4 text-sm text-neutral-600">
                    No evidence units match the current filters.
                  </p>
                ) : (
                  <ul className="mt-4 space-y-3">
                    {filteredEvidence.map((eu) => (
                      <li
                        key={eu.id}
                        className="rounded border border-neutral-200 bg-neutral-50 p-3 text-sm"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <div className="text-xs text-neutral-500">evidence_unit_id</div>
                            <div className="font-mono text-xs text-neutral-900">{eu.id}</div>
                          </div>
                          <button
                            type="button"
                            className="shrink-0 rounded border border-neutral-300 bg-white px-2 py-1 text-xs font-medium text-neutral-800 hover:bg-neutral-100"
                            onClick={() => void toggleExpand(eu.id)}
                          >
                            {expandedId === eu.id ? "Collapse" : "Expand (fetch detail)"}
                          </button>
                        </div>
                        <dl className="mt-3 grid gap-1 sm:grid-cols-[minmax(9rem,auto)_1fr]">
                          <dt className="text-neutral-500">artifact_id</dt>
                          <dd className="font-mono text-xs">{eu.artifact_id}</dd>
                          <dt className="text-neutral-500">modality</dt>
                          <dd>{eu.modality}</dd>
                          <dt className="text-neutral-500">content_type</dt>
                          <dd>{eu.content_type}</dd>
                          <dt className="text-neutral-500">source_fidelity</dt>
                          <dd className="font-medium text-neutral-900">{eu.source_fidelity}</dd>
                          <dt className="text-neutral-500">confidence</dt>
                          <dd>{eu.confidence ?? "(none)"}</dd>
                          <dt className="text-neutral-500">location</dt>
                          <dd className="font-mono text-xs whitespace-pre-wrap">
                            {eu.location == null || Object.keys(eu.location).length === 0
                              ? "(none)"
                              : formatJson(eu.location)}
                          </dd>
                          <dt className="text-neutral-500">metadata</dt>
                          <dd className="text-xs text-neutral-700">
                            Not present on{" "}
                            <code className="font-mono">EvidenceUnitResponse</code> in the current
                            API schema (no field returned).
                          </dd>
                          <dt className="text-neutral-500">text</dt>
                          <dd>
                            <EvidenceTextBlock
                              text={eu.text}
                              unitId={eu.id}
                              showFull={!!fullTextRows[eu.id]}
                              onToggle={toggleFullText}
                            />
                          </dd>
                        </dl>

                        {expandedId === eu.id && (
                          <div className="mt-4 border-t border-neutral-200 pt-3">
                            <div className="text-xs font-medium text-neutral-600">
                              Detail from <code className="font-mono">GET /evidence-units/{eu.id}</code>
                            </div>
                            {expandedLoading && (
                              <p className="mt-2 text-sm text-neutral-600">Loading detail…</p>
                            )}
                            {expandedError && (
                              <p className="mt-2 whitespace-pre-wrap text-sm text-red-800">
                                {expandedError}
                              </p>
                            )}
                            {!expandedLoading && expandedDetail && expandedDetail.id === eu.id && (
                              <dl className="mt-3 grid gap-1 text-xs sm:grid-cols-[minmax(9rem,auto)_1fr]">
                                <dt className="text-neutral-500">evidence_unit_id</dt>
                                <dd className="font-mono">{expandedDetail.id}</dd>
                                <dt className="text-neutral-500">artifact_id</dt>
                                <dd className="font-mono">{expandedDetail.artifact_id}</dd>
                                <dt className="text-neutral-500">modality</dt>
                                <dd>{expandedDetail.modality}</dd>
                                <dt className="text-neutral-500">content_type</dt>
                                <dd>{expandedDetail.content_type}</dd>
                                <dt className="text-neutral-500">source_fidelity</dt>
                                <dd className="font-medium text-neutral-900">
                                  {expandedDetail.source_fidelity}
                                </dd>
                                <dt className="text-neutral-500">confidence</dt>
                                <dd>{expandedDetail.confidence ?? "(none)"}</dd>
                                <dt className="text-neutral-500">location</dt>
                                <dd className="whitespace-pre-wrap font-mono">
                                  {expandedDetail.location == null ||
                                  Object.keys(expandedDetail.location).length === 0
                                    ? "(none)"
                                    : formatJson(expandedDetail.location)}
                                </dd>
                                <dt className="text-neutral-500">metadata</dt>
                                <dd className="text-neutral-700">
                                  Not present on{" "}
                                  <code className="font-mono">EvidenceUnitResponse</code> in the
                                  current API schema.
                                </dd>
                                <dt className="text-neutral-500">text</dt>
                                <dd>
                                  <EvidenceTextBlock
                                    text={expandedDetail.text}
                                    unitId={`${eu.id}-detail`}
                                    showFull={!!fullTextRows[`${eu.id}-detail`]}
                                    onToggle={(id) => toggleFullText(id)}
                                  />
                                </dd>
                                <dt className="text-neutral-500">created_at</dt>
                                <dd className="font-mono">{expandedDetail.created_at}</dd>
                                <dt className="text-neutral-500">updated_at</dt>
                                <dd className="font-mono">{expandedDetail.updated_at}</dd>
                              </dl>
                            )}
                          </div>
                        )}
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
