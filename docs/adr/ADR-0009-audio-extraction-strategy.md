# ADR-0009: Audio extraction strategy (Phase 5 Slice G shell)

## Status

Accepted.

## Context

Audio ingestion requires at least **two** concerns: **container validation** (real media bytes) and **transcription** (speech-to-text for `EvidenceUnitCandidate` text). Phase 5 must stay **local-first**, avoid **heavy ASR stacks** without explicit approval, and **never** return success with no evidence when transcription is not implemented.

## Decision

- **Slice G** adds only:
  - Optional **`audio`** extra with **mutagen** for **probe/validation** of uploaded audio bytes.
  - An **`AudioExtractor`** that loads persisted bytes via **`RawSourceStore.read_persisted_bytes`**, opens with **mutagen.File**, and then raises **`ExtractorUnavailableError`** with an explicit message that **transcription is not configured** (until a later approved slice).
- **No** faster-whisper, whisper.cpp, ffmpeg, pydub, Torch, model downloads, or cloud transcription in Slice G.
- **No** `EvidenceUnitCandidate` emission in Slice G, so **no** `source_fidelity` on audio evidence yet.
- **Reserved** future `content_type`: **`audio_transcript_segment`**. Future ASR output should use **`SourceFidelity.extracted`**.

## Consequences

- **Routing:** Multipart audio uploads resolve to `artifact_type=audio` / `Modality.audio`; registry registers **`AudioExtractor`** when mutagen is installed, or a **placeholder** (**503**) when mutagen is missing.
- **User-visible behavior:** With mutagen installed, **`POST /artifacts`** for valid audio returns **503** after validation with a clear “transcription not configured” message — **not** 200 with zero evidence.
- **Corrupt / unsupported bytes:** **`AudioExtractionError`** (**HTTP 400**), not **`ExtractorUnavailableError`**.

## Alternatives considered

- **Ship ASR in Slice G:** Rejected for this slice to limit dependency and operational surface.
- **Return empty candidate list:** Rejected — explicit **`ExtractorUnavailableError`** after validation preserves honest semantics.
