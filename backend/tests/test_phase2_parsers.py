from __future__ import annotations

import pytest

from app.services.parsers.markdown_parser import MarkdownParser
from app.services.parsers.plain_text_parser import PlainTextParser


def test_plain_text_parser_creates_paragraphs_with_line_metadata() -> None:
    parser = PlainTextParser()
    text = "Hello\n\nWorld\nLine2\n"
    blocks = parser.parse(text)

    assert len(blocks) == 2
    assert blocks[0].content_type == "paragraph"
    assert blocks[0].text == "Hello"
    assert blocks[0].location["line_start"] == 1
    assert blocks[0].location["line_end"] == 1

    assert blocks[1].text == "World\nLine2"
    assert blocks[1].location["line_start"] == 3
    assert blocks[1].location["line_end"] == 4


def test_markdown_parser_captures_headings_lists_and_code_blocks() -> None:
    parser = MarkdownParser()
    md = """# H1

Para

- item

```python
print('x')
```
"""
    blocks = parser.parse(md)
    content_types = [b.content_type for b in blocks]

    assert "heading" in content_types
    assert "paragraph" in content_types
    assert "list_item" in content_types
    assert "code_block" in content_types


def test_markdown_unclosed_code_fence_fails_clearly() -> None:
    parser = MarkdownParser()
    md = """```\nno close\n"""
    with pytest.raises(ValueError):
        parser.parse(md)

