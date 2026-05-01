import { useCallback, useState, type FormEvent } from "react";
import { ApiError } from "../api/client";
import { postRetrieve } from "../api/retrieval";
import type {
  ActorContext,
  RetrievalPacket,
  RetrieveRequestPayload,
} from "../types/retrievalPacket";
import { RetrievalPacketPanel } from "./RetrievalPacketPanel";

type SubmitState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ok"; packet: RetrievalPacket };

const DEFAULT_MAX_EVIDENCE = 8;
const DEFAULT_MAX_DEPTH = 1;

function parseBoundedInt(raw: string, fallback: number, min: number, max: number): number {
  const n = Number.parseInt(raw, 10);
  if (Number.isNaN(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

/** Empty string → omit. Non-empty must be valid JSON object (not array, not null). */
function parseActorContextJson(raw: string): { ok: true; value: ActorContext } | { ok: false; message: string } {
  const trimmed = raw.trim();
  if (!trimmed) return { ok: true, value: {} };

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed) as unknown;
  } catch {
    return { ok: false, message: "Advanced context: invalid JSON — fix the JSON or clear the field before retrieving." };
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return {
      ok: false,
      message: "Advanced context: enter a JSON object only (not an array, string, or primitive).",
    };
  }
  return { ok: true, value: parsed as ActorContext };
}

export function QueryPlayground() {
  const [question, setQuestion] = useState("");
  const [maxEvidenceUnits, setMaxEvidenceUnits] = useState(String(DEFAULT_MAX_EVIDENCE));
  const [maxGraphDepth, setMaxGraphDepth] = useState(String(DEFAULT_MAX_DEPTH));
  const [includeAlternatives, setIncludeAlternatives] = useState(true);
  const [actorContextJson, setActorContextJson] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>({ kind: "idle" });

  const onSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      const q = question.trim();
      if (!q) {
        setSubmitState({
          kind: "error",
          message: "Enter a non-empty question before retrieving.",
        });
        return;
      }

      const maxEu = parseBoundedInt(maxEvidenceUnits, DEFAULT_MAX_EVIDENCE, 1, 64);
      const maxDepth = parseBoundedInt(maxGraphDepth, DEFAULT_MAX_DEPTH, 0, 5);

      const actorParsed = parseActorContextJson(actorContextJson);
      if (!actorParsed.ok) {
        setSubmitState({ kind: "error", message: actorParsed.message });
        return;
      }

      setSubmitState({ kind: "loading" });
      try {
        const payload: RetrieveRequestPayload = {
          question: q,
          options: {
            max_evidence_units: maxEu,
            max_graph_depth: maxDepth,
            include_alternatives: includeAlternatives,
          },
        };
        const trimmedActor = actorContextJson.trim();
        if (trimmedActor) {
          payload.actor_context = actorParsed.value;
        }
        const packet = await postRetrieve(payload);
        setSubmitState({ kind: "ok", packet });
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          setSubmitState({
            kind: "error",
            message: err.message,
          });
        } else if (err instanceof Error) {
          setSubmitState({ kind: "error", message: err.message });
        } else {
          setSubmitState({ kind: "error", message: String(err) });
        }
      }
    },
    [question, maxEvidenceUnits, maxGraphDepth, includeAlternatives, actorContextJson],
  );

  return (
    <section className="rounded-md border border-neutral-200 bg-white p-4 shadow-sm">
      <h2 className="text-sm font-medium text-neutral-700">Query playground</h2>
      <p className="mt-1 text-xs text-neutral-500">
        Submit a natural-language question to <code className="font-mono">POST /retrieve</code>.
        The UI shows the returned RetrievalPacket only — no mocked retrieval data.
      </p>

      <form className="mt-4 space-y-4" onSubmit={onSubmit}>
        <div>
          <label htmlFor="gc-question" className="block text-xs font-medium text-neutral-600">
            Question
          </label>
          <textarea
            id="gc-question"
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm text-neutral-900 shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
            rows={4}
            value={question}
            onChange={(ev) => setQuestion(ev.target.value)}
            placeholder="Ask something about your ingested corpus…"
            disabled={submitState.kind === "loading"}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="gc-max-eu" className="block text-xs font-medium text-neutral-600">
              max_evidence_units (1–64)
            </label>
            <input
              id="gc-max-eu"
              type="number"
              min={1}
              max={64}
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
              value={maxEvidenceUnits}
              onChange={(ev) => setMaxEvidenceUnits(ev.target.value)}
              disabled={submitState.kind === "loading"}
            />
          </div>
          <div>
            <label htmlFor="gc-max-depth" className="block text-xs font-medium text-neutral-600">
              max_graph_depth (0–5)
            </label>
            <input
              id="gc-max-depth"
              type="number"
              min={0}
              max={5}
              className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 text-sm shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
              value={maxGraphDepth}
              onChange={(ev) => setMaxGraphDepth(ev.target.value)}
              disabled={submitState.kind === "loading"}
            />
          </div>
          <div className="flex items-end pb-2">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-700">
              <input
                type="checkbox"
                checked={includeAlternatives}
                onChange={(ev) => setIncludeAlternatives(ev.target.checked)}
                disabled={submitState.kind === "loading"}
              />
              include_alternatives
            </label>
          </div>
        </div>

        <details className="rounded border border-neutral-200 bg-neutral-50/80 p-3 text-sm">
          <summary className="cursor-pointer select-none font-medium text-neutral-700">
            Advanced context (optional)
          </summary>
          <p className="mt-2 text-xs text-neutral-600">
            Optional JSON object for <code className="font-mono">actor_context</code>. Recorded on the packet only.
            Does not change retrieval ranking or evidence selection in the current baseline. Leave empty to omit{" "}
            <code className="font-mono">actor_context</code>.
          </p>
          <label htmlFor="gc-actor-context" className="mt-2 block text-xs font-medium text-neutral-600">
            actor_context (JSON object)
          </label>
          <textarea
            id="gc-actor-context"
            className="mt-1 w-full rounded border border-neutral-300 bg-white px-3 py-2 font-mono text-xs text-neutral-900 shadow-sm focus:border-neutral-500 focus:outline-none focus:ring-1 focus:ring-neutral-400"
            rows={5}
            value={actorContextJson}
            onChange={(ev) => setActorContextJson(ev.target.value)}
            placeholder='{}'
            spellCheck={false}
            disabled={submitState.kind === "loading"}
          />
        </details>

        <button
          type="submit"
          className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
          disabled={submitState.kind === "loading"}
        >
          {submitState.kind === "loading" ? "Retrieving…" : "Retrieve"}
        </button>
      </form>

      <div className="mt-6">
        {submitState.kind === "loading" && (
          <p className="text-sm text-neutral-600">Loading RetrievalPacket…</p>
        )}
        {submitState.kind === "error" && (
          <p className="whitespace-pre-wrap rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            {submitState.message}
          </p>
        )}
        {submitState.kind === "ok" && <RetrievalPacketPanel packet={submitState.packet} />}
      </div>
    </section>
  );
}
