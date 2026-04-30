from __future__ import annotations

from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate


class PlainTextParser:
    """Parse plain text into paragraph/raw_text_block evidence candidates."""

    def parse(self, text: str) -> list[EvidenceUnitCandidate]:
        """Return evidence candidates preserving line boundaries."""

        if text == "":
            return []

        lines = text.splitlines()
        candidates: list[EvidenceUnitCandidate] = []

        block_lines: list[str] = []
        block_start_line: int | None = None
        block_index = 0

        def flush_block(end_line: int) -> None:
            nonlocal block_lines, block_start_line, block_index
            if block_start_line is None:
                return
            block_text = "\n".join(block_lines).strip("\n")
            if block_text.strip() == "":
                block_lines = []
                block_start_line = None
                return

            candidates.append(
                EvidenceUnitCandidate(
                    modality=Modality.text,
                    content_type="paragraph",
                    text=block_text,
                    location={
                        "line_start": block_start_line,
                        "line_end": end_line,
                        "block_index": block_index,
                        "section_path": [],
                    },
                    source_fidelity=SourceFidelity.verbatim,
                    confidence=1.0,
                )
            )
            block_index += 1
            block_lines = []
            block_start_line = None

        for i, line in enumerate(lines, start=1):
            if line.strip() == "":
                if block_lines:
                    flush_block(i - 1)
                continue

            if block_start_line is None:
                block_start_line = i
            block_lines.append(line)

        if block_lines and block_start_line is not None:
            flush_block(len(lines))

        return candidates

