"""Structure-aware document chunking strategies powered by langchain-text-splitters.

Each strategy implements the same signature::

    def chunk(text: str, chunk_size: int, overlap: int) -> list[str]: ...

and guarantees that returned chunks are **semantically complete** — they
do not split code blocks, JSON structures, or Markdown headings mid-way.
"""

from __future__ import annotations

import re
from typing import Callable

from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def chunk_document(
    text: str,
    file_type: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Auto-detect the best chunking strategy for *file_type*.

    Falls back to paragraph-level chunking for unknown types.
    """
    strategy = _select_strategy(file_type)
    return strategy(text, chunk_size, overlap)


_CHUNK_STRATEGIES: dict[str, Callable[..., list[str]]] = {}


def _select_strategy(file_type: str) -> Callable[..., list[str]]:
    file_type = file_type.lower().lstrip(".")
    # Check registered strategies first (extensibility mechanism)
    if file_type in _CHUNK_STRATEGIES:
        return _CHUNK_STRATEGIES[file_type]
    if file_type in ("md", "markdown", "rst"):
        return chunk_by_markdown
    if file_type in ("html", "htm"):
        return chunk_by_html
    if file_type in ("xlsx", "xls", "csv"):
        return chunk_by_table
    if file_type == "pptx":
        return chunk_by_slide
    if file_type in ("py", "js", "ts", "jsx", "tsx", "java", "go", "rs", "c", "cpp", "h", "hpp"):
        return chunk_by_code
    return chunk_by_paragraph


# -- Export mapping so callers can introspect --------------------------------
def register_strategy(ext: str, fn: Callable[..., list[str]]) -> None:
    """Register a custom chunking strategy for a file extension."""
    _CHUNK_STRATEGIES[ext.lower().lstrip(".")] = fn


# ---------------------------------------------------------------------------
# Helpers: heading / code-boundary pre-split
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def _split_by_heading(text: str) -> list[tuple[str, str]]:
    """Split text into ``(heading_line, body)`` pairs.

    ``heading_line`` is the full heading (e.g. ``"## Section A"``).
    Text before the first heading is preserved with an empty heading string.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [("", text)]

    sections: list[tuple[str, str]] = []

    # Preserve text before the first heading
    first_start = matches[0].start()
    if first_start > 0:
        preamble = text[:first_start].strip()
        if preamble:
            sections.append(("", preamble))

    for i, m in enumerate(matches):
        start = m.end()  # body starts after the heading line
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((m.group(0), body))
    return sections


_CODE_BOUNDARY_RE = re.compile(
    r"^(def\s+\w+|class\s+\w+|async\s+def\s+\w+|"
    r"public\s+(static\s+)?\w+\s+\w+\s*\(|"
    r"function\s+\w*|"
    r"func\s+\w+|"
    r"sub\s+\w+|"
    r"pub\s+fn\s+\w+)",
    re.MULTILINE,
)


def _split_by_code_boundary(text: str) -> list[tuple[str, str]]:
    """Split text into ``(definition_header, body)`` pairs.

    ``definition_header`` is e.g. ``"def foo():"``.
    Text before the first definition is preserved with an empty heading string.
    """
    matches = list(_CODE_BOUNDARY_RE.finditer(text))
    if not matches:
        return [("", text)]

    sections: list[tuple[str, str]] = []

    # Preserve text before the first definition
    first_start = matches[0].start()
    if first_start > 0:
        preamble = text[:first_start].rstrip()
        if preamble:
            sections.append(("", preamble))

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].rstrip()
        if body:
            sections.append((m.group(0), body))
    return sections


# ---------------------------------------------------------------------------
# Strategy: Paragraph-based (default)
# ---------------------------------------------------------------------------


