from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    source_file: str
    page_number: int
    chunk_index: int


def extract_text_by_page(pdf_path: str) -> list[tuple[int, str]]:
    """Return list of (page_number, text) for every page in the PDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("pymupdf is required: pip install pymupdf")

    results: list[tuple[int, str]] = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        logger.error("Failed to open PDF %s: %s", pdf_path, exc)
        return results

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Use blocks sorted by vertical position for multi-column handling
        blocks = page.get_text("blocks")
        blocks_sorted = sorted(blocks, key=lambda b: (round(b[1] / 20), b[0]))
        page_text = "\n".join(
            b[4].strip() for b in blocks_sorted if b[4].strip()
        )
        if page_text:
            results.append((page_num + 1, page_text))
        else:
            logger.debug("Page %d of %s has no extractable text (image-only?)", page_num + 1, pdf_path)

    doc.close()
    return results


def chunk_text(
    pages: list[tuple[int, str]],
    source_file: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split page text into overlapping word-level chunks."""
    chunks: list[Chunk] = []
    chunk_index = 0

    # Build a flat list of (word, page_number) pairs
    word_page_pairs: list[tuple[str, int]] = []
    for page_num, text in pages:
        for word in text.split():
            word_page_pairs.append((word, page_num))

    if not word_page_pairs:
        return chunks

    step = chunk_size - overlap
    total_words = len(word_page_pairs)
    start = 0

    while start < total_words:
        end = min(start + chunk_size, total_words)
        segment = word_page_pairs[start:end]
        text = " ".join(w for w, _ in segment)
        # Page number = the page of the first word in the chunk
        page_num = segment[0][1]
        chunks.append(Chunk(
            text=text,
            source_file=Path(source_file).name,
            page_number=page_num,
            chunk_index=chunk_index,
        ))
        chunk_index += 1
        if end == total_words:
            break
        start += step

    return chunks
