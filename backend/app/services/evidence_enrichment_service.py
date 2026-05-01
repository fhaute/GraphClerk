"""Evidence enrichment pipeline for ingestion candidates (Phase 7).

Slice 7A introduces ``EvidenceEnrichmentService`` as a **no-op shell**: callers
receive the same candidate instances in order without mutation. Future slices may
attach routing metadata (for example language hints on ``metadata_json``) while
preserving evidence text and ``source_fidelity`` invariants.

Ownership:
    Extractors produce candidates; enrichment annotates; persistence layers own
    EvidenceUnit creation. This module performs **no** DB I/O, retrieval, LLM
    calls, or language detection.

Error semantics:
    Slice 7A does not raise enrichment-specific errors; invalid inputs are the
    caller's responsibility.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class EvidenceEnrichmentService:
    """Apply enrichment steps to evidence candidates before persistence.

    Slice 7A performs identity enrichment only: same objects, same order, no
    reads or writes of candidate fields (including ``text`` and
    ``source_fidelity``).

    Forbidden for this service (enforced by design in Slice 7A; expand only via
    scoped slices): database access, EvidenceUnit creation, extractors, LLMs,
    language detectors, retrieval, and silent mutation of source-bearing fields.
    """

    def enrich(self, candidates: Sequence[T]) -> list[T]:
        """Return ``candidates`` as a new list with identical elements and order.

        Accepts any ``Sequence`` (for example ``list`` or ``tuple``). Does not
        mutate elements or the passed-in mutable sequence.

        Args:
            candidates: Ordered sequence of upstream candidate objects.

        Returns:
            A new ``list`` referencing the same instances as ``candidates``.
        """
        return list(candidates)
