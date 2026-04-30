from __future__ import annotations

import re

from app.models.enums import Modality, SourceFidelity
from app.schemas.evidence_unit_candidate import EvidenceUnitCandidate


class MarkdownParser:
    """Parse Markdown into basic structural evidence candidates.

    Phase 2 supports headings, paragraphs, lists, fenced code blocks, blockquotes,
    and basic tables stored as `table_text`.
    """

    _heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    _ul_re = re.compile(r"^\s*[-*+]\s+(.*)$")
    _ol_re = re.compile(r"^\s*\d+\.\s+(.*)$")

    def parse(self, markdown: str) -> list[EvidenceUnitCandidate]:
        """Return evidence candidates with line numbers and section_path."""

        lines = markdown.splitlines()
        section_path: list[str] = []
        candidates: list[EvidenceUnitCandidate] = []
        block_index = 0

        i = 0
        in_code = False
        code_start = 0
        code_fence = ""
        code_lines: list[str] = []

        paragraph_start = 0
        paragraph_lines: list[str] = []

        def flush_paragraph(end_line: int) -> None:
            nonlocal paragraph_start, paragraph_lines, block_index
            if not paragraph_lines:
                return
            text = "\n".join(paragraph_lines).strip()
            if text:
                candidates.append(
                    EvidenceUnitCandidate(
                        modality=Modality.text,
                        content_type="paragraph",
                        text=text,
                        location={
                            "section_path": list(section_path),
                            "line_start": paragraph_start,
                            "line_end": end_line,
                            "block_index": block_index,
                        },
                        source_fidelity=SourceFidelity.verbatim,
                        confidence=1.0,
                    )
                )
                block_index += 1
            paragraph_lines = []
            paragraph_start = 0

        def flush_code(end_line: int) -> None:
            nonlocal code_start, code_lines, block_index
            text = "\n".join(code_lines)
            candidates.append(
                EvidenceUnitCandidate(
                    modality=Modality.text,
                    content_type="code_block",
                    text=text,
                    location={
                        "section_path": list(section_path),
                        "line_start": code_start,
                        "line_end": end_line,
                        "block_index": block_index,
                    },
                    source_fidelity=SourceFidelity.verbatim,
                    confidence=1.0,
                )
            )
            block_index += 1
            code_lines = []
            code_start = 0

        def add_simple(content_type: str, text: str, line_no: int) -> None:
            nonlocal block_index
            candidates.append(
                EvidenceUnitCandidate(
                    modality=Modality.text,
                    content_type=content_type,
                    text=text,
                    location={
                        "section_path": list(section_path),
                        "line_start": line_no,
                        "line_end": line_no,
                        "block_index": block_index,
                    },
                    source_fidelity=SourceFidelity.verbatim,
                    confidence=1.0,
                )
            )
            block_index += 1

        def is_table_line(line: str) -> bool:
            return "|" in line and line.strip().startswith("|") and line.strip().endswith("|")

        while i < len(lines):
            line_no = i + 1
            line = lines[i]

            # fenced code blocks
            if line.strip().startswith("```"):
                if not in_code:
                    flush_paragraph(line_no - 1)
                    in_code = True
                    code_start = line_no + 1  # content starts after fence
                    code_fence = line.strip()
                    code_lines = []
                    i += 1
                    continue
                else:
                    # close
                    in_code = False
                    flush_code(line_no - 1)
                    code_fence = ""
                    i += 1
                    continue

            if in_code:
                code_lines.append(line)
                i += 1
                continue

            # headings
            m = self._heading_re.match(line)
            if m:
                flush_paragraph(line_no - 1)
                level = len(m.group(1))
                heading_text = m.group(2).strip()
                # update section path
                section_path[:] = section_path[: level - 1]
                section_path.append(heading_text)
                add_simple("heading", heading_text, line_no)
                i += 1
                continue

            # tables (basic contiguous table lines)
            if is_table_line(line):
                flush_paragraph(line_no - 1)
                table_start = line_no
                table_lines = [line]
                j = i + 1
                while j < len(lines) and is_table_line(lines[j]):
                    table_lines.append(lines[j])
                    j += 1
                table_text = "\n".join(table_lines)
                candidates.append(
                    EvidenceUnitCandidate(
                        modality=Modality.text,
                        content_type="table_text",
                        text=table_text,
                        location={
                            "section_path": list(section_path),
                            "line_start": table_start,
                            "line_end": table_start + len(table_lines) - 1,
                            "block_index": block_index,
                        },
                        source_fidelity=SourceFidelity.verbatim,
                        confidence=1.0,
                    )
                )
                block_index += 1
                i = j
                continue

            # list items
            m = self._ul_re.match(line) or self._ol_re.match(line)
            if m:
                flush_paragraph(line_no - 1)
                add_simple("list_item", m.group(1).strip(), line_no)
                i += 1
                continue

            # blockquote
            if line.strip().startswith(">"):
                flush_paragraph(line_no - 1)
                text = line.lstrip()[1:].lstrip()
                add_simple("blockquote", text, line_no)
                i += 1
                continue

            # blank lines end paragraphs
            if line.strip() == "":
                flush_paragraph(line_no - 1)
                i += 1
                continue

            # paragraph accumulation
            if not paragraph_lines:
                paragraph_start = line_no
            paragraph_lines.append(line)
            i += 1

        flush_paragraph(len(lines))

        # Unclosed code fence is treated as explicit parse error in Phase 2.
        if in_code:
            raise ValueError(f"Unclosed code fence starting at line {code_start - 1}: {code_fence!r}")

        return candidates