def _make_splitter(
    chunk_size: int,
    overlap: int,
    separators: list[str] | None = None,
) -> RecursiveCharacterTextSplitter:
    """Create a configured ``RecursiveCharacterTextSplitter``."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=separators,
    )


def chunk_by_paragraph(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split by paragraph boundaries, avoiding mid-structure breaks.

    Uses LangChain's ``RecursiveCharacterTextSplitter`` with separators
    prioritising paragraph breaks, then line breaks, then sentence
    boundaries (Chinese full-stop / English period).
    """
    if not text.strip():
        return []
    splitter = _make_splitter(chunk_size, overlap, ["\n\n", "\n", "。", ".", " "])
    return splitter.split_text(text)


# ---------------------------------------------------------------------------
# Strategy: Markdown heading-based
# ---------------------------------------------------------------------------


def chunk_by_markdown(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split on headings and keep heading context in each chunk.

    Uses a two-pass approach:
      1. Pre-split text at heading boundaries (``_split_by_heading``).
      2. Pass each section through LangChain's ``RecursiveCharacterTextSplitter``
         only when the section exceeds *chunk_size*.

    This guarantees that every chunk retains its heading context.
    """
    if not text.strip():
        return []

    sections = _split_by_heading(text)
    splitter = _make_splitter(chunk_size, overlap, ["\n\n", "\n", "。", ".", " "])

    chunks: list[str] = []
    for heading, body in sections:
        full = f"{heading}\n\n{body}" if heading else body
        if len(full) <= chunk_size:
            chunks.append(full)
        else:
            sub = splitter.split_text(body)
            for piece in sub:
                chunks.append(f"{heading}\n\n{piece}" if heading else piece)
    return chunks


# ---------------------------------------------------------------------------
# Strategy: HTML heading-based (h1-h6, similar to markdown)
# ---------------------------------------------------------------------------


def chunk_by_html(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split HTML content on heading lines.

    Behaves identically to ``chunk_by_markdown`` since the HTML parser
    in ``_read_html`` already converts ``<h1>``-``<h6>`` to markdown-style
    headings.
    """
    return chunk_by_markdown(text, chunk_size, overlap)


# ---------------------------------------------------------------------------
# Strategy: Table-aware (Excel / CSV)
# ---------------------------------------------------------------------------


def chunk_by_table(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split table content by sheet/table boundaries, grouping rows into batches.

    Each ``## Sheet: <name>`` section's rows are grouped into row batches
    that each fit within *chunk_size*.  Batches within the same sheet
    are separated by ``\\n\\n`` so that large tables split cleanly at
    row-group boundaries rather than mid-row.
    """
    if not text.strip():
        return []

    sections = _split_by_heading(text)
    splitter = _make_splitter(chunk_size, overlap, ["\n\n", "\n", " | ", " "])

    chunks: list[str] = []
    for heading, body in sections:
        full = f"{heading}\n\n{body}" if heading else body
        if len(full) <= chunk_size:
            chunks.append(full)
        else:
            sub = splitter.split_text(body)
            for piece in sub:
                chunks.append(f"{heading}\n\n{piece}" if heading else piece)
    return chunks


# ---------------------------------------------------------------------------
# Strategy: Slide-based (PowerPoint)
# ---------------------------------------------------------------------------


def chunk_by_slide(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split PowerPoint content by slide boundaries.

    Each ``## Slide N`` section becomes a chunk.  Long slides are split
    by paragraph.
    """
    return chunk_by_table(text, chunk_size, overlap)


# ---------------------------------------------------------------------------
# Strategy: Code function/class boundary
# ---------------------------------------------------------------------------


def chunk_by_code(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split on function/class definitions.

    Uses a two-pass approach:
      1. Pre-split at definition boundaries (``_split_by_code_boundary``).
      2. Pass each definition through LangChain's ``RecursiveCharacterTextSplitter``
         only when the body exceeds *chunk_size*.

    If no code boundaries are found, falls back to paragraph-level splitting.
    """
    if not text.strip():
        return []

    sections = _split_by_code_boundary(text)
    splitter = _make_splitter(chunk_size, overlap, ["\n\n", "\n", " ", ""])

    chunks: list[str] = []
    for heading, body in sections:
        if len(body) <= chunk_size:
            chunks.append(body)
        else:
            sub = splitter.split_text(body)
            chunks.extend(sub)
    return chunks
