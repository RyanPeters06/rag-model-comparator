from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    source_file: str  # full absolute path — needed for image rendering
    page_number: int
    chunk_index: int

    @property
    def display_name(self) -> str:
        return Path(self.source_file).name


def extract_text_by_page(pdf_path: str) -> list[tuple[int, str]]:
    """Return list of (page_number, text) for every page in the PDF.

    Image-only pages get a placeholder so they still appear in the index
    and their images can be rendered and sent to vision models.
    """
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

    filename = Path(pdf_path).name
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        blocks_sorted = sorted(blocks, key=lambda b: (round(b[1] / 20), b[0]))
        page_text = "\n".join(b[4].strip() for b in blocks_sorted if b[4].strip())
        if page_text:
            results.append((page_num + 1, page_text))
        else:
            # Image-only page — placeholder lets it get indexed and its image retrieved
            placeholder = f"[Image page {page_num + 1} of {filename}]"
            results.append((page_num + 1, placeholder))
            logger.debug("Page %d of %s is image-only; using placeholder", page_num + 1, pdf_path)

    doc.close()
    return results


def render_page_as_base64(pdf_path: str, page_num: int, dpi: int = 96) -> str | None:
    """Render a PDF page as PNG and return the base64-encoded string.

    Falls back to searching INDEX_DIR if pdf_path is just a filename (old index format).
    """
    resolved = _resolve_pdf_path(pdf_path)
    if resolved is None:
        logger.warning("Cannot locate PDF for rendering: %s", pdf_path)
        return None
    try:
        import fitz
        doc = fitz.open(resolved)
        if page_num < 1 or page_num > len(doc):
            doc.close()
            return None
        page = doc[page_num - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        doc.close()
        return base64.b64encode(png_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning("Failed to render page %d of %s: %s", page_num, pdf_path, exc)
        return None


def _resolve_pdf_path(pdf_path: str) -> str | None:
    """Return an existing file path for the given pdf_path string.

    Handles old index entries that stored just a filename instead of a full path
    by searching INDEX_DIR as a fallback.
    """
    p = Path(pdf_path)
    if p.exists():
        return str(p)
    # Old index: bare filename — search INDEX_DIR
    if not p.is_absolute():
        from app.config import INDEX_DIR
        candidate = INDEX_DIR / p.name
        if candidate.exists():
            return str(candidate)
    return None


def chunk_text(
    pages: list[tuple[int, str]],
    source_file: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Split page text into overlapping word-level chunks."""
    chunks: list[Chunk] = []
    chunk_index = 0

    word_page_pairs: list[tuple[str, int]] = []
    for page_num, text in pages:
        for word in text.split():
            word_page_pairs.append((word, page_num))

    if not word_page_pairs:
        return chunks

    # Store full absolute path so image rendering can locate the file
    full_path = str(Path(source_file).resolve())
    step = chunk_size - overlap
    total_words = len(word_page_pairs)
    start = 0

    while start < total_words:
        end = min(start + chunk_size, total_words)
        segment = word_page_pairs[start:end]
        text = " ".join(w for w, _ in segment)
        page_num = segment[0][1]
        chunks.append(Chunk(
            text=text,
            source_file=full_path,
            page_number=page_num,
            chunk_index=chunk_index,
        ))
        chunk_index += 1
        if end == total_words:
            break
        start += step

    return chunks
