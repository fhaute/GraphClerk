"""HTTP request schemas for retrieval (Phase 4 base request + Phase 7 actor context).

Slice 7G: validated request metadata only. Slice 7H: echoed on ``RetrievalPacket`` via
``PacketActorContextRecording`` — recording-only; still not used for retrieval routing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

MAX_ACTOR_STRING_FIELD_LEN = 512


class ActorContext(BaseModel):
    """Optional caller-supplied hints. Not used for route or evidence selection in Slice 7G."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    actor_type: str | None = None
    role: str | None = None
    expertise_level: str | None = None
    preferred_language: str | None = None
    purpose: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator(
        "actor_id",
        "actor_type",
        "role",
        "expertise_level",
        "preferred_language",
        "purpose",
        mode="before",
    )
    @classmethod
    def _optional_nonempty_bounded_str(cls, v: Any) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("must be a string or null")
        stripped = v.strip()
        if stripped == "":
            raise ValueError("must not be empty or whitespace-only")
        if len(stripped) > MAX_ACTOR_STRING_FIELD_LEN:
            raise ValueError(f"must be at most {MAX_ACTOR_STRING_FIELD_LEN} characters")
        return stripped

    @field_validator("metadata", mode="before")
    @classmethod
    def _metadata_must_be_object(cls, v: Any) -> dict[str, Any] | None:
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("metadata must be an object")
        return v
