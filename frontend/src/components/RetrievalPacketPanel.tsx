import type { ReactNode } from "react";
import type { RetrievalPacket } from "../types/retrievalPacket";

const TEXT_PREVIEW_MAX = 400;

function previewText(text: string | null | undefined): string {
  if (text == null || text === "") return "(no text)";
  if (text.length <= TEXT_PREVIEW_MAX) return text;
  return `${text.slice(0, TEXT_PREVIEW_MAX)}…`;
}

function formatLocation(loc: Record<string, unknown> | null | undefined): string {
  if (loc == null || Object.keys(loc).length === 0) return "(none)";
  try {
    return JSON.stringify(loc, null, 2);
  } catch {
    return String(loc);
  }
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h3 className="mt-6 border-b border-neutral-200 pb-1 text-sm font-semibold text-neutral-800 first:mt-0">
      {children}
    </h3>
  );
}

function Mono({ children }: { children: ReactNode }) {
  return <span className="font-mono text-xs text-neutral-800">{children}</span>;
}

function fmtOptionalNumber(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return String(n);
}

export function RetrievalPacketPanel({ packet }: { packet: RetrievalPacket }) {
  const json = JSON.stringify(packet, null, 2);
  const noEvidence = packet.evidence_units.length === 0;

  return (
    <div className="space-y-4">
      {noEvidence && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          No evidence units were returned in this packet. The retrieval trace below still
          reflects indexes, graph paths, intent, and budgeting decisions.
        </div>
      )}

      <div className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-700">Retrieval trace (readable)</h2>

        <SectionTitle>Question</SectionTitle>
        <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-800">{packet.question}</p>

        <SectionTitle>Interpreted intent</SectionTitle>
        <dl className="mt-2 grid gap-1 text-sm sm:grid-cols-[minmax(8rem,auto)_1fr]">
          <dt className="text-neutral-500">intent_type</dt>
          <dd>
            <Mono>{packet.interpreted_intent.intent_type}</Mono>
          </dd>
          <dt className="text-neutral-500">confidence</dt>
          <dd>
            <Mono>{packet.interpreted_intent.confidence}</Mono>
          </dd>
          <dt className="text-neutral-500">notes</dt>
          <dd className="text-neutral-800">
            {packet.interpreted_intent.notes.length === 0
              ? "(none)"
              : packet.interpreted_intent.notes.join(" · ")}
          </dd>
        </dl>

        <SectionTitle>Selected indexes</SectionTitle>
        {packet.selected_indexes.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-600">(none)</p>
        ) : (
          <ul className="mt-2 space-y-3">
            {packet.selected_indexes.map((idx) => (
              <li
                key={idx.semantic_index_id}
                className="rounded border border-neutral-100 bg-neutral-50 p-3 text-sm"
              >
                <div className="font-mono text-xs text-neutral-900">{idx.semantic_index_id}</div>
                <div className="mt-1 text-neutral-800">{idx.meaning}</div>
                <div className="mt-1 text-xs text-neutral-600">
                  score: <Mono>{idx.score}</Mono> · {idx.selection_reason}
                </div>
              </li>
            ))}
          </ul>
        )}

        <SectionTitle>Graph paths</SectionTitle>
        {packet.graph_paths.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-600">(none)</p>
        ) : (
          <ul className="mt-2 space-y-3">
            {packet.graph_paths.map((gp, i) => (
              <li
                key={`${gp.start_node_id}-${i}`}
                className="rounded border border-neutral-100 bg-neutral-50 p-3 text-sm"
              >
                <div className="text-xs text-neutral-600">
                  start_node_id: <Mono>{gp.start_node_id}</Mono> · depth:{" "}
                  <Mono>{gp.depth}</Mono>
                </div>
                <div className="mt-2 text-xs">
                  <span className="text-neutral-500">nodes </span>
                  <Mono>{gp.nodes.length ? gp.nodes.join(", ") : "(empty)"}</Mono>
                </div>
                <div className="mt-1 text-xs">
                  <span className="text-neutral-500">edges </span>
                  <Mono>{gp.edges.length ? gp.edges.join(", ") : "(empty)"}</Mono>
                </div>
              </li>
            ))}
          </ul>
        )}

        <SectionTitle>Evidence units</SectionTitle>
        {packet.evidence_units.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-600">(none)</p>
        ) : (
          <ul className="mt-2 space-y-4">
            {packet.evidence_units.map((eu) => (
              <li
                key={eu.evidence_unit_id}
                className="rounded border border-neutral-200 bg-white p-3 text-sm shadow-sm"
              >
                <dl className="grid gap-1 sm:grid-cols-[minmax(10rem,auto)_1fr]">
                  <dt className="text-neutral-500">evidence_unit_id</dt>
                  <dd className="font-mono text-xs">{eu.evidence_unit_id}</dd>
                  <dt className="text-neutral-500">artifact_id</dt>
                  <dd className="font-mono text-xs">{eu.artifact_id}</dd>
                  <dt className="text-neutral-500">modality</dt>
                  <dd>{eu.modality}</dd>
                  <dt className="text-neutral-500">content_type</dt>
                  <dd>{eu.content_type}</dd>
                  <dt className="text-neutral-500">source_fidelity</dt>
                  <dd>{eu.source_fidelity}</dd>
                  <dt className="text-neutral-500">location</dt>
                  <dd className="whitespace-pre-wrap font-mono text-xs text-neutral-800">
                    {formatLocation(eu.location ?? undefined)}
                  </dd>
                  <dt className="text-neutral-500">confidence</dt>
                  <dd>{eu.confidence ?? "(none)"}</dd>
                  <dt className="text-neutral-500">selection_reason</dt>
                  <dd className="text-neutral-700">{eu.selection_reason}</dd>
                  <dt className="text-neutral-500">text preview</dt>
                  <dd className="whitespace-pre-wrap text-neutral-800">{previewText(eu.text)}</dd>
                </dl>
              </li>
            ))}
          </ul>
        )}

        <SectionTitle>Alternative interpretations</SectionTitle>
        {packet.alternative_interpretations.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-600">(none)</p>
        ) : (
          <ul className="mt-2 space-y-3">
            {packet.alternative_interpretations.map((alt, i) => (
              <li key={i} className="rounded border border-neutral-100 bg-neutral-50 p-3 text-sm">
                <div className="font-medium text-neutral-800">{alt.if_user_meant}</div>
                <div className="mt-1 text-xs text-neutral-600">{alt.reason}</div>
                <div className="mt-2 font-mono text-xs text-neutral-800">
                  indexes:{" "}
                  {alt.suggested_semantic_indexes.length
                    ? alt.suggested_semantic_indexes.join(", ")
                    : "(none)"}
                </div>
              </li>
            ))}
          </ul>
        )}

        <SectionTitle>Context budget</SectionTitle>
        <dl className="mt-2 grid gap-1 text-sm sm:grid-cols-[minmax(12rem,auto)_1fr]">
          <dt className="text-neutral-500">max_evidence_units</dt>
          <dd>{packet.context_budget.max_evidence_units}</dd>
          <dt className="text-neutral-500">selected_evidence_units</dt>
          <dd>{packet.context_budget.selected_evidence_units}</dd>
          <dt className="text-neutral-500">pruned_evidence_units</dt>
          <dd>{packet.context_budget.pruned_evidence_units}</dd>
          <dt className="text-neutral-500">pruning_reasons</dt>
          <dd>
            {packet.context_budget.pruning_reasons.length === 0
              ? "(none)"
              : packet.context_budget.pruning_reasons.join(" · ")}
          </dd>
          <dt className="text-neutral-500">max_graph_paths</dt>
          <dd>{packet.context_budget.max_graph_paths ?? "(default)"}</dd>
          <dt className="text-neutral-500">max_selected_indexes</dt>
          <dd>{packet.context_budget.max_selected_indexes ?? "(default)"}</dd>
        </dl>

        <SectionTitle>Language context (metadata)</SectionTitle>
        <p className="mt-2 text-xs text-neutral-600">
          Language context is metadata aggregated from selected evidence metadata. It is not
          translation, not personalization, and not evidence by itself.
        </p>
        {packet.language_context == null ? (
          <p className="mt-2 text-sm text-neutral-600">No language context recorded.</p>
        ) : (
          <div className="mt-2 space-y-3 text-sm">
            <dl className="grid gap-1 sm:grid-cols-[minmax(10rem,auto)_1fr]">
              <dt className="text-neutral-500">source</dt>
              <dd>
                <Mono>{packet.language_context.source}</Mono>
              </dd>
              <dt className="text-neutral-500">primary_evidence_language</dt>
              <dd>
                {packet.language_context.primary_evidence_language ?? "—"}
              </dd>
              <dt className="text-neutral-500">distinct_evidence_language_count</dt>
              <dd>
                <Mono>{packet.language_context.distinct_evidence_language_count}</Mono>
              </dd>
              <dt className="text-neutral-500">evidence_units_without_language_metadata_count</dt>
              <dd>
                <Mono>{packet.language_context.evidence_units_without_language_metadata_count}</Mono>
              </dd>
              <dt className="text-neutral-500">query_language</dt>
              <dd>{packet.language_context.query_language ?? "—"}</dd>
              <dt className="text-neutral-500">version</dt>
              <dd>
                <Mono>{packet.language_context.version}</Mono>
              </dd>
            </dl>
            <div>
              <div className="text-xs font-medium text-neutral-600">Evidence languages</div>
              {packet.language_context.evidence_languages.length === 0 ? (
                <p className="mt-1 text-sm text-neutral-600">(none)</p>
              ) : (
                <div className="mt-2 overflow-x-auto rounded border border-neutral-200">
                  <table className="w-full min-w-[28rem] border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-neutral-200 bg-neutral-50 text-left text-neutral-600">
                        <th className="px-2 py-1.5 font-medium">language</th>
                        <th className="px-2 py-1.5 font-medium">units</th>
                        <th className="px-2 py-1.5 font-medium">avg conf.</th>
                        <th className="px-2 py-1.5 font-medium">min</th>
                        <th className="px-2 py-1.5 font-medium">max</th>
                      </tr>
                    </thead>
                    <tbody>
                      {packet.language_context.evidence_languages.map((row, i) => (
                        <tr
                          key={`${row.language}-${i}`}
                          className="border-b border-neutral-100 last:border-0"
                        >
                          <td className="px-2 py-1.5 font-mono text-neutral-900">{row.language}</td>
                          <td className="px-2 py-1.5 font-mono">{row.evidence_unit_count}</td>
                          <td className="px-2 py-1.5 font-mono">
                            {fmtOptionalNumber(row.average_confidence ?? undefined)}
                          </td>
                          <td className="px-2 py-1.5 font-mono">
                            {fmtOptionalNumber(row.min_confidence ?? undefined)}
                          </td>
                          <td className="px-2 py-1.5 font-mono">
                            {fmtOptionalNumber(row.max_confidence ?? undefined)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            {packet.language_context.warnings.length > 0 && (
              <div>
                <div className="text-xs font-medium text-neutral-600">Warnings</div>
                <ul className="mt-1 list-disc space-y-1 border border-amber-200 bg-amber-50 px-5 py-2 text-xs text-amber-950">
                  {packet.language_context.warnings.map((w, i) => (
                    <li key={i} className="whitespace-pre-wrap">
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <SectionTitle>Actor context (recording)</SectionTitle>
        <p className="mt-2 text-xs text-neutral-600">
          Actor context is recording-only on the packet and does not influence retrieval in the
          current baseline (no ranking or evidence selection changes from this field).
        </p>
        {packet.actor_context == null ? (
          <p className="mt-2 text-sm text-neutral-600">No actor context recording.</p>
        ) : (
          <div className="mt-2 space-y-3 text-sm">
            <dl className="grid gap-1 sm:grid-cols-[minmax(10rem,auto)_1fr]">
              <dt className="text-neutral-500">used</dt>
              <dd>{packet.actor_context.used ? "yes" : "no"}</dd>
              <dt className="text-neutral-500">source</dt>
              <dd>
                <Mono>{packet.actor_context.source}</Mono>
              </dd>
              <dt className="text-neutral-500">influence</dt>
              <dd>
                <Mono>{packet.actor_context.influence}</Mono>
              </dd>
            </dl>
            {packet.actor_context.warnings.length > 0 && (
              <div>
                <div className="text-xs font-medium text-neutral-600">Warnings</div>
                <ul className="mt-1 list-disc space-y-1 border border-amber-200 bg-amber-50 px-5 py-2 text-xs text-amber-950">
                  {packet.actor_context.warnings.map((w, i) => (
                    <li key={i} className="whitespace-pre-wrap">
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {packet.actor_context.recorded_context == null ? (
              <p className="text-sm text-neutral-600">(no recorded_context on packet)</p>
            ) : (
              <div>
                <div className="text-xs font-medium text-neutral-600">recorded_context</div>
                <dl className="mt-1 grid gap-1 rounded border border-neutral-100 bg-neutral-50 p-3 sm:grid-cols-[minmax(10rem,auto)_1fr]">
                  <dt className="text-neutral-500">actor_id</dt>
                  <dd className="font-mono text-xs">
                    {packet.actor_context.recorded_context.actor_id ?? "—"}
                  </dd>
                  <dt className="text-neutral-500">actor_type</dt>
                  <dd className="font-mono text-xs">
                    {packet.actor_context.recorded_context.actor_type ?? "—"}
                  </dd>
                  <dt className="text-neutral-500">role</dt>
                  <dd>{packet.actor_context.recorded_context.role ?? "—"}</dd>
                  <dt className="text-neutral-500">expertise_level</dt>
                  <dd>{packet.actor_context.recorded_context.expertise_level ?? "—"}</dd>
                  <dt className="text-neutral-500">preferred_language</dt>
                  <dd className="font-mono text-xs">
                    {packet.actor_context.recorded_context.preferred_language ?? "—"}
                  </dd>
                  <dt className="text-neutral-500">purpose</dt>
                  <dd className="whitespace-pre-wrap">
                    {packet.actor_context.recorded_context.purpose ?? "—"}
                  </dd>
                  <dt className="text-neutral-500">metadata</dt>
                  <dd className="whitespace-pre-wrap font-mono text-xs text-neutral-800">
                    {packet.actor_context.recorded_context.metadata == null ||
                    Object.keys(packet.actor_context.recorded_context.metadata).length === 0
                      ? "—"
                      : JSON.stringify(packet.actor_context.recorded_context.metadata, null, 2)}
                  </dd>
                </dl>
              </div>
            )}
          </div>
        )}

        <SectionTitle>Warnings</SectionTitle>
        {packet.warnings.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-600">(none)</p>
        ) : (
          <ul className="mt-2 list-disc space-y-1 border border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-950">
            {packet.warnings.map((w, i) => (
              <li key={i} className="whitespace-pre-wrap">
                {w}
              </li>
            ))}
          </ul>
        )}

        <SectionTitle>Confidence &amp; answer mode</SectionTitle>
        <dl className="mt-2 grid gap-1 text-sm sm:grid-cols-[minmax(8rem,auto)_1fr]">
          <dt className="text-neutral-500">confidence</dt>
          <dd>
            <Mono>{packet.confidence}</Mono>
          </dd>
          <dt className="text-neutral-500">answer_mode</dt>
          <dd>
            <Mono>{packet.answer_mode}</Mono>
          </dd>
        </dl>

        <div className="mt-6 rounded-md border border-neutral-300 bg-neutral-100 px-3 py-3 text-sm text-neutral-800">
          <strong className="font-medium">Answer synthesis</strong>
          <p className="mt-1">
            Answer synthesis is not implemented in this backend. RetrievalPacket trace is the
            current output.
          </p>
        </div>
      </div>

      <div className="rounded-md border border-neutral-200 bg-neutral-950 p-4 shadow-sm">
        <h2 className="text-sm font-medium text-neutral-300">Raw JSON</h2>
        <pre className="mt-3 max-h-[min(70vh,640px)] overflow-auto whitespace-pre-wrap break-words text-xs text-neutral-100">
          {json}
        </pre>
      </div>
    </div>
  );
}
