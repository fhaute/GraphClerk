from __future__ import annotations

from enum import StrEnum


class SourceFidelity(StrEnum):
    """How closely an EvidenceUnit matches the original artifact content."""

    verbatim = "verbatim"
    extracted = "extracted"
    derived = "derived"
    computed = "computed"


class Modality(StrEnum):
    """Modality of the source or evidence representation."""

    text = "text"
    pdf = "pdf"
    slide = "slide"
    image = "image"
    audio = "audio"
    video = "video"
    code = "code"
    web = "web"


class GraphNodeType(StrEnum):
    """Type of GraphNode (persistence shape only in Phase 1)."""

    concept = "concept"
    claim = "claim"
    entity = "entity"
    artifact = "artifact"
    source = "source"
    technique = "technique"
    problem = "problem"
    decision = "decision"
    metric = "metric"
    modality = "modality"


class GraphRelationType(StrEnum):
    """Typed relation between two graph nodes."""

    supports = "supports"
    explains = "explains"
    improves = "improves"
    causes = "causes"
    reduces = "reduces"
    contradicts = "contradicts"
    depends_on = "depends_on"
    part_of = "part_of"
    related_to = "related_to"
    mentions = "mentions"
    represents = "represents"
    has_source = "has_source"

